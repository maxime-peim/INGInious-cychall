import os
import pwd
import shutil
import yaml

import inginious_container_api.utils
from inginious_container_api.run_types import run_types

import utils
import flag
import config

_step_configuration_filename = os.path.join(config._default_scripts_dir, '.__step.yaml')

def _load_step_config():
    with open(_step_configuration_filename, 'r') as step_in:
        return yaml.safe_load(step_in)

def get_config(field_name=None):
    """" Returns the specified problem answer in the form 
         problem: problem id
         Returns string, or bytes if a file is loaded
    """
    configuration = _load_step_config()
    if field_name is None:
        return configuration
    
    field_split = field_name.split(":")
    step_configuration = configuration[field_split[0]]
    if isinstance(step_configuration, dict) and "filename" in step_configuration and "value" in step_configuration:
        if len(field_split) > 1 and field_split[1] == 'filename':
            return step_configuration["filename"]
        else:
            with open(step_configuration["value"], 'rb') as fin:
                return fin.read()
    else:
        return step_configuration


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

    def _create_associated_user(self):
        """
            Create the user associated with the challenge
        """
        utils.create_user(self._name, groups=["worker"])
        self._user_infos = pwd.getpwnam(self._name)

    def _detect_script_command(self, script_name):
        script_path = os.path.join(self._step_folder, script_name)

        if os.path.exists(script_path):
            return [script_path]
        for ext, cmd in run_types.items():
            if os.path.exists(script_path + ext):
                return cmd + [script_path + ext]

        return None

    def _set_default_permissions(self):
        if self._user_infos is None:
            return
        
        os.chmod(self._step_folder, 0o700)
        os.chown(self._step_folder, self._user_infos.pw_uid, 4242)

        for root, dirs, files in os.walk(self._step_folder):
            for momo in dirs + files:
                fullpath = os.path.join(root, momo)
                if fullpath not in self._setup_files:
                    os.chown(os.path.join(root, momo), self._user_infos.pw_uid, 4242)

    def _clean_files(self):
        utils.remove_files(
            os.path.join(self._step_folder, file)
            for file in self._step_files
        )

    def _write_step_config(self):
        with open(_step_configuration_filename, 'w') as step_out:
            yaml.safe_dump(self._configuration, step_out)
    
    def _allow_remove_passwd(self):
        with open("/etc/sudoers", "a") as sudoers:
            sudoers.write(f"{self._name} ALL=(root) NOPASSWD: /usr/bin/passwd -d {self._name}\n")

    def build(self):
        # if there is a missing step, advertise
        if not os.path.exists(self._step_folder):
            raise StepGenerationError(f"{self._step_folder} folder does not exist.")
        self._step_files = os.listdir(self._step_folder)

        self._create_associated_user()

        setup_command = self._detect_script_command("setup")
        
        self._allow_remove_passwd()

        self._write_step_config()
        
        if setup_command is not None:
            inginious_container_api.utils.execute_process(setup_command, user=utils.get_username(), cwd=self._step_folder)

        # self._set_default_permissions()

        self._clean_files()


class EndStep(Step):

    def __init__(self, general_output_folder):
        super().__init__("end", None, general_output_folder)

    def build(self):
        os.makedirs(self._step_folder, exist_ok=True)
        self._create_associated_user()
        
        self._allow_remove_passwd()
        
        flag.write_flag(
            flag.generate_flag(),
            os.path.join(self._step_folder, "flag")
        )

        self._set_default_permissions()