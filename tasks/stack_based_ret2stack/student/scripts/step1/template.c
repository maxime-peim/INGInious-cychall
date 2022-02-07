#include <stdio.h>
#include <string.h>

void check_identity()
{
    char buffer[@buffer_size = random_integer(low=200,high=300)@];
    int approved = 0;

    printf("Here is the address of buffer: %p\nWho knows, you might need it.\n", buffer);

    printf("What is your name: \n");
    gets(buffer);

    if (approved)
        printf("Welcome Michael! How was your day?\n");
    else
        printf("Hello %s! Unfortunatly you are not welcome here.\n", buffer);
}

int main()
{
    check_identity();

    return 0;
}