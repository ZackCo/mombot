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
    
    def register_puzzle(self, name: str, author_id: int, author_name: str, solution_string: str, sorted_items_npc: str, solved_response: str) -> None:
        solution_string = solution_string or uuid4().hex
        sorted_items_npc = sorted_items_npc or uuid4().hex

        puzzle_id = self._db.insert({
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
        })

    def _get_author_puzzles(self, author_id: int) -> dict[str, Document]:
        return {puzzle.name: puzzle for puzzle in self._db.search(self._query.author_id == author_id)}
    
    def _get_solve_status(self, puzzle: Document) -> str:
        if not puzzle.first_solver:
            return "Unsolved"
        
        return f"First solved by {puzzle.first_solver} at {puzzle.first_solve_time}"
    
    def _create_puzzle(self, name: str, author_id: int, author_name: str, solution_string: str, sorted_items_npc: str, solved_response: str) -> dict:
        pass

    def puzzle_exists(self, author_id: int, name: str) -> bool:
        return name in self._get_author_puzzles(author_id)

    def get_author_puzzles_status(self, author_id: int) -> list[str]:
        author_puzzles = self._get_author_puzzles(author_id)
        return [f"{puzzle_name} - {self._get_solve_status(puzzle)}" for puzzle_name, puzzle in author_puzzles]

    def delete_puzzle(self, author_id: int, name: str) -> bool:
        return len(self._db.remove((self._query.author_id == author_id) & (self._query.name == name))) > 0

    def update(self, author_id: int, name: str, ) -> None:
        replace_index = self.active_puzzles.index(old_puzzle)
        self.active_puzzles[replace_index] = new_puzzle
        self._save()
    
    def solved(self, puzzle: 'Puzzle', author_name: str, author_id: int) -> None:
        solve_index = self.active_puzzles.index(puzzle)
        solved_puzzle = self.active_puzzles.pop(solve_index)
        solved_puzzle.solved(author_name, author_id)
        self.solved_puzzles.append(solved_puzzle)
        self._save()
