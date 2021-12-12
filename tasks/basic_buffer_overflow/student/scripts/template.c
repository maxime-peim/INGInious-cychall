#include <stdio.h>
#include <string.h>

int main()
{
    char buffer[%buffer_size%];
    int pass = 0;

    printf("\n Enter the password : \n");
    gets(buffer);

    if(strcmp(buffer, "%hidden_random_string%"))
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
        setreuid(0, 0);
        system("cat /task/student/flag.txt");
    }

    return 0;
}