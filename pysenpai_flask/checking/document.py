import inspect
import io
import sys
import pysenpai_flask.callbacks.defaults as flask_defaults
from pysenpai.exceptions import NoAdditionalInfo, NotCallable, OutputParseError
from pysenpai_flask.exceptions import NoFlaskApp, NoFlaskDb
from pysenpai_flask.utils.checker import find_app, find_db
import pysenpai.callbacks.defaults as defaults
#from pysenpai_flask.exceptions import NoAdditionalInfo, NotCallable, OutputParseError
from pysenpai.output import json_output
from pysenpai.messages import load_messages, Codes
from pysenpai.output import output
from pysenpai.utils.internal import StringOutput, get_exception_line
from pysenpai.checking.testcase import TestCase, run_test_cases

class DocumentTestCase(TestCase):

    def __init__(self,
                 ref_schema=None,
                 ref_result=None,
                 ref_implementation=None,
                 args=None,
                 inputs=None,
                 data=None,
                 weight=1,
                 tag="",
                 validator=None,
                 output_validator=None,
                 eref_results=None,
                 internal_config=None,
                 presenters=None):

        self.args = args or []
        self.inputs = inputs or []
        self.data = data
        self.weight = weight
        self.tag = tag
        self.ref_result = ref_result
        self.ref_schema = ref_schema
        self.ref_implementation = ref_implementation
        self.validator = validator
        self.output_validator = output_validator
        self.eref_results = eref_results or []
        self.correct = False
        self.schema_valid = False
        self.internal_config = internal_config or {}
        self.presenters = {
            "validation": defaults.default_call_presenter,
            "call": defaults.default_call_presenter,
            "doc": flask_defaults.default_document_presenter,
        }
        if presenters:
            self.presenters.update(presenters)

    def schema_validation(self, res, parsed, output):
        raise NotImplementedError

    def retrieve_next(self, document):
        return document

    def present_validation(self, target):
        raise NotImplementedError

    def present_call(self, target):
        raise NotImplementedError


def run_document_cases(category, test_target, st_document, test_cases, lang,
                       custom_msgs={},
                       show_document=True,
                       grader=flask_defaults.valid_correct_grader):

    msgs = load_messages(lang, category, "pysenpai_flask")
    msgs.update(custom_msgs)

    json_output.new_test(
        msgs.get_msg("TargetName", lang)["content"].format(name=test_target)
    )

    # call test and input producing functions
    if inspect.isfunction(test_cases):
        test_cases = test_cases()

    for i, test in enumerate(test_cases):
        json_output.new_run()

        output(
            msgs.get_msg("PrintTestVector", lang), Codes.DEBUG,
            call=test.present_call(test_target)
        )

        try:
            res = test.wrap(st_document, test_target)
        except Exception as e:
            etype, evalue, etrace = sys.exc_info()
            ename = evalue.__class__.__name__
            emsg = str(evalue)
            output(
                msgs.get_msg(ename, lang, default="GenericErrorMsg"), Codes.ERROR,
                emsg=emsg,
                ename=ename
            )
            test.teardown()
            continue

        if show_document:
            output(
                msgs.get_msg("ShowDocument", lang), Codes.DEBUG,
                doc=test.present_object("doc", res)
            )

        output(
            msgs.get_msg("PrintValidation", lang), Codes.DEBUG,
            call=test.present_validation(test_target)
        )

        try:
            test.schema_validation(res, None, None)
            output(msgs.get_msg("ValidDocument", lang), Codes.CORRECT)
        except Exception as e:
            output(
                msgs.get_msg("InvalidDocument", lang), Codes.INCORRECT,
                reason=str(e)
            )

        if test.validator is not None:
            try:
                test.validate_result(res, None, None)
                output(msgs.get_msg("CorrectResult", lang), Codes.CORRECT)
            except AssertionError as e:
                # Result was incorrect
                output(msgs.get_msg(e, lang, "IncorrectResult"), Codes.INCORRECT)
                output(msgs.get_msg("AdditionalTests", lang), Codes.INFO)

                # Extra feedback
                for msg_key, format_args in test.feedback(res, None, o.content):
                    output(msgs.get_msg(msg_key, lang), Codes.INFO, **format_args)

        try:
            st_document = test.retrieve_next(st_document)
        except Exception as e:
            output(
                msgs.get_msg("TestAborted", lang), Codes.ERROR,
                reason=str(e)
            )
            return 0

        test.teardown()

    return grader(test_cases)













