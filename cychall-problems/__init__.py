# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import json
import yaml

from inginious.common.base import get_json_or_yaml

from . import constants, pages
from .template_manager import TemplateManager

__version__ = "0.1.dev0"


def generate_task_steps(course, taskid, task_data, task_fs):
    subproblems = task_data['problems']

    is_there_cychall = any(subproblem["type"] == "cychall" for subproblem in subproblems.values())
    is_all_cychall = all(subproblem["type"] == "cychall" for subproblem in subproblems.values())

    if not is_there_cychall:
        return
    
    elif not is_all_cychall:
        return json.dumps({"status": "error", "message": "There is at least one sub-problem of type cychall, all must be."})
    
    task_fs.delete()
    student_fs = task_fs.from_subfolder("student")
    scripts_fs = student_fs.from_subfolder("scripts")
    scripts_fs.ensure_exists()

    task_configuration = {"steps": {}}
    for stepi, subproblem in enumerate(subproblems.values(), start=1):
        step_name = f"step{stepi}"
        step_fs = student_fs.from_subfolder(step_name)
        step_fs.copy_to(subproblem["exercise-path"])

        task_configuration["steps"][step_name] = {
            **(subproblem.get("options", {})),
            "difficulty": subproblem["difficulty"],
            "next-user": f"step{stepi+1}" if stepi < len(subproblems) else "end"
        }

    yaml_content = get_json_or_yaml("build.yaml", task_configuration)
    
    scripts_fs.put("build.yaml", yaml_content)

    task_fs.put("run", constants.DEFAULT_RUN)


def init(plugin_manager, course_factory, client, plugin_config):

    paths_to_exercise_templates = plugin_config.get("templates_folder", "")
    TemplateManager.init_singleton(course_factory, common_path=paths_to_exercise_templates)

    plugin_manager.add_page('/plugins/cychall/static/<path:path>', pages.problem.StaticMockPage.as_view("cychallproblemstaticpage"))
    plugin_manager.add_hook("css", lambda: "/plugins/cychall/static/cychall.css")
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/cychall/static/cychall.js")
    plugin_manager.add_hook('task_editor_submit', generate_task_steps)
    course_factory.get_task_factory().add_problem_type(pages.problem.DisplayableCychallProblem)
    
    plugin_manager.add_page('/admin/<courseid>/templates', pages.template.TemplatesList.as_view('templates'))
    plugin_manager.add_page('/admin/<courseid>/templates/edit/<templateid>', pages.template.TemplateEdit.as_view('template_edit'))
    plugin_manager.add_page('/admin/<courseid>/templates/edit/<templateid>/files', pages.template.TemplateFiles.as_view('template_files'))
    plugin_manager.add_page('/admin/<courseid>/edit/task/<taskid>/exercise_options', pages.options.ExerciseConfigurationOptions.as_view('exercise_options'))
    plugin_manager.add_hook('course_admin_menu', pages.template.templates_menu)
