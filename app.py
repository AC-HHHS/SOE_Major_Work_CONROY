from flask import Flask, render_template, request, redirect, url_for, session
from waitress import serve
import sqlite3
import os
import time
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__) # Creates an instance of the Flask objected called "__name__"
app.secret_key = 'secret_key' # Sets the secret key for the Flask application, which is used for securely signing the session cookie
@app.route('/') # A route that triggers the function login()
def login():
    return render_template('login.html') # Renders the login.html template when the user visits the root URL

@app.route('/login_validation', methods=['POST']) # A route that triggers the function login_validation() when a POST request is made to the URL "/login_validation"
def login_validation():
    if request.method == 'POST': # Checks if the request method is POST
        email = request.form.get('email') # Retrieves the value of the "email" field from the submitted form data
        password = request.form.get('password') # Retrieves the value of the "password" field from the submitted form data

        connection = sqlite3.connect('database/LoginData.db') # Establishes a connection to the SQLite database named "LoginData.db"
        cursor = connection.cursor() # Creates a cursor object to interact with the database

        cursor.execute('SELECT id, password, is_admin FROM users WHERE email=?', (email,)) # Executes a SQL query to retrieve the id, password, and is_admin status of the user with the provided email
        user = cursor.fetchone() # Fetches the first row of the query result, which contains the user's id, password, and is_admin status
        connection.close() # Closes the connection to the database

        if user and check_password_hash(user[1], password): # Checks if a user was found and if the provided password matches the hashed password stored in the database
            session['user_id'] = user[0] # Stores the user's id in the session
            session['is_admin'] = user[2] # Stores the user's is_admin status in the session        
            return redirect(url_for('teacher_home')) # Redirects the user to the dashboard page if the login is successful 

        return "Invalid Login"
    return render_template('login.html')
   
        
@app.route('/dashboard')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = sqlite3.connect('database/LoginData.db')
    cursor = connection.cursor()
    cursor.execute('SELECT first_name, last_name, email FROM users WHERE id=?', (session['user_id'],))
    user = cursor.fetchone()
    connection.close()

    return render_template('dashboard.html', first_name=user[0], last_name=user[1], email=user[2]) 

# Pracctice code for teacher dashboard - to be deleted later
@app.route('/teacher_dashboard')
def teacher_home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = sqlite3.connect('database/LoginData.db')
    cursor = connection.cursor()
    cursor.execute('SELECT first_name, last_name, email FROM users WHERE id=?', (session['user_id'],))
    user = cursor.fetchone()
    connection.close()

    return render_template('teacherHome.html', first_name=user[0], last_name=user[1], email=user[2]) 

@app.route('/register') # A route that triggers the function signUp() when a GET request is made to the URL "/signUp"
def register():
    return render_template('register.html') # Renders the register.html template when the user visits the "/signUp" URL

@app.route('/add_user', methods=['GET', 'POST']) # A route that triggers the function add_user() when a POST request is made to the URL "/add_user"
def add_user():
    if request.method == 'POST': # Checks if the request method is POST
        first_name = request.form.get('first_name') # Retrieves the value of the "first_name" field from the submitted form data
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password') # Retrieves the value of the "password" field from the submitted form data

        if not email.endswith('@education.nsw.gov.au'):
            return "You must use DOE email address to register." # Returns a message if the email does not end with "@education.nsw.gov.au"
        
        hashed_password = generate_password_hash(password) # Hashes the password using the generate_password_hash function from the werkzeug.security module

        connection = sqlite3.connect('database/LoginData.db') # Establishes a connection to the SQLite database named "LoginData.db"
        cursor = connection.cursor() # Creates a cursor object to interact with the database

        ans = cursor.execute('SELECT * FROM users WHERE email=?', (email,)).fetchall() # Executes a SQL query to check if there is already a user in the "users" table with the provided email
        if len(ans) > 0: # If a user is found (i.e., the length of the ans list is greater than 0)
            connection.close() # Closes the connection to the database
            return render_template('login.html') # Renders the login.html template if the user already exists
        else:
            cursor.execute('INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)', (first_name, last_name, email, hashed_password)) # Executes a SQL query to insert a new user into the "users" table with the provided first name, last name, email, and password
            connection.commit() # Commits the changes to the database
            connection.close() 
    return render_template('login.html') # Renders the login.html template after successfully adding a new user

  

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    # Fetch collected DATA from CollectedData.db
    data_conn = sqlite3.connect("database/CollectedData.db")
    data_cursor = data_conn.cursor()

    data_cursor.execute("SELECT * FROM DATA")
    data_rows = data_cursor.fetchall()
    data_columns = [description[0] for description in data_cursor.description]
    data_conn.close()

    # Fetch USERS from the login database
    users_conn = sqlite3.connect("database/LoginData.db")
    users_cursor = users_conn.cursor()
    users_cursor.execute("SELECT first_name, last_name, email, is_admin FROM users")
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

    connection = sqlite3.connect("database/LoginData.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE users SET is_admin = True WHERE email = ?", 
        (email,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("admin"))

@app.route("/admin/users")
def admin_users():
    if not session.get("is_admin"):
        return redirect(url_for('login'))
    
    connection = sqlite3.connect("database/LoginData.db")
    cursor = connection.cursor()

    users = cursor.execute(
        "SELECT first_name, last_name, email, is_admin FROM users"
    ).fetchall()

    connection.close()

    return render_template("teacherHome.html", users=users) 

@app.route('/usermanagement')
def user_management():
    return render_template('studentManagement.html')


@app.route('/add_quiz', methods=['POST'])
def add_quiz():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    topic = request.form.get('topic')
    level = request.form.get('level')

    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO quizzes (name, topic, level) VALUES (?, ?, ?)', (name, topic, level))
    connection.commit()
    connection.close()

@app.route('/add_question_page')
def add_question_page():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    quizzes = cursor.execute('SELECT * FROM quizzes').fetchall()
    connection.close()

    return render_template('createQuiz.html', quizzes=quizzes)

@app.route('/add_question', methods=['POST'])
def add_question():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    quiz_id = request.form.get('quiz_id')
    topic = request.form.get('topic')
    level = request.form.get('level')
    question_text = request.form.get('question_text')
    option_a = request.form.get('option_a')
    option_b = request.form.get('option_b')
    option_c = request.form.get('option_c')
    option_d = request.form.get('option_d')
    correct_answer = request.form.get('correct_answer')

    options = {'A': option_a, 'B': option_b, 'C': option_c, 'D': option_d}
    correct_text = options[correct_answer]

    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO questions (quiz_id, topic, level, question_text, option_a, option_b, option_c, option_d, correct_answer) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (quiz_id, topic, level, question_text, option_a, option_b, option_c, option_d, correct_answer))
    connection.commit()
    connection.close()

    return redirect(url_for('add_question_page'))

if __name__ == '__main__':
    app.run(debug=True)
    
 # Starts the Flask application using the Waitress WSGI server, listening on all available network interfaces (
