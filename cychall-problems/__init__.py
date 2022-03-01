# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import json
import yaml
import uuid

from flask import send_from_directory, request
from jinja2 import Environment, FileSystemLoader


from inginious.common.tasks_problems import Problem
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.task_problems import DisplayableProblem
from inginious.frontend.parsable_text import ParsableText

from . import utils, template_manager

__version__ = "0.1.dev0"

def load_configuration(path, filename="configuration.yaml"):
	configuration_path = os.path.join(path, filename)

	if not os.path.exists(configuration_path):
		raise FileNotFoundError(f"Exercice configuration file {path} should exists.")

	with open(configuration_path, 'r') as config_file:
		config = yaml.safe_load(config_file)
	return config


class StaticMockPage(INGIniousPage):
	def GET(self, path):
		return send_from_directory(os.path.join(utils.PATH_TO_PLUGIN, "static"), path)

	def POST(self, path):
		return self.GET(path)


class CychallProblem(Problem):
	"""Display an input box and check that the content is correct"""

	def __init__(self, problemid, content, translations, taskfs):
		Problem.__init__(self, problemid, content, translations, taskfs)
		self._header = str(content.get("header", ""))
		self._exercice_path = str(content.get("exercice-path", ""))
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

	_template_manager_singleton = None
		
	def __init__(self, problemid, content, translations, taskfs):
		CychallProblem.__init__(self, problemid, content, translations, taskfs)

	@classmethod
	def set_template_manager(cls, template_manager):
		if cls._template_manager_singleton is not None:
			raise ValueError("Template manager singleton already set.")
		cls._template_manager_singleton = template_manager

	@classmethod
	def get_type_name(self, language):
		return "cychall"

	def show_input(self, template_helper, language, seed):
		""" Show CychallProblem """
		header = ParsableText(self.gettext(language, self._header), "rst",
							  translation=self.get_translation_obj(language))
		exercice_configuration = load_configuration(self._exercice_path)

		return template_helper.render("cychall.html",
									  template_folder=utils.PATH_TO_TEMPLATES,
									  pid=self.get_id(),
									  exercice_name=exercice_configuration.get("name", ""),
									  difficulty=self._difficulty,
									  header=header)

	@classmethod
	def show_editbox(cls, template_helper, key, language):
		return template_helper.render("cychall_edit.html",
									  template_folder=utils.PATH_TO_TEMPLATES,
									  key=key, exercices_configurations=cls.exercices_configurations)

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

def generate_task_steps(course, taskid, task_data, task_fs):
	subproblems = task_data['problems']

	if any(subproblem["type"] == "cychall" for subproblem in subproblems.values()) and \
		not all(subproblem["type"] == "cychall" for subproblem in subproblems.values()):
		return json.dumps({"status": "error", "message": "There is at least one sub-problem of type cychall, all must be."})

	# task_fs.delete()

	n_steps = len(subproblems)
	if n_steps == 0:
		return

	task_configuration = {}

	scripts_fs = task_fs.from_subfolder("student/scripts")
	scripts_fs.ensure_exists() # Create scripts dir
	
	for stepi, subproblem in enumerate(subproblems.values(), start=1):
		exercice_path = subproblem["exercice-path"]
		to_modify = subproblem.get("modify", False)
		is_local = exercice_path.startswith(scripts_fs.prefix)

		if to_modify and not is_local:
			local_exercice_fs = scripts_fs.from_subfolder(os.path.basename(exercice_path))
			if not local_exercice_fs.exists():
				local_exercice_fs.ensure_exists()
				local_exercice_fs.copy_to(exercice_path)
			exercice_path = local_exercice_fs.prefix

		task_configuration[f"step{stepi}"] = {
			"exercice-path": exercice_path,
			"difficulty": subproblem["difficulty"],
			"next-user": f"step{stepi+1}" if stepi < len(subproblems) else "end"
		}
	
	task_fs.put("build.yaml", yaml.safe_dump(task_configuration))
	task_fs.put("run", default_run_file_content())


def init(plugin_manager, course_factory, client, plugin_config):

	paths_to_exercise_templates = plugin_config.get("exercise_templates", "")
	template_manager_singleton = template_manager.TemplateManager(course_factory, common_path=paths_to_exercise_templates)

	DisplayableCychallProblem.set_template_manager(template_manager_singleton)
	template_manager.TemplateManagerPage.set_template_manager(template_manager_singleton)

	plugin_manager.add_page('/plugins/cychall/static/<path:path>', StaticMockPage.as_view("cychallproblemstaticpage"))
	plugin_manager.add_hook("css", lambda: "/plugins/cychall/static/cychall.css")
	plugin_manager.add_hook("javascript_header", lambda: "/plugins/cychall/static/cychall.js")
	plugin_manager.add_hook('task_editor_submit', generate_task_steps)
	course_factory.get_task_factory().add_problem_type(DisplayableCychallProblem)
	
	plugin_manager.add_page('/admin/<courseid>/templates', template_manager.TemplatesList.as_view('templates'))
	plugin_manager.add_page('/admin/<courseid>/edit/templates/<templateid>', template_manager.TemplateEdit.as_view('template_edit'))
	plugin_manager.add_page('/admin/<courseid>/edit/templates/<templateid>/files', template_manager.TemplateFiles.as_view('template_files'))
	plugin_manager.add_hook('course_admin_menu', template_manager.templates_menu)
