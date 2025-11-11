from flask import Flask, render_template, request, redirect, url_for, session, abort
import mysql.connector

app = Flask(__name__)
app.secret_key = '1234'  

# connect to the database; if it fails, set conn = None so the app can still run
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Anita@#123",
        database="college"
    )
    if conn.is_connected():
        print("Connected to MySQL Database!")
except mysql.connector.Error as e:
    print("Warning: could not connect to database:", e)
    conn = None
# avoid creating a global cursor at import time; create cursors per-request

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not conn:
            msg = 'Database is unavailable. Try again later.'
            return render_template('login.html', msg=msg)

        cursor = conn.cursor(buffered=True)
        try:
            cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
            user = cursor.fetchone()
        finally:
            cursor.close()

        if user:
            session['username'] = username
            return redirect(url_for('main'))
        else:
            msg = 'Invalid credentials. Please try again.'
    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if not conn:
            msg = 'Database is unavailable. Try again later.'
            return render_template('register.html', msg=msg)

        cursor = conn.cursor(buffered=True)
        try:
            cursor.execute('SELECT * FROM users WHERE username=%s', (username,))
            account = cursor.fetchone()

            if account:
                msg = 'Username already exists!'
            else:
                cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                               (username, email, password))
                conn.commit()
                msg = 'Registration successful! You can now login.'
        finally:
            cursor.close()
    return render_template('register.html', msg=msg)

@app.route('/main')
def main():
    if 'username' in session:
        username = session['username']
        return f"<h2>Welcome, {username}!</h2><br><a href='/logout'>Logout</a>"
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/_debug/users')
def _debug_users():
    """Temporary debug route to list users. Only works when app.debug is True.
       Shows (id, username, email, password) to help diagnose login issues.
    """
    if not app.debug:
        abort(404)
    if not conn:
        return "No DB connection"
    cur = conn.cursor(buffered=True)
    try:
        cur.execute("SELECT id, username, email, password FROM users LIMIT 200")
        rows = cur.fetchall()
    finally:
        cur.close()
    # Render a simple plain text response
    out = []
    for r in rows:
        out.append(str(r))
    return "<pre>" + "\n".join(out) + "</pre>"


if __name__ == '__main__':
    app.run(debug=True)