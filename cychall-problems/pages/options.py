import copy
import os

from flask import request
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage

from .. import constants, utils
from ..template_manager import TemplateManagerHandler


def check_option_format(option_dict):
    return "id" in option_dict and "type" in option_dict


def check_default_attributes(element, check_type=True):
    res = False
    if "id" in element and (not check_type or (check_type and "type" in element)):
        if "label" not in element:
            element["label"] = element["id"]
        res = True
    return res


def parse_default_element_option(element, difficulty):
    if check_default_attributes(element):
        if (
            "modes" not in element or difficulty in element["modes"]
        ):  # Modes not specified -> available everywhere
            return parse_element_specific_options(element)


def parse_element_specific_options(element):
    options = ["id", "label", "type"]
    if element["type"] == "text":
        options += ["placeholder", "size"]

    elif element["type"] == "checkbox":
        options += ["checked"]

    elif element["type"] == "select":
        if "values" not in element:
            return None
        options += ["values"]

        if "default" in element and element["default"] in element["values"]:
            options += ["default"]

    elif element["type"] == "radio":
        if "buttons" not in element:
            return None
        options += ["default", "buttons"]

        valid_buttons = []
        for button in element["buttons"]:
            if check_default_attributes(button, check_type=False):
                valid_buttons.append(button)

        if not valid_buttons:
            return None

        element["buttons"] = valid_buttons

    else:  # Default case: cancel
        return None

    element_copy = copy.deepcopy(element)
    keys = element.keys()
    for key in keys:
        if key not in options:
            element_copy.pop(key)
    return element_copy


class ExerciseConfigurationOptions(INGIniousAdminPage, TemplateManagerHandler):
    def POST_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ

        self.get_course_and_check_rights(courseid, allow_all_staff=False)

        user_input = request.form
        if (
            user_input.get("problem_id") is not None
            and user_input.get("difficulty") is not None
            and user_input.get("exercise-path") is not None
        ):
            templateid = os.path.basename(user_input.get("exercise-path"))
            exercise_options_elements = self._template_manager.get_template(
                courseid, templateid
            ).elements
            exercise_switch = self._template_manager.get_template(
                courseid, templateid
            ).step_switch
            return self.show_exercise_options_tab(
                courseid,
                taskid,
                user_input.get("problem_id"),
                exercise_options_elements,
                user_input.get("difficulty"),
                exercise_switch,
            )
        return self.template_helper.render(
            "exercise_options.html", template_folder=constants.PATH_TO_TEMPLATES
        )

    def get_build_options(self, courseid, taskid, problemid):
        task_fs = self.course_factory.get_task(courseid, taskid).get_fs()
        build_config = utils.load_build_config(task_fs)
        if build_config is not None:
            for step in build_config["steps"]:
                options = build_config["steps"][step]
                if options["problemid"] == problemid:
                    return options

    def fill_options(self, courseid, taskid, problemid, options):
        current_task_options = self.get_build_options(courseid, taskid, problemid)
        if current_task_options is not None:
            for element in options:
                if element["id"] in current_task_options.keys():
                    value = current_task_options[element["id"]]
                    if element["type"] == "checkbox" and value == "on":
                        element["checked"] = True

                    elif element["type"] == "text":
                        element["value"] = value

                    elif element["type"] == "select" or element["type"] == "radio":
                        element["default"] = value
        return options

    def show_exercise_options_tab(
        self,
        courseid,
        taskid,
        problem_id,
        exercise_options_elements,
        difficulty,
        exercise_switch,
    ):
        options_elements = []
        for element in exercise_options_elements:
            options = parse_default_element_option(element, difficulty)
            if options is not None:
                options_elements.append(options)
        options_elements = self.fill_options(
            courseid, taskid, problem_id, options_elements
        )
        return self.template_helper.render(
            "exercise_options.html",
            template_folder=constants.PATH_TO_TEMPLATES,
            exercise_options=options_elements,
            PID=problem_id,
            exercise_switch=exercise_switch,
        )
