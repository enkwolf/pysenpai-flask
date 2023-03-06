import json
import pysenpai_flask.callbacks.defaults as defaults
from pysenpai_flask.utils.checker import GeneratedRequest
from pysenpai_flask.checking.flask import FlaskTestCase

class MasonBaseCase(FlaskTestCase):

    def __init__(self, doc_source, ctrl_key, *args, **kwargs):
        self.doc_source = doc_source
        self.ctrl_key = ctrl_key
        self.request = None
        self.document = {}
        super().__init__(*args, **kwargs)

    def parse_response(self, response):
        if response.status_code == 200:
            try:
                response.parsed_data = json.loads(response.data)
                self.document.update(response.parsed_data)
            except:
                response.parsed_data = response.data
        else:
            response.parsed_data = ""

    def present_call(self, module):
        return '{{{highlight=python3\n' + f'document["@controls"]["{self.ctrl_key}"]' + ' \n}}}'

    def present_object(self, category, value):
        if category == "res":
            res_object = defaults.default_response_presenter(value)
            res_object.request = self.request
            return res_object
        return super().present_object(category, value)


class MasonHrefCase(MasonBaseCase):

    def wrap(self, module, target):
        document = self.doc_source.document
        href = document["@controls"][self.ctrl_key]["href"]
        self.method = document["@controls"][self.ctrl_key].get("method", "get")
        self.request = GeneratedRequest(href, method=self.method)
        result = super().wrap(module, href)
        self.ref_result = self.ref_result(module)
        return result


class MasonSchemaCase(MasonBaseCase):

    def wrap(self, module, target):
        document = self.doc_source.document
        ctrl = document["@controls"][self.ctrl_key]
        href = ctrl["href"]
        self.method = ctrl["method"].lower()
        encoding = ctrl["encoding"].lower()
        schema = ctrl["schema"]
        data = self.generate_from_schema(schema)
        self.request = GeneratedRequest(href, method=self.method, data=data)
        self.ref_result = self.ref_result(module, data)
        self.data = data
        result = super().wrap(module, href)
        return result

    def generate_from_schema(self, schema):
        raise NotImplementedError



class MasonItemHrefCase(MasonBaseCase):

    def __init__(self, items_key, item_idx, *args, **kwargs):
        self.items_key = items_key
        self.item_idx = item_idx
        super().__init__(*args, **kwargs)

    def wrap(self, module, target):
        document = self.doc_source.document
        href = document[self.items_key][self.item_idx]["@controls"][self.ctrl_key]["href"]
        self.method = document["@controls"][self.ctrl_key].get("method", "get")
        self.request = GeneratedRequest(href, method=self.method)
        result = super().wrap(module, href)
        self.ref_result = self.ref_result(module)
        return result

    def present_call(self, module):
        return (
            '{{{highlight=python3\n'
            f'document["{self.items_key}"][{self.item_idx}]["@controls"]["{self.ctrl_key}"]\n'
            '}}}'
        )
