import pytest
import os
from database import EmailDatabase
from config import Config

class TestEmailDatabase:
    """Test cases for EmailDatabase"""
    
    def setup_method(self):
        """Set up test database"""
        self.test_db_path = 'test_emails.db'
        self.db = EmailDatabase(self.test_db_path)
    
    def teardown_method(self):
        """Clean up test database"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_database_initialization(self):
        """Test database tables are created"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'sent_emails' in tables
        assert 'monitored_emails' in tables
        assert 'notification_rules' in tables
        
        conn.close()
    
    def test_log_sent_email(self):
        """Test logging sent email"""
        email_id = self.db.log_sent_email(
            recipient='test@example.com',
            subject='Test Email',
            status='sent'
        )
        
        assert email_id is not None
        assert email_id > 0
    
    def test_add_notification_rule(self):
        """Test adding notification rule"""
        rule_id = self.db.add_notification_rule(
            rule_name='Test Rule',
            sender_filter='important@example.com',
            subject_filter='urgent'
        )
        
        assert rule_id is not None
        assert rule_id > 0
    
    def test_get_active_rules(self):
        """Test retrieving active rules"""
        self.db.add_notification_rule(
            rule_name='Rule 1',
            sender_filter='sender1@example.com'
        )
        self.db.add_notification_rule(
            rule_name='Rule 2',
            subject_filter='important'
        )
        
        rules = self.db.get_active_rules()
        assert len(rules) == 2
    
    def test_email_stats(self):
        """Test email statistics"""
        # Add some test data
        self.db.log_sent_email('test1@example.com', 'Subject 1', status='sent')
        self.db.log_sent_email('test2@example.com', 'Subject 2', status='sent')
        self.db.log_sent_email('test3@example.com', 'Subject 3', status='failed')
        
        stats = self.db.get_email_stats()
        
        assert stats['sent'] == 2
        assert stats['failed'] == 1
        assert stats['monitored'] == 0

class TestConfig:
    """Test cases for Config"""
    
    def test_config_has_required_attributes(self):
        """Test Config class has all required attributes"""
        assert hasattr(Config, 'SMTP_SERVER')
        assert hasattr(Config, 'SMTP_PORT')
        assert hasattr(Config, 'IMAP_SERVER')
        assert hasattr(Config, 'IMAP_PORT')
        assert hasattr(Config, 'EMAIL_ADDRESS')
        assert hasattr(Config, 'EMAIL_PASSWORD')

if __name__ == '__main__':
    pytest.main([__file__, '-v'])