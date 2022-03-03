import os

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")

with open(os.path.join(PATH_TO_PLUGIN, "static/default_run")) as default_run_fd:
	DEFAULT_RUN = default_run_fd.read()