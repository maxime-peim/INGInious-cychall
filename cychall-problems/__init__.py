# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import json
import yaml

from . import template_manager, constants, pages

__version__ = "0.1.dev0"


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
	task_fs.put("run", constants.DEFAULT_RUN)


def init(plugin_manager, course_factory, client, plugin_config):

	paths_to_exercise_templates = plugin_config.get("templates_folder", "")
	template_manager_singleton = template_manager.TemplateManager(course_factory, common_path=paths_to_exercise_templates)

	pages.problem.DisplayableCychallProblem.set_template_manager(template_manager_singleton)
	pages.template.TemplateManagerPage.set_template_manager(template_manager_singleton)

	plugin_manager.add_page('/plugins/cychall/static/<path:path>', pages.problem.StaticMockPage.as_view("cychallproblemstaticpage"))
	plugin_manager.add_hook("css", lambda: "/plugins/cychall/static/cychall.css")
	plugin_manager.add_hook("javascript_header", lambda: "/plugins/cychall/static/cychall.js")
	plugin_manager.add_hook('task_editor_submit', generate_task_steps)
	course_factory.get_task_factory().add_problem_type(pages.problem.DisplayableCychallProblem)
	
	plugin_manager.add_page('/admin/<courseid>/templates', pages.template.TemplatesList.as_view('templates'))
	plugin_manager.add_page('/admin/<courseid>/templates/edit/<templateid>', pages.template.TemplateEdit.as_view('template_edit'))
	plugin_manager.add_page('/admin/<courseid>/templates/edit/<templateid>/files', pages.template.TemplateFiles.as_view('template_files'))
	plugin_manager.add_hook('course_admin_menu', pages.template.templates_menu)
