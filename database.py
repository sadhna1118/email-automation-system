import sqlite3
from datetime import datetime
from config import Config

class EmailDatabase:
    """Manages SQLite database for email logs and tracking"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DB_PATH
        self.init_database()
    
    def get_connection(self):
        """Create and return database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Sent emails table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'sent',
                error_message TEXT
            )
        ''')
        
        # Monitored emails table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                subject TEXT NOT NULL,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                body_preview TEXT,
                notification_sent BOOLEAN DEFAULT 0
            )
        ''')
        
        # Notification rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                sender_filter TEXT,
                subject_filter TEXT,
                keyword_filter TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_sent_email(self, recipient, subject, status='sent', error_message=None):
        """Log a sent email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sent_emails (recipient, subject, status, error_message)
            VALUES (?, ?, ?, ?)
        ''', (recipient, subject, status, error_message))
        
        conn.commit()
        email_id = cursor.lastrowid
        conn.close()
        return email_id
    
    def log_monitored_email(self, sender, subject, body_preview=None):
        """Log a monitored email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monitored_emails (sender, subject, body_preview)
            VALUES (?, ?, ?)
        ''', (sender, subject, body_preview))
        
        conn.commit()
        email_id = cursor.lastrowid
        conn.close()
        return email_id
    
    def mark_notification_sent(self, email_id):
        """Mark that notification was sent for an email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE monitored_emails
            SET notification_sent = 1
            WHERE id = ?
        ''', (email_id,))
        
        conn.commit()
        conn.close()
    
    def add_notification_rule(self, rule_name, sender_filter=None, subject_filter=None, keyword_filter=None):
        """Add a notification rule"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notification_rules (rule_name, sender_filter, subject_filter, keyword_filter)
            VALUES (?, ?, ?, ?)
        ''', (rule_name, sender_filter, subject_filter, keyword_filter))
        
        conn.commit()
        rule_id = cursor.lastrowid
        conn.close()
        return rule_id
    
    def get_active_rules(self):
        """Get all active notification rules"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, rule_name, sender_filter, subject_filter, keyword_filter
            FROM notification_rules
            WHERE enabled = 1
        ''')
        
        rules = cursor.fetchall()
        conn.close()
        return rules
    
    def get_email_stats(self):
        """Get statistics about sent and monitored emails"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM sent_emails WHERE status = "sent"')
        sent_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sent_emails WHERE status = "failed"')
        failed_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM monitored_emails')
        monitored_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'sent': sent_count,
            'failed': failed_count,
            'monitored': monitored_count
        }