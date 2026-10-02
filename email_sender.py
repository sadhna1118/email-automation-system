import smtplib
import os
import time
import uuid
import mimetypes
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from urllib.parse import quote, unquote

from config import Config
from database import EmailDatabase
from validator import EmailValidator

class EmailSender:
    """Enterprise-grade SMTP sending engine with connection pooling, retry logic, and tracking"""
    
    def __init__(self, config=None, db=None):
        self.config = config or Config
        self.db = db or EmailDatabase()
        self._active_server = None
    
    def connect(self):
        """Establish and authenticate SMTP connection with TLS/SSL options"""
        if self.config.DRY_RUN:
            return None
        
        try:
            if self.config.SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(
                    self.config.SMTP_SERVER, 
                    self.config.SMTP_PORT, 
                    timeout=self.config.SMTP_TIMEOUT
                )
            else:
                server = smtplib.SMTP(
                    self.config.SMTP_SERVER, 
                    self.config.SMTP_PORT, 
                    timeout=self.config.SMTP_TIMEOUT
                )
                if self.config.SMTP_USE_TLS:
                    server.starttls()
            
            if self.config.EMAIL_ADDRESS and self.config.EMAIL_PASSWORD:
                server.login(self.config.EMAIL_ADDRESS, self.config.EMAIL_PASSWORD)
            
            return server
        except Exception as e:
            print(f"[SMTP Connect Error] {e}")
            raise
    
    def test_connection(self):
        """Test SMTP server connectivity and credentials"""
        if self.config.DRY_RUN:
            return {'success': True, 'mode': 'dry_run', 'message': 'Dry-Run simulation active. Connection test simulated successfully.'}
        
        try:
            server = self.connect()
            if server:
                server.quit()
            return {'success': True, 'mode': 'live', 'message': f'Successfully connected to SMTP server {self.config.SMTP_SERVER}:{self.config.SMTP_PORT}'}
        except Exception as e:
            return {'success': False, 'mode': 'live', 'message': f'SMTP Connection Failed: {str(e)}'}

    def _inject_tracking(self, html_body: str, tracking_id: str) -> str:
        """Inject open tracking pixel and click tracking redirect links"""
        if not self.config.TRACKING_ENABLED or not tracking_id:
            return html_body
        
        base_url = self.config.BASE_URL.rstrip('/')
        
        # 1. Inject Open Tracking Pixel
        pixel_tag = f'<img src="{base_url}/track/open/{tracking_id}" width="1" height="1" alt="" style="display:none !important; width:1px; height:1px; opacity:0; pointer-events:none;" />'
        if '</body>' in html_body:
            html_body = html_body.replace('</body>', f'{pixel_tag}</body>')
        else:
            html_body += pixel_tag
        
        # 2. Rewrite Links for Click Tracking (skip mailto, #, tel, and unsubscribe links)
        def link_replacer(match):
            href = match.group(1)
            if href.startswith(('mailto:', 'tel:', '#', 'javascript:')) or 'unsubscribe' in href.lower() or 'track/click' in href:
                return f'href="{href}"'
            tracking_url = f"{base_url}/track/click/{tracking_id}?url={quote(href, safe='')}"
            return f'href="{tracking_url}"'
        
        html_body = re.sub(r'href=["\']([^"\']+)["\']', link_replacer, html_body)
        return html_body

    def _attach_file(self, msg, file_path):
        """Cross-platform attachment helper with accurate MIME detection"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Attachment file not found: {file_path}")
        
        filename = os.path.basename(file_path)
        content_type, encoding = mimetypes.guess_type(file_path)
        
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        
        main_type, sub_type = content_type.split('/', 1)
        
        with open(file_path, 'rb') as f:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)

    def send_email(self, to_email: str, subject: str, body: str, html: bool = False, 
                   attachments: list = None, cc: list = None, bcc: list = None, 
                   reply_to: str = None, tracking_id: str = None, server_session=None) -> bool:
        """
        Send a single email with validation, retry logic, attachments, and tracking.
        """
        # Validate recipient email syntax
        val = EmailValidator.validate_email(to_email)
        if not val['valid']:
            err = f"Invalid recipient email syntax: {to_email} ({val['reason']})"
            self.db.log_sent_email(to_email, subject, status='failed', error_message=err, is_html=html, tracking_id=tracking_id)
            print(f"[Send Failed] {err}")
            return False
        
        to_email = val['email']
        tracking_id = tracking_id or str(uuid.uuid4())
        
        # Prepare message
        try:
            msg = MIMEMultipart('alternative')
            sender_header = f"{self.config.SENDER_NAME} <{self.config.EMAIL_ADDRESS}>" if self.config.SENDER_NAME else self.config.EMAIL_ADDRESS
            msg['From'] = sender_header or "noreply@example.com"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if reply_to:
                msg['Reply-To'] = reply_to
            if cc:
                msg['Cc'] = ', '.join(cc) if isinstance(cc, list) else cc
            if bcc:
                msg['Bcc'] = ', '.join(bcc) if isinstance(bcc, list) else bcc
            
            # Message Body & Tracking
            if html:
                processed_body = self._inject_tracking(body, tracking_id)
                # Plaintext fallback preview
                plain_snippet = re.sub(r'<[^>]+>', ' ', body).strip()[:300]
                msg.attach(MIMEText(plain_snippet, 'plain', 'utf-8'))
                msg.attach(MIMEText(processed_body, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Attachments
            has_attachment = bool(attachments)
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)
            
            # 1. DRY RUN / MOCK MODE
            if self.config.DRY_RUN:
                time.sleep(min(self.config.RATE_LIMIT_DELAY, 0.1))
                self.db.log_sent_email(
                    recipient=to_email,
                    subject=subject,
                    status='sent',
                    error_message=None,
                    is_html=html,
                    has_attachment=has_attachment,
                    tracking_id=tracking_id
                )
                print(f"[DRY-RUN SENT] To: {to_email} | Subject: {subject} | Tracking: {tracking_id[:8]}...")
                return True
            
            # 2. LIVE SENDING WITH RETRIES
            recipients = [to_email]
            if cc:
                recipients.extend(cc if isinstance(cc, list) else [c.strip() for c in cc.split(',')])
            if bcc:
                recipients.extend(bcc if isinstance(bcc, list) else [b.strip() for b in bcc.split(',')])
            
            server = server_session
            should_close = False
            if server is None:
                server = self.connect()
                should_close = True
            
            # Retry loop
            last_error = None
            for attempt in range(1, self.config.MAX_RETRIES + 1):
                try:
                    server.send_message(msg, from_addr=self.config.EMAIL_ADDRESS, to_addrs=recipients)
                    self.db.log_sent_email(
                        recipient=to_email,
                        subject=subject,
                        status='sent',
                        error_message=None,
                        is_html=html,
                        has_attachment=has_attachment,
                        tracking_id=tracking_id
                    )
                    print(f"[SENT SUCCESS] To: {to_email} | Subject: {subject}")
                    if should_close:
                        server.quit()
                    return True
                except Exception as e:
                    last_error = str(e)
                    print(f"[SMTP Attempt {attempt}/{self.config.MAX_RETRIES} Failed] {last_error}")
                    if attempt < self.config.MAX_RETRIES:
                        time.sleep(1.5 * attempt)
            
            if should_close and server:
                try:
                    server.quit()
                except:
                    pass
            
            self.db.log_sent_email(
                recipient=to_email,
                subject=subject,
                status='failed',
                error_message=last_error,
                is_html=html,
                has_attachment=has_attachment,
                tracking_id=tracking_id
            )
            return False
            
        except Exception as ex:
            err_msg = str(ex)
            self.db.log_sent_email(
                recipient=to_email,
                subject=subject,
                status='failed',
                error_message=err_msg,
                is_html=html,
                has_attachment=bool(attachments),
                tracking_id=tracking_id
            )
            print(f"[Send Error] Failed to send email to {to_email}: {err_msg}")
            return False

    def send_bulk_emails(self, csv_file: str, subject_template: str, body_template: str, 
                         html: bool = False, attachments: list = None, 
                         progress_callback=None) -> tuple:
        """
        Send bulk emails from CSV with template variable substitution, connection pooling, and throttling.
        """
        from template_engine import TemplateEngine
        template_engine = TemplateEngine()
        
        parse_result = EmailValidator.parse_csv(csv_file)
        if 'error' in parse_result:
            print(f"[Bulk CSV Error] {parse_result['error']}")
            return 0, 0
        
        valid_rows = parse_result['valid_rows']
        total = len(valid_rows)
        print(f"[Bulk Sending] Starting send to {total} recipients (Batch Size: {self.config.BATCH_SIZE}, Delay: {self.config.RATE_LIMIT_DELAY}s)")
        
        success_count = 0
        failed_count = 0
        
        # Connect once for the batch session if not in dry run
        server_session = None
        if not self.config.DRY_RUN:
            try:
                server_session = self.connect()
            except Exception as e:
                print(f"[Bulk SMTP Connect Error] {e}")
        
        try:
            for i, row in enumerate(valid_rows, start=1):
                to_email = row['email']
                tracking_id = str(uuid.uuid4())
                
                # Context variables
                context = dict(row)
                context['unsubscribe_url'] = f"{self.config.BASE_URL.rstrip('/')}/unsubscribe?email={quote(to_email)}"
                
                # Render personalized subject and body
                personalized_subject = template_engine.render_string(subject_template, context)
                personalized_body = template_engine.render_string(body_template, context)
                
                # Send email
                ok = self.send_email(
                    to_email=to_email,
                    subject=personalized_subject,
                    body=personalized_body,
                    html=html,
                    attachments=attachments,
                    tracking_id=tracking_id,
                    server_session=server_session
                )
                
                if ok:
                    success_count += 1
                else:
                    failed_count += 1
                
                if progress_callback:
                    progress_callback(i, total, success_count, failed_count)
                
                # Rate Limiting Throttling
                if i < total:
                    time.sleep(self.config.RATE_LIMIT_DELAY)
                    
                    # Batch pause
                    if self.config.BATCH_SIZE > 0 and i % self.config.BATCH_SIZE == 0:
                        print(f"[Batch Pause] Completed batch of {self.config.BATCH_SIZE}. Pausing for {self.config.BATCH_DELAY}s...")
                        time.sleep(self.config.BATCH_DELAY)
                        
        finally:
            if server_session:
                try:
                    server_session.quit()
                except:
                    pass
        
        print(f"\n[Bulk Send Summary] Total: {total} | Sent: {success_count} | Failed: {failed_count}")
        return success_count, failed_count

    def send_notification(self, subject: str, body: str, html: bool = False) -> bool:
        """Send notification email to configured notification address"""
        notification_email = self.config.NOTIFICATION_EMAIL
        if not notification_email:
            print("[Notification Warning] No NOTIFICATION_EMAIL configured.")
            return False
        return self.send_email(notification_email, subject, body, html=html)