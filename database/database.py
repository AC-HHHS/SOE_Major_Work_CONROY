import sqlite3
from werkzeug.security import generate_password_hash   

connection = sqlite3.Connection('database/LoginData.db') #Creates a python connection to a database called 'LoginData.db'
cursor = connection.cursor() #Creates a cursor object that python can point to, to reference the database

cmd1 = '''CREATE TABLE IF NOT EXISTS users (id INTEGER primary key AUTOINCREMENT,
                                            first_name VARCHAR(50) NOT NULL, 
                                            last_name VARCHAR(50) NOT NULL, 
                                            email VARCHAR(50) UNIQUE NOT NULL, 
                                            password VARCHAR(50) NOT NULL,
                                            level INTEGER DEFAULT 1,
                                            is_admin BOOLEAN DEFAULT FALSE)''' # Creates a string called cmd1 whihc specifies SQL instructions to create a table with 4 fields each of type variable characters with a max length of 50
cursor.execute(cmd1) # executes the string variable cmd1 against the database

cmd_results = '''CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    score REAL,
    accuracy REAL,
    avg_time REAL,
    wrong_questions TEXT,
    written_answers TEXT,
    written_marks TEXT,
    marking_complete INTEGER DEFAULT 0,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id))'''
cursor.execute(cmd_results)
connection.commit()

hashed_password = generate_password_hash("testerP") # Hashes the password "testerP" using the generate_password_hash function from the werkzeug.security module

cmd2 = """INSERT INTO users (first_name, last_name, email, password, level, is_admin) 
          VALUES (?, ?, ?, ?, ?, ?)"""  # use parameterised query for safety
cursor.execute(cmd2, ('tester', 'test', 'tester@education.nsw.gov.au', hashed_password, 1, False))
connection.commit() # updates the database with this new record

cmd5 = """INSERT INTO users (first_name, last_name, email, password, level, is_admin) 
          VALUES (?, ?, ?, ?, ?, ?)"""  # use parameterised query for safety
cursor.execute(cmd5, ('admin', 'user', 'admin@education.nsw.gov.au', hashed_password, 1, True))
connection.commit()

ans = cursor.execute("SELECT * FROM users").fetchall()


for i in ans:
    print(i)