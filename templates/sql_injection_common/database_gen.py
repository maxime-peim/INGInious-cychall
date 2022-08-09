import sys
import sqlite3
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
	next_user = sys.argv[1]
	flag = sys.argv[2]
	
	with open('usernames.txt', 'r', encoding="ascii", errors="surrogateescape") as f:
		usernames = f.readlines()
	
	usernames = random.sample(usernames, 19)
	passwords = random.sample(usernames, 19)
	
	usernames.append(next_user)
	passwords.append(flag)
	
	for username, password in zip(usernames, passwords):
		con.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (username, password))
		
	con.commit()

if __name__ == "__main__":
	create_database("database.db")
