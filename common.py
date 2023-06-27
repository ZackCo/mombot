import hashlib

def hash(string: str) -> str:
    if string == None:
        return ""
    return hashlib.sha256(clean(string).encode("UTF-8")).hexdigest()

def clean(string: str) -> str:
    if string == None:
        return ""
    return string.replace(" ", "").upper()
