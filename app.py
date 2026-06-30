from flask import Flask, render_template, request, redirect, url_for, session
from waitress import serve
import sqlite3
import os
import time
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
import json
import csv
import io

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
            return redirect(url_for('home')) # Redirects the user to the dashboard page if the login is successful 

        return "Invalid Login"
    return render_template('login.html')
   
        
@app.route('/dashboard')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Redirect admins to teacher dashboard
    if session.get('is_admin'):
        return redirect(url_for('teacher_home'))

    login_conn = sqlite3.connect('database/LoginData.db')
    login_cursor = login_conn.cursor()
    login_cursor.execute('SELECT first_name, last_name, email, level FROM users WHERE id=?', (session['user_id'],))
    user = login_cursor.fetchone()

    # Recent results for this student
    try:
        login_cursor.execute('''
            SELECT id, quiz_id, accuracy, avg_time, date
            FROM results WHERE user_id = ?
            ORDER BY date DESC LIMIT 5
        ''', (session['user_id'],))
        recent_raw = login_cursor.fetchall()
    except Exception:
        recent_raw = []
    login_conn.close()

    # Attach quiz names
    q_conn = sqlite3.connect('database/Questions.db')
    q_cursor = q_conn.cursor()
    recent = []
    for r in recent_raw:
        quiz = q_cursor.execute('SELECT name FROM quizzes WHERE id=?', (r[1],)).fetchone()
        quiz_name = quiz[0] if quiz else 'Unknown Quiz'
        recent.append({'result_id': r[0], 'quiz_name': quiz_name,
                       'accuracy': r[2], 'avg_time': r[3], 'date': r[4]})

    # All quizzes grouped by topic
    quizzes = q_cursor.execute('SELECT id, name, topic, level FROM quizzes ORDER BY topic, name').fetchall()
    q_conn.close()

    topics = {}
    for quiz in quizzes:
        topic = quiz[2]
        if topic not in topics:
            topics[topic] = []
        topics[topic].append(quiz)

    return render_template('dashboard.html',
        first_name=user[0], last_name=user[1], email=user[2],
        user_level=user[3] if user[3] else 1,
        topics=topics,
        recent=recent) 


@app.route('/teacher_dashboard')
def teacher_home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if not session.get('is_admin'):
        return redirect(url_for('home'))

    login_conn = sqlite3.connect('database/LoginData.db')
    login_cursor = login_conn.cursor()

    login_cursor.execute('SELECT first_name, last_name, email FROM users WHERE id=?', (session['user_id'],))
    user = login_cursor.fetchone()

    # Summary stats
    total_students = login_cursor.execute(
        "SELECT COUNT(*) FROM users WHERE is_admin = 0").fetchone()[0]
    total_attempts = login_cursor.execute(
        "SELECT COUNT(*) FROM results").fetchone()[0]
    avg_accuracy = login_cursor.execute(
        "SELECT ROUND(AVG(accuracy),1) FROM results").fetchone()[0] or 0

    # Recent activity — last 10 attempts across all students
    recent_raw = login_cursor.execute('''
        SELECT r.id, r.user_id, u.first_name, u.last_name,
               r.quiz_id, r.accuracy, r.avg_time, r.date
        FROM results r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.date DESC LIMIT 10
    ''').fetchall()
    login_conn.close()

    # Attach quiz names to recent activity
    q_conn = sqlite3.connect('database/Questions.db')
    q_cursor = q_conn.cursor()
    total_quizzes = q_cursor.execute("SELECT COUNT(*) FROM quizzes").fetchone()[0]
    total_questions = q_cursor.execute("SELECT COUNT(*) FROM questions").fetchone()[0]

    recent = []
    for r in recent_raw:
        quiz = q_cursor.execute('SELECT name FROM quizzes WHERE id=?', (r[4],)).fetchone()
        recent.append({
            'result_id': r[0], 'user_id': r[1],
            'student': f"{r[2]} {r[3]}",
            'quiz_name': quiz[0] if quiz else 'Unknown',
            'accuracy': r[5], 'avg_time': r[6], 'date': r[7]
        })
    q_conn.close()

    return render_template('teacherHome.html',
        first_name=user[0], last_name=user[1], email=user[2],
        total_students=total_students, total_quizzes=total_quizzes,
        total_questions=total_questions, total_attempts=total_attempts,
        avg_accuracy=avg_accuracy, recent=recent) 

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

