import sqlite3
import json
from datetime import datetime
import pandas as pd

class ChatDatabase:
    def __init__(self, db_path="chatbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                question TEXT,
                answer TEXT,
                intent TEXT,
                language TEXT,
                user_email TEXT
            )
        ''')
        
        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE DEFAULT CURRENT_DATE,
                total_questions INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                top_intent TEXT,
                avg_session_length REAL DEFAULT 0
            )
        ''')
        
        # Email queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_email TEXT,
                subject TEXT,
                content TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                sent_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, session_id, question, answer, intent, language, user_email=None):
        """Save conversation to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (session_id, question, answer, intent, language, user_email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, question, answer, intent, language, user_email))
        
        conn.commit()
        conn.close()
    
    def get_analytics(self):
        """Get analytics data"""
        conn = sqlite3.connect(self.db_path)
        
        # Total conversations
        total_conversations = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM conversations", conn
        ).iloc[0]['count']
        
        # Questions by intent
        intent_data = pd.read_sql_query(
            "SELECT intent, COUNT(*) as count FROM conversations GROUP BY intent", conn
        )
        
        # Questions by language
        language_data = pd.read_sql_query(
            "SELECT language, COUNT(*) as count FROM conversations GROUP BY language", conn
        )
        
        # Daily activity
        daily_data = pd.read_sql_query(
            "SELECT DATE(timestamp) as date, COUNT(*) as count FROM conversations GROUP BY DATE(timestamp) ORDER BY date DESC LIMIT 30", conn
        )
        
        conn.close()
        
        return {
            'total_conversations': total_conversations,
            'intent_data': intent_data,
            'language_data': language_data,
            'daily_data': daily_data
        }