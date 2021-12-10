import os
import hashlib

def generate_flag(prefix='INGInious', size=16):
    """
        Return a random flag with the given prefix.
    """
    randomness = os.urandom(size)
    flag_intern = hashlib.sha256(randomness).hexdigest()
    return f'{prefix}{{{flag_intern}}}'

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