from sqlalchemy.orm.attributes import InstrumentedAttribute

def default_client_getter(st_module, st_app):
    return st_app.test_client()

# from http://flask.pocoo.org/docs/1.0/testing/
def client_with_db_getter(st_module, st_app):
    db_fd, st_app.config["DATABASE"] = tempfile.mkstemp()
    st_app.config["TESTING"] = True
    client = st_app.test_client()

    with st_app.app_context():
        db = find_db(st_module)
        db.create_all()

    return client

def default_response_validator(ref, res):
    assert ref.status_code == res.status_code
    assert ref.parsed_data == res.parsed_data

def default_db_populator(st_module, db):
    pass

def default_route_presenter(value, method):
    return "{{{[" + method.upper() + "] " + value.replace("{", "<").replace("}", ">") + "}}}"

def default_query_presenter(value):
    if value:
        return "{{{" + "?" + "&".join("{}={}".format(*pair) for pair in value.items()) + "}}}"
    else:
        return ""

def default_database_presenter(value):
    return ""

def default_document_presenter(value):
    if isinstance(value, str):
        return "{{{\n" + value + "\n}}}"
    try:
        return "{{{highlight=json\n" + json.dumps(value, indent=4) + "\n}}}"
    except:
        return "{{{\n" + repr(value) + "\n}}}"

def default_response_presenter(value):
    return value

def default_output_presenter(value):
    content = html.escape(value.decode("utf-8"))
    return "{{{\n" + content + "\n}}}"

def default_instance_presenter(value):
    content = ""
    for name in dir(value):
        if not name.startswith("_"):
            if isinstance(getattr(value.__class__, name), InstrumentedAttribute):
                attr_value = getattr(value, name)
                if isinstance(attr_value, str):
                    content += "{}: {} (str {})\n".format(name, repr(attr_value), len(attr_value))
                else:
                    content += "{}: {} ({})\n".format(name, repr(attr_value), type(attr_value))
    return "{{{\n" + content + "}}}"

def default_data_parser(response):
    response.parsed_data = response.data.decode("utf-8")
