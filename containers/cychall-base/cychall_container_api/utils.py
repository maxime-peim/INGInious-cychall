import os
import sys
import subprocess
import shlex
import grp
import hashlib

from randomness import Random

def generate_flag(prefix='INGInious', size=16):
    """
        Return a random flag with the given prefix.
    """
    return f'{prefix}{{{Random.generate("hash")}}}'

def write_flag(flag, flag_path, student_read=False):
    o_flags = os.O_CREAT | os.O_WRONLY
    mode = 0o644 if student_read else 0o640
    fd = os.open(flag_path, o_flags, mode)
    
    with os.fdopen(fd, 'w') as flag_out:
        flag_out.write(flag)

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

def execute_command(command_name, options=None):
    process = subprocess.run([command_name, *shlex.split(options or {})], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process


def create_user(name, uid=None, gid=None, home_dir=None):
    options = [name]

    if gid is not None:
        options.append(f'--gid {gid}')

    groupadd_proc = execute_command('groupadd', ' '.join(options))

    if groupadd_proc.returncode != 0:
        sys.stderr.buffer.write(b'An error occured while adding a new user group:\n')
        sys.stderr.buffer.write(groupadd_proc.stderr)
        sys.exit(2)


    # add group name
    options.append(f'-g {name}')

    if uid is not None:
        options.append(f'--uid {uid}')

    home_dir = home_dir or f'/task/student/{name}'
    
    try:
        os.makedirs(home_dir)
    except OSError as e:
        sys.stderr.buffer.write(b'An error occured while adding a new user:\n')
        sys.stderr.buffer.write(str(e).encode())
        sys.exit(2)

    options.append(f'--home-dir {home_dir}')

    useradd_proc = execute_command('useradd', ' '.join(options))

    if useradd_proc.returncode != 0:
        sys.stderr.buffer.write(b'An error occured while adding a new user:\n')
        sys.stderr.buffer.write(useradd_proc.stderr)
        sys.exit(2)

    execute_command(f'usermod -a -G worker {name}')
