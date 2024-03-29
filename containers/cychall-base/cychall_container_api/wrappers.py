# coding=utf-8
""" Allow to resolve wrapper functions from wrapper names. """
import os
import stat
import sys
import subprocess

import steps
import utils
import config
import flag
import inginious_container_api.utils


def __wrapper_sgid(challenge_file_path, **kwargs):
    challenge_permissions = os.stat(challenge_file_path)
    os.chmod(challenge_file_path, challenge_permissions.st_mode | stat.S_ISGID)


def __wrapper_suid(challenge_file_path, **kwargs):
    challenge_permissions = os.stat(challenge_file_path)
    os.chmod(challenge_file_path, challenge_permissions.st_mode | stat.S_ISUID)


def __wrapper_sguid(challenge_file_path, **kwargs):
    challenge_permissions = os.stat(challenge_file_path)
    os.chmod(
        challenge_file_path, challenge_permissions.st_mode | stat.S_ISUID | stat.S_ISGID
    )


def __wrapper_shell_c(
    challenge_file_path, *, outfile="wrapped", command=None, **kwargs
):
    wrapper_file = "shell-c.j2"
    wrapper_path = os.path.join(config.WRAPPER_DIR, wrapper_file)
    executable = os.path.basename(challenge_file_path)
    step_configuration = steps.get_from_context()

    if command is None:
        command = "./" + executable

    parsed = utils.parse(
        wrapper_path,
        render_parameters={"executable": executable, "command": command, "options": step_configuration},
    )

    try:
        with open("__shell.c", "w") as out:
            out.write(parsed)

        next_user = step_configuration["next-user"]
        next_user_uid = utils.get_uid(next_user)
        next_user_gid = utils.get_gid(next_user)

        utils.compile_gcc("__shell.c", outfile, remove_source=True)

        os.chown(outfile, next_user_uid, next_user_gid)
        os.chmod(outfile, stat.S_ISUID | stat.S_ISGID | 0o555)

        os.chown(challenge_file_path, next_user_uid, next_user_gid)
        os.chmod(challenge_file_path, 0o555)

    except FileExistsError as e:
        sys.stderr.write("Error: " + str(e))
        sys.exit(2)
    except IOError as e:
        sys.stderr.write("Error: " + str(e))
        sys.exit(2)
    except ValueError as e:
        sys.stderr.write(f"Input is not compatible: {e}")
        sys.exit(2)


def __wrapper_shell_python(
    challenge_file_path, *, outfile="wrapped", command=None, **kwargs
):
    wrapper_file = "shell-python.j2"
    wrapper_path = os.path.join(config.WRAPPER_DIR, wrapper_file)
    executable = os.path.basename(challenge_file_path)
    step_configuration = steps.get_from_context()

    if command is None:
        command = "./" + executable

    parsed = utils.parse(
        wrapper_path,
        render_parameters={"executable": executable, "command": command, "options": step_configuration},
    )

    try:
        with open(outfile, "w") as out:
            out.write(parsed)

        current_user = step_configuration["current-user"]
        next_user = step_configuration["next-user"]
        next_user_uid = utils.get_uid(next_user)
        next_user_gid = utils.get_gid(next_user)

        with open("/etc/sudoers", "a") as sudoers:
            sudoers.write(
                f"{current_user} ALL=({next_user}) NOPASSWD: {os.path.abspath(outfile)}\n"
            )

        os.chown(outfile, next_user_uid, next_user_gid)
        os.chmod(outfile, 0o555)

        os.chown(challenge_file_path, next_user_uid, next_user_gid)
        os.chmod(challenge_file_path, 0o555)

    except FileExistsError as e:
        sys.stderr.write(f"Error: {e}")
        sys.exit(2)
    except IOError as e:
        sys.stderr.write(f"Error: {e}")
        sys.exit(2)
    except ValueError as e:
        sys.stderr.write(f"Input is not compatible: {e}")
        sys.exit(2)


