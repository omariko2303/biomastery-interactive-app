import sqlite3

def init_local_db():
    conn = sqlite3.connect("biomastery.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            name TEXT,
            topic TEXT,
            score INTEGER,
            questions_count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def log_score(email, name, topic, score, q_count=1):
    conn = sqlite3.connect("biomastery.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO student_scores (email, name, topic, score, questions_count)
        VALUES (?, ?, ?, ?, ?)
    """, (email, name, topic, score, q_count))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect("biomastery.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, SUM(score) as total_score, SUM(questions_count) as total_qs,
               ROUND((CAST(SUM(score) AS FLOAT) / SUM(questions_count)) * 100, 1) as accuracy
        FROM student_scores
        GROUP BY email
        ORDER BY total_score DESC, accuracy DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows
