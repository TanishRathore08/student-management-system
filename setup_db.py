
import mysql.connector
import random
from datetime import datetime, timedelta

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Anita@#123",
        database="college"
    )

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    tables = {
        'students': """
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                course VARCHAR(100),
                enrollment_date DATE,
                status VARCHAR(20) DEFAULT 'Active'
            )
        """,
        'courses': """
            CREATE TABLE IF NOT EXISTS courses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                status VARCHAR(20) DEFAULT 'Active'
            )
        """,
        'fees': """
            CREATE TABLE IF NOT EXISTS fees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT,
                amount DECIMAL(10, 2),
                status VARCHAR(20) DEFAULT 'Pending',
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """
    }

    print("Creating tables...")
    for name, sql in tables.items():
        cursor.execute(sql)
        print(f"Table '{name}' check/create done.")

    # Populate Data
    print("\nPopulating data...")
    
    # Courses
    cursor.execute("TRUNCATE TABLE courses") # Reset for fresh start
    courses_data = [('Computer Science', 'Active'), ('Mathematics', 'Active'), 
                    ('Physics', 'Active'), ('Chemistry', 'Active'), ('Biology', 'Active')]
    cursor.executemany("INSERT INTO courses (name, status) VALUES (%s, %s)", courses_data)
    
    # Students
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE students")
    cursor.execute("TRUNCATE TABLE fees")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    students_data = []
    course_names = [c[0] for c in courses_data]
    statuses = ['Active', 'Active', 'Active', 'Pending'] # bias towards active
    
    for i in range(20):
        name = f"Student {i+1}"
        course = random.choice(course_names)
        date = datetime.now() - timedelta(days=random.randint(0, 365))
        status = random.choice(statuses)
        students_data.append((name, course, date.strftime('%Y-%m-%d'), status))

    cursor.executemany("INSERT INTO students (name, course, enrollment_date, status) VALUES (%s, %s, %s, %s)", students_data)
    
    # Fees
    cursor.execute("SELECT id from students WHERE status='Pending'")
    pending_students = cursor.fetchall()
    
    fees_data = []
    for (sid,) in pending_students:
        fees_data.append((sid, random.randint(500, 2000), 'Pending'))
        
    if fees_data:
        cursor.executemany("INSERT INTO fees (student_id, amount, status) VALUES (%s, %s, %s)", fees_data)

    conn.commit()
    print("Database setup completed successfully!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        setup_database()
    except Exception as e:
        print(f"Error: {e}")
