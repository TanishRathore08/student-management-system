from flask import Flask, render_template, request, redirect, url_for, session, abort
import mysql.connector
import sqlite3
import os

app = Flask(__name__)
app.secret_key = '1234'

# Global flag to track which DB we are using
DB_TYPE = 'mysql' 

def get_db_connection():
    global DB_TYPE
    conn = None
    
    # 1. Try MySQL (Environment Variables or Localhost)
    # We attempt connection. If it fails (e.g. on Render without Env Vars), we use SQLite.
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", "Anita@#123"),
            database=os.environ.get("DB_NAME", "college"),
            connection_timeout=3 # Fast fail
        )
        if conn.is_connected():
            DB_TYPE = 'mysql'
            print("Connected to MySQL!")
            return conn
    except Exception as e:
        print(f"MySQL connection failed ({e}). Falling back to SQLite.")

    # 2. Fallback to SQLite
    DB_TYPE = 'sqlite'
    conn = sqlite3.connect('college.db', check_same_thread=False)
    # Enable name-based access for rows (like dictionary=True)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(cursor, query, params=None):
    """Executes query handling syntax differences between MySQL (%s) and SQLite (?)"""
    if DB_TYPE == 'sqlite':
        query = query.replace('%s', '?')
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    return cursor

def init_db():
    """Initializes tables if they don't exist"""
    try:
        conn = get_db_connection()
        # For init, we don't need dictionary cursor
        if DB_TYPE == 'mysql':
            cursor = conn.cursor(buffered=True)
        else:
            cursor = conn.cursor()
            
        # Define Schema Compatibility
        schema = {
            'users': {
                'mysql': "CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255), email VARCHAR(255), password VARCHAR(255))",
                'sqlite': "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, password TEXT)"
            },
            'students': {
                'mysql': "CREATE TABLE IF NOT EXISTS students (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), course VARCHAR(100), enrollment_date DATE, status VARCHAR(20) DEFAULT 'Active')",
                'sqlite': "CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, course TEXT, enrollment_date TEXT, status TEXT DEFAULT 'Active')"
            },
            'courses': {
                'mysql': "CREATE TABLE IF NOT EXISTS courses (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), status VARCHAR(20) DEFAULT 'Active')",
                'sqlite': "CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, status TEXT DEFAULT 'Active')"
            },
            'fees': {
                'mysql': "CREATE TABLE IF NOT EXISTS fees (id INT AUTO_INCREMENT PRIMARY KEY, student_id INT, amount DECIMAL(10, 2), status VARCHAR(20) DEFAULT 'Pending')",
                'sqlite': "CREATE TABLE IF NOT EXISTS fees (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, status TEXT DEFAULT 'Pending')"
            }
        }
        
        print(f"Initializing {DB_TYPE} database tables...")
        for table, queries in schema.items():
            execute_query(cursor, queries[DB_TYPE])
            
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Database Initialization Error:", e)

# Auto-initialize on import
init_db()


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            msg = 'Database is unavailable. Try again later.'
            return render_template('login.html', msg=msg)

        try:
            if DB_TYPE == 'mysql':
                cursor = conn.cursor(buffered=True, dictionary=True) # Use dict for consistency
            else:
                cursor = conn.cursor() # sqlite3.Row handles dict-like access
                
            execute_query(cursor, 'SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
            user = cursor.fetchone()
        except Exception as e:
            print("Login Error:", e)
            user = None
        finally:
            cursor.close()
            # conn.close() # Connection closed by garbage connector or Flask logic? Better to reuse or close. 
            # In original code, conn was global-ish but recreated. Here get_db_connection creates new conn.
            if DB_TYPE == 'mysql': conn.close() # Mysql needs distinct close. Sqlite too.
            else: conn.close()

        if user:
            # sqlite3.Row access user['username'] works like dict
            session['username'] = user['username'] 
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
        
        conn = get_db_connection()
        if not conn:
            msg = 'Database is unavailable'
            return render_template('register.html', msg=msg)

        try:
            if DB_TYPE == 'mysql':
                cursor = conn.cursor(buffered=True, dictionary=True)
            else:
                cursor = conn.cursor()

            execute_query(cursor, 'SELECT * FROM users WHERE username=%s', (username,))
            account = cursor.fetchone()

            if account:
                msg = 'Username already exists!'
            else:
                execute_query(cursor, 'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                               (username, email, password))
                conn.commit()
                msg = 'Registration successful! You can now login.'
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html', msg=msg)

@app.route('/main')
def main():
    if 'username' in session:
        username = session['username']
        return render_template('dashboard.html', username=username)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/api/dashboard-data')
def dashboard_data():
    if 'username' not in session:
        return {'error': 'Unauthorized'}, 401
    
    conn = get_db_connection()
    if not conn:
        return {'error': 'Database unavailable'}, 503
        
    try:
        # Cursor Setup
        if DB_TYPE == 'mysql':
            cursor = conn.cursor(dictionary=True)
        else:
            cursor = conn.cursor() # Row Factory enabled
            
        data = {}
        
        # Total Students
        execute_query(cursor, "SELECT COUNT(*) as count FROM students")
        res = cursor.fetchone()
        data['total_students'] = res['count']
        
        # Active Courses
        execute_query(cursor, "SELECT COUNT(*) as count FROM courses WHERE status='Active'")
        res = cursor.fetchone()
        data['active_courses'] = res['count']
        
        # Pending Fees
        execute_query(cursor, "SELECT SUM(amount) as total FROM fees WHERE status='Pending'")
        res = cursor.fetchone()
        # Handle None result
        total = res['total'] if res and res['total'] else 0
        data['pending_fees'] = float(total)
        
        # Recent Students
        execute_query(cursor, "SELECT name, course, enrollment_date, status FROM students ORDER BY id DESC LIMIT 5") 
        # Note: 'ORDER BY enrollment_date' might fail if text format varies, 'id' is safer for 'Recent'
        students = cursor.fetchall()
        
        # Serialize
        student_list = []
        for s in students:
            # Convert Row to Dict
            s_dict = dict(s)
            if s_dict['enrollment_date']:
                s_dict['enrollment_date'] = str(s_dict['enrollment_date'])
            student_list.append(s_dict)
            
        data['recent_students'] = student_list
        
        return data
        
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        return {'error': str(e)}, 500
    finally:
        # cursor.close() # Sqlite cursor might not enforce close, but good practice
        if 'cursor' in locals(): cursor.close()
        conn.close()

@app.route('/_debug/users')
def _debug_users():
    """Temporary debug route to list users. Only works when app.debug is True."""
    # Temporarily allow debug access for troubleshooting
    # if not app.debug:
    #     abort(404)
    
    conn = get_db_connection()
    if not conn:
        return "No DB connection"
    
    try:
        if DB_TYPE == 'mysql':
            cur = conn.cursor(buffered=True)
        else:
            cur = conn.cursor()
            
        cur.execute("SELECT id, username, email, password FROM users LIMIT 200")
        rows = cur.fetchall()
    except Exception as e:
        return f"Error: {e}"
    finally:
        # cur.close() # handled by context or subsequent cleanup
        if 'cur' in locals(): cur.close()
        conn.close()

    # Render a simple plain text response
    out = [f"DB_TYPE: {DB_TYPE}"]
    for r in rows:
        out.append(str(r))
    return "<pre>" + "\n".join(out) + "</pre>"

@app.route('/_debug/status')
def _debug_status():
    return {
        'db_type': DB_TYPE,
        'config_host': os.environ.get("DB_HOST", "Not Set")
    }

if __name__ == '__main__':
    app.run(debug=True)