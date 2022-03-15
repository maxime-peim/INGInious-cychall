import os

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")

def get_dirs(path):
    root, dirs, files = next(os.walk(path))
    return dirs
