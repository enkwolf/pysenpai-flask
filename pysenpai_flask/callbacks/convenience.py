import random
import string
from jsonschema import validate, Draft7Validator, ValidationError

alnum = string.ascii_letters + string.digits

def sqlite_uri_builder():
    fname = "".join(random.choices(alnum, k=20))
    return f"sqlite:///{fname}.db"

def status_only_validator(ref, res):
    assert ref.status_code == res.status_code

def validate_against_schema(ref, res):
    assert ref.status_code == res.status_code
    schema = ref.parsed_data
    try:
        validate(res.parsed_data, schema, cls=Draft7Validator)
    except ValidationError:
        raise AssertionError
