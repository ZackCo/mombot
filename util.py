import hashlib
import re
import cryptocode as cr

python_hash = hash

def hash(string: str) -> str:
    if string == None:
        return ""
    return hashlib.sha256(clean(string).encode("UTF-8")).hexdigest()

def clean(string: str) -> str:
    if string == None:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", string).strip().upper()

def obscure(string: str) -> str:
    '''
    Obscure a string so it can't be read. 
    This is not a secure operation, it is only so I can view the DB without seeing names.
    '''
    return cr.encrypt(string, ".")

def unobscure(string: str) -> str:
    '''
    Unobscure an obscured string.
    '''
    return cr.decrypt(string, ".")

