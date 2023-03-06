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


class FlaskTestCase(TestCase):

    def __init__(self, ref_result,
                 args=None,
                 inputs=None,
                 data=None,
                 weight=1,
                 tag="",
                 validator=flask_defaults.default_response_validator,
                 output_validator=None,
                 data_validator=None,
                 eref_results=None,
                 internal_config=None,
                 presenters=None,
                 method="get"):

        self.args = args or {}
        self.inputs = inputs or {}
        self.data = data
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
        self.presenters = {
            "arg": str,
            "input": flask_defaults.default_query_presenter,
            "data": flask_defaults.default_document_presenter,
            "ref": flask_defaults.default_response_presenter,
            "res": flask_defaults.default_response_presenter,
            "parsed": str,
            "call": flask_defaults.default_route_presenter,
            "db": str,
        }
        if presenters:
            self.presenters.update(presenters)

    def wrap(self, module, target):
        app = find_app(module)
        client = app.test_client()
        route = target.format(**self.args)
        response = getattr(client, self.method.lower())(route, query_string=self.inputs, json=self.data)
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
        response.parsed_data = response.data.decode("utf-8")

    def output_response(self, response):
        print(response.data.decode("utf-8"))

    def present_call(self, target):
        return self.presenters["call"](target.format(**self.args), self.method)



def run_with_context(category, test_target, st_module, test_cases, lang,
                     db_interface=None,
                     **kwargs):

    msgs = load_messages(lang, "context", "pysenpai_flask")

    try:
        app = find_app(st_module)
    except NoFlaskApp:
        output(
            msgs.get_msg("NoFlaskApp", lang), Codes.ERROR,
            name=test_target
        )
        return 0

    with app.app_context():
        if db_interface:
            try:
                db_handle = find_db(st_module)
                db_interface.configure(app, db_handle, st_module)
                db_interface.populate()
            except NoFlaskDb:
                output(msgs.get_msg("NoFlaskDb", lang), Codes.ERROR, name=st_module.__name__)
                return 0
            except:
                etype, evalue, etrace = sys.exc_info()
                ename = evalue.__class__.__name__
                emsg = str(evalue)
                output(msgs.get_msg(ename, lang, default="GenericErrorMsg"), Codes.ERROR,
                    emsg=emsg,
                    ename=ename
                )
                return 0

        result = run_flask_cases(
            category, test_target, st_module, test_cases, lang,
            db_interface=db_interface,
            **kwargs
        )

        if db_interface:
            db_interface.clean()


        return result


def run_flask_cases(category, test_target, st_module, test_cases, lang,
                    db_interface=None,
                    parent_object=None,
                    msg_module="pysenpai",
                    custom_msgs={},
                    hide_output=True,
                    test_recurrence=True,
                    validate_exception=False,
                    grader=defaults.pass_fail_grader):



    # One time preparations
    save = sys.stdout
    save_err = sys.stderr
    msgs = load_messages(lang, category, module=msg_module)
    msgs.update(custom_msgs)

    # call test and input producing functions
    if inspect.isfunction(test_cases):
        test_cases = test_cases()

    # Show the name of the function
    # output(msgs.get_msg("FunctionName", lang).format(name=func_names[lang]), INFO)
    json_output.new_test(
        msgs.get_msg("TargetName", lang)["content"].format(name=test_target)
    )

    if parent_object is None:
        parent_object = st_module

    prev_res = None

    o = StringOutput()
    err = StringOutput()

    for i, test in enumerate(test_cases):
        json_output.new_run()

        try:
            inps = test.inputs
            sys.stdin = io.StringIO("\n".join([str(x) for x in inps]))
        except IndexError:
            inps = []

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

        # Calling the student function
        try:
            res = test.wrap(st_module, test_target)
        except NotCallable as e:
            sys.stdout = save
            output(msgs.get_msg("IsNotFunction", lang), Codes.ERROR, name=e.callable_name)
            return 0
        except Exception as e:
            if validate_exception:
                res = e
            else:
                sys.stdout = save
                sys.stderr = save_err
                etype, evalue, etrace = sys.exc_info()
                ename = evalue.__class__.__name__
                emsg = str(evalue)
                elineno, eline = get_exception_line(st_module, etrace)
                output(
                    msgs.get_msg(ename, lang, default="GenericErrorMsg"), Codes.ERROR,
                    emsg=emsg,
                    ename=ename
                )
                output(msgs.get_msg("PrintExcLine", lang), Codes.DEBUG,
                    lineno=elineno, line=eline
                )
                test.teardown()
                continue

        # Validating function results
        sys.stdout = save
        sys.stderr = save_err
        if not hide_output:
            output(msgs.get_msg("PrintStudentOutput", lang), Codes.INFO, output=o.content)

        output(
            msgs.get_msg("PrintStudentResult", lang), Codes.DEBUG,
            res=test.present_object("res", res),
            output=o.content
        )


        # Validate results
        try:
            test.validate_result(res, None, o.content)
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
            for msg_key, format_args in test.feedback(res, None, o.content):
                output(msgs.get_msg(msg_key, lang), Codes.INFO, **format_args)

        # Validate contents of the database
        if test.data_validator:
            try:
                db_interface.rollback()
                output(
                    msgs.get_msg("PrintDatabaseState", lang), Codes.DEBUG,
                    data=test.present_object("db", db_interface)
                )
                test.validate_data(db_interface)
                output(msgs.get_msg("CorrectData", lang), Codes.CORRECT)
            except AssertionError as e:
                output(msgs.get_msg(e, lang, "IncorrectData"), Codes.INCORRECT)
            except Excepton as e:
                etype, evalue, etrace = sys.exc_info()
                ename = evalue.__class__.__name__
                emsg = str(evalue)
                output(
                    msgs.get_msg("DbError", lang), codes.ERROR,
                    emsg=emsg,
                    ename=ename
                )

        test.teardown()
        prev_res = res

    return grader(test_cases)
