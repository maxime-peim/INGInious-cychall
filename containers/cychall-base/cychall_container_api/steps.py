import os

import utils


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