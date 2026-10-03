import sqlite3
from datetime import datetime

DB_FILE = "biomastery_interactive.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # User Profile / Student Session
    c.execute('''
        CREATE TABLE IF NOT EXISTS student_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            syllabus_code TEXT NOT NULL,
            total_questions INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            score_percentage REAL DEFAULT 0.0,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Detailed Question Log
    c.execute('''
        CREATE TABLE IF NOT EXISTS question_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            question_id TEXT NOT NULL,
            syllabus_code TEXT NOT NULL,
            selected_option TEXT,
            is_correct INTEGER,
            time_taken_sec INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES student_sessions(session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_session_results(student_name, syllabus_code, total_q, correct_q, log_details):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    pct = round((correct_q / total_q) * 100, 1) if total_q > 0 else 0.0
    c.execute('''
        INSERT INTO student_sessions (student_name, syllabus_code, total_questions, correct_answers, score_percentage)
        VALUES (?, ?, ?, ?, ?)
    ''', (student_name, syllabus_code, total_q, correct_q, pct))
    
    session_id = c.lastrowid
    
    for log in log_details:
        c.execute('''
            INSERT INTO question_logs (session_id, question_id, syllabus_code, selected_option, is_correct)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, log['question_id'], log['syllabus_code'], log['selected_option'], 1 if log['is_correct'] else 0))
        
    conn.commit()
    conn.close()
    return session_id

def get_student_performance(student_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT session_id, syllabus_code, total_questions, correct_answers, score_percentage, completed_at 
        FROM student_sessions 
        WHERE student_name = ? 
        ORDER BY completed_at DESC
    ''', (student_name,))
    rows = c.fetchall()
    conn.close()
    return rows
