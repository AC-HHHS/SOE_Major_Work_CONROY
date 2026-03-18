from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from waitress import serve
import sqlite3
import os

from sqlalchemy.sql import func

app = Flask(__name__) # Creates an instance of the Flask objected called "__name__"
app.secret_key = os.urandom(24) # Assigning a key to encrypt flask data that is stored in cookies

ANSWER_KEY = {
    "q1": "b1"
}

@app.route('/') # A route that triggers the function login()
def login():
    return render_template('login.html') # Renders the login.html template when the user visits the root URL

@app.route('/login_validation', methods=['POST']) # A route that triggers the function login_validation() when a POST request is made to the URL "/login_validation"
def login_validation():
    email = request.form.get('email') # Retrieves the value of the "email" field from the submitted form data
    password = request.form.get('password') # Retrieves the value of the "password" field from the submitted form data

    connection = sqlite3.connect('LoginData.db') # Establishes a connection to the SQLite database named "LoginData.db"
    cursor = connection.cursor() # Creates a cursor object to interact with the database

    user = cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchall() # Executes a SQL query to check if there is a user in the "users" table with the provided email and password
    if len(user) > 0: # If a user is found (i.e., the length of the user list is greater than 0)
        return redirect(f'/home?fname={user[0][0]}&lname={user[0][1]}&email={user[0][2]}') # Redirects the user to the home page and passes the first name, last name, and email as query parameters
    else:
        return redirect('/') # Redirects the user back to the login page if the login is unsuccessful

@app.route('/home') # A route that triggers the function home() when a GET request is made to the URL "/home"
def home():
    fname = request.args.get('fname') # Retrieves the value of the "fname" query parameter from the URL
    lname = request.args.get('lname') # Retrieves the value of the "lname" query parameter from the URL
    email = request.args.get('email') # Retrieves the value of the "email" query parameter from the URL

    return render_template('home.html', fname=fname, lname=lname, email=email) # Renders the home.html template and passes the first name, last name, and email as variables to be used in the template

@app.route('/signUp') # A route that triggers the function signUp() when a GET request is made to the URL "/signUp"
def signUp():
    return render_template('signUp.html') # Renders the signUp.html template when the user visits the "/signUp" URL

@app.route('/add_user', methods=['POST']) # A route that triggers the function add_user() when a POST request is made to the URL "/add_user"
def add_user():
    fname = request.form.get('fname') # Retrieves the value of the "fname" field from the submitted form data
    lname = request.form.get('lname') # Retrieves the value of the "lname" field from the submitted form data
    email = request.form.get('email') # Retrieves the value of the "email" field from the submitted form data
    password = request.form.get('password') # Retrieves the value of the "password" field from the submitted form data

    connection = sqlite3.connect('LoginData.db') # Establishes a connection to the SQLite database named "LoginData.db"
    cursor = connection.cursor() # Creates a cursor object to interact with the database

    ans = cursor.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password)).fetchall() # Executes a SQL query to check if there is already a user in the "users" table with the provided email and password
    if len(ans) > 0: # If a user is found (i.e., the length of the ans list is greater than 0)    cursor.execute('INSERT INTO users (fname, lname, email, password) VALUES (?, ?, ?, ?)', (fname, lname, email, password)) # Executes a SQL query to insert a new user into the "users" table with the provided first name, last name, email, and password
        connection.close() # Closes the connection to the database
        return render_template('login.html') # Renders the login.html template if the user already exists
    else:
        cursor.execute('INSERT INTO users (fname, lname, email, password) VALUES (?, ?, ?, ?)', (fname, lname, email, password)) # Executes a SQL query to insert a new user into the "users" table with the provided first name, last name, email, and password
        connection.commit() # Commits the changes to the database
        connection.close() # Closes the connection to the database
        return render_template('login.html') # Renders the login.html template after successfully adding a new user

@app.route('/firstquiz')
def quiz():
    return render_template('quizPage.html')

@app.route('/quiz', methods=["GET", "post"])
def quiz_view():
    if request.method == "post":
        user_answers = {
            "q1": request.form.get("q1")
        }

        feedback = {}
        results = {}
        score = 0
        total_questions = len(ANSWER_KEY)

        for q, correct in ANSWER_KEY.items():
            if user_answers.get(q) == correct:
                feedback[q] = f"{q.upper()} is correct!"
                results[q] = "correct"
                score += 1
            else:
                feedback[q] = f"{q.upper()} is incorrect."
                results[q]  = "incorrect"

  
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8080) # Starts the Flask application using the Waitress WSGI server, listening on all available network interfaces (
