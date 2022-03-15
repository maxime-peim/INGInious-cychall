import os

from flask import send_from_directory

from inginious.common.base import load_json_or_yaml
from inginious.common.tasks_problems import Problem
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.task_problems import DisplayableProblem
from inginious.frontend.parsable_text import ParsableText

from ..template_manager import TemplateManagerHandler
from .. import constants


class StaticMockPage(INGIniousPage):
    def GET(self, path):
        return send_from_directory(os.path.join(constants.PATH_TO_PLUGIN, "static"), path)

    def POST(self, path):
        return self.GET(path)


class CychallProblem(Problem):
    """Display an input box and check that the content is correct"""

    def __init__(self, problemid, content, translations, taskfs):
        Problem.__init__(self, problemid, content, translations, taskfs)
        self._header = str(content.get("header", ""))
        self._exercise_path = str(content.get("exercise-path", ""))
        self._difficulty = str(content.get("difficulty", ""))

    @classmethod
    def get_type(cls):
        return "cychall"

    def input_is_consistent(self, task_input, default_allowed_extension, default_max_size):
        return self.get_id() in task_input

    def input_type(self):
        return str

    def check_answer(self, task_input, language):
        return None, None, None, 0, ""

    @classmethod
    def parse_problem(self, problem_content):
        return Problem.parse_problem(problem_content)

    @classmethod
    def get_text_fields(cls):
        return Problem.get_text_fields()


class DisplayableCychallProblem(CychallProblem, DisplayableProblem, TemplateManagerHandler):
    """ A displayable match problem """
        
    def __init__(self, problemid, content, translations, taskfs):
        CychallProblem.__init__(self, problemid, content, translations, taskfs)

    @classmethod
    def get_type_name(self, language):
        return "cychall"

    def show_input(self, template_helper, language, seed):
        """ Show CychallProblem """
        header = ParsableText(self.gettext(language, self._header), "rst",
                              translation=self.get_translation_obj(language))
        exercise_configuration = load_json_or_yaml(os.path.join(self._exercise_path, "configuration.yaml"))

        return template_helper.render("cychall.html",
                                      template_folder=constants.PATH_TO_TEMPLATES,
                                      pid=self.get_id(),
                                      exercise_name=exercise_configuration.get("name", ""),
                                      difficulty=self._difficulty,
                                      header=header)

    @classmethod
    def show_editbox(cls, template_helper, key, language, course=None, taskid=None, *args, **kwargs):
        public_templates, course_templates = cls._template_manager.get_all_templates(course.get_id())

        return template_helper.render("cychall_edit.html",
                                      template_folder=constants.PATH_TO_TEMPLATES,
                                      key=key, public_templates=public_templates,
                                      course_templates=course_templates)

    @classmethod
    def show_editbox_templates(cls, template_helper, key, language, course=None, taskid=None, *args, **kwargs):
        return ""
