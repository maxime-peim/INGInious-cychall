import os
import yaml


CYCHALL_DIR = "/.__cychall"
WRAPPER_DIR = os.path.join(CYCHALL_DIR, "wrappers")
STUDENT_DIR = "/task/student"
SCRIPT_DIR = os.path.join(STUDENT_DIR, "scripts")

BUILD_FILENAME = ".__build.yaml"
STEP_FILENAME = ".__step.yaml"
FLAGS_FILENAME = ".__flags.yaml"

BUILD_FILE_PATH = os.path.join(SCRIPT_DIR, BUILD_FILENAME)
STEP_FILE_PATH = os.path.join(SCRIPT_DIR, STEP_FILENAME)
GENERATED_FLAGS_FILE_PATH = os.path.join(SCRIPT_DIR, FLAGS_FILENAME)
STUDENT_FLAGS_FILE_PATH = os.path.join(STUDENT_DIR, FLAGS_FILENAME)


def _load_build_config():
    """Open existing config file"""
    with open(BUILD_FILE_PATH, "r") as build_in:
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
