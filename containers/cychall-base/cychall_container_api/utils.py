from multiprocessing.sharedctypes import Value
import os
import sys
import grp
import pwd
from tokenize import group

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

def copy_skel_files(home_dir):
    return inginious_container_api.utils.execute_process(['cp', '-a', '/etc/skel/.', home_dir], internal_command=True)

def create_user(name, uid=None, gid=None, home_dir=None, shell=None, groups=None, create_self_group=False, copy_skel=True):
    options = [name]

    home_dir = f'/task' if home_dir is None else home_dir
    
    try:
        os.makedirs(home_dir, exist_ok=True)
    except OSError as e:
        sys.stderr.buffer.write(b'An error occured while adding a new user:\n')
        sys.stderr.buffer.write(str(e).encode())
        sys.exit(2)

    options += ['--home-dir', home_dir]
    
    if create_self_group:
        options.append('--user-group')
    elif gid is not None:
        options += ['--gid', str(gid)]
    
    if groups is not None and len(groups) > 0:
        options += ['--groups', ",".join(groups)]

    # create the new user, in his own group
    if uid is not None:
        options += ['--uid', str(uid)]
    
    if shell is not None:
        options += ['--shell', shell]

    stdout, stderr = inginious_container_api.utils.execute_process(['useradd', *options], internal_command=True)
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

def get_wrapper(name, folder):
    wrappers = get_directory_content(folder)
    for w in wrappers:
        if w == name:
            return os.path.join(folder, name)
        elif os.path.splitext(w)[0] == name:
            return os.path.join(folder, w)

def add_wrapper(outfile, executable, mode, folder, command=None):
    step_configuration = steps.get_config()
    wrapper_path = get_wrapper(mode, folder)
    wrapper_file = os.path.basename(wrapper_path)

    if wrapper_path is None:
        sys.stderr.write("Invalid wrapper name")
        sys.exit(2)

    env = Environment(loader = FileSystemLoader(os.path.dirname(wrapper_path)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(wrapper_file)

    if command is None:
        command = "./" + executable

    try:
        with open(wrapper_file, "w") as out:
            out.write(template.render(executable=executable, command=command, options=step_configuration))

        if os.path.splitext(wrapper_file)[1] == ".c": # compile, then delete file
            compile_gcc(wrapper_file, outfile, remove_source=True)
        else:
            sys.stderr.write(f"Cannot create wrapper from '{wrapper_file}'.")
            sys.exit(2)
        
        next_user_uid = get_uid(step_configuration['next-user'])

        os.chown(outfile, next_user_uid, next_user_uid)
        os.chmod(outfile, 0o6551)

        os.chown(executable, next_user_uid, 4242)
        os.chmod(executable, 0o500)

    except IOError as e:
        sys.stderr.write("Error: " + str(e))
        sys.exit(2)
    except ValueError as e:
        sys.stderr.write("Input is not compatible")
        sys.exit(2)

def parse_template(outfile, infile):
    step_configuration = steps.get_config()
    env = Environment(
        loader = FileSystemLoader(
            os.path.dirname(os.path.abspath(infile))
        ), 
        trim_blocks=True, 
        lstrip_blocks=True, 
        extensions=['jinja2_ansible_filters.AnsibleCoreFiltersExtension']
    )
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
        #stdout, stderr = inginious_container_api.utils.execute_process( ["gcc", "-o", outfile, c_file], internal_command=True, cwd=os.getcwd(), user=pwd.getpwuid(os.getuid()).pw_name)
    else:
        os.system(command)
        #stdout, stderr = inginious_container_api.utils.execute_process(command.split(), internal_command=True, cwd=os.getcwd(), user=pwd.getpwuid(os.getuid()).pw_name)
    
    """if stderr != "":
        sys.stderr.buffer.write(b'An error occured while compiling:\n')
        sys.stderr.buffer.write(stderr)
        sys.exit(2)"""
    
    if remove_source:
        os.remove(c_file)
        
def recursive_chown(path, username, group_name):
    if not os.path.exists(path):
        raise ValueError(f"{path} does not exists.")
    
    owner_uid = get_uid(username)
    owner_gid = get_gid(group_name)

    if os.path.isfile(path):
        os.chown(path, owner_gid, owner_gid)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for momo in dirs + files:
                fullpath = os.path.join(root, momo)
                os.chown(fullpath, owner_uid, owner_gid)
    else:
        raise ValueError(f"{path} is not a folder nor a file.")