{% if command %}
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char ** const argv) {
	setreuid(geteuid(), geteuid());
	int rc = system("{{command}}");

	if (rc == 0){
		printf("\nStep finished: switching to next user!\n");
		rc = system("sudo passwd -d {{options['next-user']}} &> /dev/null");
		if (rc == 0){
			system("su -l {{options['next-user']}}");
		}
		else{
			printf("\nERROR: An error occurred while trying to switch to next user. Please contact the course administrator.\n");
		}
	}
	else if (rc == 1){
		printf("\nFail: Try again!\n");
	}
	else { // -1 process exec failed
	}
	return rc;
}
{% endif %}