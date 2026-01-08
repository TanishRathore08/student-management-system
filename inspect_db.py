
import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Anita@#123",
        database="college"
    )
    if conn.is_connected():
        print("Connected to MySQL Database 'college'!")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Tables:", tables)
        
        for (table_name,) in tables:
            print(f"\nSchema for {table_name}:")
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            for col in columns:
                print(col)
                
except mysql.connector.Error as e:
    print("Error:", e)
