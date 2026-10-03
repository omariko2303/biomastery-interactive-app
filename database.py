import sqlite3

DB_FILE = "biomastery_local.db"

def init_local_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS local_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT,
            topic TEXT,
            score INTEGER,
            total INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_score(candidate_name, topic, score, total):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO local_logs (candidate_name, topic, score, total) VALUES (?, ?, ?, ?)", 
              (candidate_name, topic, score, total))
    conn.commit()
    conn.close()
