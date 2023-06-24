import json
import re

def clean(s):
    return re.sub(r"[^A-Za-z0-9]", "", s).strip().upper()

# Parse the OSRS Wiki formatted mapping.js into key list for mombot.
def parse(name="mapping.json"):
    mapping = open(name)
    items = json.load(mapping)
    print(len(items))

    res = {}
    for item in items:
        name = clean(item["name"])
        res[name] = str(item["id"])
    
    out = open("items.json", "w")
    json.dump(res, out)

parse()