#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <stdlib.h>

void setid()
{
    setreuid(geteuid(), geteuid());
    setregid(getegid(), getegid());
}

void shell()
{
    system("/bin/sh");
}

void super_shell()
{
	setid();
	shell();
}

int check_blacklist(char *arr[], char* value, int length)
{
	int i;
	char* ret;
	for (i = 0; i < length; ++i)
	{
		ret = strstr(value, arr[i]);
		if (ret){
			printf("Blacklisted keyword detected!\n");
			return 0;
		}
	}
	return 1;
}

int main(int argc, char **argv)
{
	char cmd[30] = "ping -c4 ";
	char ip[20];
	char *blacklist[] = {"ls", "cat", "sh", "less", "more", "whoami", "echo", "head", "tac", "grep"};
	int blacklist_length = sizeof(blacklist) / sizeof(*blacklist);
	printf("Enter an ip to ping: ");
	fgets(ip, 20, stdin);
	
	if (check_blacklist(blacklist, ip, blacklist_length)){
		strcat(cmd, ip);
		setid();
		system(cmd);
	}
    return 0;
}
