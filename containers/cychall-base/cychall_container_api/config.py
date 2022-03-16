import os
import yaml

_default_scripts_dir = '/task/student/scripts/'
_build_configuration_filename = os.path.join(_default_scripts_dir, 'build.yaml')

def _load_build_config():
    """ Open existing config file """
    with open(_build_configuration_filename, 'r') as build_in:
        return yaml.safe_load(build_in)

def get_config(field_name):
    """" Returns the specified problem answer in the form 
         problem: problem id
         Returns string, or bytes if a file is loaded
    """
    configuration = _load_build_config()
    field_split = field_name.split(":")
    build_configuration = configuration[field_split[0]]
    if isinstance(build_configuration, dict) and "filename" in build_configuration and "value" in build_configuration:
        if len(field_split) > 1 and field_split[1] == 'filename':
            return build_configuration["filename"]
        else:
            with open(build_configuration["value"], 'rb') as fin:
                return fin.read()
    else:
        return build_configuration