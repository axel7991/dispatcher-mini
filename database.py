import sqlite3

def get_connection():
    connection = sqlite3.connect("dispatcher.db")
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