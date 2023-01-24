import pysenpai_flask.callbacks.defaults as defaults
from pysenpai_flask.utils.checker import find_app, find_db
from pysenpai_flask.exceptions import NoFlaskApp
from pysenpai.checking.testcase import TestCase, run_test_cases
from pysenpai.messages import load_messages, Codes
from pysenpai.output import output, json_output

class CommitTestCase(TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_validator = None

    def wrap(self, module, target):
        app = find_app(module)
        db_handle = find_db(module)
        try:
            db_handle.session.add(self.args)
            db_handle.session.commit()
        except Exception as e:
            db_handle.session.rollback()
            return e
        else:
            return self.args


def verify_model(st_module, db_handle, model_name, attr_list,
               lang="en",
               custom_msgs={}):

    msgs = load_messages(lang, "model", module="pysenpai_flask")
    msgs.update(custom_msgs)

    json_output.new_test(msgs.get_msg("StartModelTest", lang)["content"].format(name=model_name))
    json_output.new_run()

    try:
        model_class = getattr(st_module, model_name)
    except:
        output(msgs.get_msg("MissingModel", lang), Codes.INCORRECT, name=model_name)
        return False

    #if not db_handle.Model in model_class.__bases__:
        #output(msgs.get_msg("NotModel", lang), Codes.INCORRECT, name=model_name)
        #return False

    missing = []
    for attr in attr_list:
        if not hasattr(model_class, attr):
            missing.append(attr)

    if missing:
        output(msgs.get_msg("MissingFields", lang), Codes.INCORRECT, fields=missing)
        return False
    else:
        output(msgs.get_msg("CorrectFields", lang), Codes.CORRECT)
        return True



