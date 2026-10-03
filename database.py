import sqlite3

DB_FILE = "biomastery_local.db"

def init_local_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS local_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT,
            student_name TEXT,
            topic TEXT,
            score INTEGER,
            total INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_score(student_email, student_name, topic, score, total):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO local_logs (student_email, student_name, topic, score, total) VALUES (?, ?, ?, ?, ?)", 
        (student_email, student_name, topic, score, total)
    )
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT 
            student_name,
            SUM(score) as total_score,
            SUM(total) as total_questions,
            ROUND((CAST(SUM(score) AS FLOAT) / CAST(SUM(total) AS FLOAT)) * 100, 1) as accuracy
        FROM local_logs
        GROUP BY student_email
        HAVING total_questions > 0
        ORDER BY total_score DESC, accuracy DESC
    ''')
    rows = c.fetchall()
    conn.close()
    return rows
