import flask
import flask_sqlalchemy
import inspect
import os
import tempfile
from pysenpai_flask.exceptions import NoModelClass, NoFlaskApp, NoFlaskDb

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


class SqliteInterface(object):

    def configure(self, app, db_handle, st_module):
        self.app = app
        self.db_handle = db_handle
        self.db_handle.create_all()
        self.st_module = st_module

    def populate(self):
        pass

    def rollback(self):
        self.db_handle.session.rollback()

    def clean(self):
        self.db_handle.drop_all()
        self.db_handle.session.remove()

    def __str__(self):
        return ""




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
