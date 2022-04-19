import os

import yaml

_default_scripts_dir = "/task/student/scripts/"
_build_configuration_filename = os.path.join(_default_scripts_dir, "build.yaml")


def _load_build_config():
    """Open existing config file"""
    with open(_build_configuration_filename, "r") as build_in:
        return yaml.safe_load(build_in)


def get_config(field_name):
    build_configuration = _load_build_config()
    field_split = field_name.split(":")
    field_configuration = build_configuration.get(field_split[0], None)

    field_split = field_name.split(":")
    if field_split[0] not in build_configuration:
        raise ValueError(f"'{field_split[0]}' field not found.")

    field_configuration = build_configuration[field_split[0]]
    if (
        isinstance(field_configuration, dict)
        and "filename" in field_configuration
        and "value" in field_configuration
    ):
        if len(field_split) > 1 and field_split[1] == "filename":
            return field_configuration["filename"]
        else:
            with open(field_configuration["value"], "rb") as fin:
                return fin.read()
    else:
        return field_configuration
