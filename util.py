import hashlib
import re

def hash(string: str) -> str:
    if string == None:
        return ""
    return hashlib.sha256(clean(string).encode("UTF-8")).hexdigest()

def clean(string: str) -> str:
    if string == None:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", string).strip().upper()
