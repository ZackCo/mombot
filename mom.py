import discord
from discord.ext import commands

import shutil
import json
import re
import io
from pathlib import Path

from word2number import w2n

import util
from puzzles import PuzzleManager, Puzzle

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
mom = commands.Bot(intents=intents, command_prefix="/")

puzzle_manager = PuzzleManager()

# Clue Generation Properties
blank_clue_path = Path("assets/blank_clue.png")
font_path = Path("assets/RuneScape-Chat-07.ttf")
generated_clue_name = "generated_clue.png"

clue_generator = ClueGenerator(blank_clue_path, font_path, generated_clue_name)

# Load items
with open("items.json") as fp:
    items = json.load(fp)

# Credentials
credentials_path = Path("credentials.json")
if not credentials_path.exists():
    shutil.copy2("credentials_template.json", "credentials.json")

with open(credentials_path) as fp:
    credentials = json.load(fp)

token = credentials.get("token", "")
if not token or token == "REPLACE_WITH_TOKEN":
    print("Replace your token in credentials.json with your discord bot's token")
    exit()

test_guild = credentials.get("test_guild", 0)
print(f"Using test guild value {test_guild}")

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
    if solved_response.count('\n') > 3:
        await interaction.response.send_message("Please keep solutions under 4 messages long.")
        return
    
    try:
        sorted_items_npc = await sort_items_npc(solution_items_npc, ",", response=interaction.response)
    except ValueError:
        return
    
    puzzle = Puzzle(name, interaction.user.id, interaction.user.name, solution_string, sorted_items_npc, solved_response)
    
    # Check for matching puzzles for updating
    author_matching_puzzles = puzzle_manager.get_author_puzzles(interaction.user.id, puzzle.name)
    if author_matching_puzzles:
        puzzle_manager.update(author_matching_puzzles[0], puzzle) # List should be 1 long since puzzle names are unique
        await interaction.response.send_message(f"Updated {puzzle.name}!")
        return

    # Check for existing puzzle solutions
    if puzzle_manager.check_matching_hashes(puzzle):
        await interaction.response.send_message(f"Solution {puzzle.name} already exists. Either update your previous puzzle, or choose a more complex solution.")
        return
    
    queue_pos = puzzle_manager.register(puzzle)
    suffix = {
        1: "st",
        2: "nd",
        3: "rd"
    }

    await interaction.response.send_message(f"Registered {puzzle.name}, it is {queue_pos}{suffix.get(queue_pos, 'th')} in queue!")

@mom.tree.command(name = "list")
async def list(interaction: discord.Interaction):
    """
    List all my puzzles
    """
    author_puzzles = puzzle_manager.get_author_puzzles(interaction.user.id)
    if not author_puzzles:
        await interaction.response.send_message("No clues found.")
        return
    
    await interaction.response.send_message("\n".join(str(puzzle) for puzzle in author_puzzles))

@mom.tree.command(name = "delete")
async def delete(interaction: discord.Interaction, name: str):
    """
    Delete my puzzle by name.
    """
    found_puzzles = puzzle_manager.get_author_puzzles(interaction.user.id, name)
    if not found_puzzles:
        await interaction.response.send_message(f"No clue found with name {name}.")
        return
    
    for puzzle in found_puzzles:
        success = puzzle_manager.delete(puzzle)
        if success:
            await interaction.response.send_message(f"Deleted puzzle: {puzzle.name}.")
        else:
            await interaction.response.send_message(f"Failed to delete puzzle: {puzzle.name}.")

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
    img = clue_generator.generate_clue(text_list, scalar=clue_scalar) 
    await interaction.response.send_message(file=discord.File(img, filename=generated_clue_name))
    
@mom.listen('on_message')
async def listen_for_message(message: discord.Message):
    content = discord.utils.remove_markdown(message.content)

    # Ignore messages from ourself
    if message.author.id == mom.user.id:
        return

    # Check if "sync" command was used and run by bot owner
    if content == "sync" and await mom.is_owner(message.author):
        await sync(message)
        return
    
    # Message is all uppercase and numbers
    if len(content) >= 10 and not re.search(r"[^A-Z0-9]", content):
        content = util.clean(message.content)
        await try_solution(message, content, True)
        return
    
    for delimeter in (",", "\n"):
        if content.count(delimeter) <= 0:
            continue

        try:
            split_content = await sort_items_npc(content, delimeter, message=message)
        except ValueError:
            return
        
        await try_solution(message, split_content, False)

async def try_solution(message: discord.Message, cleanedContent: str, matchSolutionString: bool):
    solution_match = puzzle_manager.get_solution_matches(cleanedContent, matchSolutionString)
    if solution_match is None:
        await message.add_reaction("❌")
        return
    
    if solution_match.authorID == message.author.id:
        await message.add_reaction("⭐") # Solved their own puzzle?
        return
    
    await message.add_reaction("✅")

    solve_messages = solution_match.decrypt(cleanedContent)
    for solveMsg in solve_messages:
        await message.reply(solveMsg)

    puzzle_manager.solved(solution_match, message.author.name, message.author.id)
    
async def sync(message: discord.Message):
    print(message.guild)
    guild = mom.get_guild(test_guild)
    if guild != None:
        mom.tree.copy_global_to(guild=guild)
    await mom.tree.sync()
    print("Synced commands to " + str(guild))
    await message.add_reaction("🔁")
    
# Parse and sort a list of items so order doesn't matter
async def sort_items_npc(text: str, delimeter: str, message: str = None, response: str = None):
    if not text:
        return

    elements = [re.sub(r'\s+', ' ', m) for m in text.split(delimeter)]
    handin = util.clean(elements[-1])

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

def main():
    print(f"Running with token {token[:3]}...")
    try:
        mom.run(token)
    except KeyboardInterrupt:
        puzzle_manager.exit()

if __name__ == "__main__":
    main()