@app.route("/usermanagement")
def user_management():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    login_conn = sqlite3.connect('database/LoginData.db')
    login_cursor = login_conn.cursor()

    users = login_cursor.execute(
        "SELECT first_name, last_name, email, is_admin, id, level FROM users ORDER BY last_name"
    ).fetchall()

    # Class-wide stats
    total_students = login_cursor.execute(
        "SELECT COUNT(*) FROM users WHERE is_admin = 0").fetchone()[0]
    class_avg = login_cursor.execute(
        "SELECT ROUND(AVG(accuracy),1) FROM results").fetchone()[0] or 0

    login_conn.close()

    # Most attempted quiz
    q_conn = sqlite3.connect('database/Questions.db')
    q_cursor = q_conn.cursor()
    login_conn2 = sqlite3.connect('database/LoginData.db')
    login_cursor2 = login_conn2.cursor()
    top_quiz_row = login_cursor2.execute(
        "SELECT quiz_id, COUNT(*) as cnt FROM results GROUP BY quiz_id ORDER BY cnt DESC LIMIT 1"
    ).fetchone()
    top_quiz_name = ''
    if top_quiz_row:
        q = q_cursor.execute('SELECT name FROM quizzes WHERE id=?', (top_quiz_row[0],)).fetchone()
        top_quiz_name = q[0] if q else 'Unknown'
    q_conn.close()
    login_conn2.close()

    return render_template("studentManagement.html",
        users=users, total_students=total_students,
        class_avg=class_avg, top_quiz_name=top_quiz_name)


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

    return redirect(url_for('add_question_page'))

