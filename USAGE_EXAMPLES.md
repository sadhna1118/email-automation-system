# Usage Examples

This document provides practical examples for using the Email Automation & Notification System.

## Example 1: Send a Single Email

```
Menu Option: 1
Recipient email: john.doe@example.com
Subject: Meeting Reminder
Body: Hi John, Just a reminder about our meeting tomorrow at 10 AM.
Send as HTML? (y/n): n
```

## Example 2: Send Bulk Personalized Emails

### Step 1: Create CSV file (recipients.csv)
```csv
email,name,company,position
john.doe@example.com,John Doe,Acme Corp,Manager
jane.smith@example.com,Jane Smith,Tech Inc,Developer
bob.wilson@example.com,Bob Wilson,StartupCo,CEO
```

### Step 2: Use Menu Option 2
```
Menu Option: 2
CSV file path: recipients.csv
Subject template: Welcome to {company}, {name}!
Body template: Dear {name},

Welcome to your new role as {position} at {company}!

We're excited to have you on board.

Best regards,
HR Team
Send as HTML? (y/n): n
```

## Example 3: HTML Email Template

### Subject Template
```
Newsletter - {month} Edition
```

### Body Template (HTML)
```html
<html>
<body>
    <h1>Hello {name}!</h1>
    <p>Welcome to our {month} newsletter.</p>
    <p>Here are the highlights:</p>
    <ul>
        <li>Feature 1</li>
        <li>Feature 2</li>
        <li>Feature 3</li>
    </ul>
    <p>Best regards,<br>{company}</p>
</body>
</html>
```

## Example 4: Email Monitoring with Notification Rules

### Add Notification Rule for Important Emails
```
Menu Option: 4
Rule name: Important Client Emails
Sender filter: client@importantcompany.com
Subject filter: urgent
Keyword filter: (leave empty)
```

### Add Notification Rule for Support Tickets
```
Menu Option: 4
Rule name: Support Tickets
Sender filter: (leave empty)
Subject filter: [Support]
Keyword filter: help
```

### Start Monitoring
```
Menu Option: 3
Check interval in seconds: 300
```

This will check for new emails every 5 minutes and send notifications when rules match.

## Example 5: Schedule Daily Bulk Email

### Schedule a daily newsletter
```
Menu Option: 6
Scheduling Options: 1
CSV file path: newsletter_recipients.csv
Subject template: Daily Update for {name}
Body template: Hi {name}, here's your daily update...
Time (HH:MM format, 24-hour): 09:00
Send as HTML? (y/n): y
```

This will send emails every day at 9:00 AM.

## Example 6: Schedule Periodic Email Monitoring

```
Menu Option: 6
Scheduling Options: 2
Interval in minutes: 10
```

This will check inbox every 10 minutes continuously.

## Example 7: Schedule Weekly Report

```
Menu Option: 6
Scheduling Options: 3
Day of week: Monday
Time (HH:MM format, 24-hour): 08:00
```

This will send email statistics report every Monday at 8:00 AM.

## Example 8: Product Launch Campaign

### Create product_launch.csv
```csv
email,name,product,discount_code
customer1@example.com,Alice,Premium Plan,LAUNCH50
customer2@example.com,Bob,Standard Plan,LAUNCH30
customer3@example.com,Carol,Premium Plan,LAUNCH50
```

### Subject Template
```
Exclusive Launch: {product} with {discount_code}!
```

### Body Template
```
Dear {name},

We're excited to announce the launch of our {product}!

As a valued customer, you get an exclusive discount code: {discount_code}

This offer is valid for 7 days only.

Visit our website to learn more.

Best regards,
Product Team
```

## Example 9: Event Invitation

### Create event_invites.csv
```csv
email,name,event,date,time,venue
john@example.com,John,Annual Gala,Dec 15 2024,7:00 PM,Grand Hotel
jane@example.com,Jane,Annual Gala,Dec 15 2024,7:00 PM,Grand Hotel
```

