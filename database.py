import sqlite3

DB_FILE = "biomastery_local.db"

def init_local_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create main table if it doesn't exist
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
    
    # Safely migrate existing tables if columns are missing
    c.execute("PRAGMA table_info(local_logs)")
    columns = [column[1] for column in c.fetchall()]
    
    if "student_email" not in columns:
        c.execute("ALTER TABLE local_logs ADD COLUMN student_email TEXT")
    if "student_name" not in columns:
        c.execute("ALTER TABLE local_logs ADD COLUMN student_name TEXT")
        
    conn.commit()
    conn.close()

def log_score(student_email, student_name, topic, score, total):
    init_local_db()  # Ensure table structure is valid
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO local_logs (student_email, student_name, topic, score, total) VALUES (?, ?, ?, ?, ?)", 
        (student_email, student_name, topic, score, total)
    )
    conn.commit()
    conn.close()

def get_leaderboard():
    init_local_db()  # Ensure table structure is valid
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT 
                COALESCE(student_name, 'Anonymous Candidate') as student_name,
                SUM(score) as total_score,
                SUM(total) as total_questions,
                ROUND((CAST(SUM(score) AS FLOAT) / CAST(SUM(total) AS FLOAT)) * 100, 1) as accuracy
            FROM local_logs
            GROUP BY student_email
            HAVING total_questions > 0
            ORDER BY total_score DESC, accuracy DESC
        ''')
        rows = c.fetchall()
    except Exception as e:
        print(f"[Leaderboard Error] {e}")
        rows = []
    finally:
        conn.close()
    return rows
