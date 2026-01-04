# Email Automation & Notification System

A Python-based application for automated bulk email sending with personalization, email monitoring, and condition-based notifications.

## Features

- **Bulk Email Sending**: Send personalized emails to multiple recipients from CSV files
- **Email Monitoring**: Monitor incoming emails using IMAP
- **Notification System**: Trigger notifications based on predefined rules (sender, subject, keywords)
- **Task Scheduling**: Schedule email sending and monitoring tasks
- **Database Logging**: Track all sent and monitored emails in SQLite database
- **Personalization**: Use template variables for personalized email content

## Technologies Used

- Python 3.12
- SMTP (Simple Mail Transfer Protocol)
- IMAP (Internet Message Access Protocol)
- Libraries: `smtplib`, `email`, `imaplib`, `schedule`, `csv`, `sqlite3`

## Setup

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Email Settings

Copy `.env.example` to `.env` and update with your credentials:

```powershell
Copy-Item .env.example .env
```

Edit the `.env` file with your email settings:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

NOTIFICATION_EMAIL=notification_recipient@gmail.com
CHECK_INTERVAL=300

DB_PATH=emails.db
```

**Note for Gmail users**: You need to use an App Password instead of your regular password. Enable 2-factor authentication and generate an app password at: https://myaccount.google.com/apppasswords

## Usage

### Running the Application

```powershell
python main.py
```

### Main Menu Options

1. **Send Single Email**: Send a one-time email to a single recipient
2. **Send Bulk Emails from CSV**: Send personalized emails to multiple recipients
3. **Start Email Monitoring**: Monitor inbox for new emails
4. **Add Notification Rule**: Create rules for triggering notifications
5. **View Email Statistics**: See stats about sent and monitored emails
6. **Schedule Tasks**: Schedule recurring email tasks
7. **Exit**: Close the application

### Bulk Email with CSV

Create a CSV file with recipient data:

```csv
email,name,company
john@example.com,John Doe,Acme Corp
jane@example.com,Jane Smith,Tech Inc
```

Use placeholders in your email template:

```
Subject: Hello {name}
Body: Dear {name}, Welcome to {company}!
```

### Email Monitoring

The system monitors your inbox and can trigger notifications based on:
- Sender email address
- Subject keywords
- Body keywords

Add notification rules through the menu to get alerts when specific emails arrive.

### Scheduling Tasks

Schedule tasks to run automatically:
- **Bulk emails**: Send emails at specific times daily
- **Email monitoring**: Check inbox at regular intervals
- **Weekly reports**: Get statistics reports on specific days

## Database Structure

The system uses SQLite to store:
- **sent_emails**: Log of all sent emails with status
- **monitored_emails**: Log of monitored incoming emails
- **notification_rules**: Configured notification rules

## File Structure

```
Email Automation & Notification System/
├── main.py                    # Main application entry point
├── config.py                  # Configuration management
├── email_sender.py            # SMTP email sending functionality
├── email_monitor.py           # IMAP email monitoring
├── database.py                # SQLite database operations
├── scheduler.py               # Task scheduling
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment configuration
├── sample_recipients.csv      # Sample CSV for bulk emails
├── README.md                 # This file
└── emails.db                 # SQLite database (created on first run)
```

## Security Notes

- Never commit your `.env` file with actual credentials
- Use app-specific passwords for email services
- Keep your email password secure
- The `.env` file is excluded from version control

## Testing

Run tests with pytest:

```powershell
pytest
```

## Troubleshooting

**Connection errors**: 
- Check your email server settings (SMTP/IMAP servers and ports)
- Ensure "Less secure app access" is enabled (for Gmail, use App Password instead)
- Check firewall settings

**Authentication errors**:
- Verify email address and password in `.env`
- For Gmail, use an App Password

**CSV parsing errors**:
- Ensure CSV has headers
- Check for proper encoding (UTF-8)
- Verify column names match template placeholders

## License

This project is provided as-is for educational and automation purposes.