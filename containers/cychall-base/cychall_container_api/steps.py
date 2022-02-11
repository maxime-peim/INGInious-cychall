import os
import pwd
import shutil

import utils
import flag

import inginious_container_api.utils
from inginious_container_api.run_types import run_types


is_step_path = \
    lambda path: os.path.basename(path).startswith("step")


def count_steps(path="/task/student/scripts"):
    return sum(is_step_path(p) for p in utils.get_directory_content(path))


def add_sudoers_nopasswd(privileged_user, normal_user, command):
    with open("/etc/sudoers.d/chellenge", "a") as sudoers:
        sudoers.write(f"{normal_user} ALL=({privileged_user}) NOPASSWD: {command}\n")


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

    def __init__(self, name, general_input_folder, general_output_folder):
        # get the current user name and scripts source and destination
        self._name = name
        self._input_folder = None if general_input_folder is None else os.path.join(general_input_folder, name)
        self._output_folder = None if general_output_folder is None else os.path.join(general_output_folder, name)
        self._user_infos = None
        self._setup_files = []
        
        if self._input_folder is not None:
            # if there is a missing step, advertise
            if not os.path.exists(self._input_folder):
                raise StepGenerationError(f"{self._input_folder} folder does not exist.")

            self._setup_files = [
                os.path.join(self._output_folder, p)
                for p in os.listdir(self._input_folder)
            ]

    def _copy_step_files(self):
        """
            Copy the sources to build the challenge
        """
        try:
            shutil.copytree(self._input_folder, self._output_folder)
        except shutil.Error:
            raise StepGenerationError("Error while copying a step content.")

    def _create_associated_user(self):
        """
            Create the user associated with the challenge
        """
        utils.create_user(self._name, groups=["worker"])
        self._user_infos = pwd.getpwnam(self._name)

    def _detect_script_command(self, script_name):
        script_path = os.path.join(self._output_folder, script_name)

        if os.path.exists(script_path):
            return [script_path]
        for ext, cmd in run_types.items():
            if os.path.exists(script_path + ext):
                return cmd + [script_path + ext]

        return None

    def _set_default_permissions(self):
        if self._user_infos is None:
            return
        
        os.chmod(self._output_folder, 0o700)
        os.chown(self._output_folder, self._user_infos.pw_uid, 4242)

        for root, dirs, files in os.walk(self._output_folder):
            for momo in dirs + files:
                fullpath = os.path.join(root, momo)
                if fullpath not in self._setup_files:
                    os.chown(os.path.join(root, momo), self._user_infos.pw_uid, 4242)

    def _clean_files(self):
        utils.remove_files(self._setup_files)

    def build(self):
        self._create_associated_user()
        self._copy_step_files()

        setup_command = self._detect_script_command("setup")
        post_command = self._detect_script_command("post")
        
        if setup_command is not None:
            inginious_container_api.utils.execute_process(setup_command, user=utils.get_username(), cwd=self._output_folder)

        self._set_default_permissions()

        if post_command is not None:
            inginious_container_api.utils.execute_process(post_command, user=utils.get_username(), cwd=self._output_folder)

        self._clean_files()


class EndStep(Step):

    def __init__(self, general_output_folder):
        super().__init__("end", None, general_output_folder)

    def build(self):
        os.makedirs(self._output_folder, exist_ok=True)
        self._create_associated_user()

        flag.write_flag(
            flag.generate_flag(),
            os.path.join(self._output_folder, "flag")
        )

        self._set_default_permissions()