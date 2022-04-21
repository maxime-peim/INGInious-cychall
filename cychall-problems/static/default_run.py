from inginious_container_api import ssh_student
from inginious_container_api import feedback
from cychall_container_api import flag

if __name__ == "__main__":
    # si container et environment_type ne sont pas spécifiés
    # lorsqu'on quitte le student container on ne reçoit pas
    # de feedback. Un message de clôture est perdu en route,
    # aucune idée de la raison, alors que None est la valeur
    # par défaut...
    ssh_student.ssh_student(setup_script="cychall-build", script_as_root=True, user="step1", container=None, environment_type=None)
    all_correct, n_correct, correct_flags = flag.check_all_flag()
    n_flags = len(correct_flags)

    if n_flags == 0:
        feedback.set_global_result("success")
        feedback.set_global_feedback("There was no flag to find.")
    else:
        feedback.set_global_result("success" if all_correct else "failed")
        feedback.set_grade(100*n_correct/n_flags)
        feedback.set_global_feedback(
            f"""{'Congratulations' if all_correct else 'Keep going'}!

            You found {n_correct} our of {n_flags} flags.
            """
        )