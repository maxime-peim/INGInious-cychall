import os
import sys
import subprocess
import shlex
import grp
import hashlib
import pwd

from jinja2 import Environment, FileSystemLoader
import inginious_container_api.utils
import cychall_container_api.steps as steps

def extract_value(direct_value, value_path):
    if direct_value is not None:
        return direct_value
    
    if value_path is None:
        sys.stderr.buffer.write(b'No value given to check to extact.')
        sys.exit(2)

    try:
        with open(value_path) as fin:
            return fin.read()
    except OSError:
        sys.stderr.buffer.write(b'Cannot read value from file.')
        sys.exit(2)


def create_user(name, uid=None, gid=None, home_dir=None, groups=None, create_group=False):
    create_group |= groups is None
    options = [name]

    # create a new group for the user, with the name of the user
    if gid is not None or create_group:
        groupadd_options = [] if gid is None else ['--gid', str(gid)]
        options += ['-g', name]
        stdout, stderr = inginious_container_api.utils.execute_process(['groupadd', *groupadd_options, name], internal_command=True)
    else:
        options += ['-g', groups[0]]
        groups.pop(0)

    # if stderr != "":
    #     sys.stderr.buffer.write(b'An error occured while adding a new user group:\n')
    #     sys.stderr.buffer.write(stderr)
    #     sys.exit(2)

    # create the new user, in his own group
    if uid is not None:
        options += ['--uid', str(uid)]

    home_dir = home_dir or f'/task'
    
    try:
        os.makedirs(home_dir, exist_ok=True)
    except OSError as e:
        sys.stderr.buffer.write(b'An error occured while adding a new user:\n')
        sys.stderr.buffer.write(str(e).encode())
        sys.exit(2)

    options += ['--home-dir', home_dir]

    stdout, stderr = inginious_container_api.utils.execute_process(['useradd', *options], internal_command=True)

    # if stderr != "":
    #     sys.stderr.buffer.write(b'An error occured while adding a new user:\n')
    #     sys.stderr.buffer.write(stderr)
    #     sys.exit(2)

    if groups is not None:
        # and add the new user to additional groups
        inginious_container_api.utils.execute_process(['usermod', '-a', '-G', *groups, name], internal_command=True)


def get_directory_content(path):
    """
        Return the content of a directory.
    """
    if not os.path.isdir(path):
        return []
    return os.listdir(path)


def get_username():
    return pwd.getpwuid(os.getuid()).pw_name


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

def get_wrapper(name):
    wrappers = get_directory_content(os.path.join('/', 'bin', 'ingi-wrappers'))
    for w in wrappers:
        if w == name:
            return os.path.join('/', 'bin', 'ingi-wrappers', name)
        elif os.path.splitext(w)[0] == name:
            return os.path.join('/', 'bin', 'ingi-wrappers', w)

def add_wrapper(outfile, executable, wrapper_name, command=None):
    step_configuration = steps.get_config()
    wrapper_path = get_wrapper(wrapper_name)

    if wrapper_path is None:
        sys.stderr.write("Invalid wrapper name")
        sys.exit(2)

    env = Environment(loader = FileSystemLoader(os.path.dirname(wrapper_path)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(os.path.basename(wrapper_path))

    if command is None:
        command = "./" + executable

    try:
        wrapper_file = os.path.basename(wrapper_path)
        with open(wrapper_file, "w") as out:
            out.write(template.render(executable=executable, command=command, options=step_configuration))

        if os.path.splitext(wrapper_file)[1] == ".c": # compile, then delete file
            compile_gcc(wrapper_file, outfile, remove_source=True)

    except IOError as e:
        sys.stderr.write("Error: " + str(e))
        sys.exit(2)
    except ValueError as e:
        sys.stderr.write("Input is not compatible")
        sys.exit(2)

def parse_template(outfile, infile):
    step_configuration = steps.get_config()
    env = Environment(loader = FileSystemLoader(os.path.dirname(os.path.abspath(infile))), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(os.path.basename(infile))

    # Do the real job
    try:
        with open(outfile, "w") as out:
            out.write(template.render(options=step_configuration))
    except IOError as e:
        sys.stderr.write("Error: " + str(e))
        sys.exit(2)
    except ValueError as e:
        sys.stderr.write("Input is not compatible")
        sys.exit(2)

def compile_gcc(c_file, outfile, command=None, remove_source=False):
    if not os.path.isfile(c_file):
        sys.stderr.write("Input file does not exist.")
        sys.exit(2)

    if command is None:
        os.system(f"gcc -o {outfile} {c_file}")
    else:
        os.system(command)
    
    if remove_source:
        os.remove(c_file)
        