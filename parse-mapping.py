import json
import re

def clean(s):
    return re.sub(r"[^A-Za-z0-9]", "", s).strip().upper()

# Parse the OSRS Wiki formatted mapping.js into key list for mombot.
# https://prices.runescape.wiki/api/v1/osrs/mapping
def parse_wiki(name="mapping.json"):
    mapping = open(name)
    items = json.load(mapping)
    print(len(items))

    res = {}
    for item in items:
        name = clean(item["name"])
        res[name] = str(item["id"])
    
    out = open("items.json", "w")
    json.dump(res, out)

# Parse osrsbox list of items into key list for mombot
# https://github.com/osrsbox/osrsbox-db/blob/master/docs/items-complete.json
def parse_osrsbox(name="items-complete.json"):
    mapping = open(name)
    items = json.load(mapping)
    print(len(items))

    res = {}
    for key in items:
        name = clean(items[key]["name"])
        res[name] = str(items[key]["id"])
    
    out = open("items.json", "w")
    json.dump(res, out)