### Subject Template
```
You're Invited: {event}
```

### Body Template (HTML)
```html
<html>
<body>
    <h2>Dear {name},</h2>
    <p>You're cordially invited to our <strong>{event}</strong></p>
    
    <div style="background-color: #f0f0f0; padding: 15px; margin: 20px 0;">
        <h3>Event Details</h3>
        <p><strong>Date:</strong> {date}</p>
        <p><strong>Time:</strong> {time}</p>
        <p><strong>Venue:</strong> {venue}</p>
    </div>
    
    <p>Please RSVP by replying to this email.</p>
    
    <p>Looking forward to seeing you!</p>
</body>
</html>
```

## Example 10: Job Application Auto-Response

### Setup Notification Rule
```
Rule name: New Job Applications
Sender filter: (leave empty)
Subject filter: Application for
Keyword filter: resume
```

This will trigger notifications whenever someone sends a job application.

## Example 11: View Statistics

```
Menu Option: 5
```

Output:
```
==================================================
Email Statistics
==================================================
Sent emails: 150
Failed emails: 3
Monitored emails: 45
==================================================
```

## Tips for Success

### CSV File Tips
1. **Always include headers** in your CSV file
2. **Use consistent column names** that match your templates
3. **Encode files as UTF-8** to handle special characters
4. **Test with small batches** first (5-10 recipients)

### Template Tips
1. **Use curly braces** for placeholders: `{column_name}`
2. **Preview your templates** before sending bulk emails
3. **Test HTML rendering** by sending to yourself first
4. **Keep subjects concise** (under 50 characters)

### Monitoring Tips
1. **Start with longer intervals** (5-10 minutes) to avoid rate limits
2. **Be specific with filters** to reduce false positives
3. **Test rules** with sample emails first
4. **Check notification email** regularly

### Scheduling Tips
1. **Use 24-hour format** for times (e.g., 14:00 for 2 PM)
2. **Consider time zones** when scheduling
3. **Test scheduled tasks** during development
4. **Monitor execution** to ensure tasks run as expected

## Common Use Cases

### Marketing Campaigns
- Newsletter distribution
- Product announcements
- Promotional offers
- Event invitations

### Customer Support
- Auto-responses
- Ticket notifications
- Status updates
- Survey requests

### Internal Communications
- Team announcements
- Meeting reminders
- Report distribution
- Policy updates

### HR & Recruitment
- Job application responses
- Interview invitations
- Onboarding materials
- Employee newsletters

## Error Handling Examples

### Failed Email Handling
If an email fails to send, it's automatically logged in the database with the error message. View failed emails:

```python
# Check database for failed emails
SELECT * FROM sent_emails WHERE status = 'failed';
```

### Retry Failed Emails
You can export failed emails and retry them:

```python
# Export failed recipients to new CSV
# Retry with same or modified template
```

## Advanced Usage

### Multiple Notification Rules
You can create multiple rules for different purposes:

1. **Urgent Client Emails** → sender: client.com, subject: urgent
2. **Support Tickets** → subject: [Support]
3. **Sales Leads** → keyword: interested in
4. **HR Applications** → subject: Application, keyword: resume

### Combining Features
- Schedule bulk emails AND monitor for responses
- Set up notification rules AND schedule weekly reports
- Send personalized HTML campaigns AND track delivery

## Best Practices

1. **Always test with yourself first** before bulk sending
2. **Keep your App Password secure** and never share it
3. **Monitor rate limits** to avoid being flagged as spam
4. **Personalize emails** to increase engagement
5. **Track and analyze** statistics regularly
6. **Follow email marketing laws** (CAN-SPAM, GDPR)
7. **Maintain clean email lists** (remove bounced emails)
8. **Use clear subject lines** to improve open rates

## Getting Help

If you need more examples or have questions:
1. Check the main README.md
2. Review SETUP_GUIDE.md for configuration
3. Examine sample_recipients.csv for CSV format
4. Test with small batches first