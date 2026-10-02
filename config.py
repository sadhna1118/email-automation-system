import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """Configuration class for email automation system with enterprise defaults"""
    
    # SMTP Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USE_SSL = os.getenv('SMTP_USE_SSL', 'false').lower() in ('true', '1', 'yes')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() in ('true', '1', 'yes')
    SMTP_TIMEOUT = int(os.getenv('SMTP_TIMEOUT', 30))
    
    # IMAP Configuration
    IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    IMAP_PORT = int(os.getenv('IMAP_PORT', 993))
    IMAP_USE_SSL = os.getenv('IMAP_USE_SSL', 'true').lower() in ('true', '1', 'yes')
    IMAP_TIMEOUT = int(os.getenv('IMAP_TIMEOUT', 30))
    
    # Email Credentials
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    SENDER_NAME = os.getenv('SENDER_NAME', 'Email Automation System')
    
    # Notification & Monitoring Settings
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', '')
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))  # seconds
    
    # Rate Limiting & Throttling
    RATE_LIMIT_DELAY = float(os.getenv('RATE_LIMIT_DELAY', 1.0))  # delay between emails in seconds
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 50))  # emails per batch
    BATCH_DELAY = int(os.getenv('BATCH_DELAY', 60))  # pause between batches in seconds
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    # Simulation & Safety Mode (Dry Run)
    # When DRY_RUN is True, emails are simulated and logged without contacting real SMTP/IMAP
    DRY_RUN = os.getenv('DRY_RUN', 'true').lower() in ('true', '1', 'yes')
    
    # Tracking & Analytics
    TRACKING_ENABLED = os.getenv('TRACKING_ENABLED', 'true').lower() in ('true', '1', 'yes')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')
    
    # Webhook Settings
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    
    # Web Dashboard Server
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', 8000))
    
    # Database
    DB_PATH = os.getenv('DB_PATH', 'emails.db')
    
    @classmethod
    def validate(cls, strict=False):
        """
        Validate required configuration.
        If strict is True or DRY_RUN is False, requires valid EMAIL_ADDRESS and EMAIL_PASSWORD.
        """
        if (strict or not cls.DRY_RUN) and (not cls.EMAIL_ADDRESS or not cls.EMAIL_PASSWORD):
            raise ValueError(
                "EMAIL_ADDRESS and EMAIL_PASSWORD must be configured in your .env file. "
                "Alternatively, set DRY_RUN=true to run in simulation/test mode."
            )
        return True
    
    @classmethod
    def to_dict(cls):
        """Return safe dictionary representation of config (without password)"""
        return {
            'smtp_server': cls.SMTP_SERVER,
            'smtp_port': cls.SMTP_PORT,
            'smtp_use_ssl': cls.SMTP_USE_SSL,
            'smtp_use_tls': cls.SMTP_USE_TLS,
            'imap_server': cls.IMAP_SERVER,
            'imap_port': cls.IMAP_PORT,
            'imap_use_ssl': cls.IMAP_USE_SSL,
            'email_address': cls.EMAIL_ADDRESS,
            'sender_name': cls.SENDER_NAME,
            'notification_email': cls.NOTIFICATION_EMAIL,
            'check_interval': cls.CHECK_INTERVAL,
            'rate_limit_delay': cls.RATE_LIMIT_DELAY,
            'batch_size': cls.BATCH_SIZE,
            'batch_delay': cls.BATCH_DELAY,
            'dry_run': cls.DRY_RUN,
            'tracking_enabled': cls.TRACKING_ENABLED,
            'base_url': cls.BASE_URL,
            'webhook_url': cls.WEBHOOK_URL,
            'web_host': cls.WEB_HOST,
            'web_port': cls.WEB_PORT,
            'db_path': cls.DB_PATH,
            'has_password': bool(cls.EMAIL_PASSWORD)
        }