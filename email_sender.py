import smtplib
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config import Config
from database import EmailDatabase

class EmailSender:
    """Handles sending emails via SMTP"""
    
    def __init__(self):
        self.config = Config
        self.db = EmailDatabase()
    
    def connect(self):
        """Establish SMTP connection"""
        try:
            server = smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            server.starttls()
            server.login(self.config.EMAIL_ADDRESS, self.config.EMAIL_PASSWORD)
            return server
        except Exception as e:
            print(f"Failed to connect to SMTP server: {e}")
            raise
    
    def send_email(self, to_email, subject, body, html=False, attachments=None):
        """Send a single email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_ADDRESS
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            mime_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, mime_type))
            
            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)
            
            # Send email
            server = self.connect()
            server.send_message(msg)
            server.quit()
            
            # Log success
            self.db.log_sent_email(to_email, subject, status='sent')
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.db.log_sent_email(to_email, subject, status='failed', error_message=error_msg)
            print(f"Failed to send email to {to_email}: {error_msg}")
            return False
    
    def _attach_file(self, msg, file_path):
        """Attach a file to the email"""
        try:
            with open(file_path, 'rb') as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={file_path.split("/")[-1]}')
                msg.attach(part)
        except Exception as e:
            print(f"Failed to attach file {file_path}: {e}")
    
    def send_bulk_emails(self, csv_file, subject_template, body_template, html=False):
        """Send bulk emails from CSV file with personalization"""
        success_count = 0
        failed_count = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Personalize subject and body
                    subject = subject_template.format(**row)
                    body = body_template.format(**row)
                    
                    # Send email
                    if self.send_email(row['email'], subject, body, html=html):
                        success_count += 1
                    else:
                        failed_count += 1
            
            print(f"\nBulk email summary:")
            print(f"Successfully sent: {success_count}")
            print(f"Failed: {failed_count}")
            
            return success_count, failed_count
            
        except Exception as e:
            print(f"Error processing CSV file: {e}")
            return success_count, failed_count
    
    def send_notification(self, subject, body):
        """Send notification email to configured recipient"""
        notification_email = self.config.NOTIFICATION_EMAIL
        if notification_email:
            return self.send_email(notification_email, subject, body)
        else:
            print("No notification email configured")
            return False