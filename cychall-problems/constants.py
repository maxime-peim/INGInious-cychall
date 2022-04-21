import os

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")

with open(os.path.join(PATH_TO_PLUGIN, "static/default_run.py")) as default_run_fd:
    DEFAULT_RUN_PY = default_run_fd.read()

with open(os.path.join(PATH_TO_PLUGIN, "static/default_setup")) as default_setup_fd:
    DEFAULT_SETUP = default_setup_fd.read()
