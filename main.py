import sys
from config import Config
from email_sender import EmailSender
from email_monitor import EmailMonitor
from database import EmailDatabase
from scheduler import EmailScheduler

def print_menu():
    """Display main menu"""
    print("\n" + "="*50)
    print("Email Automation & Notification System")
    print("="*50)
    print("1. Send Single Email")
    print("2. Send Bulk Emails from CSV")
    print("3. Start Email Monitoring")
    print("4. Add Notification Rule")
    print("5. View Email Statistics")
    print("6. Schedule Tasks")
    print("7. Exit")
    print("="*50)

def send_single_email():
    """Send a single email"""
    sender = EmailSender()
    
    to_email = input("Recipient email: ")
    subject = input("Subject: ")
    body = input("Body: ")
    html = input("Send as HTML? (y/n): ").lower() == 'y'
    
    sender.send_email(to_email, subject, body, html=html)

def send_bulk_emails():
    """Send bulk emails from CSV"""
    sender = EmailSender()
    
    csv_file = input("CSV file path: ")
    subject_template = input("Subject template (use {fieldname} for personalization): ")
    body_template = input("Body template (use {fieldname} for personalization): ")
    html = input("Send as HTML? (y/n): ").lower() == 'y'
    
    sender.send_bulk_emails(csv_file, subject_template, body_template, html=html)

def start_monitoring():
    """Start email monitoring"""
    monitor = EmailMonitor()
    interval = input("Check interval in seconds (default 300): ")
    interval = int(interval) if interval else 300
    
    monitor.start_monitoring(interval=interval)

def add_notification_rule():
    """Add a notification rule"""
    db = EmailDatabase()
    
    rule_name = input("Rule name: ")
    sender_filter = input("Sender filter (leave empty for any): ") or None
    subject_filter = input("Subject filter (leave empty for any): ") or None
    keyword_filter = input("Keyword filter (leave empty for any): ") or None
    
    db.add_notification_rule(rule_name, sender_filter, subject_filter, keyword_filter)
    print(f"Notification rule '{rule_name}' added successfully")

def view_statistics():
    """View email statistics"""
    db = EmailDatabase()
    stats = db.get_email_stats()
    
    print("\n" + "="*50)
    print("Email Statistics")
    print("="*50)
    print(f"Sent emails: {stats['sent']}")
    print(f"Failed emails: {stats['failed']}")
    print(f"Monitored emails: {stats['monitored']}")
    print("="*50)

def schedule_tasks():
    """Schedule tasks"""
    scheduler = EmailScheduler()
    
    print("\nScheduling Options:")
    print("1. Schedule bulk email")
    print("2. Schedule email monitoring")
    print("3. Schedule weekly report")
    
    choice = input("Select option: ")
    
    if choice == '1':
        csv_file = input("CSV file path: ")
        subject = input("Subject template: ")
        body = input("Body template: ")
        time_str = input("Time (HH:MM format, 24-hour): ")
        html = input("Send as HTML? (y/n): ").lower() == 'y'
        
        scheduler.schedule_bulk_email(csv_file, subject, body, time_str, html=html)
    
    elif choice == '2':
        interval = input("Interval in minutes (default 5): ")
        interval = int(interval) if interval else 5
        scheduler.schedule_email_monitoring(interval_minutes=interval)
    
    elif choice == '3':
        day = input("Day of week (Monday, Tuesday, etc.): ")
        time_str = input("Time (HH:MM format, 24-hour): ")
        scheduler.schedule_weekly_report(day, time_str)
    
    scheduler.run()

def main():
    """Main application loop"""
    try:
        # Validate configuration
        Config.validate()
        
        while True:
            print_menu()
            choice = input("\nSelect option: ")
            
            if choice == '1':
                send_single_email()
            elif choice == '2':
                send_bulk_emails()
            elif choice == '3':
                start_monitoring()
            elif choice == '4':
                add_notification_rule()
            elif choice == '5':
                view_statistics()
            elif choice == '6':
                schedule_tasks()
            elif choice == '7':
                print("Exiting...")
                sys.exit(0)
            else:
                print("Invalid option. Please try again.")
    
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("Please create a .env file with required settings (see .env.example)")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()