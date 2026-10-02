"""
Comprehensive Automated Test Suite for Email Automation System
Tests email validation, CSV parsing, template personalization, database operations,
SMTP error handling (with mocks), and notification rule matching without sending real emails.
"""

import os
import pytest
import sqlite3
from unittest.mock import MagicMock, patch

from database import EmailDatabase
from validator import EmailValidator
from template_engine import TemplateEngine
from email_sender import EmailSender
from email_monitor import EmailMonitor
from config import Config

TEST_DB_PATH = "test_system_automation.db"

@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database and clean it up after the test"""
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    db = EmailDatabase(TEST_DB_PATH)
    yield db

    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

# 1. Email Validation Tests
class TestEmailValidation:
    def test_valid_emails(self):
        valid_cases = [
            "user@example.com",
            "first.last@company.org",
            "support+tag@sub.domain.co",
            "developer_123@tech.io"
        ]
        for email in valid_cases:
            res = EmailValidator.validate_email(email)
            assert res['valid'] is True
            assert res['email'] == email.lower()

    def test_invalid_syntax_emails(self):
        invalid_cases = [
            "",
            "plainaddress",
            "@missinguser.com",
            "missingdomain@",
            "user@.com",
            "user@domain..com"
        ]
        for email in invalid_cases:
            res = EmailValidator.validate_email(email)
            assert res['valid'] is False
            assert 'reason' in res

    def test_disposable_domain_detection(self):
        disposable = "fake_user@mailinator.com"
        res = EmailValidator.validate_email(disposable)
        assert res['valid'] is True
        assert res['is_disposable'] is True
        assert res['warning'] is not None

# 2. Template Personalization Tests
class TestTemplatePersonalization:
    def test_single_bracket_substitution(self):
        engine = TemplateEngine()
        template = "Hello {name}, welcome to {company}!"
        context = {"name": "Sadhna", "company": "Tech Innovations"}
        rendered = engine.render_string(template, context)
        assert rendered == "Hello Sadhna, welcome to Tech Innovations!"

    def test_jinja2_template_rendering(self):
        engine = TemplateEngine()
        template = "Hi {{ name|default('Friend') }}, your plan expires in {{ days }} days."
        context = {"name": "Alex", "days": 5}
        rendered = engine.render_string(template, context)
        assert rendered == "Hi Alex, your plan expires in 5 days."

    def test_missing_placeholder_fallback(self):
        engine = TemplateEngine()
        template = "Dear {{ name|default('Valued Customer') }}!"
        context = {}
        rendered = engine.render_string(template, context)
        assert rendered == "Dear Valued Customer!"

# 3. CSV Validation Tests
class TestCSVValidation:
    def test_valid_csv_parsing(self):
        raw_csv = """email,name,company
john.doe@example.com,John Doe,Acme Corp
jane.smith@example.com,Jane Smith,Tech Solutions
"""
        parsed = EmailValidator.parse_csv(raw_csv, is_raw_text=True)
        assert parsed['total_rows'] == 2
        assert len(parsed['valid_rows']) == 2
        assert len(parsed['invalid_rows']) == 0
        assert parsed['valid_rows'][0]['email'] == "john.doe@example.com"
        assert parsed['valid_rows'][0]['name'] == "John Doe"

    def test_missing_email_column(self):
        raw_csv = """name,company,phone
John Doe,Acme Corp,555-1234
"""
        parsed = EmailValidator.parse_csv(raw_csv, is_raw_text=True)
        assert 'error' in parsed
        assert "must contain an \"email\" column" in parsed['error']

    def test_empty_csv(self):
        parsed = EmailValidator.parse_csv("", is_raw_text=True)
        assert 'error' in parsed
        assert "CSV file is empty" in parsed['error']

    def test_csv_duplicate_removal(self):
        raw_csv = """email,name
