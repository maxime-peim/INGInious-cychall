# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import json
import yaml
import uuid

from flask import send_from_directory
from jinja2 import Environment, FileSystemLoader

from inginious.common.tasks_problems import Problem
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.task_problems import DisplayableProblem
from inginious.frontend.parsable_text import ParsableText

__version__ = "0.1.dev0"

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")


def get_dirs(path):
    root, dirs, files = next(os.walk(path))
    return dirs

def load_config(path):
    with open(path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config


class StaticMockPage(INGIniousPage):
    def GET(self, path):
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)

    def POST(self, path):
        return self.GET(path)


class CychallProblem(Problem):
    """Display an input box and check that the content is correct"""

    def __init__(self, problemid, content, translations, taskfs):
        Problem.__init__(self, problemid, content, translations, taskfs)
        self._header = str(content.get("header", ""))
        self._exercice = str(content.get("exercice", ""))
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


class DisplayableCychallProblem(CychallProblem, DisplayableProblem):
    """ A displayable match problem """

    __paths_to_exercices = []

    def __init__(self, problemid, content, translations, taskfs):
        CychallProblem.__init__(self, problemid, content, translations, taskfs)

    @classmethod
    def add_path_to_exercices(cls, path):
        if os.path.exists(path):
            cls.__paths_to_exercices.append(path)

    @classmethod
    def get_all_exercices_config(cls):
        configs = []
        for path in cls.__paths_to_exercices:
            for exercice_folder in get_dirs(path):
                exercice_path = os.path.join(path, exercice_folder)
                config_path = os.path.join(exercice_path, "configuration.yaml")

                if not os.path.exists(config_path):
                    raise FileNotFoundError(f"Exercice configuration file {config_path} should exists.")

                config = load_config(config_path)
                config["__id"] = uuid.uuid4()
                config["__path"] = exercice_path
                config["__folder"] = exercice_folder
                
                configs.append(config)
        return configs

    @classmethod
    def get_type_name(self, language):
        return "cychall"

    def show_input(self, template_helper, language, seed):
        """ Show CychallProblem """
        header = ParsableText(self.gettext(language, self._header), "rst",
                              translation=self.get_translation_obj(language))
        return template_helper.render("cychall.html",
                                      template_folder=PATH_TO_TEMPLATES,
                                      inputId=self.get_id(),
                                      exercice=self._exercice,
                                      difficulty=self._difficulty,
                                      header=header)

    @classmethod
    def show_editbox(cls, template_helper, key, language):
        return template_helper.render("cychall_edit.html", 
                                      template_folder=PATH_TO_TEMPLATES, 
                                      key=key, exercices_config=cls.get_all_exercices_config())

    @classmethod
    def show_editbox_templates(cls, template_helper, key, language):
        return ""


def default_run_file_content():
	# Temporary function
	return """#!/bin/bash
    # Configuration has to be done directly onto the student container
    ssh_student --user step1 --script-as-root --setup-script "generate-steps"
    check-flag --student-flag-path /task/student/answer --correct-flag-path /task/student/end/flag
    """

def add_next_step(stepi, exercice_template, scripts_fs, last_step=False):
    current_user = f'step{stepi}'
    next_user = f'step{stepi+1}' if not last_step else 'end'

    step_fs = scripts_fs.from_subfolder(current_user)
    step_fs.ensure_exists() # Create step dir
    
    step_fs.copy_to(exercice_template) # Copy template files to step dir
    
    # TODO: needed for all step files
    if step_fs.exists("post"): # Set file owner(s) in post script
        env = Environment(loader=FileSystemLoader(step_fs.prefix))
        post_script_template = env.get_template('post')
        post_script_parsed = post_script_template.render(current_user=current_user, next_user=next_user)
        step_fs.put("post", post_script_parsed)

def generate_task_steps(course, taskid, task_data, task_fs):
    subproblems = task_data['problems']

    if any(subproblem["type"] == "cychall" for subproblem in subproblems.values()) and \
        not all(subproblem["type"] == "cychall" for subproblem in subproblems.values()):
        return json.dumps({"status": "error", "message": "There is at least one sub-problem of type cychall, all must be."})

    task_fs.delete()

    n_steps = len(subproblems)
    if n_steps == 0:
        return

    scripts_fs = task_fs.from_subfolder("student/scripts")
    scripts_fs.ensure_exists() # Create scripts dir
    
    for stepi, subproblem in enumerate(subproblems.values(), start=1):
        print(stepi, subproblem["exercice"])
        add_next_step(stepi, subproblem["exercice"], scripts_fs, stepi==n_steps)
    
    task_fs.put("run", default_run_file_content())


def init(plugin_manager, course_factory, client, plugin_config):
    path_to_exercices = plugin_config.get("exercice_templates", "")
    DisplayableCychallProblem.add_path_to_exercices(path_to_exercices)

    plugin_manager.add_page('/plugins/cychall/static/<path:path>', StaticMockPage.as_view("cychallproblemstaticpage"))
    plugin_manager.add_hook("css", lambda: "/plugins/cychall/static/cychall.css")
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/cychall/static/cychall.js")
    plugin_manager.add_hook('task_editor_submit', generate_task_steps)
    course_factory.get_task_factory().add_problem_type(DisplayableCychallProblem)