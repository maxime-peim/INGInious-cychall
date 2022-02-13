#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <stdlib.h>

#include <sqlite3.h>

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

sqlite3* open_database(char* filename)
{
	sqlite3* DB;

	int rc = sqlite3_open_v2(filename, &DB, SQLITE_OPEN_READONLY, NULL);
	if (rc != SQLITE_OK)
	{
		printf("Error: couldn't open database %s\n", filename);
		return NULL;
	}

	return DB;
}

int login(sqlite3* DB, char* username, char* password)
{
	char query[1024];
	sqlite3_stmt *result;
	int rc;
	
	sprintf(query, "SELECT * FROM users WHERE username = '%s' AND password = '%s';", username, password);
	
	rc = sqlite3_prepare(DB, query, -1, &result, NULL);
	if (rc != SQLITE_OK)
	{
		fprintf(stderr, "SQLITE error: %s\n", sqlite3_errmsg(DB));
	}
	
	if (sqlite3_step(result) == SQLITE_DONE) /* Nothing found */
	{ 
		return 0;
	}
	
	return 1;
}

int main()
{
	char username[40];
	char password[40];
	int done = 0;

	setid();
	sqlite3* DB = open_database("database.db");
	
	if (!DB)
	{
		return 1;
	}
	
	while (!done) /* Login loop */
	{
		printf("Enter your username:");
		fgets(username, 40, stdin);
		
		printf("Enter your password:");
		fgets(password, 40, stdin);
		
		done = login(DB, username, password);
		
		if (!done)
		{
			printf("Invalid username or password!\n");
		}
	}

	sqlite3_close(DB);

	printf("Successful login: Welcome!\n");
	
	shell();
	
    return 0;
}
