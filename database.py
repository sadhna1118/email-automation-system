import sqlite3
import json
from datetime import datetime, timedelta
import os
from config import Config

class EmailDatabase:
    """Enterprise SQLite Database Manager for Email Automation Platform"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DB_PATH
        self.init_database()
    
    def get_connection(self):
        """Create and return optimized database connection with dict-like row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable Write-Ahead Logging for high concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def init_database(self):
        """Initialize all database tables, indexes, and initial configurations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Sent Emails Log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'sent',
                error_message TEXT,
                is_html BOOLEAN DEFAULT 0,
                has_attachment BOOLEAN DEFAULT 0,
                tracking_id TEXT,
                opened BOOLEAN DEFAULT 0,
                opened_at TIMESTAMP,
                clicked BOOLEAN DEFAULT 0,
                clicked_at TIMESTAMP
            )
        ''')
        
        # 2. Monitored Emails Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT,
                subject TEXT NOT NULL,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                body_preview TEXT,
                body_html TEXT,
                body_text TEXT,
                has_attachments BOOLEAN DEFAULT 0,
                attachments_info TEXT,
                rule_matches TEXT,
                actions_taken TEXT,
                notification_sent BOOLEAN DEFAULT 0,
                message_uid TEXT UNIQUE
            )
        ''')
        
        # 3. Notification Rules Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                sender_filter TEXT,
                subject_filter TEXT,
                keyword_filter TEXT,
                condition_logic TEXT DEFAULT 'AND',
                action_type TEXT DEFAULT 'alert',
                action_config TEXT,
                enabled BOOLEAN DEFAULT 1,
                trigger_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 4. Contacts Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT,
                company TEXT,
                phone TEXT,
                tags TEXT,
                status TEXT DEFAULT 'active',
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 5. Contact Lists (Groups/Segments)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 6. Contact List Members (Many-to-Many)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_list_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                contact_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (list_id) REFERENCES contact_lists(id) ON DELETE CASCADE,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                UNIQUE (list_id, contact_id)
            )
        ''')
        
        # 7. Email Templates Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT DEFAULT 'general',
                subject_template TEXT NOT NULL,
                body_html TEXT NOT NULL,
                body_text TEXT,
                variables_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 8. Campaigns Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                template_id INTEGER,
                contact_list_id INTEGER,
                status TEXT DEFAULT 'draft',
                total_recipients INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                open_count INTEGER DEFAULT 0,
                click_count INTEGER DEFAULT 0,
                batch_size INTEGER DEFAULT 50,
                delay_seconds REAL DEFAULT 1.0,
                scheduled_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE SET NULL,
                FOREIGN KEY (contact_list_id) REFERENCES contact_lists(id) ON DELETE SET NULL
            )
        ''')
        
        # 9. Campaign Logs (Per Recipient)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT,
                status TEXT DEFAULT 'queued',
                error_message TEXT,
                tracking_id TEXT,
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            )
        ''')
        
        # 10. Scheduled Tasks Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                schedule_expr TEXT NOT NULL,
                params_json TEXT,
                enabled BOOLEAN DEFAULT 1,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 11. Activity & Audit Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                details_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 12. System Settings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Indexes for fast lookup
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sent_emails_recipient ON sent_emails(recipient)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sent_emails_sent_at ON sent_emails(sent_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_monitored_sender ON monitored_emails(sender)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_monitored_received ON monitored_emails(received_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaign_logs_campaign ON campaign_logs(campaign_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaign_logs_tracking ON campaign_logs(tracking_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sent_tracking ON sent_emails(tracking_id)')
        
        # Ensure migration columns
        try:
            cursor.execute('ALTER TABLE notification_rules ADD COLUMN notification_email TEXT')
        except Exception:
            pass

        conn.commit()
        conn.close()

    # ------------------ Logging & Emails ------------------ #

    def log_sent_email(self, recipient, subject, status='sent', error_message=None, 
                       is_html=False, has_attachment=False, tracking_id=None):
        """Log a sent email record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sent_emails (recipient, subject, status, error_message, is_html, has_attachment, tracking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (recipient, subject, status, error_message, 1 if is_html else 0, 1 if has_attachment else 0, tracking_id))
        conn.commit()
        email_id = cursor.lastrowid
        conn.close()
        return email_id

    def log_monitored_email(self, sender, subject, body_preview=None, body_html=None, body_text=None,
                            has_attachments=False, attachments_info=None, rule_matches=None, 
                            actions_taken=None, message_uid=None):
        """Log an incoming monitored email with full details and duplicate prevention"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO monitored_emails 
                (sender, subject, body_preview, body_html, body_text, has_attachments, attachments_info, 
                 rule_matches, actions_taken, message_uid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sender, subject, body_preview, body_html, body_text,
                1 if has_attachments else 0,
                json.dumps(attachments_info) if isinstance(attachments_info, (list, dict)) else attachments_info,
                json.dumps(rule_matches) if isinstance(rule_matches, (list, dict)) else rule_matches,
                json.dumps(actions_taken) if isinstance(actions_taken, (list, dict)) else actions_taken,
                message_uid
            ))
            conn.commit()
            email_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Duplicate UID, ignore
            email_id = None
        finally:
            conn.close()
        return email_id

    def is_message_processed(self, message_uid):
        """Check if message UID has already been processed"""
        if not message_uid:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM monitored_emails WHERE message_uid = ?', (message_uid,))
        res = cursor.fetchone()
        conn.close()
        return res is not None

    def mark_notification_sent(self, email_id):
        """Mark notification as sent for monitored email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE monitored_emails SET notification_sent = 1 WHERE id = ?', (email_id,))
        conn.commit()
        conn.close()

    def record_open_tracking(self, tracking_id):
        """Record email open tracking event"""
        if not tracking_id:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update sent_emails
        cursor.execute('''
            UPDATE sent_emails 
            SET opened = 1, opened_at = COALESCE(opened_at, ?) 
            WHERE tracking_id = ?
        ''', (now, tracking_id))
        
        # Update campaign_logs & campaign count
        cursor.execute('''
            UPDATE campaign_logs 
            SET opened_at = COALESCE(opened_at, ?) 
            WHERE tracking_id = ?
        ''', (now, tracking_id))
        
        # Get campaign_id if exists
        cursor.execute('SELECT campaign_id FROM campaign_logs WHERE tracking_id = ?', (tracking_id,))
        row = cursor.fetchone()
        if row:
            cid = row['campaign_id']
            cursor.execute('''
                UPDATE campaigns 
                SET open_count = (SELECT COUNT(DISTINCT id) FROM campaign_logs WHERE campaign_id = ? AND opened_at IS NOT NULL)
                WHERE id = ?
            ''', (cid, cid))
            
        conn.commit()
        conn.close()
        return True

    def record_click_tracking(self, tracking_id):
        """Record email click tracking event"""
        if not tracking_id:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            UPDATE sent_emails 
            SET clicked = 1, clicked_at = COALESCE(clicked_at, ?) 
            WHERE tracking_id = ?
        ''', (now, tracking_id))
        
        cursor.execute('''
            UPDATE campaign_logs 
            SET clicked_at = COALESCE(clicked_at, ?) 
            WHERE tracking_id = ?
        ''', (now, tracking_id))
        
        cursor.execute('SELECT campaign_id FROM campaign_logs WHERE tracking_id = ?', (tracking_id,))
        row = cursor.fetchone()
        if row:
            cid = row['campaign_id']
            cursor.execute('''
                UPDATE campaigns 
                SET click_count = (SELECT COUNT(DISTINCT id) FROM campaign_logs WHERE campaign_id = ? AND clicked_at IS NOT NULL)
                WHERE id = ?
            ''', (cid, cid))
            
        conn.commit()
        conn.close()
        return True

    # ------------------ Rules Management ------------------ #

    def add_notification_rule(self, rule_name, sender_filter=None, subject_filter=None, keyword_filter=None,
                              condition_logic='AND', action_type='alert', action_config=None, notification_email=None):
        """Add a smart notification rule"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cfg = {}
        if action_config:
            if isinstance(action_config, dict):
                cfg = dict(action_config)
            elif isinstance(action_config, str):
                try:
                    cfg = json.loads(action_config)
                except Exception:
                    cfg = {}
        if notification_email:
            cfg['notification_email'] = notification_email

        try:
            cursor.execute('''
                INSERT INTO notification_rules 
                (rule_name, sender_filter, subject_filter, keyword_filter, condition_logic, action_type, action_config, notification_email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (rule_name, sender_filter, subject_filter, keyword_filter, condition_logic, action_type, 
                  json.dumps(cfg), notification_email))
        except Exception:
            cursor.execute('''
                INSERT INTO notification_rules 
                (rule_name, sender_filter, subject_filter, keyword_filter, condition_logic, action_type, action_config)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (rule_name, sender_filter, subject_filter, keyword_filter, condition_logic, action_type, 
                  json.dumps(cfg)))
        conn.commit()
        rule_id = cursor.lastrowid
        conn.close()
        return rule_id

    def get_active_rules(self):
        """Get all active notification rules"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notification_rules WHERE enabled = 1 ORDER BY id DESC')
        rows = cursor.fetchall()
        rules = [dict(row) for row in rows]
        conn.close()
        return rules

    def get_all_rules(self):
        """Get all notification rules"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notification_rules ORDER BY id DESC')
        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rules

    def toggle_rule(self, rule_id, enabled=None):
        """Toggle or set rule status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if enabled is None:
            cursor.execute('UPDATE notification_rules SET enabled = CASE WHEN enabled = 1 THEN 0 ELSE 1 END WHERE id = ?', (rule_id,))
        else:
            cursor.execute('UPDATE notification_rules SET enabled = ? WHERE id = ?', (1 if enabled else 0, rule_id))
        conn.commit()
        conn.close()

    def increment_rule_trigger(self, rule_id):
        """Increment rule trigger count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE notification_rules SET trigger_count = trigger_count + 1 WHERE id = ?', (rule_id,))
        conn.commit()
        conn.close()

    def delete_rule(self, rule_id):
        """Delete a notification rule"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notification_rules WHERE id = ?', (rule_id,))
        conn.commit()
        conn.close()

    # ------------------ Contacts & Lists ------------------ #

    def add_contact(self, email, name=None, company=None, phone=None, tags=None, metadata=None):
        """Add or update a contact"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contacts (email, name, company, phone, tags, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name = COALESCE(excluded.name, contacts.name),
                company = COALESCE(excluded.company, contacts.company),
                phone = COALESCE(excluded.phone, contacts.phone),
                tags = COALESCE(excluded.tags, contacts.tags),
                metadata_json = COALESCE(excluded.metadata_json, contacts.metadata_json)
        ''', (
            email.strip().lower(), name, company, phone, 
            json.dumps(tags) if isinstance(tags, list) else tags,
            json.dumps(metadata) if isinstance(metadata, dict) else metadata
        ))
        conn.commit()
        contact_id = cursor.lastrowid
        conn.close()
        return contact_id

    def get_contacts(self, search=None, status='active', limit=100, offset=0):
        """List contacts with optional search filter"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM contacts WHERE 1=1"
        params = []
        if status and status != 'all':
            query += " AND status = ?"
            params.append(status)
        if search:
            query += " AND (email LIKE ? OR name LIKE ? OR company LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return contacts

    def count_contacts(self, status='active'):
        """Count total contacts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if status and status != 'all':
            cursor.execute('SELECT COUNT(*) FROM contacts WHERE status = ?', (status,))
        else:
            cursor.execute('SELECT COUNT(*) FROM contacts')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def unsubscribe_contact(self, email):
        """Mark contact as unsubscribed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE contacts SET status = "unsubscribed" WHERE email = ?', (email.strip().lower(),))
        conn.commit()
        conn.close()

    def create_contact_list(self, name, description=None):
        """Create a contact list / audience segment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO contact_lists (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
        list_id = cursor.lastrowid
        conn.close()
        return list_id

    def get_contact_lists(self):
        """Get all contact lists with subscriber counts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cl.*, COUNT(clm.contact_id) as member_count
            FROM contact_lists cl
            LEFT JOIN contact_list_members clm ON cl.id = clm.list_id
            GROUP BY cl.id
            ORDER BY cl.id DESC
        ''')
        lists = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return lists

    def add_contacts_to_list(self, list_id, contact_ids):
        """Add list of contact IDs to a contact list"""
        conn = self.get_connection()
        cursor = conn.cursor()
        for cid in contact_ids:
            cursor.execute('''
                INSERT OR IGNORE INTO contact_list_members (list_id, contact_id)
                VALUES (?, ?)
            ''', (list_id, cid))
        conn.commit()
        conn.close()

    def get_contacts_by_list(self, list_id):
        """Get all contacts belonging to a specific list"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*
            FROM contacts c
            JOIN contact_list_members clm ON c.id = clm.contact_id
            WHERE clm.list_id = ? AND c.status = 'active'
        ''', (list_id,))
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return contacts

    # ------------------ Templates ------------------ #

    def save_template(self, name, subject_template, body_html, body_text=None, category='general', variables=None):
        """Save or update an email template"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO templates (name, subject_template, body_html, body_text, category, variables_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                subject_template = excluded.subject_template,
                body_html = excluded.body_html,
                body_text = excluded.body_text,
                category = excluded.category,
                variables_json = excluded.variables_json,
                updated_at = excluded.updated_at
        ''', (
            name, subject_template, body_html, body_text, category,
            json.dumps(variables) if isinstance(variables, list) else variables,
            now
        ))
        conn.commit()
        template_id = cursor.lastrowid
        conn.close()
        return template_id

    def get_templates(self, category=None):
        """Get all templates"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if category:
            cursor.execute('SELECT * FROM templates WHERE category = ? ORDER BY id DESC', (category,))
        else:
            cursor.execute('SELECT * FROM templates ORDER BY id DESC')
        templates = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return templates

    def get_template(self, template_id):
        """Get single template by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM templates WHERE id = ?', (template_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_template(self, template_id):
        """Delete template by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM templates WHERE id = ?', (template_id,))
        conn.commit()
        conn.close()

    # ------------------ Campaigns ------------------ #

    def create_campaign(self, name, template_id=None, contact_list_id=None, total_recipients=0, 
                        batch_size=50, delay_seconds=1.0, scheduled_at=None):
        """Create a new campaign"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO campaigns (name, template_id, contact_list_id, total_recipients, batch_size, delay_seconds, scheduled_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, template_id, contact_list_id, total_recipients, batch_size, delay_seconds, scheduled_at, 'draft' if not scheduled_at else 'scheduled'))
        conn.commit()
        campaign_id = cursor.lastrowid
        conn.close()
        return campaign_id

    def update_campaign_status(self, campaign_id, status, started_at=None, completed_at=None):
        """Update campaign status and timestamps"""
        conn = self.get_connection()
        cursor = conn.cursor()
        updates = ['status = ?']
        params = [status]
        if started_at:
            updates.append('started_at = ?')
            params.append(started_at)
        if completed_at:
            updates.append('completed_at = ?')
            params.append(completed_at)
        params.append(campaign_id)
        
        cursor.execute(f"UPDATE campaigns SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()

    def update_campaign_progress(self, campaign_id, sent_delta=0, failed_delta=0):
        """Increment campaign sent and failed counters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE campaigns 
            SET sent_count = sent_count + ?, failed_count = failed_count + ?
            WHERE id = ?
        ''', (sent_delta, failed_delta, campaign_id))
        conn.commit()
        conn.close()

    def log_campaign_recipient(self, campaign_id, recipient, subject, status='sent', error_message=None, tracking_id=None):
        """Log per-recipient campaign send record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO campaign_logs (campaign_id, recipient, subject, status, error_message, tracking_id, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (campaign_id, recipient, subject, status, error_message, tracking_id, now if status == 'sent' else None))
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        return log_id

    def get_campaigns(self, limit=50):
        """Get campaigns list with template & list names"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, t.name as template_name, cl.name as list_name
            FROM campaigns c
            LEFT JOIN templates t ON c.template_id = t.id
            LEFT JOIN contact_lists cl ON c.contact_list_id = cl.id
            ORDER BY c.id DESC LIMIT ?
        ''', (limit,))
        campaigns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return campaigns

    def get_campaign(self, campaign_id):
        """Get campaign details by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, t.name as template_name, cl.name as list_name
            FROM campaigns c
            LEFT JOIN templates t ON c.template_id = t.id
            LEFT JOIN contact_lists cl ON c.contact_list_id = cl.id
            WHERE c.id = ?
        ''', (campaign_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_campaign_logs(self, campaign_id, limit=100):
        """Get recipient send logs for a campaign"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM campaign_logs WHERE campaign_id = ? ORDER BY id DESC LIMIT ?', (campaign_id, limit))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs

    # ------------------ Scheduled Tasks ------------------ #

    def add_scheduled_task(self, task_name, task_type, schedule_expr, params=None):
        """Add a persistent scheduled task"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scheduled_tasks (task_name, task_type, schedule_expr, params_json)
            VALUES (?, ?, ?, ?)
        ''', (task_name, task_type, schedule_expr, json.dumps(params) if params else None))
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        return task_id

    def get_scheduled_tasks(self):
        """Get all scheduled tasks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM scheduled_tasks ORDER BY id DESC')
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks

    def toggle_scheduled_task(self, task_id, enabled=None):
        """Toggle scheduled task status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if enabled is None:
            cursor.execute('UPDATE scheduled_tasks SET enabled = CASE WHEN enabled = 1 THEN 0 ELSE 1 END WHERE id = ?', (task_id,))
        else:
            cursor.execute('UPDATE scheduled_tasks SET enabled = ? WHERE id = ?', (1 if enabled else 0, task_id))
        conn.commit()
        conn.close()

    def update_task_execution(self, task_id, last_run=None, next_run=None):
        """Update task run timestamps"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE scheduled_tasks SET last_run = ?, next_run = ? WHERE id = ?', (last_run, next_run, task_id))
        conn.commit()
        conn.close()

    def delete_scheduled_task(self, task_id):
        """Delete a scheduled task by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM scheduled_tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()

    def get_email_history(self, limit=200, offset=0, status=None, search=None, start_date=None, end_date=None):
        """Get sent email history with robust filtering by status, search keyword, and date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM sent_emails WHERE 1=1"
        params = []
        
        if status and status.lower() != 'all':
            st_clean = status.lower().strip()
            if st_clean in ('sent', 'success'):
                query += " AND status IN ('sent', 'success')"
            elif st_clean in ('failed', 'error'):
                query += " AND status IN ('failed', 'error')"
            else:
                query += " AND status = ?"
                params.append(st_clean)
        
        if search and search.strip():
            kw = f"%{search.strip()}%"
            query += " AND (recipient LIKE ? OR subject LIKE ? OR error_message LIKE ?)"
            params.extend([kw, kw, kw])
            
        if start_date:
            query += " AND date(sent_at) >= ?"
            params.append(str(start_date))
            
        if end_date:
            query += " AND date(sent_at) <= ?"
            params.append(str(end_date))
            
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ------------------ System & Activity Logs ------------------ #

    def log_activity(self, event_type, description, details=None):
        """Log system or user activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activity_logs (event_type, description, details_json)
            VALUES (?, ?, ?)
        ''', (event_type, description, json.dumps(details) if isinstance(details, (dict, list)) else details))
        conn.commit()
        conn.close()

    def get_activity_logs(self, limit=50):
        """Get recent activity logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?', (limit,))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs

    # ------------------ Analytics & Statistics ------------------ #

    def get_email_stats(self):
        """Get comprehensive statistics across the entire platform"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Sent counts (treats both 'sent' and 'success' as successful)
        cursor.execute("SELECT COUNT(*) FROM sent_emails WHERE status IN ('sent', 'success')")
        sent_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sent_emails WHERE status IN ('failed', 'error')")
        failed_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sent_emails")
        total_emails = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sent_emails WHERE opened = 1')
        opened_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sent_emails WHERE clicked = 1')
        clicked_count = cursor.fetchone()[0]
        
        # Monitored count
        cursor.execute('SELECT COUNT(*) FROM monitored_emails')
        monitored_count = cursor.fetchone()[0]

        # Triggered notifications count
        cursor.execute("SELECT COUNT(*) FROM monitored_emails WHERE notification_sent = 1 OR (rule_matches IS NOT NULL AND rule_matches != '[]' AND rule_matches != '')")
        notification_count = cursor.fetchone()[0]
        
        # Contacts count
        cursor.execute('SELECT COUNT(*) FROM contacts WHERE status = "active"')
        active_contacts = cursor.fetchone()[0]
        
        # Campaigns count
        cursor.execute('SELECT COUNT(*) FROM campaigns')
        total_campaigns = cursor.fetchone()[0]
        
        # Active rules
        cursor.execute('SELECT COUNT(*) FROM notification_rules WHERE enabled = 1')
        active_rules = cursor.fetchone()[0]

        # Active scheduled tasks
        cursor.execute('SELECT COUNT(*) FROM scheduled_tasks WHERE enabled = 1')
        active_scheduled_tasks = cursor.fetchone()[0]
        
        # Calculate rates
        delivery_rate = round((sent_count / total_emails * 100), 1) if total_emails > 0 else 100.0
        open_rate = round((opened_count / sent_count * 100), 1) if sent_count > 0 else 0.0
        click_rate = round((clicked_count / sent_count * 100), 1) if sent_count > 0 else 0.0
        
        # 7-day activity history
        cursor.execute('''
            SELECT date(sent_at) as date, 
                   SUM(CASE WHEN status IN ('sent', 'success') THEN 1 ELSE 0 END) as sent,
                   SUM(CASE WHEN status IN ('failed', 'error') THEN 1 ELSE 0 END) as failed
            FROM sent_emails
            WHERE sent_at >= date('now', '-7 days')
            GROUP BY date(sent_at)
            ORDER BY date(sent_at) ASC
        ''')
        daily_stats = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total': total_emails,
            'sent': sent_count,
            'failed': failed_count,
            'opened': opened_count,
            'clicked': clicked_count,
            'monitored': monitored_count,
            'notifications': notification_count,
            'active_contacts': active_contacts,
            'total_campaigns': total_campaigns,
            'active_rules': active_rules,
            'active_scheduled_tasks': active_scheduled_tasks,
            'delivery_rate': delivery_rate,
            'success_rate': delivery_rate,
            'open_rate': open_rate,
            'click_rate': click_rate,
            'daily_stats': daily_stats
        }

    def get_recent_sent_emails(self, limit=20):
        """Get list of recent sent emails"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sent_emails ORDER BY id DESC LIMIT ?', (limit,))
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return emails

    def get_monitored_emails(self, limit=50):
        """Get list of recent monitored emails"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM monitored_emails ORDER BY id DESC LIMIT ?', (limit,))
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return emails