#include <stdio.h>
#include <string.h>

void check_identity(unsigned int size)
{
    char buffer[size];
    int approved = 0;

    printf("What is your name: ");
    gets(buffer);

    if (strncmp(buffer, "Michael", 7) == 0)
        approved = 1;

    if (approved)
        printf("Welcome Michael! How was your day?\n");
    else
        printf("Hello %s! Unfortunatly you are not welcome here.", buffer);
}

int main()
{
    check_identity(@buffer_size = random_integer(low=100,high=500)@);

    return 0;
}