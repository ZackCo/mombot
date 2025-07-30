import discord
from discord.ext import commands
from tinydb import TinyDB, Query

import shutil
import json
import re
import io
from pathlib import Path

import cryptocode as cr
import uuid
import util
from util import hash, obscure, unobscure

from datetime import datetime

from word2number import w2n

import util
import clueGenerator as cg
from puzzles import PuzzleManager

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
mom = commands.Bot(intents=intents, command_prefix="/")

# Load items
with open("items.json") as fp:
    items = json.load(fp)

# Credentials
credentialsPath = Path("credentials.json")
if not credentialsPath.exists():
    shutil.copy2("credentials_template.json", "credentials.json")

with open(credentialsPath) as fp:
    credentials: dict = json.load(fp)

token = credentials.get("token", "")
if not token or token == "REPLACE_WITH_TOKEN":
    print("Replace your token in credentials.json with your discord bot's token")
    exit()

test_guild = credentials.get("test", 0)
print(f"Using test guild value {test_guild}")

restrict_to_channel = credentials.get("restrict_to_channel", False)

# Set up db manager
puzzle_manager = PuzzleManager("solutions.json")

@mom.tree.command(name = "register")
async def register(interaction: discord.Interaction, name: str, solved_response: str, solution_string: str = None, solution_items_npc: str = None):
    """
    Register a new puzzle. Only use this in DMs! Please provide at least one solution text.
    
    Parameters
    ----------
    name: str
        A memorable name for your clue, that does not reveal anything not included in the clue.
    solved_response: str
        The text to respond with when the clue is solved. Perhaps an image link to another clue, or a simple gz.
    solution_string: 
        The solution string for your clue, i.e. "TINOREEGGSLOGS". Do not use if your clue is unordered.
    solution_items_npc:
        A comma-separated list of items and an NPC, i.e. "732 coins, 7 onions, sigismund". Please spell the items correctly, and end with an NPC or other hand-in location. Please note, if your hand-in is not an npc, the spelling cannot be validated.
    """
    if solved_response.count('\\n') > 3:
        await interaction.response.send_message("Please keep solutions under 4 messages long.")
        return

    try:
        sorted_items_npc = await sort_items_npc(solution_items_npc, ",", response=interaction.response)
    except ValueError:
        return
    
    exists = puzzle_manager.puzzle_exists(name)
    ownership = puzzle_manager.author_owns_puzzle(interaction.user.id, name)

    if ownership or not exists:
        puzzle_manager.update_puzzle(name, interaction.user.id, interaction.user.name, solution_string, sorted_items_npc, solved_response)
        await interaction.response.send_message(f"Updated puzzle: {name}" if exists else f"Registered new puzzle: {name}!")
        return
    
    await interaction.response.send_message(f"Another person already has a puzzle with this name, try again with a different one.")

@mom.tree.command(name = "delete")
async def list(interaction: discord.Interaction, name: str):
    """
    Delete my puzzle by name.
    """
    if not puzzle_manager.puzzle_exists(interaction.user.id, name):
        await interaction.response.send_message(f"No puzzle found with name: {name}.")
        return

    success = puzzle_manager.delete_puzzle(interaction.user.id, name)
    if success:
        await interaction.response.send_message(f"Successfully deleted puzzle: {name}")
    else:
        await interaction.response.send_message(f"Failed to delete puzzle: {name}")

@mom.tree.command(name = "list")
async def list(interaction: discord.Interaction):
    """
    List all my puzzles
    """
    author_puzzles = puzzle_manager.get_author_puzzles_status(interaction.user.id)
    if not author_puzzles:
        await interaction.response.send_message("You have no registered puzzles.")
        return
    
    await interaction.response.send_message(author_puzzles)

@mom.tree.command(name = "scroll")
async def scroll(interaction: discord.Interaction, clue_text: str, clue_scalar: float = 1.0):
    """
    Generate CTC looking scroll

    Parameters:
    ----------
    clue_text:
        Text to appear on your clue. Add new lines with "\n".
    clue_scalar: float
        A larger values reduces text size.
    """
    text_list = [clue_text] if "\\n" not in clue_text else clue_text.split("\\n")
    img = cg.generate_clue(text_list, scalar=clue_scalar) 
    await interaction.response.send_message(file=discord.File(img, filename=cg.generated_file_name))

