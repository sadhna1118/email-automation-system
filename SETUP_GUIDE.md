# Setup Guide - Email Automation & Notification System

## Prerequisites

- Python 3.12 or higher
- Gmail account (or other email service)
- Internet connection

## Step-by-Step Setup

### 1. Install Python Dependencies

Open PowerShell in the project directory and run:

```powershell
pip install -r requirements.txt
```

### 2. Configure Gmail App Password (for Gmail users)

**Important:** Gmail requires App Passwords for third-party applications.

1. Go to your Google Account: https://myaccount.google.com/
2. Click on **Security** in the left sidebar
3. Enable **2-Step Verification** if not already enabled
4. After enabling 2FA, go back to **Security**
5. Click on **App passwords** (search for "App passwords" if you can't find it)
6. Select **Mail** as the app and **Windows Computer** as the device
7. Click **Generate**
8. Copy the 16-character app password (no spaces)

### 3. Configure Email Settings

Edit the `.env` file and replace the placeholder values:

```
EMAIL_ADDRESS=your_actual_email@gmail.com
EMAIL_PASSWORD=your_16_character_app_password
NOTIFICATION_EMAIL=where_to_receive_notifications@gmail.com
```

**Example:**
```
EMAIL_ADDRESS=john.doe@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
NOTIFICATION_EMAIL=john.doe@gmail.com
```

### 4. Test the Installation

Run the test suite to verify everything is working:

```powershell
pytest test_email_system.py -v
```

### 5. Run the Application

```powershell
python main.py
```

## Configuration for Other Email Providers

### Outlook/Hotmail

```
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
IMAP_SERVER=outlook.office365.com
IMAP_PORT=993
```

### Yahoo Mail

```
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
IMAP_SERVER=imap.mail.yahoo.com
IMAP_PORT=993
```

### Custom Email Server

Update the `.env` file with your email provider's SMTP and IMAP settings.

## Troubleshooting

### Error: "Username and Password not accepted"

**Solutions:**
1. Make sure you're using an App Password, not your regular password (for Gmail)
2. Check that 2-Factor Authentication is enabled on your Google account
3. Verify the email address and app password are correct in `.env`
4. Try regenerating the App Password

### Error: "Connection refused" or "Timeout"

**Solutions:**
1. Check your internet connection
2. Verify firewall isn't blocking SMTP (port 587) or IMAP (port 993)
3. Make sure SMTP_SERVER and IMAP_SERVER are correct for your email provider
4. Some networks block email ports - try a different network

### Error: "Module not found"

**Solutions:**
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Make sure you're running Python 3.12 or higher: `python --version`
3. Try creating a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

### Error: "Cannot open CSV file"

**Solutions:**
1. Make sure the CSV file path is correct
2. Use absolute path if relative path doesn't work
3. Ensure CSV file has proper headers matching template placeholders

## Features Quick Start

### 1. Send Single Email
- Select option 1 from menu
- Enter recipient email, subject, and body
- Choose plain text or HTML format

### 2. Send Bulk Emails
- Prepare a CSV file with columns: `email`, `name`, `company`, etc.
- Use `sample_recipients.csv` as a template
- In subject/body templates, use `{column_name}` for personalization
- Example: `Hello {name} from {company}`

### 3. Monitor Emails
- Select option 3 from menu
- Set check interval (in seconds)
- Press Ctrl+C to stop monitoring

### 4. Add Notification Rules
- Select option 4 from menu
- Create rules based on sender, subject, or keywords
- Get alerts when matching emails arrive

### 5. Schedule Tasks
- Select option 6 from menu
- Schedule bulk emails, monitoring, or reports
- Uses 24-hour time format (HH:MM)

## Security Best Practices

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Use App Passwords** - Never use your main email password
3. **Restrict permissions** - Keep `.env` file permissions limited
4. **Regular updates** - Keep dependencies updated for security patches
5. **Monitor logs** - Check `emails.db` for unusual activity

## Getting Help

If you encounter issues:

1. Check the error message carefully
2. Review this setup guide
3. Verify your email provider's SMTP/IMAP settings
4. Test with a simple single email first
5. Check Python and package versions

## Additional Resources

- Gmail App Passwords: https://support.google.com/accounts/answer/185833
- SMTP/IMAP Settings: https://www.systoolsgroup.com/imap/
- Python Email Libraries: https://docs.python.org/3/library/email.html

## Project Structure

```
Email Automation & Notification System/
├── .env                      # Your email credentials (DO NOT COMMIT)
├── .env.example             # Template for .env
├── .gitignore               # Git ignore rules
├── README.md                # Project overview
├── SETUP_GUIDE.md          # This file
├── requirements.txt         # Python dependencies
├── main.py                  # Main application
├── config.py                # Configuration loader
├── email_sender.py          # SMTP email sending
├── email_monitor.py         # IMAP email monitoring
├── database.py              # SQLite database
├── scheduler.py             # Task scheduling
├── test_email_system.py     # Unit tests
├── sample_recipients.csv    # Sample data for bulk emails
└── emails.db               # Database (created on first run)
```

## Success Checklist

- [ ] Python 3.12+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Gmail App Password generated (or other provider configured)
- [ ] `.env` file configured with real credentials
- [ ] Tests passing (`pytest test_email_system.py -v`)
- [ ] Application runs without errors (`python main.py`)
- [ ] Successfully sent a test email

Once all items are checked, your Email Automation System is ready to use!