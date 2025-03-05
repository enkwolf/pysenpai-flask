import inspect
import sys
import requests
from pysenpai.checking.testcase import TestCase
from pysenpai.callbacks import defaults
from pysenpai.messages import load_messages, Codes
from pysenpai.output import json_output, output
from pysenpai.utils.internal import StringOutput
import pysenpai_flask.callbacks.defaults as flask_defaults
from pysenpai_flask.utils.checker import RefResponse

def requests_response_presenter(value):
    try:
        formatted = "\n{{{highlight=json\n" + json.dumps(value.parsed_data, indent=4) + "\n}}}"
    except:
        formatted = value.parsed_data
    return RefResponse(
        status_code=value.status_code,
        data=value.content,
        parsed_data=formatted,
        headers=dict(value.headers),
    )



class HttpTestCase(TestCase):

    def __init__(self, ref_result,
                 args=None,
                 inputs=None,
                 data=None,
                 headers=None,
                 weight=1,
                 tag="",
                 validator=flask_defaults.default_response_validator,
                 output_validator=None,
                 data_validator=None,
                 eref_results=None,
                 internal_config=None,
                 presenters=None,
                 method="get",
                 cert=None,
                 ):

        self.args = args or {}
        self.inputs = inputs or {}
        self.data = data
        self.headers = headers or {}
        self.weight = weight
        self.tag = tag
        self.ref_result = ref_result
        self.validator = validator
        self.data_validator = data_validator
        self.eref_results = eref_results or []
        self.correct = False
        self.data_correct = False
        self.output_correct = False
        self.internal_config = internal_config or {}
        self.method = method
        self.cert = cert
        self.presenters = {
            "arg": str,
            "input": flask_defaults.default_query_presenter,
            "data": flask_defaults.default_document_presenter,
            "ref": flask_defaults.default_response_presenter,
            "res": requests_response_presenter,
            "parsed": str,
            "call": flask_defaults.default_route_presenter,
            "db": str,
        }
        if presenters:
            self.presenters.update(presenters)

    def _get_response(self, module, route):
        if self.cert:
            return requests.request(
                self.method, route,
                json=self.data,
                headers=self.headers,
                params=self.inputs,
                verify=self.cert
            )
        else:
            return requests.request(
                self.method, route, json=self.data, headers=self.headers, params=self.inputs
            )

    def wrap(self, module, target):
        route = target.format(**self.args)
        response = self._get_response(module, route)
        self.parse_response(response)
        self.output_response(response)
        return response

    def validate_result(self, res, parsed, output):
        self.validator(self.ref_result, res)
        self.correct = True

    def validate_data(self, db):
        self.data_validator(self.ref_result, self.args, self.inputs, self.data, db)
        self.data_correct = True

    def parse_response(self, response):
        response.parsed_data = response.content.decode("utf-8")

    def output_response(self, response):
        print(response.content.decode("utf-8"))

    def present_call(self, target):
        return self.presenters["call"](target.format(**self.args), self.method)


def run_http_cases(category, test_target, test_cases, lang,
                    msg_module="pysenpai",
                    custom_msgs={},
                    test_recurrence=True,
                    grader=defaults.pass_fail_grader):

    save = sys.stdout
    save_err = sys.stderr
    msgs = load_messages(lang, category, module=msg_module)
    msgs.update(custom_msgs)
    if inspect.isfunction(test_cases):
        test_cases = test_cases()

    json_output.new_test(
        msgs.get_msg("TargetName", lang)["content"].format(name=test_target)
    )

    prev_res = None
    o = StringOutput()
    err = StringOutput()

    for i, test in enumerate(test_cases):
        json_output.new_run()

        output(
            msgs.get_msg("PrintTestVector", lang), Codes.DEBUG,
            args=test.present_object("arg", test.args),
            call=test.present_call(test_target)
        )
        if test.inputs:
            output(
                msgs.get_msg("PrintInputVector", lang), Codes.DEBUG,
                inputs=test.present_object("input", test.inputs)
            )
        if test.data:
            output(
                msgs.get_msg("PrintTestData", lang), Codes.DEBUG,
                data=test.present_object("data", test.data)
            )

        # Test preparations
        sys.stdout = o
        sys.stderr = err
        o.clear()

        # If this fails the problem is with the checker itself
        # Therefore no handling
        res = test.wrap(None, test_target)

        sys.stdout = save
        sys.stderr = save_err

        output(
            msgs.get_msg("PrintStudentResult", lang), Codes.DEBUG,
            res=test.present_object("res", res),
            output=o.content
        )

        try:
            test.validate_result(res, None, None)
            output(msgs.get_msg("CorrectResult", lang), Codes.CORRECT)
        except AssertionError as e:
            # Result was incorrect
            output(msgs.get_msg(e, lang, "IncorrectResult"), Codes.INCORRECT)
            output(
                msgs.get_msg("PrintReference", lang),
                Codes.DEBUG,
                ref=test.present_object("ref", test.ref_result)
            )

            output(msgs.get_msg("AdditionalTests", lang), Codes.INFO)

            # Extra feedback
            for msg_key, format_args in test.feedback(res, None, None):
                output(msgs.get_msg(msg_key, lang), Codes.INFO, **format_args)

        test.teardown()
        prev_res = res

    return grader(test_cases)








