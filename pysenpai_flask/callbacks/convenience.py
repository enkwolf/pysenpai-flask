import random
import string

alnum = string.ascii_letters + string.digits

def sqlite_uri_builder():
    fname = "".join(random.choices(alnum, k=20))
    return f"sqlite:///{fname}.db"