@app.route('/add_question_page')
def add_question_page():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    quizzes = cursor.execute('SELECT * FROM quizzes').fetchall()
    # Join questions with quiz name; include question_type and marks if columns exist
    try:
        questions = cursor.execute('''
            SELECT q.id, q.topic, q.level, q.question_text, q.correct_answer,
                   q.option_a, q.option_b, q.option_c, q.option_d,
                   q.quiz_id, qz.name, q.question_type, q.marks
            FROM questions q
            JOIN quizzes qz ON q.quiz_id = qz.id
            ORDER BY qz.name, q.level, q.id
        ''').fetchall()
    except:
        questions = cursor.execute('''
            SELECT q.id, q.topic, q.level, q.question_text, q.correct_answer,
                   q.option_a, q.option_b, q.option_c, q.option_d,
                   q.quiz_id, qz.name, NULL, NULL
            FROM questions q
            JOIN quizzes qz ON q.quiz_id = qz.id
            ORDER BY qz.name, q.level, q.id
        ''').fetchall()
    connection.close()

    return render_template('createQuiz.html', quizzes=quizzes, questions=questions)

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
    cursor.execute("INSERT INTO questions (quiz_id, topic, level, question_text, option_a, option_b, option_c, option_d, correct_answer) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (quiz_id, topic, level, question_text, option_a, option_b, option_c, option_d, correct_answer))
    connection.commit()
    connection.close()

    return redirect(url_for('add_question_page'))

# Time limits in seconds per mark for each level (0 = no limit)
LEVEL_TIME_PER_MARK = {1: 0, 2: 180, 3: 144, 4: 108, 5: 90}

@app.route('/select_level/<int:quiz_id>')
def select_level(quiz_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    quiz = cursor.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    connection.close()
    return render_template('selectLevel.html', quiz=quiz)


@app.route('/quiz/<int:quiz_id>')
def quiz(quiz_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    level = int(request.args.get('level', 1))
    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    quiz = cursor.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    questions = cursor.execute("""
        SELECT id, question_text, option_a, option_b, option_c, option_d, marks
        FROM questions WHERE quiz_id = ? AND level <= ?
        ORDER BY level ASC
    """, (quiz_id, level)).fetchall()
    connection.close()
    time_per_mark = LEVEL_TIME_PER_MARK.get(level, 0)
    return render_template('quiz.html', questions=questions, quiz=quiz,
                           level=level, time_per_mark=time_per_mark)


@app.route('/upload_questions', methods=['POST'])
def upload_questions():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    file = request.files.get('csv_file')
    if not file or not file.filename.endswith('.csv'):
        return redirect(url_for('add_question_page'))
    stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
    reader = csv.DictReader(stream)
    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    # Add new columns if they don't exist yet
    try:
        cursor.execute("ALTER TABLE questions ADD COLUMN question_type TEXT DEFAULT 'mc'")
        cursor.execute("ALTER TABLE questions ADD COLUMN marks INTEGER DEFAULT 1")
        connection.commit()
    except:
        pass
    imported = 0
    errors = []
    required = ['quiz_id', 'topic', 'level', 'question_type', 'question_text', 'marks']
    for i, row in enumerate(reader, start=2):
        missing = [f for f in required if not row.get(f, '').strip()]
        if missing:
            errors.append(f"Row {i}: missing fields: {', '.join(missing)}")
            continue
        q_type = row['question_type'].strip().lower()
        if q_type not in ('mc', 'short', 'long'):
            errors.append(f"Row {i}: question_type must be mc, short, or long")
            continue
        try:
            level = int(row['level'].strip())
            marks = int(row['marks'].strip())
            quiz_id = int(row['quiz_id'].strip())
            if not 1 <= level <= 5:
                raise ValueError
        except ValueError:
            errors.append(f"Row {i}: level must be 1-5, marks and quiz_id must be integers")
            continue
        if q_type == 'mc':
            correct = row.get('correct_answer', '').strip().upper()
            if correct not in ('A', 'B', 'C', 'D'):
                errors.append(f"Row {i}: MC question must have correct_answer A, B, C, or D")
                continue
            option_a = row.get('option_a', '').strip()
            option_b = row.get('option_b', '').strip()
            option_c = row.get('option_c', '').strip()
            option_d = row.get('option_d', '').strip()
        else:
            correct = ''
            option_a = option_b = option_c = option_d = ''
        cursor.execute("""
            INSERT INTO questions (quiz_id, topic, level, question_text,
                option_a, option_b, option_c, option_d, correct_answer, question_type, marks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (quiz_id, row['topic'].strip(), level, row['question_text'].strip(),
              option_a, option_b, option_c, option_d, correct, q_type, marks))
        imported += 1
    connection.commit()
    connection.close()
    return render_template('uploadQuestions.html', imported=imported, errors=errors)


@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    if request.method == 'POST':
        cursor.execute("""
            UPDATE questions SET topic=?, level=?, question_text=?,
            option_a=?, option_b=?, option_c=?, option_d=?, correct_answer=?, marks=?
            WHERE id=?
        """, (
            request.form.get('topic'),
            int(request.form.get('level')),
            request.form.get('question_text'),
            request.form.get('option_a', ''),
            request.form.get('option_b', ''),
            request.form.get('option_c', ''),
            request.form.get('option_d', ''),
            request.form.get('correct_answer', ''),
            int(request.form.get('marks', 1)),
            question_id
        ))
        connection.commit()
        connection.close()
        return redirect(url_for('add_question_page'))
    question = cursor.execute('SELECT * FROM questions WHERE id = ?', (question_id,)).fetchone()
    quizzes = cursor.execute('SELECT * FROM quizzes').fetchall()
    connection.close()
    return render_template('editQuestion.html', question=question, quizzes=quizzes)


@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    connection.commit()
    connection.close()
    return redirect(url_for('add_question_page'))


@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = request.get_json()
    answers = data['answers']
    quiz_id = data['quiz_id']

    questions_conn = sqlite3.connect('database/Questions.db')
    q_cursor = questions_conn.cursor()

    questions = q_cursor.execute('''
        SELECT id, question_text, correct_answer, question_type, marks
        FROM questions WHERE quiz_id=?
    ''', (quiz_id,)).fetchall()
    questions_conn.close()

    total_marks = 0
    earned_marks = 0
    total_time = 0
    wrong_questions = []
    written_answers = []
    has_written = False

    for question in questions:
        q_id = str(question[0])
        q_text = question[1]
        correct = question[2]
        q_type = question[3] if question[3] else 'mc'
        marks = question[4] if question[4] else 1

        if q_id not in answers:
            continue

        user_answer = answers[q_id]['answer']
        time_taken = answers[q_id]['time']
        total_time += time_taken
        total_marks += marks

        if q_type == 'mc':
            if user_answer == correct:
                earned_marks += marks
            else:
                wrong_questions.append({
                    'question': q_text,
                    'your_answer': user_answer,
                    'correct_answer': correct
                })
        else:
            has_written = True
            written_answers.append({
                'question_id': q_id,
                'question_text': q_text,
                'question_type': q_type,
                'answer': user_answer,
                'max_marks': marks
            })

    answered = len(answers)
    accuracy = round((earned_marks / total_marks) * 100, 1) if total_marks > 0 else 0
    avg_time = round(total_time / answered, 1) if answered > 0 else 0

    
    marking_complete = 0 if has_written else 1

    login_conn = sqlite3.connect('database/LoginData.db')
    login_cursor = login_conn.cursor()

    login_cursor.execute('''INSERT INTO results 
        (user_id, quiz_id, score, accuracy, avg_time, wrong_questions,
         written_answers, written_marks, marking_complete, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (session['user_id'], quiz_id, earned_marks, accuracy, avg_time,
         json.dumps(wrong_questions), json.dumps(written_answers),
         json.dumps([]),  # empty until teacher marks
         marking_complete, str(date.today())))

    login_conn.commit()
    result_id = login_cursor.lastrowid
    login_conn.close()

    return json.dumps({'result_id': result_id})

    return json.dumps({'result_id': result_id})

@app.route('/results/<int:result_id>')
def results(result_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = sqlite3.connect('database/LoginData.db')
    cursor = connection.cursor()

    if session.get('is_admin'):
        result = cursor.execute(
            '''SELECT score, accuracy, avg_time, wrong_questions, 
               date, written_answers, written_marks, marking_complete 
               FROM results WHERE id=?''',
            (result_id,)
        ).fetchone()
    else:
        result = cursor.execute(
            '''SELECT score, accuracy, avg_time, wrong_questions,
               date, written_answers, written_marks, marking_complete
               FROM results WHERE id=? AND user_id=?''',
            (result_id, session['user_id'])
        ).fetchone()

    connection.close()

    if not result:
        return "Result not found.", 404

    try:
        wrong_questions = json.loads(result[3]) if result[3] else []
    except:
        wrong_questions = []

    try:
        written_answers = json.loads(result[5]) if result[5] else []
    except:
        written_answers = []

    try:
        written_marks = json.loads(result[6]) if result[6] else []
    except:
        written_marks = []

    marks_by_id = {str(m['question_id']): m for m in written_marks}

    return render_template('results.html',
        score=result[0],
        accuracy=result[1],
        avg_time=result[2],
        wrong_questions=wrong_questions,
        date=result[4],
        written_answers=written_answers,
        marks_by_id=marks_by_id,
        marking_complete=result[7],
        result_id=result_id)

@app.route('/student/<int:user_id>')
def student_detail(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    login_conn = sqlite3.connect('database/LoginData.db')
    login_cursor = login_conn.cursor()

    student = login_cursor.execute(
        'SELECT first_name, last_name, email, level FROM users WHERE id=?', (user_id,)
    ).fetchone()

    attempts = login_cursor.execute('''
        SELECT id, quiz_id, score, accuracy, avg_time, date
        FROM results WHERE user_id = ?
        ORDER BY date DESC
    ''', (user_id,)).fetchall()

    # Overall stats for this student
    stats = login_cursor.execute('''
        SELECT COUNT(*), ROUND(AVG(accuracy),1), ROUND(AVG(avg_time),1)
        FROM results WHERE user_id = ?
    ''', (user_id,)).fetchone()
    login_conn.close()

    # Attach quiz names
    q_conn = sqlite3.connect('database/Questions.db')
    q_cursor = q_conn.cursor()
    history = []
    for a in attempts:
        quiz = q_cursor.execute('SELECT name FROM quizzes WHERE id=?', (a[1],)).fetchone()
        history.append({
            'result_id': a[0], 'quiz_name': quiz[0] if quiz else 'Unknown',
            'score': a[2], 'accuracy': a[3], 'avg_time': a[4], 'date': a[5]
        })
    q_conn.close()

    return render_template('studentDetails.html',
        student=student, user_id=user_id, history=history,
        total_attempts=stats[0], avg_accuracy=stats[1], avg_time=stats[2])

@app.route('/manage_quizzes')
def manage_quizzes():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()

    quizzes = cursor.execute('''SELECT qz.id, qz.name, qz.topic, qz.level, COUNT(q.id) as question_count FROM quizzes qz LEFT JOIN questions q ON q.quiz_id = qz.id GROUP BY qz.id ORDER BY qz.name''').fetchall()
    connection.close()

    return render_template('manageQuizzes.html', quizzes=quizzes)

@app.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    # Delete all questions in the quiz first, then the quiz itself
    cursor.execute('DELETE FROM questions WHERE quiz_id=?', (quiz_id,))
    cursor.execute('DELETE FROM quizzes WHERE id=?', (quiz_id,))
    connection.commit()
    connection.close()

    return redirect(url_for('manage_quizzes'))


@app.route('/quiz_detail/<int:quiz_id>')
def quiz_detail(quiz_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()

    quiz = cursor.execute('SELECT * FROM quizzes WHERE id=?', (quiz_id,)).fetchone()
    questions = cursor.execute('''
        SELECT id, question_text, option_a, option_b, option_c, option_d, correct_answer, level, question_type, marks
        FROM questions WHERE quiz_id=?
        ORDER BY level, id
    ''', (quiz_id,)).fetchall()
    all_quizzes = cursor.execute('SELECT id, name FROM quizzes').fetchall()
    connection.close()

    return render_template('quizDisplay.html', quiz=quiz,
                           questions=questions, all_quizzes=all_quizzes)


@app.route('/edit_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()

    if request.method == 'POST':
        name = request.form.get('name')
        topic = request.form.get('topic')
        level = request.form.get('level')
        cursor.execute('UPDATE quizzes SET name=?, topic=?, level=? WHERE id=?',
                       (name, topic, level, quiz_id))
        connection.commit()
        connection.close()
        return redirect(url_for('quiz_detail', quiz_id=quiz_id))

    quiz = cursor.execute('SELECT * FROM quizzes WHERE id=?', (quiz_id,)).fetchone()
    connection.close()
    return render_template('editQuiz.html', quiz=quiz)


@app.route('/move_question/<int:question_id>', methods=['POST'])
def move_question(question_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    new_quiz_id = request.form.get('new_quiz_id')
    original_quiz_id = request.form.get('original_quiz_id')

    connection = sqlite3.connect('database/Questions.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE questions SET quiz_id=? WHERE id=?', (new_quiz_id, question_id))
    connection.commit()
    connection.close()

    return redirect(url_for('quiz_detail', quiz_id=original_quiz_id))

@app.route('/mark_answers/<int:result_id>', methods=['GET', 'POST'])
def mark_answers(result_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    login_conn = sqlite3.connect('database/LoginData.db')
    login_cursor = login_conn.cursor()

    if request.method == 'POST':
        written_marks = []
        total_written_marks = 0
        earned_written_marks = 0

        # Get existing result
        result = login_cursor.execute(
            'SELECT written_answers, score, accuracy FROM results WHERE id=?',
            (result_id,)
        ).fetchone()

        written_answers = json.loads(result[0])

        for wa in written_answers:
            q_id = wa['question_id']
            mark = int(request.form.get(f'mark_{q_id}', 0))
            feedback = request.form.get(f'feedback_{q_id}', '')
            max_marks = wa['max_marks']

            written_marks.append({
                'question_id': q_id,
                'question_text': wa['question_text'],
                'answer': wa['answer'],
                'mark': mark,
                'max_marks': max_marks,
                'feedback': feedback
            })

            total_written_marks += max_marks
            earned_written_marks += mark

        # Recalculate overall score and accuracy including written marks
        old_score = result[1] or 0
        new_score = old_score + earned_written_marks

        # Get total possible marks for the quiz
        q_conn = sqlite3.connect('database/Questions.db')
        q_cursor = q_conn.cursor()
        quiz_id = login_cursor.execute(
            'SELECT quiz_id FROM results WHERE id=?', (result_id,)
        ).fetchone()[0]
        total_possible = q_cursor.execute(
            'SELECT SUM(marks) FROM questions WHERE quiz_id=?', (quiz_id,)
        ).fetchone()[0] or 1
        q_conn.close()

        new_accuracy = round((new_score / total_possible) * 100, 1)

        login_cursor.execute('''UPDATE results SET
            written_marks=?, marking_complete=1,
            score=?, accuracy=?
            WHERE id=?''',
            (json.dumps(written_marks), new_score, new_accuracy, result_id))
        login_conn.commit()
        login_conn.close()

        return redirect(url_for('results', result_id=result_id))

    # GET — load the result for marking
    result = login_cursor.execute('''
        SELECT r.id, r.written_answers, r.written_marks, r.marking_complete,
               u.first_name, u.last_name, q.name
        FROM results r
        JOIN users u ON r.user_id = u.id
        JOIN quizzes q ON r.quiz_id = q.id
        WHERE r.id=?
    ''', (result_id,)).fetchone()

    # Join quizzes from Questions.db
    q_conn = sqlite3.connect('database/Questions.db')
    login_conn.close()

    written_answers = json.loads(result[1]) if result[1] else []
    written_marks = json.loads(result[2]) if result[2] else []

    # Merge existing marks back in if re-marking
    marks_by_id = {str(m['question_id']): m for m in written_marks}

    return render_template('marking.html', result=result, written_answers=written_answers, marks_by_id=marks_by_id, result_id=result_id)

if __name__ == '__main__':
    app.run(debug=True) 
 # Starts the Flask application using the Waitress WSGI server, listening on all available network interfaces (
