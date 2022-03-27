import os

from flask import request
import copy

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage

from .. import constants
from ..template_manager import TemplateManagerHandler

def check_option_format(option_dict):
    return "id" in option_dict and "type" in option_dict

class ExerciseConfigurationOptions(INGIniousAdminPage, TemplateManagerHandler):
    
    def POST_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ

        self.get_course_and_check_rights(courseid, allow_all_staff=False)

        user_input = request.form
        if user_input.get('problem_id') is not None and user_input.get('difficulty') is not None and user_input.get('exercise-path') is not None:
            templateid = os.path.basename(user_input.get('exercise-path'))
            exercise_options_elements = self._template_manager.get_template(courseid, templateid).elements
            exercise_switch = self._template_manager.get_template(courseid, templateid).next_step_switch
            return self.show_exercise_options_tab(user_input.get("problem_id"), exercise_options_elements, user_input.get("difficulty"), exercise_switch)
        return self.template_helper.render("exercise_options.html", template_folder=constants.PATH_TO_TEMPLATES)
    
    def check_default_attributes(self, element, check_type=True):
        res = False
        if "id" in element and (not check_type or (check_type and "type" in element)):
            if "label" not in element:
                element["label"] = element["id"]
            res = True
        return res

    def parse_default_element_option(self, problem_id, element, difficulty):
        if self.check_default_attributes(element):
            if "modes" not in element or difficulty in element["modes"]: # Modes not specified -> available everywhere
                return self.parse_element_specific_options(problem_id, element)

    def parse_element_specific_options(self, problem_id, element):
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
                if self.check_default_attributes(button, check_type=False):
                    valid_buttons.append(button)
            
            if not valid_buttons:
                return None
            
            element["buttons"] = valid_buttons

        else: # Default case: cancel
            return None

        element_copy = copy.deepcopy(element)
        keys = element.keys()
        for key in keys:
            if key not in options:
                element_copy.pop(key)
        return element_copy
    
    def show_exercise_options_tab(self, problem_id, exercise_options_elements, difficulty, exercise_switch):
        options_elements = []
        for element in exercise_options_elements:
            options = self.parse_default_element_option(problem_id, element, difficulty)
            if options is not None:
                options_elements.append(options)
        return self.template_helper.render("exercise_options.html", template_folder=constants.PATH_TO_TEMPLATES, exercise_options=options_elements, PID=problem_id, exercise_switch=exercise_switch)