@mom.tree.command(name = "solve")
async def solve(interaction: discord.Interaction, puzzle_name: str, solution: str):
    """
    Attempt to solve a puzzle

    Parameters:
    ----------
    puzzle_name:
        The name of the puzzle you are attempting to solve.
    solution: 
        Your suspected solution to the puzzle.
    """
    if interaction.guild and restrict_to_channel and interaction.channel.id != restrict_to_channel:
        return
    
    if not puzzle_manager.puzzle_exists(puzzle_name):
        interaction.message.add_reaction("❔")
        return
    
    if not re.search(r"[^A-Z0-9]", solution) and len(solution) >= 10:
        clean_solution = util.hash(util.clean(solution))
        await update_solution(interaction, puzzle_name, clean_solution)
        return
    
    for delimeter in (",", "\n"):
        if solution.count(delimeter) > 0:
            clean_solution = await sort_items_npc(solution, delimeter)
            await update_solution(interaction, puzzle_name, clean_solution)

@mom.tree.command(name = "sync")
async def sync(interaction: discord.Interaction):
    if not mom.is_owner(interaction.message.author):
        return
    
    guild = mom.get_guild(test_guild)
    if guild is not None:
        mom.tree.copy_global_to(guild=guild)
    
    await mom.tree.sync()
    print("Synced commands to " + str(guild))
    await interaction.message.add_reaction("🔁")

async def update_solution(interaction: discord.Interaction, puzzle_name: str, solution: str):
    success = puzzle_manager.check_solution(puzzle_name, solution)
    if not success:
        await interaction.message.add_reaction("❌")
        return

    await interaction.message.add_reaction("✅")
    if puzzle_manager.get_author_id(puzzle_name) == interaction.message.author.id or puzzle_manager.is_solved(puzzle_name): # Author solved puzzle or is already solved
        return
    
    solution_message = puzzle_manager.solved(puzzle_name, solution, interaction.message.author.name, interaction.message.author.id)
    for line in solution_message:
        interaction.message.reply(line)

# Parse and sort a list of items so order doesn't matter
async def sort_items_npc(text: str, delimeter: str, message: str = None, response: str = None):
    if not text:
        return

    elements = [re.sub(r'\s+', ' ', m) for m in text.split(delimeter)]
    handin = util.clean(elements[len(elements) - 1])

    res = []

    # Create a list with number of items and item name
    for el in elements[:-1]:
        frags =  el.strip().split(" ", 1)
        possible_number = frags[0]
        try:
            n = w2n.word_to_num(possible_number)
            res.append({
                "quantity" : n,
                "item_name" : util.clean(frags[1])
            })
        except (ValueError, IndexError):
            res.append({
                "quantity" : 1,
                "item_name" : util.clean(el)
            })
    
    found_items = []
    unknown_items = []
    for possible_item in res:
        name = possible_item["item_name"]
        try:
            found_item_id = items[name]
            found_items.append({
                "id": found_item_id,
                "item_name": name,
                "quantity": possible_item["quantity"]
            })
        except KeyError:
            # Then try with singular
            if name[-1:] != 'S':
                unknown_items.append(possible_item)
            else:
                singular_name = name[:-1]
                try:
                    found_item_id = items[singular_name]
                    found_items.append({
                        "id": found_item_id,
                        "item_name": singular_name,
                        "quantity": possible_item["quantity"]
                    })
                except KeyError:
                    unknown_items.append(possible_item)

    if len(found_items) == 0:
        return
    
    if len(unknown_items) > 0 and len(found_items) > 0:
        if message and message.guild:
            if message:
                await message.add_reaction("❔")
            return
        else:
            unknowns = ', '.join([f'{str(u["quantity"])} {u["item_name"]}' for u in unknown_items])
            if message:
                await message.reply(f"Unknown items: {unknowns}")
            else:
                await response.send_message(f"Unknown items: {unknowns}")
                # Only throw error if we are registering.
                raise ValueError("Item not found.")
            return
        
    #TODO verify handin
        
    if len(unknown_items) == 0 and len(found_items) > 0:
        sorted_items = sorted(found_items, key=lambda i:int(i["id"]))
        result = "-".join([f"{si['quantity']}{si['item_name']}" for si in sorted_items]) + "--" + handin
        return result
    
    return

# def migrate():
#     q = Query()
#     res = solutions.all()
#     print(solutions)
#     for r in res:
#         name = r['name']
#         ob = obscure(name)
#         solutions.update({'name': ob}, q.name == name)

def main():
    # migrate()
    print(f"Running with token {token[:3]}...")
    mom.run(token)

if __name__ == "__main__":
    main()
