import sqlite3
from datetime import datetime

# DB 초기화, 테이블 생성
def init_db():
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            input_text TEXT,
            emotion TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


# DB에 대화 내용 저장
def save_message(user_id, message, emotion=""):
    conn = sqlite3.connect("conversation.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO conversations (user_id, input_text, emotion, timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, message, emotion, datetime.now().isoformat()))
    conn.commit()
    conn.close()

