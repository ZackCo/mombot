from uuid import uuid4
from pathlib import Path
import cryptocode as cr
import pickle
from datetime import datetime
import util

class PuzzleManager:
    def __init__(self, saveDataFile: str = "solutions.pickle") -> 'PuzzleManager':
        self.saveDataFilePath = Path(saveDataFile)
        self._load()

    def exit(self) -> None:
        self._save()

    def _load(self, file_path: Path) -> list['Puzzle']:
        if not file_path.exists():
            self.puzzle_queue = []
            self.solved_puzzles = []
        
        with open(file_path, "rb") as fp:
            data = pickle.load(fp)

        self.puzzle_queue = data["puzzle_queue"]
        self.solved_puzzles = data["solved_puzzles"]

    def _save(self) -> None:
        data = {
            "puzzle_queue": self.puzzle_queue,
            "solved_puzzles": self.solved_puzzles
        }

        with open(self.saveDataFilePath, "wb") as fp:
            pickle.dump(data, fp)

    def check_matching_hashes(self, newPuzzle: 'Puzzle') -> bool:
        for puzzle in self.puzzle_queue:
            if puzzle.same_solution(newPuzzle):
                return True
        return False
    
    def get_author_puzzles(self, author_id: int, name_match: str = "") -> list['Puzzle']:
        matches = []
        for puzzle in self.solved_puzzles + self.puzzle_queue:
            if author_id != puzzle.author_id:
                continue
            
            if not name_match or name_match == puzzle.name:
                matches.append(puzzle)

        return matches
    
    def get_solution_matches(self, unhashedContent: str, matchsolution_string: bool) -> 'Puzzle':
        hashedContent = util.hash(unhashedContent)
        for puzzle in self.puzzle_queue:
            if puzzle.check_solution(hashedContent, matchsolution_string):
                return puzzle

        return None
    
    def register(self, newPuzzle: 'Puzzle') -> int:
        self.puzzle_queue.append(newPuzzle)
        self._save()
        return len(self.puzzle_queue)
    
    def update(self, old_puzzle: 'Puzzle', new_puzzle: 'Puzzle') -> None:
        replace_index = self.puzzle_queue.index(old_puzzle)
        self.puzzle_queue[replace_index] = new_puzzle
        self._save()
    
    def delete(self, puzzle: 'Puzzle') -> bool:
        if puzzle not in self.puzzle_queue: # Can only delete active puzzles, not solved ones
            return False
        
        self.puzzle_queue.remove(puzzle)
        self._save()
        return True
    
    def solved(self, puzzle: 'Puzzle', author_name: str, author_id: int) -> None:
        solve_index = self.puzzle_queue.index(puzzle)
        solved_puzzle = self.puzzle_queue.pop(solve_index)
        solved_puzzle.solved(author_name, author_id)
        self.solved_puzzles.append(solved_puzzle)
        self._save()

class Puzzle:
    def __init__(self, name: str, author_id: int, author_name: str, solution_string: str, sorted_items_npc: str, solved_response: str) -> 'Puzzle':
        self.name = name
        self.author_id = author_id
        self.author_name = author_name

        # Do this so you can't tell if an entry has a string, items, or both.
        solution_string = solution_string or uuid4().hex
        sorted_items_npc = sorted_items_npc or uuid4().hex

        self.hashed_solution_string = util.hash(solution_string)
        self.hashed_solution_items = util.hash(sorted_items_npc)

        self.solved_response = solved_response
        self.secret_string = cr.encrypt(solved_response, solution_string)
        self.secret_items = cr.encrypt(solved_response, sorted_items_npc)

        self.first_solver = None
        self.first_solver_id = None
        self.first_solve_time = None

    def __str__(self):
        solve_state = "Unsolved" if self.first_solver is None else f"First solved by: {self.first_solver}"
        return f"{self.name} - {solve_state}"

    def same_solution(self, other: 'Puzzle') -> bool:
        if type(self) != type(other):
            raise TypeError
        
        return self.hashed_solution_string == other.hashed_solution_string and self.hashed_solution_items == other.hashed_solution_items

    def check_solution(self, hashed_content: int, matchsolution_string: bool) -> bool:
        if matchsolution_string:
            return hashed_content == self.hashed_solution_string
        return hashed_content == self.hashed_solution_items
    
    def decrypt(self, key: str) -> str:
        return cr.decrypt(self.secret_string, key).split("\\n")

    def solved(self, author_name: str, author_id: int):
        self.first_solver = author_name
        self.first_solver_id = author_id
        self.first_solve_time = datetime.now.isoformat()
