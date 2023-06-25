import discord
from discord import app_commands
from discord.ext.commands import dm_only
from discord.ext import commands

from tinydb import TinyDB, Query

import shutil
import json
import re

import hashlib
import cryptocode as cr
import uuid

from datetime import datetime

from word2number import w2n

test_guild = 0
token = ""
solutions = TinyDB("solutions.json")
items = json.load(open("items.json"))

try:
    with open("credentials.json") as c:
        credentials = json.load(c)
        token = credentials["token"]
        if token == "REPLACE_WITH_TOKEN":
            print("Replace your token in credentials.json with your discord bot's token")
        print(f"Running with token {token[0:3]}...")
        print(credentials["test_guild"])
        if credentials["test_guild"]:
            test_guild = credentials["test_guild"]
except IOError:
    shutil.copy2("credentials_template.json", "credentials.json")

# Clue logic below

# Hash a string
def hash(s):
    if s == None:
        return ""
    return hashlib.sha256(clean(s).encode("UTF-8")).hexdigest()

def clean(s):
    if s == None:
        return ""
    return s.replace(" ", "").upper()

# Discord stuff below

intents = discord.Intents.default()
intents.message_content = True

mom = commands.Bot(intents=intents, command_prefix="/")

# @mom.event
# async def on_interaction(interaction):
#     print(interaction)

@mom.tree.command(name = "register")
async def register(interaction, name:str, solved_response:str, solution_string:str = None, solution_items_npc:str = None):
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
    #TODO: Check valid
    try:
        sorted_items_npc = await sort_items_npc(solution_items_npc, ",", response=interaction.response)
    except ValueError:
        return

    # Do this so you can't tell if an entry has a string, items, or both.
    solution_string = solution_string or uuid.uuid4().hex
    sorted_items_npc = sorted_items_npc or uuid.uuid4().hex

    print(sorted_items_npc)

    solutions.insert({
        "name" : name,
        "author_id" : interaction.user.id,
        "author_name" : interaction.user.name,
        "hashed_solution_string" : hash(solution_string),
        "hashed_solution_items" : hash(sorted_items_npc),
        "secret_string" : cr.encrypt(solved_response, solution_string),
        "secret_items" : cr.encrypt(solved_response, sorted_items_npc),
        "first_solver" : "",
        "first_solver_id" : "",
        "first_solve_time" : ""
    })
    await interaction.response.send_message(f"Registered {name}!")

@mom.tree.command(name = "list")
async def list(interaction):
    """
    List all my puzzles
    """
    await interaction.response.send_message("fds")

@mom.listen('on_message')
async def listen_for_message(message):
    content = discord.utils.remove_markdown(message.content)

    if content == "sync" and await mom.is_owner(message.author):
        await sync(message)
        return
    
    if not re.search(r"[^A-Z0-9]", content):
        await try_solution_string(message)
        return
    
    if content.count(",") > 0:
        await try_solution_items(message, ",")

    if content.count("\n") > 0:
        await try_solution_items(message, "\n")


async def sync(message):
    guild = mom.get_guild(test_guild)
    if guild != None:
        mom.tree.copy_global_to(guild=guild)
    await mom.tree.sync()
    print("Synced commands to " + str(guild))
    await message.add_reaction("🔁")

async def try_solution_string(message):
    content = clean(message.content)
    
    h = hash(content)
    q = Query()
    result = solutions.search(q.hashed_solution_string == h)

    if len(result) > 0:
        res = result[0]
        await message.add_reaction("✅")
        await message.reply(cr.decrypt(res["secret_string"], content))
        if message.author.id != res["author_id"] and res["first_solver"] == "":
            solutions.update({
                "first_solver" : message.author.name,
                "first_solver_id" : message.author.id,
                "first_solve_time" : datetime.now().isoformat()
            }, q.hashed_solution_string == h)
        return
    else:
        await message.add_reaction("❌")
        return
    
# Parse and sort a list of items so order doesn't matter
async def sort_items_npc(text, delimeter, message=None, response=None):
    if not text:
        return

    elements = [re.sub(r'\s+', ' ', m) for m in text.split(delimeter)]
    handin = clean(elements[len(elements) - 1])

    res = []

    # Create a list with number of items and item name
    for el in elements[:-1]:
        frags =  el.strip().split(" ", 1)
        possible_number = frags[0]
        try:
            n = w2n.word_to_num(possible_number)
            res.append({
                "quantity" : n,
                "item_name" : clean(frags[1])
            })
        except ValueError:
            res.append({
                "quantity" : 1,
                "item_name" : clean(el)
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
        if message.guild:
            if message:
                await message.add_reaction("❔")
            return
        else:
            unknowns = ', '.join([f'{str(u["quantity"])} {u["item_name"]}' for u in unknown_items])
            if message:
                await message.reply(f"Unknown items: {unknowns}")
            else:
                await response.send_message(f"Unknown items: {unknowns}")
            return
        
    #TODO verify handin
        
    if len(unknown_items) == 0 and len(found_items) > 0:
        sorted_items = sorted(found_items, key=lambda i:int(i["id"]))
        result = "-".join([f"{si['quantity']}{si['item_name']}" for si in sorted_items]) + "--" + handin
        return result
    
    return

# sort_items_npc("2 coal, 8 blue parthats, rope, diango", ",") == "2COAL-8BLUEPARTYHAT-1ROPE-DIANGO"

async def try_solution_items(message, delimeter):
    content = await sort_items_npc(message.content, delimeter, message=message)

    if not content:
        return

    h = hash(content)
    q = Query()
    result = solutions.search(q.hashed_solution_items == h)

    if len(result) > 0:
        res = result[0]
        await message.add_reaction("✅")
        await message.reply(cr.decrypt(res["secret_items"], content))
        if message.author.id != res["author_id"] and res["first_solver"] == "":
            solutions.update({
                "first_solver" : message.author.name,
                "first_solver_id" : message.author.id,
                "first_solve_time" : datetime.now().isoformat()
            }, q.hashed_solution_items == h)
        return
    else:
        await message.add_reaction("❌")
        return

def main():
    mom.run(token)

if __name__ == "__main__":
    main()