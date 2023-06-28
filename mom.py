import discord
from discord.ext import commands

import shutil
import json
import re
from pathlib import Path

import cryptocode as cr
from word2number import w2n

import util
from puzzles import PuzzleManager, Puzzle

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
mom = commands.Bot(intents=intents, command_prefix="/")

puzzleManager = PuzzleManager()

# Load items
with open("items.json") as fp:
    items = json.load(fp)

# Credentials
credentialsPath = Path("credentials.json")
if not credentialsPath.exists():
    shutil.copy2("credentials_template.json", "credentials.json")

with open(credentialsPath) as fp:
    credentials = json.load(fp)

token = credentials.get("token", "")
if not token or token == "REPLACE_WITH_TOKEN":
    print("Replace your token in credentials.json with your discord bot's token")
    exit()

test_guild = credentials.get("test", 0)
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
    try:
        sorted_items_npc = await sort_items_npc(solution_items_npc, ",", response=interaction.response)
    except ValueError:
        return
    
    puzzle = Puzzle(name, interaction.user.id, interaction.user.name, solution_string, sorted_items_npc, solved_response)

    if puzzleManager.checkMatchingHashes(puzzle):
        await interaction.response.send_message(f"Solution {puzzle.name} already exists. Either update your previous puzzle, or choose a more complex solution.")
        return
    
    queuePos = puzzleManager.register(puzzle)
    suffix = {
        1: "st",
        2: "nd",
        3: "rd"
    }

    await interaction.response.send_message(f"Registered {puzzle.name}, it is {suffix.get(queuePos, 'th')} in queue!")

@mom.tree.command(name = "list")
async def list(interaction: discord.Interaction):
    """
    List all my puzzles
    """
    authorPuzzles = puzzleManager.getOwnerPuzzles(interaction.user.id)
    if not authorPuzzles:
        await interaction.response.send_message("No clues found.")
        return
    
    await interaction.response.send_message("\n".join(str(puzzle) for puzzle in authorPuzzles))

@mom.tree.command(name = "delete")
async def delete(interaction: discord.Interaction, name: str):
    """
    Delete my puzzle by name.
    """
    foundPuzzles = puzzleManager.getOwnerPuzzles(interaction.user.id, name)
    if not foundPuzzles:
        await interaction.response.send_message(f"No clue found with name {name}.")
        return
    
    for puzzle in foundPuzzles:
        success = puzzleManager.delete(puzzle)
        if success:
            await interaction.response.send_message(f"Deleted puzzle: {puzzle.name}.")
        else:
            await interaction.response.send_message(f"Failed to delete puzzle: {puzzle.name}.")

@mom.listen('on_message')
async def listen_for_message(message: discord.Message):
    content = discord.utils.remove_markdown(message.content)

    # Check if "sync" command was used
    if content == "sync" and await mom.is_owner(message.author):
        await sync(message)
        return
    
    # Message is all uppercase and numbers
    if len(content) >= 10 and not re.search(r"[^A-Z0-9]", content):
        content = util.clean(message.content)
        await try_solution(message, content)
        return
    
    for delimeter in (",", "\n"):
        if content.count(delimeter) <= 0:
            continue

        splitContent = await sort_items_npc(content, delimeter, message=message)
        await try_solution(message, splitContent)

async def try_solution(message: discord.Message, cleanedContent: str, matchSolutionHash: bool):
    solutionMatch = puzzleManager.getSolutionmatches(cleanedContent, matchSolutionHash)
    if solutionMatch is None:
        await message.add_reaction("❌")
        return
    
    if solutionMatch.authorID == message.author.id:
        await message.add_reaction(":interrobang:") # Solved their own puzzle?
        return
    
    await message.add_reaction("✅")
    await message.reply(cr.decrypt(solutionMatch.secretString, cleanedContent))
    puzzleManager.solved(solutionMatch)
    
async def sync(message: discord.Message):
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
    handin = util.clean(elements[:-1])

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
        except ValueError:
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
    mom.run(token)

if __name__ == "__main__":
    main()
