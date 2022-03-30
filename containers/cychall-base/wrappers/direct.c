{% if command %}
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <errno.h>
#include <error.h>

int main(int argc, char ** const argv) {
    setreuid(getuid(), geteuid());
    setregid(getgid(), getegid());

    int status = system("{{ command }}");

    char * const __argv[] = {"/bin/bash", "-i", NULL};

    if (status != -1) {
        if (WEXITSTATUS(status)) {
            int ret = WEXITSTATUS(status);

            if(!ret) {
                printf("\nStep finished: switching to next user!\n");
                execv("/bin/bash", __argv);
            }
            else{
                printf("\nERROR: An error occurred while trying to switch to next user. Please contact the course administrator.\n");
            }
            
            return ret;
        }
        else{
            printf("\nERROR: An error occurred while trying to switch to next user. Please contact the course administrator.\n");
        }
    }
    return status != -1;
}
{% endif %}