from multiprocessing.sharedctypes import Value
import os
import secrets
import yaml

import config

def _get_flags_file_path(generated=True):
    return config.GENERATED_FLAGS_FILE_PATH if generated else config.STUDENT_FLAGS_FILE_PATH

def _check_flags_file(generated=True):
    path = _get_flags_file_path(generated)
    if not os.path.exists(path):
        with open(path, 'a'): pass
        os.chown(path, 0, 4242)
        os.chmod(path, 0o660)

def _load_flags(generated=True):
    """Open existing flags file"""
    _check_flags_file(generated)
    path = _get_flags_file_path(generated)
    with open(path, "r") as flags_in:
        flags = yaml.safe_load(flags_in)
    return flags if flags is not None else {}

def _save_flags(flags, generated=True):
    """Save flags into file"""
    _check_flags_file(generated)
    path = _get_flags_file_path(generated)
    with open(path, "w") as flags_out:
        return yaml.safe_dump(flags, flags_out)

def check_flag(flag_name):
    generated_flags = _load_flags(True)
    student_flags = _load_flags(False)
    gflag = generated_flags.get(flag_name, None)
    sflag = student_flags.get(flag_name, None)

    if gflag is None:
        raise ValueError(f"Flag '{flag_name}' does not exist.")
     
    return gflag == sflag

def check_all_flag():
    generated_flags = _load_flags(True)
    student_flags = _load_flags(False)

    correct_flags = {
        flag_name: gflag == sflag
        for (flag_name, gflag), sflag in zip(generated_flags.items(), student_flags.values())
    }
    n_correct = sum(correct_flags.values())
    all_correct = n_correct == len(correct_flags)

    return all_correct, n_correct, correct_flags

def add_flag(flag_name, flag_value):
    generated_flags = _load_flags(True)
    student_flags = _load_flags(False)

    generated_flags[flag_name] = flag_value
    student_flags[flag_name] = None

    _save_flags(generated_flags, True)
    _save_flags(student_flags, False)

def update_student_flag(flag_name, flag_value):
    student_flags = _load_flags(False)

    if flag_name not in student_flags:
        raise ValueError(f"Flag '{flag_name}' does not exist.")

    student_flags[flag_name] = flag_value

    _save_flags(student_flags, False)

def generate_flag(*, prefix="INGInious", size=16, **kwargs):
    return f"{prefix}{{{secrets.token_hex(size)}}}"
