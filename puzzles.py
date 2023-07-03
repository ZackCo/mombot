from uuid import uuid4
from pathlib import Path
import cryptocode as cr
import json
from datetime import datetime
import util

class PuzzleManager:
    def __init__(self, save_data_file: str = "saved_data.json") -> 'PuzzleManager':
        self.save_data_file_path = Path(save_data_file)
        self._load()

    def exit(self) -> None:
        self._save()

    def _load(self) -> list['Puzzle']:
        if not self.save_data_file_path.exists():
            self.active_puzzles = []
            self.solved_puzzles = []
            return
        
        with open(self.save_data_file_path) as fp:
            data = json.load(fp)

        self.active_puzzles = [Puzzle.from_import(puzzle_data) for puzzle_data in data["active_puzzles"]]
        self.solved_puzzles = [Puzzle.from_import(puzzle_data) for puzzle_data in data["solved_puzzles"]]

    def _save(self) -> None:
        data = {
            "active_puzzles": [puzzle.export() for puzzle in self.active_puzzles],
            "solved_puzzles": [puzzle.export() for puzzle in self.solved_puzzles]
        }

        with open(self.save_data_file_path, "w") as fp:
            json.dump(data, fp)

    def check_matching_hashes(self, newPuzzle: 'Puzzle') -> bool:
        for puzzle in self.active_puzzles:
            if puzzle.same_solution(newPuzzle):
                return True
        return False
    
    def get_author_puzzles(self, author_id: int, name_match: str = "") -> list['Puzzle']:
        matches = []
        for puzzle in self.solved_puzzles + self.active_puzzles:
            if author_id != puzzle.author_id:
                continue
            
            if not name_match or name_match == puzzle.name:
                matches.append(puzzle)

        return matches
    
    def get_solution_matches(self, unhashedContent: str, matchsolution_string: bool) -> 'Puzzle':
        hashedContent = util.hash(unhashedContent)
        for puzzle in self.active_puzzles:
            if puzzle.check_solution(hashedContent, matchsolution_string):
                return puzzle

        return None
    
    def register(self, newPuzzle: 'Puzzle') -> None:
        self.active_puzzles.append(newPuzzle)
        self._save()
    
    def update(self, old_puzzle: 'Puzzle', new_puzzle: 'Puzzle') -> None:
        replace_index = self.active_puzzles.index(old_puzzle)
        self.active_puzzles[replace_index] = new_puzzle
        self._save()
    
    def delete(self, puzzle: 'Puzzle') -> bool:
        if puzzle not in self.active_puzzles: # Can only delete active puzzles, not solved ones
            return False
        
        self.active_puzzles.remove(puzzle)
        self._save()
        return True
    
    def solved(self, puzzle: 'Puzzle', author_name: str, author_id: int) -> None:
        solve_index = self.active_puzzles.index(puzzle)
        solved_puzzle = self.active_puzzles.pop(solve_index)
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

        self.secret_string = cr.encrypt(solved_response, solution_string)
        self.secret_items = cr.encrypt(solved_response, sorted_items_npc)

        self.first_solver = None
        self.first_solver_id = None
        self.first_solve_time = None

    @classmethod
    def from_import(cls, properties: dict) -> None:
        basic_class = cls("", 0, "", "", "", "")

        for key, value in properties.items():
            if not hasattr(basic_class, key): # Check attribute exists in object, only load known attributes
                continue
            
            if key == "name":
                value = util.unobscure(value)

            setattr(basic_class, key, value)
        
        return basic_class

    def export(self) -> dict:
        properties = vars(self)
        properties["name"] = util.obscure(properties["name"])
        return properties
    
    def get_solve_status(self) -> str:
        return "Unsolved" if self.first_solver is None else f"First solved by: {self.first_solver}"

    def same_solution(self, other: 'Puzzle') -> bool:
        if type(self) != type(other):
            raise TypeError
        
        return self.hashed_solution_string == other.hashed_solution_string and self.hashed_solution_items == other.hashed_solution_items

    def check_solution(self, hashed_content: int, match_solution_string: bool) -> bool:
        if match_solution_string:
            return hashed_content == self.hashed_solution_string
        return hashed_content == self.hashed_solution_items
    
    def decrypt(self, key: str) -> str:
        return cr.decrypt(self.secret_string, key).split("\\n")

    def solved(self, author_name: str, author_id: int):
        self.first_solver = author_name
        self.first_solver_id = author_id
        self.first_solve_time = datetime.now.isoformat()
