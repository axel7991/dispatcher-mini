import sqlite3
import os

def get_connection():
    database_path = os.getenv("DATABASE_PATH", "dispatcher.db")
    connection = sqlite3.connect(database_path)
    return connection

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            intent TEXT,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()

def save_request(message, intent, department):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO requests (message, intent, department)
        VALUES (?, ?, ?)
    """, (message, intent, department))

    connection.commit()
    connection.close()

if __name__ == "__main__":
    create_tables()