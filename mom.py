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

test_guild = 0
token = ""
solutions = TinyDB("solutions.json")

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
    return s.replace(" ", "").upper()

# Parse and sort a list of items so order doesn't matter
def sort_items_npc(items_string):
    # TODO: Do this
    return items_string

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
        A memorable name for your clue.
    solved_response: str
        The text to respond with when the clue is solved. Perhaps an image link to another clue, or a simple gz.
    solution_string: 
        The solution string for your clue, i.e. "TINOREEGGSLOGS". Do not use if your clue is unordered.
    solution_items_npc:
        A comma-separated list of items and an NPC, i.e. "732 coins, 7 onions, sigismund". Please spell the items correctly, and end with an NPC. Do not use if your clue uses other hand-in methods.
    """
    #TODO: Check valid
    sorted_items_npc = sort_items_npc(solution_items_npc)

    solutions.insert({
        "name" : name,
        "author_id" : interaction.user.id,
        "author_name" : interaction.user.name,
        "hashed_solution_string" : hash(solution_string),
        "hashed_solution_items" : hash(sorted_items_npc),
        "secret_string" : solution_string != None and cr.encrypt(solved_response, solution_string) or "",
        "secret_items" : sorted_items_npc != None and cr.encrypt(solved_response, sorted_items_npc) or ""
    })

@mom.tree.command(name = "list")
async def list(interaction):
    """
    List all my puzzles
    """
    await interaction.response.send_message("fds")

@mom.listen('on_message')
async def sync(message):
    if message.content == "sync" and await mom.is_owner(message.author):
        guild = mom.get_guild(test_guild)
        if guild != None:
            mom.tree.copy_global_to(guild=guild)
        await mom.tree.sync()
        print("Synced commands to " + str(guild))
        await message.add_reaction("🔁")

def main():
    mom.run(token)

if __name__ == "__main__":
    main()

@mom.listen('on_message')
async def try_solution_string(message):
    h = hash(message)
    q = Query()
    result = solutions.search(q.solution_string == h)
    print(result)