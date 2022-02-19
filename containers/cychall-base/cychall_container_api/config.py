# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import re
import yaml
import datetime

_scripts_path = '/task/student/scripts/'
_build_configuration_filename = 'build.yaml'
_step_configuration_filename = 'step_configuration.yaml'

def _load_config():
    """ Open existing config file """
    with open(os.path.join(_scripts_path, _step_configuration_filename), 'r') as configuration_fd:
        return yaml.safe_load(configuration_fd)


def get_config(field_name):
    """" Returns the specified problem answer in the form 
         problem: problem id
         Returns string, or bytes if a file is loaded
    """
    configuration = _load_config()
    field_split = value_name.split(":")
    step_configuration = configuration[field_split[0]]
    if isinstance(step_configuration, dict) and "filename" in step_configuration and "value" in step_configuration:
        if len(field_split) > 1 and field_split[1] == 'filename':
            return step_configuration["filename"]
        else:
            return open(step_configuration["value"], 'rb').read()
    else:
        return step_configuration

