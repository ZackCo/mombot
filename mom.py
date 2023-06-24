import discord
from discord import app_commands

import shutil
import json

intents = discord.Intents.default()
intents.message_content = True

mom = discord.Client(intents=intents)

treeclined = app_commands.CommandTree(mom)

# @mom.event
# async def on_interaction(interaction):
#     print(interaction)

@treeclined.command(name = "solve", description="Submit an answer!")
async def solve(interaction):
    await interaction.message.add_reaction(":x:")
    print("reacted")

@mom.event
async def on_ready():
    guild = mom.get_guild(608068411557150728)
    if guild != None:
        treeclined.copy_global_to(guild=guild)
    await treeclined.sync()
    print("M.O.M is awaiting solutions")

def main():
    try:
        with open("credentials.json") as c:
            credentials = json.load(c)
            token = credentials["token"]
            if token == "REPLACE_WITH_TOKEN":
                print("Replace your token in credentials.json with your discord bot's token")
                return
            print(f"Running with token {token}")
            mom.run(token)
            
    except IOError:
        shutil.copy2("credentials_template.json", "credentials.json")
        main()

if __name__ == "__main__":
    main()
