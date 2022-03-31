{% if command %}
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <unistd.h>
#include <errno.h>
#include <error.h>
#include <signal.h>

int argsystem(const char *path, int argc, char *const argv[])
{
    sigset_t blockMask, origMask;
    struct sigaction saIgnore, saOrigQuit, saOrigInt, saDefault;
    pid_t childPid;
    int status, savedErrno;

    /* The parent process (the caller of system()) blocks SIGCHLD
       and ignore SIGINT and SIGQUIT while the child is executing.
       We must change the signal settings prior to forking, to avoid
       possible race conditions. This means that we must undo the
       effects of the following in the child after fork(). */

    sigemptyset(&blockMask);            /* Block SIGCHLD */
    sigaddset(&blockMask, SIGCHLD);
    sigprocmask(SIG_BLOCK, &blockMask, &origMask);

    saIgnore.sa_handler = SIG_IGN;      /* Ignore SIGINT and SIGQUIT */
    saIgnore.sa_flags = 0;
    sigemptyset(&saIgnore.sa_mask);
    sigaction(SIGINT, &saIgnore, &saOrigInt);
    sigaction(SIGQUIT, &saIgnore, &saOrigQuit);

    switch (childPid = fork()) {
    case -1: /* fork() failed */
        status = -1;
        break;          /* Carry on to reset signal attributes */

    case 0: /* Child: exec command */

        /* We ignore possible error returns because the only specified error
           is for a failed exec(), and because errors in these calls can't
           affect the caller of system() (which is a separate process) */

        saDefault.sa_handler = SIG_DFL;
        saDefault.sa_flags = 0;
        sigemptyset(&saDefault.sa_mask);

        if (saOrigInt.sa_handler != SIG_IGN)
            sigaction(SIGINT, &saDefault, NULL);
        if (saOrigQuit.sa_handler != SIG_IGN)
            sigaction(SIGQUIT, &saDefault, NULL);

        sigprocmask(SIG_SETMASK, &origMask, NULL);

        char **__argv = (char **)malloc(sizeof(char *) * (4 + argc));
        __argv[0] = "sh";
        __argv[1] = "-c";
        __argv[3 + argc] = NULL;

        size_t curCommandLen = strlen(path), commandLen = curCommandLen;
        unsigned int pow10 = 10, exp10 = 1;

        // execute command as : /bin/sh -c 'command $0 $1 ...' arg0 arg1 ...
        // so we need to compute the length of 'command $0 $1 ...'
        for (int argi = 0; argi < argc; argi ++) {
            if (argi >= pow10) {
                pow10 *= 10;
                exp10 ++;
            }
            // length of ' $<n>'
            commandLen += exp10 + 2;
        }

        __argv[2] = (char *)malloc(sizeof(char) * (commandLen + 1));
        strcpy(__argv[2], path);

        pow10 = 10, exp10 = 1;

        for (int argi = 0; argi < argc; argi ++) {
            if (argi >= pow10) {
                pow10 *= 10;
                exp10 ++;
            }
            // build the command with arguments
            snprintf(__argv[2] + curCommandLen, exp10 + 3, " $%d", argi);
            curCommandLen += exp10 + 2;

            __argv[3 + argi] = argv[argi];
        }

        // execute command as : /bin/sh -c 'command $0 $1 ...' arg0 arg1 ...
        execv("/bin/sh", __argv);
        _exit(127);                     /* We could not exec the shell */

    default: /* Parent: wait for our child to terminate */

        /* We must use waitpid() for this task; using wait() could inadvertently
           collect the status of one of the caller's other children */

        while (waitpid(childPid, &status, 0) == -1) {
            if (errno != EINTR) {       /* Error other than EINTR */
                status = -1;
                break;                  /* So exit loop */
            }
        }
        break;
    }

    /* Unblock SIGCHLD, restore dispositions of SIGINT and SIGQUIT */

    savedErrno = errno;                 /* The following may change 'errno' */

    sigprocmask(SIG_SETMASK, &origMask, NULL);
    sigaction(SIGINT, &saOrigInt, NULL);
    sigaction(SIGQUIT, &saOrigQuit, NULL);

    errno = savedErrno;

    return status;
}

int main(int argc, char ** const argv) {
    setreuid(geteuid(), geteuid());
    setregid(getegid(), getegid());

    int status = argsystem("{{ command }}", argc - 1, argc == 1 ? NULL : argv + 1);

    if (status != -1) {
        if (WIFEXITED(status)) {
            int ret = WEXITSTATUS(status);

            if(!ret) {
                printf("\nStep finished: switching to next user!\n");
                execv("/bin/bash", (char *const []){"bash", "-i", NULL});
            }
            else{
                printf("\nFailed to exploit the challenge.\n");
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