import sqlite3
import os
from datetime import datetime

DB_NAME = "exam.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            student_id TEXT NOT NULL,
            level TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            time_spent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_score(first_name, last_name, student_id, level, score, time_spent):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (first_name, last_name, student_id, level, score, time_spent)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (first_name, last_name, student_id, level, score, int(time_spent)))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT first_name, last_name, student_id, level, score, time_spent 
        FROM users 
        ORDER BY score DESC, time_spent ASC 
        LIMIT 50
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_scores():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, first_name, last_name, student_id, level, score, time_spent, created_at 
        FROM users 
        ORDER BY created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
