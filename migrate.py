from tinydb import TinyDB
from puzzles import Puzzle, PuzzleManager

db = TinyDB("old_solutions.json")
manager = PuzzleManager()

for entry in db.all():
    for property in ("first_solver", "first_solver_id", "first_solve_time"):
        if not entry[property]:
            entry[property] = None

    puzzle = Puzzle.from_import(entry)

    if entry["first_solver"] is None:
        manager.active_puzzles.append(puzzle)
    else:
        manager.solved_puzzles.append(puzzle)

manager.exit()
