import grp
import os
import pwd
import sys
from jinja2 import Environment, FileSystemLoader

import steps
import inginious_container_api.utils


def extract_value(direct_value, value_path):
    if direct_value is not None:
        return direct_value

    if value_path is None:
        sys.stderr.buffer.write(b"No value given to check to extact.")
        sys.exit(2)

    try:
        with open(value_path) as fin:
            return fin.read()
    except OSError:
        sys.stderr.buffer.write(b"Cannot read value from file.")
        sys.exit(2)


def copy_skel_files(home_dir):
    return inginious_container_api.utils.execute_process(
        ["/usr/bin/cp", "-a", "/etc/skel/.", home_dir], internal_command=True
    )


def create_user(
    name,
    uid=None,
    gid=None,
    home_dir=None,
    shell=None,
    groups=None,
    create_self_group=False,
    copy_skel=True,
):
    options = [name]

    home_dir = "/task" if home_dir is None else home_dir

    try:
        os.makedirs(home_dir, exist_ok=True)
    except OSError as e:
        sys.stderr.buffer.write(b"An error occured while adding a new user:\n")
        sys.stderr.buffer.write(str(e).encode())
        sys.exit(2)

    options += ["--home-dir", home_dir]

    if create_self_group:
        options.append("--user-group")
    elif gid is not None:
        options += ["--gid", str(gid)]

    if groups is not None and len(groups) > 0:
        options += ["--groups", ",".join(groups)]

    # create the new user, in his own group
    if uid is not None:
        options += ["--uid", str(uid)]

    if shell is not None:
        options += ["--shell", shell]

    stdout, stderr = inginious_container_api.utils.execute_process(
        ["/usr/sbin/useradd", *options], internal_command=True
    )
    if copy_skel:
        stdout, stderr = copy_skel_files(home_dir)

    # if stderr != "":
    #     sys.stderr.buffer.write(b'An error occured while adding a new user:\n')
    #     sys.stderr.buffer.write(stderr)
    #     sys.exit(2)


def get_directory_content(path):
    """
    Return the content of a directory.
    """
    if not os.path.isdir(path):
        return []
    return os.listdir(path)


def get_username():
    return pwd.getpwuid(os.getuid()).pw_name


def get_home(username):
    return pwd.getpwnam(username).pw_dir


def get_uid(username):
    return pwd.getpwnam(username).pw_uid


def get_gid(group_name):
    return grp.getgrnam(group_name).gr_gid


def remove_files(paths):
    for path in paths:
        try:
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)
        except FileNotFoundError:
            continue


def get_all_parts_path(path):
    parts = []
    head, tail = os.path.split(path)

    while head != "" and tail != "":
        parts.append(tail)
        head, tail = os.path.split(head)

    parts.append(head or tail)
    return parts[::-1]


def parse(infile, render_parameters=None, extensions=None):
    extensions = [] if extensions is None else extensions
    render_parameters = {} if render_parameters is None else render_parameters
    env = Environment(
        loader=FileSystemLoader(os.path.dirname(os.path.abspath(infile))),
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=extensions,
    )
    template = env.get_template(os.path.basename(infile))
    return template.render(**render_parameters)


def parse_template(outfile, infile):
    parsed = parse(
        infile,
        {"options": steps.get_config()},
        extensions=["jinja2_ansible_filters.AnsibleCoreFiltersExtension"],
    )

    # Do the real job
    try:
        with open(outfile, "w") as out:
            out.write(parsed)
    except IOError as e:
        sys.stderr.write("Error: " + str(e))
        sys.exit(2)
    except ValueError as e:
        sys.stderr.write(f"Input is not compatible: {e}")
        sys.exit(2)


def compile_gcc(c_file, outfile, command=None, remove_source=False):
    if not os.path.isfile(c_file):
        sys.stderr.write("Input file does not exist.")
        sys.exit(2)

    if command is None:
        os.system(f"gcc -o {outfile} {c_file}")
        # stdout, stderr = inginious_container_api.utils.execute_process( ["gcc", "-o", outfile, c_file], internal_command=True, cwd=os.getcwd(), user=pwd.getpwuid(os.getuid()).pw_name)
    else:
        os.system(command)
        # stdout, stderr = inginious_container_api.utils.execute_process(command.split(), internal_command=True, cwd=os.getcwd(), user=pwd.getpwuid(os.getuid()).pw_name)

    """if stderr != "":
        sys.stderr.buffer.write(b'An error occured while compiling:\n')
        sys.stderr.buffer.write(stderr)
        sys.exit(2)"""

    if remove_source:
        os.remove(c_file)


def recursive_chown(path, username, group_name, inside=False):
    if not os.path.exists(path):
        raise ValueError(f"{path} does not exists.")

    owner_uid = get_uid(username)
    owner_gid = get_gid(group_name)

    if os.path.isfile(path):
        os.chown(path, owner_gid, owner_gid)
    elif os.path.isdir(path):
        if not inside:
            os.chown(path, owner_uid, owner_gid)
        for root, dirs, files in os.walk(path):
            for momo in dirs + files:
                fullpath = os.path.join(root, momo)
                os.chown(fullpath, owner_uid, owner_gid)
    else:
        raise ValueError(f"{path} is not a folder nor a file.")
