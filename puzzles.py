from uuid import uuid4
from pathlib import Path
import cryptocode as cr
import json
from datetime import datetime, timezone
import util

from tinydb import TinyDB, Query
from tinydb.table import Document

class PuzzleManager:
    def __init__(self, save_data_file: str):
        self._db = TinyDB(save_data_file)
        self._query = Query()

    def _get_solve_status(self, puzzle: Document) -> str:
        if not puzzle.first_solver:
            return "Unsolved"
        
        return f"First solved by {puzzle.first_solver} at {puzzle.first_solve_time}"

    def puzzle_exists(self, name: str) -> bool:
        return bool(self._db.search(self._query.name == name)) # Empty list casts to False, otherwise True

    def update_puzzle(self, name: str, author_id: int, author_name: str, solution_string: str, sorted_items_npc: str, solved_response: str) -> None:
        solution_string = solution_string or uuid4().hex
        sorted_items_npc = sorted_items_npc or uuid4().hex

        puzzle_ids = self._db.upsert(
            {
                "name": util.obscure(name),
                "author_id": author_id,
                "author_name": author_name,
                "hashed_solution_str": util.hash(solution_string),
                "hashed_solution_items": util.hash(sorted_items_npc),
                "secret_string": cr.encrypt(solved_response, solution_string),
                "secret_items": cr.encrypt(solved_response, sorted_items_npc),
                "first_solver": "",
                "first_solver_id": -1,
                "first_solver_time": ""
            }
        ) # Creates the entry if it doesn't exist

    def delete_puzzle(self, author_id: int, name: str) -> bool:
        return bool(self._db.remove((self._query.author_id == author_id) & (self._query.name == name))) # Empty list casts to False, otherwise True

    def get_author_puzzles_status(self, author_id: int) -> str:
        author_puzzles = self._db.search(self._query.author_id == author_id)
        if not author_puzzles:
            return ""
        
        return "\n".join(f"{puzzle.name} - {self._get_solve_status(puzzle)}" for puzzle in author_puzzles)

    def get_author_id(self, name: str) -> int:
        return self._db.search(self._query.name == name)[0].author_id

    def check_solution(self, name: str, solution: str) -> bool:
        return bool(self._db.search((self._query.name == name) & (self._query.hashed_solution_str == solution)))

    def is_solved(self, name: str) -> bool:
        return self._db.search((self._query.name == name) & (self._query.first_solver_id >= 0))

    def solved(self, name: str, solution: str, author: str, author_id: int) -> list[str]:
        solved_puzzle = self._db.update({"first_solver": author, "first_solver_id": author_id, "first_solve_time" : datetime.now().isoformat()}, self._query.name == name)[0]
        response = cr.decrypt(solved_puzzle.secret_string, solution)
        return response.split("\n")
