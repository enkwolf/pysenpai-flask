import pysenpai_flask.callbacks.defaults as defaults
from pysenpai_flask.utils.checker import find_app
#import pysenpai.callbacks.convenience as convenience
#from pysenpai_flask.exceptions import NoAdditionalInfo, NotCallable, OutputParseError
#from pysenpai.output import json_output
#from pysenpai.messages import load_messages, Codes
#from pysenpai.output import output
#from pysenpai.utils.internal import StringOutput, get_exception_line
from pysenpai.checking.testcase import TestCase


class FlaskTestCase(TestCase):

    def __init__(self, ref_result,
                 args=None,
                 inputs=None,
                 data=None,
                 weight=1,
                 tag="",
                 validator=defaults.default_response_validator,
                 output_validator=None,
                 eref_results=None,
                 internal_config=None,
                 presenters=None):

        self.args = args or {}
        self.inputs = inputs or {}
        self.data = data
        self.weight = weight
        self.tag = tag
        self.ref_result = ref_result
        self.validator = validator
        self.output_validator = output_validator
        self.eref_results = eref_results or []
        self.correct = False
        self.output_correct = False
        self.internal_config = internal_config
        self.presenters = {
            "arg": str,
            "input": defaults.default_query_presenter,
            "data": defaults.default_document_presenter,
            "ref": defaults.default_response_presenter,
            "res": defaults.default_response_presenter,
            "parsed": str,
            "call": defaults.default_route_presenter,
        }
        if presenters:
            self.presenters.update(presenters)

    def wrap(self, module, target):
        app = find_app(module)
        client = app.test_client()
        route = target.format(**self.args)
        response = client.get(route, query_string=self.inputs)
        self.parse_response(response)
        return response

    def validate_result(self, res, parsed, output):
        self.validator(self.ref_result, res)
        self.correct = True

    def parse_response(self, response):
        response.parsed_data = response.data.decode("utf-8")

    def present_call(self, target):
        return self.presenters["call"](target.format(**self.args))
