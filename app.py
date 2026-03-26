from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from waitress import serve
import sqlite3
import os



app = Flask(__name__) # Creates an instance of the Flask objected called "__name__"
app.secret_key = os.urandom(24) # Assigning a key to encrypt flask data that is stored in cookies

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
  

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    # Fetch collected DATA from CollectedData.db
    data_conn = sqlite3.connect("questionBank.db")
    data_cursor = data_conn.cursor()

    data_cursor.execute("SELECT * FROM DATA")
    data_rows = data_cursor.fetchall()
    data_columns = [description[0] for description in data_cursor.description]
    data_conn.close()

    # Fetch USERS from the login database
    users_conn = sqlite3.connect("LoginData.db")
    users_cursor = users_conn.cursor()
    users_cursor.execute("SELECT first_name, last_name, email, is_admin FROM USERS")
    users = users_cursor.fetchall()
    users_conn.close()

    return render_template(
        "teacherHome.html",
        data_rows=data_rows,
        data_columns=data_columns,
        users=users
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/make_admin/<email>")
def make_admin(email):
    if not session.get("is_admin"):
        return redirect(url_for("login"))

    connection = sqlite3.connect("LoginData.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE USERS SET is_admin = 1 WHERE email = ?", 
        (email,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin"))

@app.route("/admin/users")
def admin_users():
    if not session.get("is_admin"):
        return redirect(url_for('login'))
    
    connection = sqlite3.connect("LoginData.db")
    cursor = connection.cursor()

    users = cursor.execute(
        "SELECT first_name, last_name, email, is_admin FROM USERS"
    ).fetchall()

    connection.close()

    return render_template("teacherHome.html", users=users) 

@app.route('/usermanagement')
def user_management():
    return render_template('studentManagement.html')


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8080) # Starts the Flask application using the Waitress WSGI server, listening on all available network interfaces (
