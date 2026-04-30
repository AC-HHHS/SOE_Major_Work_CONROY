import sqlite3

connection = sqlite3.Connection('LoginData.db') #Creates a python connection to a database called 'LoginData.db'
cursor = connection.cursor() #Creates a cursor object that python can point to, to reference the database

cmd1 = '''CREATE TABLE IF NOT EXISTS users (id INTEGER primary key AUTOINCREMENT,
                                            first_name VARCHAR(50) NOT NULL, 
                                            last_name VARCHAR(50) NOT NULL, 
                                            email VARCHAR(50) UNIQUE NOT NULL, 
                                            password VARCHAR(50) NOT NULL,
                                            level INTEGER DEFAULT 1,
                                            is_admin BOOLEAN DEFAULT FALSE)''' # Creates a string called cmd1 whihc specifies SQL instructions to create a table with 4 fields each of type variable characters with a max length of 50
cursor.execute(cmd1) # executes the string variable cmd1 against the database

cmd2 = """INSERT INTO USERS (id, first_name, last_name, email, password, level, is_admin) VALUES (1, 'tester', 'test', 'tester@gmail.com', 'testerP', 1, FALSE)""" # is a string that specifies adding a record to the database
cursor.execute(cmd2)
connection.commit() # updates the database with this new record

ans = cursor.execute("SELECT * FROM users").fetchall()


for i in ans:
    print(i)