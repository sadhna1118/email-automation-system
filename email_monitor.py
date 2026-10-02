import imaplib
import email
from email.header import decode_header
import time
import threading
import json
import re
import urllib.request
from datetime import datetime

from config import Config
from database import EmailDatabase
from email_sender import EmailSender

class EmailMonitor:
    """Smart IMAP Inbox Monitor with multi-action rules engine and background daemon"""
    
    def __init__(self, config=None, db=None, sender=None):
        self.config = config or Config
        self.db = db or EmailDatabase()
        self.sender = sender or EmailSender(config=self.config, db=self.db)
        
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
    
    def connect(self):
        """Establish IMAP connection with TLS"""
        if self.config.DRY_RUN:
            return None
        
        try:
            if self.config.IMAP_USE_SSL:
                mail = imaplib.IMAP4_SSL(self.config.IMAP_SERVER, self.config.IMAP_PORT, timeout=self.config.IMAP_TIMEOUT)
            else:
                mail = imaplib.IMAP4(self.config.IMAP_SERVER, self.config.IMAP_PORT, timeout=self.config.IMAP_TIMEOUT)
            
            if self.config.EMAIL_ADDRESS and self.config.EMAIL_PASSWORD:
                mail.login(self.config.EMAIL_ADDRESS, self.config.EMAIL_PASSWORD)
            return mail
        except Exception as e:
            print(f"[IMAP Connect Error] {e}")
            raise

    def test_connection(self):
        """Test IMAP server connectivity"""
        if self.config.DRY_RUN:
            return {'success': True, 'mode': 'dry_run', 'message': 'Dry-Run simulation active. IMAP connection simulated successfully.'}
        try:
            mail = self.connect()
            if mail:
                mail.logout()
            return {'success': True, 'mode': 'live', 'message': f'Successfully connected to IMAP server {self.config.IMAP_SERVER}:{self.config.IMAP_PORT}'}
        except Exception as e:
            return {'success': False, 'mode': 'live', 'message': f'IMAP Connection Failed: {str(e)}'}

    def decode_header_str(self, header_value):
        """Safely decode RFC 2047 encoded email headers"""
        if not header_value:
            return ""
        try:
            decoded_parts = decode_header(header_value)
            result = []
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    result.append(part.decode(encoding or 'utf-8', errors='ignore'))
                else:
                    result.append(str(part))
            return "".join(result)
        except Exception:
            return str(header_value)

    def parse_email_message(self, msg_bytes, uid_str=None):
        """Extract structured data (headers, plain body, HTML body, attachments) from RFC 822 email"""
        msg = email.message_from_bytes(msg_bytes)
        
        subject = self.decode_header_str(msg.get('Subject', '(No Subject)'))
        sender = self.decode_header_str(msg.get('From', 'unknown@example.com'))
        recipient = self.decode_header_str(msg.get('To', ''))
        date_str = self.decode_header_str(msg.get('Date', ''))
        message_id = self.decode_header_str(msg.get('Message-ID', ''))
        
        body_plain = ""
        body_html = ""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # Check for attachments
                if 'attachment' in content_disposition:
                    filename = self.decode_header_str(part.get_filename())
                    payload = part.get_payload(decode=True)
                    size = len(payload) if payload else 0
                    attachments.append({
                        'filename': filename or 'unnamed_attachment',
                        'size_bytes': size,
                        'content_type': content_type
                    })
                    continue
                
                # Check for plain text
                if content_type == 'text/plain' and not body_plain:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_plain = payload.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                    except:
                        pass
                
                # Check for HTML
                elif content_type == 'text/html' and not body_html:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_html = payload.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                    except:
                        pass
        else:
            content_type = msg.get_content_type()
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    text = payload.decode(msg.get_content_charset() or 'utf-8', errors='ignore')
                    if content_type == 'text/html':
                        body_html = text
                    else:
                        body_plain = text
            except:
                pass
        
        # Snippet preview
        preview_src = body_plain if body_plain else re.sub(r'<[^>]+>', ' ', body_html)
        preview = " ".join(preview_src.split())[:350]
        
        return {
            'subject': subject,
            'sender': sender,
            'recipient': recipient,
            'date': date_str,
            'message_id': message_id or uid_str or f"msg-{int(time.time()*1000)}",
            'body_text': body_plain,
            'body_html': body_html,
            'body_preview': preview,
            'has_attachments': len(attachments) > 0,
            'attachments': attachments
        }

    def evaluate_rules(self, email_data: dict) -> tuple:
        """
        Evaluate all active notification and automation rules against email data.
        Returns: (matched_rules_list, actions_to_execute)
        """
        active_rules = self.db.get_active_rules()
        matched_rules = []
        actions = []
        
        sender = email_data.get('sender', '').lower()
        subject = email_data.get('subject', '').lower()
        body = (email_data.get('body_text', '') + ' ' + email_data.get('body_preview', '')).lower()
        
        for rule in active_rules:
            logic = rule.get('condition_logic', 'AND').upper()
            conditions = []
            
            # 1. Sender Filter
            if rule.get('sender_filter'):
                sf = rule['sender_filter'].strip().lower()
                conditions.append(sf in sender)
                
            # 2. Subject Filter
            if rule.get('subject_filter'):
                sbf = rule['subject_filter'].strip().lower()
                conditions.append(sbf in subject)
                
            # 3. Keyword Filter
            if rule.get('keyword_filter'):
                kw = rule['keyword_filter'].strip().lower()
                conditions.append(kw in body)
            
            # If no filters set, it does not match
            if not conditions:
                continue
            
            # Check logic
            is_match = all(conditions) if logic == 'AND' else any(conditions)
            
            if is_match:
                rule_name = rule['rule_name']
                matched_rules.append(rule_name)
                self.db.increment_rule_trigger(rule['id'])
                
                # Parse actions
                action_type = rule.get('action_type', 'alert')
                action_cfg = {}
                if rule.get('action_config'):
                    try:
                        action_cfg = json.loads(rule['action_config'])
                    except:
                        pass
                
                actions.append({
                    'rule_id': rule['id'],
                    'rule_name': rule_name,
                    'action_type': action_type,
                    'action_config': action_cfg
                })
        
        return matched_rules, actions

    def execute_actions(self, email_data: dict, actions: list, email_db_id: int):
        """Execute automated workflow actions (alerts, auto-replies, webhooks)"""
        executed_logs = []
        
        for act in actions:
            act_type = act.get('action_type', 'alert')
            rule_name = act.get('rule_name')
            cfg = act.get('action_config', {})
            
            # Action 1: Email Alert
            if act_type == 'alert':
                alert_sub = f"🔔 Email Rule Triggered: [{rule_name}]"
                alert_body = f"""Rule Match Alert: {rule_name}
--------------------------------------------------
From: {email_data['sender']}
Subject: {email_data['subject']}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Message Preview:
{email_data['body_preview']}
--------------------------------------------------
Check your Email Automation Dashboard for full details."""
                target_notify = cfg.get('notification_email') or self.config.NOTIFICATION_EMAIL
                if target_notify:
                    self.sender.send_email(to_email=target_notify, subject=alert_sub, body=alert_body)
                else:
                    self.sender.send_notification(alert_sub, alert_body)
                if email_db_id:
                    self.db.mark_notification_sent(email_db_id)
                executed_logs.append(f"Sent email alert for rule '{rule_name}'")
                
            # Action 2: Auto-Reply
            elif act_type == 'auto_reply':
                reply_body = cfg.get('reply_body', 'Thank you for your message. We have received it and will follow up shortly.')
                reply_subject = f"Re: {email_data['subject']}"
                # Extract clean email from sender header "Name <email@domain.com>"
                raw_from = email_data['sender']
                match = re.search(r'<([^>]+)>', raw_from)
                target_email = match.group(1) if match else raw_from.strip()
                
                self.sender.send_email(
                    to_email=target_email,
                    subject=reply_subject,
                    body=reply_body,
                    html=cfg.get('is_html', False)
                )
                executed_logs.append(f"Auto-replied to '{target_email}' for rule '{rule_name}'")
                
            # Action 3: Webhook POST
            elif act_type == 'webhook':
                webhook_url = cfg.get('webhook_url') or self.config.WEBHOOK_URL
                if webhook_url:
                    try:
                        payload = json.dumps({
                            'event': 'email_rule_matched',
                            'rule_name': rule_name,
                            'sender': email_data['sender'],
                            'subject': email_data['subject'],
                            'preview': email_data['body_preview'],
                            'timestamp': datetime.now().isoformat()
                        }).encode('utf-8')
                        req = urllib.request.Request(
                            webhook_url, 
                            data=payload, 
                            headers={'Content-Type': 'application/json', 'User-Agent': 'EmailAutomation/2.0'}
                        )
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            executed_logs.append(f"Triggered webhook '{webhook_url}' (HTTP {resp.status})")
                    except Exception as e:
                        executed_logs.append(f"Webhook trigger failed: {e}")
        
        return executed_logs

    def monitor_inbox(self, folder='INBOX') -> int:
        """Check inbox for new unread messages, process rules, and execute actions"""
        # 1. DRY-RUN SIMULATION
        if self.config.DRY_RUN:
            print("[IMAP Monitor] Dry-Run check active (No live IMAP calls).")
            return 0
        
        try:
            mail = self.connect()
            mail.select(folder)
            
            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK' or not messages[0]:
                mail.close()
                mail.logout()
                return 0
            
            email_ids = messages[0].split()
            new_emails_count = 0
            
            for eid in email_ids:
                eid_str = eid.decode('utf-8')
                
                # Check if already processed in database
                if self.db.is_message_processed(eid_str):
                    continue
                
                status, msg_data = mail.fetch(eid, '(RFC822)')
                if status != 'OK':
                    continue
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        email_data = self.parse_email_message(response_part[1], uid_str=eid_str)
                        
                        # Evaluate rules
                        matched_rules, actions = self.evaluate_rules(email_data)
                        
                        # Log to database
                        email_db_id = self.db.log_monitored_email(
                            sender=email_data['sender'],
                            subject=email_data['subject'],
                            body_preview=email_data['body_preview'],
                            body_html=email_data['body_html'],
                            body_text=email_data['body_text'],
                            has_attachments=email_data['has_attachments'],
                            attachments_info=email_data['attachments'],
                            rule_matches=matched_rules,
                            actions_taken=[],
                            message_uid=eid_str
                        )
                        
                        # Execute actions
                        if actions:
                            executed_logs = self.execute_actions(email_data, actions, email_db_id)
                            # Update actions in db
                            conn = self.db.get_connection()
                            conn.execute('UPDATE monitored_emails SET actions_taken = ? WHERE id = ?', 
                                         (json.dumps(executed_logs), email_db_id))
                            conn.commit()
                            conn.close()
                        
                        new_emails_count += 1
                        print(f"[IMAP Received] From: {email_data['sender']} | Subject: {email_data['subject']} | Matched: {matched_rules}")
            
            mail.close()
            mail.logout()
            return new_emails_count
            
        except Exception as e:
            print(f"[IMAP Monitor Error] {e}")
            return 0

    def simulate_incoming_email(self, sender: str, subject: str, body: str, attachments: list = None):
        """Simulate an incoming email for testing rules and workflows in UI or dry-run mode"""
        uid = f"sim-{int(time.time()*1000)}"
        email_data = {
            'sender': sender,
            'subject': subject,
            'recipient': self.config.EMAIL_ADDRESS or 'inbox@example.com',
            'date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000'),
            'message_id': uid,
            'body_text': body,
            'body_html': f"<p>{body}</p>",
            'body_preview': body[:300],
            'has_attachments': bool(attachments),
            'attachments': attachments or []
        }
        
        matched_rules, actions = self.evaluate_rules(email_data)
        
        email_db_id = self.db.log_monitored_email(
            sender=sender,
            subject=subject,
            body_preview=email_data['body_preview'],
            body_html=email_data['body_html'],
            body_text=email_data['body_text'],
            has_attachments=email_data['has_attachments'],
            attachments_info=email_data['attachments'],
            rule_matches=matched_rules,
            actions_taken=[],
            message_uid=uid
        )
        
        executed_logs = []
        if actions:
            executed_logs = self.execute_actions(email_data, actions, email_db_id)
            conn = self.db.get_connection()
            conn.execute('UPDATE monitored_emails SET actions_taken = ? WHERE id = ?', 
                         (json.dumps(executed_logs), email_db_id))
            conn.commit()
            conn.close()
        
        self.db.log_activity('simulated_email', f"Processed incoming test email from {sender}: {subject}", {
            'matched_rules': matched_rules,
            'actions_taken': executed_logs
        })
        
        return {
            'id': email_db_id,
            'matched_rules': matched_rules,
            'actions_taken': executed_logs
        }

    def start_background_daemon(self, interval=None):
        """Start non-blocking background monitoring daemon thread"""
        if self._running:
            print("[IMAP Daemon] Monitor is already running.")
            return
        
        interval = interval or self.config.CHECK_INTERVAL
        self._running = True
        self._stop_event.clear()
        
        def loop():
            print(f"[IMAP Daemon] Background inbox monitor started (interval: {interval}s)")
            while not self._stop_event.is_set():
                try:
                    self.monitor_inbox()
                except Exception as ex:
                    print(f"[IMAP Daemon Loop Error] {ex}")
                self._stop_event.wait(timeout=interval)
            print("[IMAP Daemon] Background inbox monitor stopped.")
        
        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop_background_daemon(self):
        """Stop background monitoring daemon"""
        if self._running:
            self._running = False
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2)
            print("[IMAP Daemon] Stop signal sent.")

    def is_running(self):
        """Return True if background monitor daemon is active"""
        return self._running