#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>

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

int main()
{
    char buffer[@buffer_size = random_integer(low=100,high=500)@];
    int pass = 0;

    printf("\n Enter the password : \n");
    gets(buffer);

    if(strcmp(buffer, "@hidden_password = random_hash(hash_name='md5')@"))
    {
        printf ("\n Wrong Password \n");
    }
    else
    {
        printf ("\n Correct Password \n");
        pass = 1;
    }

    if(pass)
    {
        super_shell();
    }

    return 0;
}