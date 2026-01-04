import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for email automation system"""
    
    # SMTP Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    
    # IMAP Configuration
    IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    IMAP_PORT = int(os.getenv('IMAP_PORT', 993))
    
    # Email Credentials
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    
    # Notification Settings
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))
    
    # Database
    DB_PATH = os.getenv('DB_PATH', 'emails.db')
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.EMAIL_ADDRESS or not Config.EMAIL_PASSWORD:
            raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env file")
        return True