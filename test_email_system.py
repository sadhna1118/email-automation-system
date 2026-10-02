import pytest
import os
import io
import json
from datetime import datetime

from database import EmailDatabase
from config import Config
from template_engine import TemplateEngine
from validator import EmailValidator
from email_sender import EmailSender
from email_monitor import EmailMonitor
from campaign_engine import CampaignEngine
from fastapi.testclient import TestClient
from api import app

# ----------------- Database Tests ----------------- #

class TestEmailDatabase:
    """Test suite for SQLite Database Layer"""
    
    def setup_method(self):
        self.test_db_path = 'test_aura_emails.db'
        self.db = EmailDatabase(self.test_db_path)
    
    def teardown_method(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_database_initialization(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        expected_tables = [
            'sent_emails', 'monitored_emails', 'notification_rules',
            'contacts', 'contact_lists', 'contact_list_members',
            'templates', 'campaigns', 'campaign_logs', 'scheduled_tasks',
            'activity_logs', 'system_settings'
        ]
        for t in expected_tables:
            assert t in tables

    def test_log_sent_email_and_tracking(self):
        tracking_id = 'test-track-123'
        email_id = self.db.log_sent_email(
            recipient='user@example.com',
            subject='Test Subject',
            status='sent',
            is_html=True,
            tracking_id=tracking_id
        )
        assert email_id is not None
        
        # Test Open Tracking
        self.db.record_open_tracking(tracking_id)
        # Test Click Tracking
        self.db.record_click_tracking(tracking_id)
        
        stats = self.db.get_email_stats()
        assert stats['sent'] == 1
        assert stats['opened'] == 1
        assert stats['clicked'] == 1

    def test_contacts_and_lists(self):
        cid1 = self.db.add_contact('alice@domain.com', name='Alice', company='Acme')
        cid2 = self.db.add_contact('bob@domain.com', name='Bob', company='Beta')
        assert cid1 is not None and cid2 is not None
        
        lid = self.db.create_contact_list('VIP Clients', 'High priority')
        self.db.add_contacts_to_list(lid, [cid1, cid2])
        
        members = self.db.get_contacts_by_list(lid)
        assert len(members) == 2
        assert {m['email'] for m in members} == {'alice@domain.com', 'bob@domain.com'}

    def test_templates_crud(self):
        tid = self.db.save_template(
            name='Test Promo',
            subject_template='Special for {{ name }}',
            body_html='<h1>Hello {{ name }}</h1>',
            category='marketing'
        )
        assert tid is not None
        
        tmpl = self.db.get_template(tid)
        assert tmpl['name'] == 'Test Promo'
        assert tmpl['subject_template'] == 'Special for {{ name }}'
        
        templates = self.db.get_templates(category='marketing')
        assert len(templates) >= 1

    def test_campaign_lifecycle_db(self):
        cid = self.db.create_campaign(name='Black Friday', total_recipients=10)
        assert cid is not None
        
        self.db.update_campaign_progress(cid, sent_delta=5, failed_delta=1)
        camp = self.db.get_campaign(cid)
        assert camp['sent_count'] == 5
        assert camp['failed_count'] == 1
        
        self.db.log_campaign_recipient(cid, 'test@test.com', 'Subj', status='sent', tracking_id='trk-1')
        logs = self.db.get_campaign_logs(cid)
        assert len(logs) == 1

    def test_smart_rules_and_triggers(self):
        rid = self.db.add_notification_rule(
            rule_name='Urgent Invoices',
            subject_filter='invoice',
            keyword_filter='overdue',
            condition_logic='AND',
            action_type='alert'
        )
        assert rid is not None
        
        rules = self.db.get_active_rules()
        assert len(rules) == 1
        
        self.db.increment_rule_trigger(rid)
        all_rules = self.db.get_all_rules()
        assert all_rules[0]['trigger_count'] == 1

# ----------------- Template Engine Tests ----------------- #

class TestTemplateEngine:
    """Test suite for Jinja2 Template Engine and Spam Analyzer"""
    
    def setup_method(self):
        self.engine = TemplateEngine()
    
    def test_render_jinja2(self):
        template = "Hello {{ name }}, welcome to {{ company }}!"
        context = {"name": "David", "company": "TechNova"}
        rendered = self.engine.render_string(template, context)
        assert rendered == "Hello David, welcome to TechNova!"
    
    def test_render_bracket_fallback(self):
        template = "Hi {name}, your code is {code}."
        context = {"name": "Sarah", "code": "9876"}
        rendered = self.engine.render_string(template, context)
        assert rendered == "Hi Sarah, your code is 9876."

    def test_built_in_templates_exist(self):
        assert 'welcome_onboarding' in self.engine.BUILT_IN_TEMPLATES
        assert 'newsletter_announcement' in self.engine.BUILT_IN_TEMPLATES
        assert 'transactional_invoice' in self.engine.BUILT_IN_TEMPLATES
        assert 'system_alert' in self.engine.BUILT_IN_TEMPLATES
        assert len(self.engine.BUILT_IN_TEMPLATES) == 6

    def test_spam_analyzer_clean_email(self):
        subject = "Your Monthly Account Summary & Analytics"
        body = "Hello Alex, here is your performance report for September. You can unsubscribe at any time below."
        analysis = self.engine.analyze_spam_score(subject, body)
        assert analysis['score'] < 30
        assert analysis['status'] == 'safe'

    def test_spam_analyzer_flagged_spam(self):
        subject = "100% FREE CASH BONUS ACT NOW!!!! MAKE MONEY $$$"
        body = "CLICK HERE NOW for guaranteed wealth and double your income! Buy direct with no risk! Call now!"
        analysis = self.engine.analyze_spam_score(subject, body)
        assert analysis['score'] >= 50
        assert len(analysis['found_keywords']) >= 3
        assert analysis['status'] in ('warning', 'danger')

# ----------------- Email Validator Tests ----------------- #

class TestEmailValidator:
    """Test suite for Email and CSV Validator"""
    
    def test_valid_syntax(self):
        assert EmailValidator.is_valid_syntax("user@example.com") is True
        assert EmailValidator.is_valid_syntax("first.last+tag@sub.domain.co.uk") is True
        assert EmailValidator.is_valid_syntax("invalid-email") is False
        assert EmailValidator.is_valid_syntax("@missing-user.com") is False
        assert EmailValidator.is_valid_syntax("missing-at.com") is False

    def test_disposable_detection(self):
        assert EmailValidator.is_disposable("temp@mailinator.com") is True
        assert EmailValidator.is_disposable("temp@10minutemail.com") is True
        assert EmailValidator.is_disposable("real@gmail.com") is False

    def test_csv_parser_normalization_and_dedup(self):
        csv_data = """Full Name,E-mail Address,Company Name
John Doe,john@acme.com,Acme Inc
Jane Smith,jane@tech.org,Tech Corp
Duplicate John,john@acme.com,Acme Inc
Invalid Person,bad-email-format,Bad Co
"""
        result = EmailValidator.parse_csv(csv_data, is_raw_text=True)
        assert len(result['valid_rows']) == 2
        assert len(result['invalid_rows']) == 1
        assert result['duplicates_removed'] == 1
        assert result['valid_rows'][0]['email'] == 'john@acme.com'
        assert result['valid_rows'][0]['name'] == 'John Doe'
        assert result['valid_rows'][0]['company'] == 'Acme Inc'

# ----------------- Email Sender Tests ----------------- #

class TestEmailSender:
    """Test suite for SMTP Email Sender in Dry Run Mode"""
    
    def setup_method(self):
        self.test_db_path = 'test_sender.db'
        self.db = EmailDatabase(self.test_db_path)
        Config.DRY_RUN = True
        self.sender = EmailSender(config=Config, db=self.db)
    
    def teardown_method(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_send_single_dry_run(self):
        ok = self.sender.send_email(
            to_email="recipient@example.com",
            subject="Dry Run Test",
            body="<h1>Hello World</h1>",
            html=True
        )
        assert ok is True
        stats = self.db.get_email_stats()
        assert stats['sent'] == 1

    def test_send_bulk_dry_run(self):
        csv_data = "email,name,company\nuser1@test.com,User One,Co 1\nuser2@test.com,User Two,Co 2\n"
        csv_path = "test_bulk_temp.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_data)
        
        try:
            success, failed = self.sender.send_bulk_emails(
                csv_file=csv_path,
                subject_template="Update for {name}",
                body_template="Hello {name} from {company}",
                html=False
            )
            assert success == 2
            assert failed == 0
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

# ----------------- Email Monitor Tests ----------------- #

class TestEmailMonitor:
    """Test suite for IMAP Monitor Rules Engine and Simulation"""
    
    def setup_method(self):
        self.test_db_path = 'test_monitor.db'
        self.db = EmailDatabase(self.test_db_path)
        Config.DRY_RUN = True
        self.sender = EmailSender(config=Config, db=self.db)
        self.monitor = EmailMonitor(config=Config, db=self.db, sender=self.sender)
    
    def teardown_method(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_rule_evaluation_and_simulation(self):
        self.db.add_notification_rule(
            rule_name="Critical Server Incident",
            sender_filter="ops@company.com",
            subject_filter="outage",
            keyword_filter=None,
            condition_logic="AND",
            action_type="alert"
        )
        
        # Test simulated incoming email
        res = self.monitor.simulate_incoming_email(
            sender="ops@company.com",
            subject="Major outage detected in us-east-1",
            body="Database connectivity degraded."
        )
        
        assert res['id'] is not None
        assert "Critical Server Incident" in res['matched_rules']

# ----------------- FastAPI REST Endpoints Tests ----------------- #

class TestAPIEndpoints:
    """Test suite for FastAPI Web Server & REST API"""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_health_check(self):
        res = self.client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

    def test_stats_endpoint(self):
        res = self.client.get("/api/stats")
        assert res.status_code == 200
        data = res.json()
        assert "sent" in data
        assert "monitored" in data
        assert "delivery_rate" in data

    def test_templates_crud_api(self):
        # Create
        create_res = self.client.post("/api/templates", json={
            "name": "API Test Template",
            "subject_template": "Hello {{ name }}",
            "body_html": "<p>Content</p>",
            "category": "marketing"
        })
        assert create_res.status_code == 200
        tid = create_res.json()["template_id"]
        
        # Read
        get_res = self.client.get(f"/api/templates/{tid}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "API Test Template"
        
        # Delete
        del_res = self.client.delete(f"/api/templates/{tid}")
        assert del_res.status_code == 200

    def test_open_tracking_pixel(self):
        res = self.client.get("/track/open/test-uuid-999")
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/gif"
        assert res.content.startswith(b'GIF89a')
        assert len(res.content) == 42

if __name__ == '__main__':
    pytest.main([__file__, '-v'])