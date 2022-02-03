import os

import utils


is_step_path = \
    lambda path: os.path.basename(path).startswith("step")


def count_steps(path="/task/student/scripts"):
    return sum(is_step_path(p) for p in utils.get_directory_content(path))


def add_sudoers_nopasswd(privileged_user, normal_user, command):
    with open("/etc/sudoers.d/chellenge", "a") as sudoers:
        sudoers.write(f"{normal_user} ALL=({privileged_user}) NOPASSWD: {command}\n")