import hashlib

def hash(s):
    if s == None:
        return ""
    return hashlib.sha256(clean(s).encode("UTF-8")).hexdigest()

def clean(s):
    if s == None:
        return ""
    return s.replace(" ", "").upper()