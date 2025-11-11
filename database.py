import mysql.connector

try:
    
    conn = mysql.connector.connect(
        host="localhost",       
        user="root",            
        password="Anita@#123",        
        database="student_db"      
    )


    if conn.is_connected():
        print("Connected to MySQL Database!")

    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT * from students;")
    records = cursor.fetchall()
    # print the first record (if any) for a quick sanity check
    print("Current database:", records[0] if records else None)
    cursor.close()

except mysql.connector.Error as e:
    print("Database connection failed:", e)