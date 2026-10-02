import schedule
import time
import threading
import json
from datetime import datetime

from config import Config
from database import EmailDatabase
from email_sender import EmailSender
from email_monitor import EmailMonitor

class EmailScheduler:
    """Enterprise Background Task Scheduler synchronized with SQLite database"""
    
    def __init__(self, config=None, db=None, sender=None, monitor=None):
        self.config = config or Config
        self.db = db or EmailDatabase()
        self.sender = sender or EmailSender(config=self.config, db=self.db)
        self.monitor = monitor or EmailMonitor(config=self.config, db=self.db, sender=self.sender)
        
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
    
    def schedule_bulk_email(self, csv_file, subject_template, body_template, time_str, html=False):
        """Schedule a daily bulk email task"""
        def job():
            print(f"\n[Scheduled Job] Executing bulk email task at {time_str}")
            self.sender.send_bulk_emails(csv_file, subject_template, body_template, html=html)
            self.db.log_activity('scheduled_task_executed', f"Executed daily bulk email task scheduled for {time_str}")
        
        schedule.every().day.at(time_str).do(job)
        print(f"[Scheduler] Scheduled bulk email task for {time_str} daily")

    def schedule_email_monitoring(self, interval_minutes=5):
        """Schedule periodic email monitoring"""
        def job():
            new_count = self.monitor.monitor_inbox()
            if new_count > 0:
                print(f"[Scheduled Job] Inbox monitor processed {new_count} new emails")
        
        schedule.every(interval_minutes).minutes.do(job)
        print(f"[Scheduler] Scheduled email monitoring every {interval_minutes} minutes")

    def schedule_weekly_report(self, day, time_str):
        """Schedule weekly email statistics report to notification recipient"""
        def job():
            stats = self.db.get_email_stats()
            subject = f"📊 Weekly Email Automation Performance Digest - {datetime.now().strftime('%B %d, %Y')}"
            body = f"""Weekly Email Statistics & Performance Report
=====================================================
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Key Metrics:
- Total Sent: {stats['sent']}
- Failed: {stats['failed']}
- Delivery Rate: {stats['delivery_rate']}%
- Open Rate: {stats['open_rate']}%
- Click Rate: {stats['click_rate']}%
- Monitored Incoming Emails: {stats['monitored']}
- Active Subscribers: {stats['active_contacts']}
- Active Notification Rules: {stats['active_rules']}

=====================================================
Manage your automation system at: {self.config.BASE_URL}
"""
            self.sender.send_notification(subject, body)
            self.db.log_activity('weekly_report_sent', "Sent automated weekly performance report")
        
        getattr(schedule.every(), day.lower()).at(time_str).do(job)
        print(f"[Scheduler] Scheduled weekly digest report for every {day} at {time_str}")

    def schedule_single_email(self, to_email, subject, body, time_str, html=False):
        """Schedule a single email at a specific time daily or on trigger"""
        def job():
            print(f"\n[Scheduled Job] Sending scheduled single email to {to_email}")
            self.sender.send_email(to_email=to_email, subject=subject, body=body, html=html)
            self.db.log_activity('scheduled_task_executed', f"Executed scheduled email to {to_email} at {time_str}")
        
        try:
            schedule.every().day.at(time_str).do(job)
        except Exception:
            schedule.every(1).hours.do(job)
        print(f"[Scheduler] Scheduled single email to {to_email} at {time_str}")

    def load_db_tasks(self):
        """Load and register active tasks from SQLite database"""
        tasks = self.db.get_scheduled_tasks()
        for t in tasks:
            if not t.get('enabled'):
                continue
            
            task_type = t['task_type']
            schedule_expr = t['schedule_expr']
            params = {}
            if t.get('params_json'):
                try:
                    params = json.loads(t['params_json'])
                except Exception:
                    pass
            
            if task_type in ('monitor_inbox', 'Email Monitoring'):
                interval = params.get('interval_minutes', 5)
                self.schedule_email_monitoring(interval_minutes=int(interval))
            elif task_type in ('weekly_report', 'Weekly Report'):
                day = params.get('day', 'monday')
                time_str = params.get('time', '09:00')
                self.schedule_weekly_report(day, time_str)
            elif task_type in ('single_email', 'Single Email'):
                to_email = params.get('to_email') or params.get('recipient')
                subject = params.get('subject', 'Scheduled Notification')
                body = params.get('body', 'This is a scheduled automated email.')
                time_str = params.get('time', '09:00')
                if to_email:
                    self.schedule_single_email(to_email, subject, body, time_str)
            elif task_type in ('bulk_email', 'Bulk Email'):
                csv_file = params.get('csv_file', 'sample_recipients.csv')
                sub_tmpl = params.get('subject_template', 'Update for {name}')
                body_tmpl = params.get('body_template', 'Hello {name}, updates from {company}.')
                time_str = params.get('time', '10:00')
                self.schedule_bulk_email(csv_file, sub_tmpl, body_tmpl, time_str)

    def is_running(self):
        """Return True if scheduler daemon is currently running"""
        return self._running

    def start_background(self):
        """Start scheduler execution loop in a background daemon thread"""
        if self._running:
            return
        
        schedule.clear()
        self.load_db_tasks()
        self._running = True
        self._stop_event.clear()
        
        def run_loop():
            print("[Scheduler] Background scheduler thread active.")
            while not self._stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

    def stop_background(self):
        """Stop background scheduler thread"""
        if self._running:
            self._running = False
            self._stop_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2)
            schedule.clear()

    def run(self):
        """Run blocking scheduler loop (for CLI use)"""
        print("[Scheduler] Starting scheduler in foreground... (Press Ctrl+C to stop)")
        self.load_db_tasks()
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Scheduler] Scheduler stopped by user.")