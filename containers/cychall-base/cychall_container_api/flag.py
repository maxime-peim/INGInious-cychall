import os

from randomness import Random

def generate_flag(prefix='INGInious', size=16):
    """
        Return a random flag with the given prefix.
    """
    return f'{prefix}{{{Random.generate("hash")}}}'

def write_flag(flag, flag_path, student_read=False):
    """
        Write the flag in a file, and gives the rights.
    """
    o_flags = os.O_CREAT | os.O_WRONLY
    mode = 0o440 if student_read else 0o400
    fd = os.open(flag_path, o_flags, mode)
    
    with os.fdopen(fd, 'w') as flag_out:
        flag_out.write(flag)