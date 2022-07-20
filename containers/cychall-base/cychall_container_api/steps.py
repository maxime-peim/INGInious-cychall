import os
import pwd
import yaml

import flag
import utils
import config
import inginious_container_api.utils
from inginious_container_api.run_types import run_types

_step_configuration_filename = os.path.join(config.SCRIPT_DIR, ".__step.yaml")


def _load_step_config():
    with open(_step_configuration_filename, "r") as step_in:
        return yaml.safe_load(step_in)


def get_config(field_name=None):
    step_configuration = _load_step_config()
    if field_name is None:
        return step_configuration

    field_split = field_name.split(":")
    if field_split[0] not in step_configuration:
        raise ValueError(f"'{field_split[0]}' field not found.")

    field_configuration = step_configuration[field_split[0]]
    if (
        isinstance(step_configuration, dict)
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


def fix_output_directory_permissions(path):
    head, tail = path, " "

    while head != "" and tail != "":
        os.chown(head, 4242, 4242)
        os.chmod(head, 0o770)
        head, tail = os.path.split(head)

    last = head or tail
    if last != "" and last != "/":
        os.chown(last, 4242, 4242)
        os.chmod(last, 0o770)


class StepGenerationError(Exception):
    pass


class Step:
    def __init__(self, name, configuration, general_output_folder):
        # get the current user name and scripts source and destination
        self._name = name
        self._configuration = {} if configuration is None else configuration
        self._step_folder = os.path.join(general_output_folder, name)
        self._user_infos = None
        self._setup_files = []

        self._configuration["current-user"] = name

        self._next_user = self._configuration.get("next-user", "nobody")
        self._next_user_infos = pwd.getpwnam(self._next_user)

    def _create_associated_user(self):
        """
        Create the user associated with the challenge
        """
        home_dir = os.path.join("/task/student", self._name)
        utils.create_user(
            self._name,
            create_self_group=True,
            home_dir=home_dir,
            shell="/bin/bash",
            groups=["worker"],
            copy_skel=False,
        )
        self._user_infos = pwd.getpwnam(self._name)

    def _detect_script_command(self, script_name):
        script_path = os.path.join(self._step_folder, script_name)

        if os.path.exists(script_path):
            return [script_path]
        for ext, cmd in run_types.items():
            if os.path.exists(script_path + ext):
                return cmd + [script_path + ext]

        return None

    def _set_step_folder_defaults(self):
        if self._user_infos is None:
            return

        utils.copy_skel_files(self._step_folder)

        os.chmod(self._step_folder, 0o550)
        os.chown(
            self._step_folder, self._user_infos.pw_uid, self._next_user_infos.pw_uid
        )

    def _clean_files(self):
        utils.remove_files(
            os.path.join(self._step_folder, file) for file in self._step_files
        )

    def _write_step_config(self):
        with open(_step_configuration_filename, "w") as step_out:
            yaml.safe_dump(self._configuration, step_out)

    def _allow_remove_passwd(self):
        with open("/etc/sudoers", "a") as sudoers:
            sudoers.write(
                f"{self._name} ALL=(root) NOPASSWD: /usr/bin/passwd -d {self._name}\n"
            )

    def build(self):
        # if there is a missing step, advertise
        if not os.path.exists(self._step_folder):
            raise StepGenerationError(f"{self._step_folder} folder does not exist.")
        self._step_files = os.listdir(self._step_folder)

        self._create_associated_user()

        setup_command = self._detect_script_command("setup")

        self._write_step_config()

        if setup_command is not None:
            inginious_container_api.utils.execute_process(
                setup_command, user=utils.get_username(), cwd=self._step_folder
            )

        self._set_step_folder_defaults()

        self._clean_files()


class EndStep(Step):
    def __init__(self, general_output_folder):
        super().__init__("end", None, general_output_folder)

    def build(self):
        os.makedirs(self._step_folder, exist_ok=True)
        self._create_associated_user()

        flag_value = flag.generate_flag()
        with open(os.path.join(self._step_folder, "flag"), "w") as fp:
            fp.write(
                f"""Well done, you have found the final flag!
Don't forget to use the `found-flag` command to validate the flag.

Flag: {flag_value}\n\n"""
            )
        flag.add_flag(self._name, flag_value)

        utils.recursive_chown(self._step_folder, self._name, "worker", inside=True)

        self._set_step_folder_defaults()