def __wrapper_password(challenge_file_path, *, pwd_flag=None, **kwargs):
    step_configuration = steps.get_from_context()
    next_user = step_configuration["next-user"]
    current_user = step_configuration["current-user"]
    
    # Generate flag
    if pwd_flag is None:
        next_user_pwd = flag.generate_flag() if next_user != "end" else flag.get_flag("end")
    else:
        next_user_pwd = pwd_flag
    
    # Change next_user password
    std_out, std_err = inginious_container_api.utils.execute_process(["/usr/bin/bash", "-c", f"echo '{next_user}:{next_user_pwd}' | chpasswd"],
                    internal_command=True, user='root')
    
    if std_err:
        sys.stderr.write(f"An error occurred while changing the user password:\n{std_err}\n")
        sys.exit(2)

    if next_user != "end" and pwd_flag is None:
        # Add flag
        flag.add_flag(current_user, next_user_pwd)
        # Save to file
        flag_file = os.path.join(config.STUDENT_DIR, next_user, 'flag')

        with open(flag_file, 'w') as f:
            f.write(
            f"""Well done, you have found the flag for {current_user}!
Don't forget to use the `found-flag` command to validate it.
Flag: {next_user_pwd}
The flag is the password of the next user: {next_user}!\n\n"""
        )
        next_user_uid = utils.get_uid(next_user)
        next_user_gid = utils.get_gid(next_user)
        os.chown(flag_file, next_user_uid, next_user_gid)
        os.chmod(flag_file, 0o440)


def __wrapper_ssh(challenge_file_path, **kwargs):
    # ne marche pas, je n'arrive pas à me connecter en tant que l'utilisateur
    # suivant... je pense que c'est à cause des paramètres de sshd lors du
    # lancement du student container
    current_user = steps.get_from_context("current-user")
    next_user = steps.get_from_context("next-user")
    current_ssh_folder = os.path.join(os.getcwd(), ".ssh")
    next_ssh_folder = os.path.join(utils.get_home(next_user), ".ssh")
    id_file = os.path.join(current_ssh_folder, next_user)
    auth_keys_file = os.path.join(next_ssh_folder, "authorized_keys")

    os.makedirs(current_ssh_folder, mode=0o700, exist_ok=True)
    os.makedirs(next_ssh_folder, mode=0o700, exist_ok=True)

    absolute_challenge_path = os.path.abspath(challenge_file_path)
    inginious_container_api.utils.execute_process(
        ["/usr/sbin/usermod", "--shell", absolute_challenge_path, next_user],
        internal_command=True,
        user=utils.get_username(),
    )

    inginious_container_api.utils.execute_process(
        [
            "/usr/bin/ssh-keygen",
            "-q",  # quiet
            "-f", id_file,
            "-t", "ecdsa",
            "-b", "521",
            "-N", "''",  # no passphrase
        ],
        internal_command=True,
        user=utils.get_username(),
    )

    with open(f"{id_file}.pub") as pubkey_fp, open(auth_keys_file, "a") as auth_keys_fp:
        pubkey = pubkey_fp.read()
        auth_keys_fp.write(pubkey)

    utils.recursive_chown(current_ssh_folder, current_user, "worker")
    utils.recursive_chown(next_ssh_folder, next_user, "worker")

    os.chmod(auth_keys_file, 0o644)
    os.chmod(f"{id_file}.pub", 0o644)
    os.chmod(id_file, 0o600)

wrappers = {
    "sgid": __wrapper_sgid,
    "suid": __wrapper_suid,
    "sguid": __wrapper_sguid,
    "shell-c": __wrapper_shell_c,
    "shell-python": __wrapper_shell_python,
    "password": __wrapper_password,
    "ssh": __wrapper_ssh,
}


def resolve(wrapper_name):
    wrapper_name = wrapper_name.lower()

    if wrapper_name not in wrappers:
        raise ValueError(f"Wrapper {wrapper_name} does not exists.")

    wrapper_function = wrappers[wrapper_name]
    if not callable(wrapper_function):
        raise ValueError(f"Wrapper {wrapper_function!r} is not callable.")

    return wrapper_function
