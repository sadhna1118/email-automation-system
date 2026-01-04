import schedule
import time
from email_sender import EmailSender
from email_monitor import EmailMonitor

class EmailScheduler:
    """Schedule email sending and monitoring tasks"""
    
    def __init__(self):
        self.sender = EmailSender()
        self.monitor = EmailMonitor()
    
    def schedule_bulk_email(self, csv_file, subject_template, body_template, time_str, html=False):
        """Schedule bulk email sending at specific time"""
        def job():
            print(f"\nExecuting scheduled bulk email task at {time_str}")
            self.sender.send_bulk_emails(csv_file, subject_template, body_template, html=html)
        
        schedule.every().day.at(time_str).do(job)
        print(f"Scheduled bulk email task for {time_str} daily")
    
    def schedule_email_monitoring(self, interval_minutes=5):
        """Schedule periodic email monitoring"""
        def job():
            self.monitor.monitor_inbox()
        
        schedule.every(interval_minutes).minutes.do(job)
        print(f"Scheduled email monitoring every {interval_minutes} minutes")
    
    def schedule_weekly_report(self, day, time_str):
        """Schedule weekly email statistics report"""
        def job():
            from database import EmailDatabase
            db = EmailDatabase()
            stats = db.get_email_stats()
            
            subject = "Weekly Email Report"
            body = f"""
Weekly Email Statistics:

Sent: {stats['sent']}
Failed: {stats['failed']}
Monitored: {stats['monitored']}
            """
            
            self.sender.send_notification(subject, body)
        
        getattr(schedule.every(), day.lower()).at(time_str).do(job)
        print(f"Scheduled weekly report for {day} at {time_str}")
    
    def run(self):
        """Start the scheduler"""
        print("Starting scheduler...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nScheduler stopped")