alice@example.com,Alice 1
alice@example.com,Alice Duplicate
bob@example.com,Bob
"""
        parsed = EmailValidator.parse_csv(raw_csv, is_raw_text=True)
        assert len(parsed['valid_rows']) == 2
        assert parsed['duplicates_removed'] == 1

# 4. Database Insertion Tests
class TestDatabaseInsertion:
    def test_insert_sent_email(self, test_db):
        email_id = test_db.log_sent_email(
            recipient="test@example.com",
            subject="Test Subject",
            status="sent",
            is_html=True
        )
        assert email_id is not None
        assert email_id > 0

    def test_insert_monitored_email(self, test_db):
        email_id = test_db.log_monitored_email(
            sender="sender@example.com",
            subject="Incoming Subject",
            body_preview="Preview snippet",
            rule_matches=["Rule 1"]
        )
        assert email_id is not None

    def test_insert_notification_rule(self, test_db):
        rule_id = test_db.add_notification_rule(
            rule_name="Job Interview Alert",
            subject_filter="Interview",
            notification_email="alerts@company.com"
        )
        assert rule_id is not None
        assert rule_id > 0

    def test_insert_scheduled_task(self, test_db):
        task_id = test_db.add_scheduled_task(
            task_name="Daily Digest",
            task_type="Weekly Report",
            schedule_expr="Daily at 09:00",
            params={"day": "monday"}
        )
        assert task_id is not None
        assert task_id > 0

# 5. Database Retrieval & Filtering Tests
class TestDatabaseRetrieval:
    def test_get_email_history_and_filters(self, test_db):
        test_db.log_sent_email(recipient="alice@test.com", subject="Offer Letter", status="sent")
        test_db.log_sent_email(recipient="bob@test.com", subject="Server Alert", status="failed", error_message="Timeout")

        # Test all
        all_emails = test_db.get_email_history()
        assert len(all_emails) == 2

        # Filter by success
        successful = test_db.get_email_history(status="SUCCESS")
        assert len(successful) == 1
        assert successful[0]['recipient'] == "alice@test.com"

        # Filter by search
        search_res = test_db.get_email_history(search="Alert")
        assert len(search_res) == 1
        assert search_res[0]['recipient'] == "bob@test.com"

    def test_get_email_stats(self, test_db):
        test_db.log_sent_email(recipient="user1@test.com", subject="Test 1", status="sent")
        test_db.log_sent_email(recipient="user2@test.com", subject="Test 2", status="failed")
        test_db.log_monitored_email(sender="client@test.com", subject="Hello")

        stats = test_db.get_email_stats()
        assert stats['total'] == 2
        assert stats['sent'] == 1
        assert stats['failed'] == 1
        assert stats['monitored'] == 1
        assert stats['delivery_rate'] == 50.0

# 6. SMTP Error Handling Tests (Mocks Used)
class TestSMTPErrorHandling:
    def test_invalid_recipient_rejected_cleanly(self, test_db):
        sender = EmailSender(db=test_db)
        success = sender.send_email(to_email="invalid-email-address", subject="Test", body="Body")
        assert success is False

        # Verify logged as failed in database
        recent = test_db.get_recent_sent_emails(limit=1)
        assert len(recent) == 1
        assert recent[0]['status'] == "failed"
        assert "Invalid recipient email syntax" in recent[0]['error_message']

    def test_smtp_network_failure_handling(self, test_db):
        # Configure non dry-run mode with mocked SMTP connection error
        mock_config = MagicMock()
        mock_config.DRY_RUN = False
        mock_config.SMTP_SERVER = "smtp.mock.server"
        mock_config.SMTP_PORT = 587
        mock_config.SMTP_USE_SSL = False
        mock_config.SMTP_USE_TLS = True
        mock_config.SMTP_TIMEOUT = 5
        mock_config.EMAIL_ADDRESS = "sender@mock.com"
        mock_config.EMAIL_PASSWORD = "mock_password"
        mock_config.SENDER_NAME = "Tester"
        mock_config.MAX_RETRIES = 1
        mock_config.TRACKING_ENABLED = False

        sender = EmailSender(config=mock_config, db=test_db)

        with patch("smtplib.SMTP", side_effect=ConnectionRefusedError("Connection refused by mock")):
            success = sender.send_email(
                to_email="recipient@mock.com",
                subject="Test Connection Error",
                body="Hello"
            )
            assert success is False

            recent = test_db.get_recent_sent_emails(limit=1)
            assert len(recent) == 1
            assert recent[0]['status'] == "failed"
            assert "Connection refused" in recent[0]['error_message']

# 7. Notification Rule Matching Tests
class TestNotificationRuleMatching:
    def test_rule_subject_and_keyword_match(self, test_db):
        rule_id = test_db.add_notification_rule(
            rule_name="Interview Schedule Alert",
            subject_filter="Interview",
            keyword_filter="technical round",
            condition_logic="AND"
        )
        assert rule_id is not None

        monitor = EmailMonitor(db=test_db)

        matching_email = {
            "sender": "hr@google.com",
            "subject": "Invitation for Google Interview",
            "body_text": "We would like to invite you for a technical round.",
            "body_preview": "technical round"
        }
        matched_rules, actions = monitor.evaluate_rules(matching_email)
        assert "Interview Schedule Alert" in matched_rules
        assert len(actions) == 1

        non_matching_email = {
            "sender": "promo@deals.com",
            "subject": "Discount on Shoes",
            "body_text": "Buy 1 get 1 free today only!",
            "body_preview": "Buy 1 get 1"
        }
        matched_rules2, actions2 = monitor.evaluate_rules(non_matching_email)
        assert len(matched_rules2) == 0
        assert len(actions2) == 0

    def test_rule_or_logic_matching(self, test_db):
        test_db.add_notification_rule(
            rule_name="Urgent Alert",
            subject_filter="urgent",
            keyword_filter="critical",
            condition_logic="OR"
        )

        monitor = EmailMonitor(db=test_db)

        email1 = {"sender": "bot@infra.com", "subject": "Normal alert", "body_text": "A critical issue arose", "body_preview": ""}
        matched1, _ = monitor.evaluate_rules(email1)
        assert "Urgent Alert" in matched1

        email2 = {"sender": "bot@infra.com", "subject": "Urgent notice", "body_text": "Everything is fine", "body_preview": ""}
        matched2, _ = monitor.evaluate_rules(email2)
        assert "Urgent Alert" in matched2
