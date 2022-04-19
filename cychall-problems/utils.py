import os

from inginious.common.base import load_json_or_yaml

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")


def load_build_config(task_fs):
    scripts_fs = task_fs.from_subfolder("student/scripts")
    if scripts_fs.exists("build.yaml"):
        build_config = load_json_or_yaml(os.path.join(scripts_fs.prefix, "build.yaml"))
        return build_config
