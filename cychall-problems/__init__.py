# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import json
import os

from inginious.common.base import get_json_or_yaml
from inginious.common.filesystems.local import LocalFSProvider

from . import constants, pages, utils
from .template_manager import TemplateManager

__version__ = "0.1.dev0"


class PluginMissingParameter(Exception):
    def __init__(self, parameter):
        super().__init__(f"'{parameter}' variable must be set in order to use this plugin.")

def find_matching_subproblem(build_config, problemid):
    for step in build_config["steps"]:
        if build_config["steps"][step]["problemid"] == problemid:
            return step

def generate_task_steps(course, taskid, task_data, task_fs):
    subproblems = task_data["problems"]

    is_there_cychall = any(
        subproblem["type"] == "cychall" for subproblem in subproblems.values()
    )
    is_all_cychall = all(
        subproblem["type"] == "cychall" for subproblem in subproblems.values()
    )

    if not is_there_cychall:
        return

    elif not is_all_cychall:
        return json.dumps(
            {
                "status": "error",
                "message": "There is at least one sub-problem of type cychall, all must be.",
            }
        )

    original_build_config = utils.load_build_config(task_fs)
    student_fs = task_fs.from_subfolder("student")
    scripts_fs = student_fs.from_subfolder("scripts")
    scripts_fs.ensure_exists()

    if original_build_config is not None:
        old_fs = task_fs.from_subfolder("old")
        if old_fs.exists():
            old_fs.delete()
        os.rename(task_fs.prefix + "student", task_fs.prefix + "old") # Move files to task/old
        student_fs.ensure_exists()

    task_configuration = {"steps": {}}
    for stepi, subproblem_id in enumerate(subproblems.keys(), start=1):
        subproblem = subproblems[subproblem_id]
        step_name = f"step{stepi}"
        template_name = os.path.basename(subproblem["exercise-path"])
        step_fs = student_fs.from_subfolder(step_name)

        replace = True
        if original_build_config is not None: # Do not replace files if problemid and templateid are the same as existing build config
            previous_step = find_matching_subproblem(original_build_config, subproblem_id)
            if previous_step is not None and original_build_config["steps"][previous_step].get("template", None) == template_name:
                step_fs.ensure_exists()
                step_fs.copy_to(old_fs.prefix + previous_step) # Copy files from previous state
                replace = False

        if replace:
            if step_fs.exists():
                step_fs.delete()
            step_fs.ensure_exists()
            step_fs.copy_to(subproblem["exercise-path"]) # Copy files from template

        task_configuration["steps"][step_name] = {
            **(subproblem.get("options", {})),
            "step-switch": subproblem["step-switch"],
            "problemid": subproblem_id,
            "template": template_name,
            "difficulty": subproblem.get("difficulty", "Easy"),
            "next-user": f"step{stepi+1}" if stepi < len(subproblems) else "end",
        }

    yaml_content = get_json_or_yaml(".__build.yaml", task_configuration)

    scripts_fs.put(".__build.yaml", yaml_content)

    if not task_fs.exists("run.py"): # Add default run file
        task_fs.put("run.py", constants.DEFAULT_RUN_PY)
    
    if original_build_config is not None: # Delete previous state
        if old_fs.exists():
            old_fs.delete()


def init(plugin_manager, course_factory, client, plugin_config):

    default_templates_fs = LocalFSProvider(
        os.path.split(course_factory.get_fs().prefix[:-1])[0]
    ).from_subfolder("templates")
    
    if "templates_folder" not in plugin_config:
        default_templates_fs.ensure_exists()
    
    paths_to_exercise_templates = plugin_config.get("templates_folder", default_templates_fs.prefix)
    TemplateManager.init_singleton(
        course_factory, common_path=paths_to_exercise_templates
    )

    plugin_manager.add_page(
        "/plugins/cychall/static/<path:path>",
        pages.problem.StaticMockPage.as_view("cychallproblemstaticpage"),
    )
    plugin_manager.add_hook("css", lambda: "/plugins/cychall/static/cychall.css")
    plugin_manager.add_hook(
        "javascript_header", lambda: "/plugins/cychall/static/cychall.js"
    )
    plugin_manager.add_hook("task_editor_submit", generate_task_steps)
    course_factory.get_task_factory().add_problem_type(
        pages.problem.DisplayableCychallProblem
    )

    plugin_manager.add_page(
        "/admin/<courseid>/templates", pages.template.TemplatesList.as_view("templates")
    )
    plugin_manager.add_page(
        "/admin/<courseid>/templates/edit/<templateid>",
        pages.template.TemplateEdit.as_view("template_edit"),
    )
    plugin_manager.add_page(
        "/admin/<courseid>/templates/edit/<templateid>/files",
        pages.template.TemplateFiles.as_view("template_files"),
    )
    plugin_manager.add_page(
        "/admin/<courseid>/edit/task/<taskid>/exercise_options",
        pages.options.ExerciseConfigurationOptions.as_view("exercise_options"),
    )
    plugin_manager.add_hook("course_admin_menu", pages.template.templates_menu)
