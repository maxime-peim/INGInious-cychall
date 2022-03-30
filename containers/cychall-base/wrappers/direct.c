{% if command %}
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <errno.h>
#include <error.h>

int main(int argc, char ** const argv) {
    setreuid(geteuid(), geteuid());
    setregid(getegid(), getegid());

    int status = system("{{ command }}");

    char * const __argv[] = {"/bin/bash", "-i", NULL};

    if (status != -1) {
        if (WIFEXITED(status)) {
            int ret = WEXITSTATUS(status);

            if(!ret) {
                printf("\nStep finished: switching to next user!\n");
                execv(__argv[0], __argv);
            }
            else{
                printf("\nFailed to exploit the challenge. returned code: %d\n", ret);
            }
            
            return ret;
        }
        else{
            printf("\nERROR: An error occurred while trying to switch to next user. Please contact the course administrator. %d\n", status);
        }
    }
    return status != -1;
}
{% endif %}