import sqlite3
from tkinter import ON 

foreign_keys = ON; #Enables the use of foreign keys
connection = sqlite3.Connection('database/Questions.db') #Creates a python connection to a database called 'LoginData.db'
cursor = connection.cursor() #Creates a cursor object that python can point to, to reference the database

cmd3 = '''CREATE TABLE IF NOT EXISTS quizzes (id INTEGER primary key AUTOINCREMENT,
                                                name TEXT NOT NULL,
                                                topic TEXT NOT NULL,
                                                level INTEGER NOT NULL)'''
cursor.execute(cmd3)

cmd4 = '''CREATE TABLE IF NOT EXISTS questions (id INTEGER primary key AUTOINCREMENT,
                                                topic TEXT NOT NULL,
                                                level INTEGER NOT NULL,
                                                question_text TEXT NOT NULL,
                                                correct_answer TEXT NOT NULL,
                                                option_a TEXT NOT NULL,
                                                option_b TEXT NOT NULL,
                                                option_c TEXT NOT NULL,
                                                option_d TEXT NOT NULL,
                                                quiz_id INTEGER NOT NULL,
                                                question_type TEXT DEFAULT 'multiple_choice',
                                                marks INTEGER DEFAULT 1,
                                                FOREIGN KEY (quiz_id) REFERENCES quizzes(id))'''

cursor.execute(cmd4)                           

# This is the test quiz????
cursor.execute("INSERT INTO quizzes (name, topic, level) VALUES (?, ?, ?)", ('World Capitals Quiz', 'Geography', 1))

# This is the test question
cursor.execute("INSERT INTO questions (topic, level, question_text, correct_answer, option_a, option_b, option_c, option_d, quiz_id, question_type, marks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
               ('Geography', 1, 'What is the capital of France?', 'A', 'Paris', 'Berlin', 'Madrid', 'Rome', 1, 'mc', 1))

connection.commit() # adds new record :)
