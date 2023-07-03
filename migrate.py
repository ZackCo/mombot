from tinydb import TinyDB
from puzzles import Puzzle, PuzzleManager

db = TinyDB("solutions.json")
manager = PuzzleManager()

for entry in db.all():
    name = entry.get("name", "")
    author_id = entry.get("author_id", "")
    author_name = entry.get("author_name", "")
    hashed_solution_string = entry.get("hashed_solution_string", "")
    hashed_solution_items = entry.get("hashed_solution_items", "")
    secret_string = entry.get("secret_string", "")
    secret_items = entry.get("secret_items", "")
    first_solver = entry.get("first_solver", "")
    first_solver_id = entry.get("first_solver_id", "")
    first_solve_time = entry.get("first_solve_time", "")

    blank_puzzle = Puzzle(name, author_id, author_name, "", "", "")
    blank_puzzle.hashed_solution_string = hashed_solution_string
    blank_puzzle.hashed_solution_items = hashed_solution_items
    blank_puzzle.secret_string = secret_string
    blank_puzzle.secret_items = secret_items

    blank_puzzle.first_solver = first_solver if first_solver else None
    blank_puzzle.first_solver_id = first_solver_id if first_solver_id else None
    blank_puzzle.first_solve_time = first_solve_time if first_solve_time else None

    if first_solver:
        manager.solved_puzzles.append(blank_puzzle)
    else:
        manager.active_puzzles.append(blank_puzzle)

manager.exit()
