# Changelog

All notable changes to the Email Automation & Notification System project.

## [1.0.0] - 2026-01-04

### Added
- Initial release of Email Automation & Notification System
- Single email sending functionality with SMTP
- Bulk email sending from CSV files with personalization
- Email monitoring using IMAP
- Notification system with rule-based triggers
- Task scheduling for automated operations
- SQLite database for logging and tracking
- Comprehensive test suite with pytest
- Configuration management with python-dotenv
- Sample CSV file for bulk email testing
- Complete documentation (README.md, SETUP_GUIDE.md)
- Quick start PowerShell script
- Environment configuration templates

### Features
- **Email Sending**
  - Single email delivery
  - Bulk email campaigns with CSV import
  - Template personalization with placeholders
  - HTML and plain text support
  - Attachment support
  - Success/failure tracking

- **Email Monitoring**
  - IMAP-based inbox monitoring
  - Configurable check intervals
  - Email preview extraction
  - Notification rule matching

- **Notification System**
  - Custom notification rules
  - Filter by sender, subject, or keywords
  - Automatic alert emails
  - Rule management

- **Task Scheduling**
  - Daily bulk email scheduling
  - Periodic email monitoring
  - Weekly statistics reports
  - Time-based automation

- **Database**
  - SQLite storage
  - Sent email logging
  - Monitored email tracking
  - Notification rule management
  - Statistics aggregation

- **Security**
  - Environment-based configuration
  - App password support
  - Secure credential storage
  - .gitignore protection

### Technologies
- Python 3.12+
- SMTP/IMAP protocols
- SQLite3 database
- Libraries: schedule, pytest, python-dotenv

### Documentation
- Comprehensive README with features and usage
- Detailed setup guide with troubleshooting
- Quick start script for easy setup
- Sample CSV for testing
- Inline code documentation