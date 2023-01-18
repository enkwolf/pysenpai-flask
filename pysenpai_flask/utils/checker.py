import flask
import flask_sqlalchemy

class RefResponse(object):
    status_code = 0
    data = ""
    parsed_data = ""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class GeneratedRequest(object):

    def __init__(self, href, method="get", query=None, data=None, extra_kw=None):
        self.href = href
        self.method = method
        self.query = query or []
        self.extra_kw = extra_kw or {}
        self.data = data or []


def find_app(st_module):
    for name in dir(st_module):
        if not name.startswith("_"):
            if isinstance(getattr(st_module, name), flask.app.Flask):
                return getattr(st_module, name)
    else:
        raise NoFlaskApp

def find_db(st_module):
    for name in dir(st_module):
        if not name.startswith("_"):
            if isinstance(getattr(st_module, name), flask_sqlalchemy.SQLAlchemy):
                return getattr(st_module, name)
    else:
        raise NoFlaskDb
