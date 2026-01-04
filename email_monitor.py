import imaplib
import email
from email.header import decode_header
import time
from config import Config
from database import EmailDatabase
from email_sender import EmailSender

class EmailMonitor:
    """Monitors incoming emails and triggers notifications"""
    
    def __init__(self):
        self.config = Config
        self.db = EmailDatabase()
        self.sender = EmailSender()
        self.processed_emails = set()
    
    def connect(self):
        """Establish IMAP connection"""
        try:
            mail = imaplib.IMAP4_SSL(self.config.IMAP_SERVER, self.config.IMAP_PORT)
            mail.login(self.config.EMAIL_ADDRESS, self.config.EMAIL_PASSWORD)
            return mail
        except Exception as e:
            print(f"Failed to connect to IMAP server: {e}")
            raise
    
    def decode_email_subject(self, subject):
        """Decode email subject"""
        if subject:
            decoded_parts = decode_header(subject)
            decoded_subject = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_subject += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_subject += part
            return decoded_subject
        return ""
    
    def get_email_body(self, msg):
        """Extract email body"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                pass
        return body[:500]  # Return preview
    
    def check_notification_rules(self, sender, subject, body):
        """Check if email matches any notification rules"""
        rules = self.db.get_active_rules()
        matched_rules = []
        
        for rule in rules:
            rule_id, rule_name, sender_filter, subject_filter, keyword_filter = rule
            
            match = True
            
            # Check sender filter
            if sender_filter and sender_filter.lower() not in sender.lower():
                match = False
            
            # Check subject filter
            if subject_filter and subject_filter.lower() not in subject.lower():
                match = False
            
            # Check keyword filter
            if keyword_filter and keyword_filter.lower() not in body.lower():
                match = False
            
            if match:
                matched_rules.append(rule_name)
        
        return matched_rules
    
    def monitor_inbox(self, folder='INBOX', mark_as_read=False):
        """Monitor inbox for new emails"""
        try:
            mail = self.connect()
            mail.select(folder)
            
            # Search for unseen emails
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            new_emails = 0
            
            for email_id in email_ids:
                if email_id in self.processed_emails:
                    continue
                
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Extract email details
                        subject = self.decode_email_subject(msg['subject'])
                        sender = msg['from']
                        body = self.get_email_body(msg)
                        
                        # Log email
                        email_db_id = self.db.log_monitored_email(sender, subject, body)
                        
                        # Check notification rules
                        matched_rules = self.check_notification_rules(sender, subject, body)
                        
                        if matched_rules:
                            # Send notification
                            notification_subject = f"Email Alert: {', '.join(matched_rules)}"
                            notification_body = f"""
New email matching notification rules: {', '.join(matched_rules)}

From: {sender}
Subject: {subject}

Preview:
{body[:200]}...
                            """
                            
                            self.sender.send_notification(notification_subject, notification_body)
                            self.db.mark_notification_sent(email_db_id)
                        
                        self.processed_emails.add(email_id)
                        new_emails += 1
                        
                        print(f"Processed email from {sender}: {subject}")
            
            mail.close()
            mail.logout()
            
            return new_emails
            
        except Exception as e:
            print(f"Error monitoring inbox: {e}")
            return 0
    
    def start_monitoring(self, interval=None):
        """Start continuous email monitoring"""
        interval = interval or self.config.CHECK_INTERVAL
        
        print(f"Starting email monitoring (checking every {interval} seconds)...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                new_emails = self.monitor_inbox()
                if new_emails > 0:
                    print(f"Found and processed {new_emails} new email(s)")
                else:
                    print("No new emails")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")