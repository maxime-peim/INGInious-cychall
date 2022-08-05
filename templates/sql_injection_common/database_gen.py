import sqlite3
import uuid
import random


def create_database(filename):
	con = sqlite3.connect(filename)
	cur = con.cursor()
	
	cur.execute('''DROP TABLE IF EXISTS users''')
	con.commit()
	
	cur.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT NOT NULL, password TEXT NOT NULL)''')
	con.commit()
	
	insert_rows(con)
	con.close()

def insert_rows(con):
	flag = 'INGInious{' + str(uuid.uuid1()) + '}'
	
	with open('usernames.txt', 'r', encoding="ascii", errors="surrogateescape") as f:
		usernames = f.readlines()
		random_usernames = random.sample(usernames, 19)
		random_passwords = random.sample(usernames, 19)
		
		random_usernames.append('admin')
		random_passwords.append(flag)
		
		for username, password in zip(random_usernames, random_passwords):
			con.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (username, password))
		
	con.commit()

if __name__ == "__main__":
	create_database("database.db")
