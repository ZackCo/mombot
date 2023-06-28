from uuid import uuid4
from pathlib import Path
import cryptocode as cr
import pickle
from datetime import datetime

class PuzzleManager:
    def __init__(self, solvedPuzzlesFile: str = "solvedPuzzles.pickle", activePuzzlesFile: str = "activePuzzles.pickle") -> 'PuzzleManager':
        self.solvedPuzzlesPath = Path(solvedPuzzlesFile)
        self.activePuzzlesPath = Path(activePuzzlesFile)

        self.solvedPuzzles = self._load(self.solvedPuzzlesPath)
        self.puzzleQueue = self._load(self.activePuzzlesPath)

    def exit(self) -> None:
        self._save()

    def _load(self, filePath: Path) -> list['Puzzle']:
        if not filePath.exists():
            return []
        
        with open(filePath, "rb") as fp:
            return pickle.load(fp)

    def _save(self) -> None:
        with open(self.solvedPuzzlesPath, "wb") as fp:
            pickle.dump(self.solvedPuzzles, fp)

        with open(self.activePuzzlesPath, "wb") as fp:
            pickle.dump(self.puzzleQueue, fp)

    def checkMatchingHashes(self, newPuzzle: 'Puzzle') -> bool:
        for puzzle in self.puzzleQueue:
            if puzzle.sameSolution(newPuzzle):
                return True
        return False
    
    def getAuthorPuzzles(self, authorID: int, nameMatch: str = "") -> list['Puzzle']:
        matches = []
        for puzzle in self.solvedPuzzles + self.puzzleQueue:
            if authorID != puzzle.authorID:
                continue
            
            if not nameMatch or nameMatch == puzzle.name:
                matches.append(puzzle)

        return matches
    
    def getSolutionmatches(self, unhashedContent: str, matchSolutionString: bool) -> 'Puzzle':
        hashedContent = hash(unhashedContent)
        for puzzle in self.puzzleQueue:
            if puzzle.checkSolution(hashedContent, matchSolutionString):
                return puzzle

        return None
    
    def register(self, newPuzzle: 'Puzzle') -> int:
        self.puzzleQueue.append(newPuzzle)
        self._save()
        return len(self.puzzleQueue)
    
    def delete(self, puzzle: 'Puzzle') -> bool:
        if puzzle not in self.puzzleQueue: # Can only delete active puzzles, not solved ones
            return False
        
        self.puzzleQueue.remove(puzzle)
        self._save()
        return True
    
    def solved(self, puzzle: 'Puzzle', authorName: str, authorID: int) -> None:
        solveIndex = self.puzzleQueue.index(puzzle)
        solvedPuzzle = self.puzzleQueue.pop(solveIndex)
        solvedPuzzle.solved(authorName, authorID)
        self.solvedPuzzles.append(solvedPuzzle)
        self._save()

class Puzzle:
    def __init__(self, name: str, authorID: int, authorName: str, solutionString: str, sortedItemsNPC: str, solvedResponse: str) -> 'Puzzle':
        self.name = name
        self.authorID = authorID
        self.authorName = authorName

        # Do this so you can't tell if an entry has a string, items, or both.
        self.solutionString = solutionString or uuid4().hex
        self.sortedItemsNPC = sortedItemsNPC or uuid4().hex

        print(f"Saving puzzle with solns {solutionString} and {sortedItemsNPC}")

        self.hashedSolutionString = hash(self.solutionString)
        self.hashedSolutionItems = hash(self.sortedItemsNPC)

        self.solvedResponse = solvedResponse
        self.secretString = cr.encrypt(solvedResponse, self.solutionString)
        self.secretItems = cr.encrypt(solvedResponse, self.sortedItemsNPC)

        self.firstSolver = None
        self.firstSolverID = None
        self.firstSolveTime = None

    def __str__(self):
        solveState = "Unsolved" if self.firstSolver is None else f"First solved by: {self.firstSolver}"
        return f"{self.name} - {solveState}"

    def sameSolution(self, other: 'Puzzle') -> bool:
        if type(self) != type(other):
            raise TypeError
        
        return self.hashedSolutionString == other.hashedSolutionString and self.hashedSolutionItems == other.hashedSolutionItems

    def checkSolution(self, hashedContent: int, matchSolutionString: bool) -> bool:
        if matchSolutionString:
            print(f"Str received: {hashedContent}, actual: {self.hashedSolutionString}")
            return hashedContent == self.hashedSolutionString
        print(f"Items received: {hashedContent}, actual: {self.hashedSolutionItems}")
        return hashedContent == self.hashedSolutionItems
    
    def solved(self, authorName: str, authorID: int):
        self.firstSolver = authorName
        self.firstSolverID = authorID
        self.firstSolveTime = datetime.now.isoformat()
