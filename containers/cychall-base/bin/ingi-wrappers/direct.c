{% if command %}
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char ** const argv) {
	setreuid(geteuid(), geteuid());
	int rc = system("{{command}}");

	if (rc == 0){
		system("sh");
	}
	else if (rc == 1){
	}
	else { // -1 process exec failed
	}
	return rc;
}
{% endif %}