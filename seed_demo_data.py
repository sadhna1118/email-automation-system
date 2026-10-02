import sys
import os

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from database import EmailDatabase
from template_engine import TemplateEngine

def seed():
    print("[+] Seeding demo data into Email Automation Database...")
    db = EmailDatabase()
    
    # 1. Built-in Templates
    for key, tmpl in TemplateEngine.BUILT_IN_TEMPLATES.items():
        db.save_template(
            name=tmpl['name'],
            subject_template=tmpl['subject'],
            body_html=tmpl['body_html'],
            body_text=tmpl['body_text'],
            category=tmpl['category'],
            variables=tmpl['variables']
        )
    print("  [OK] Built-in templates populated (6 high-converting HTML templates)")

    # 2. Contact Lists
    vip_list_id = db.create_contact_list("VIP Enterprise Clients", "Top-tier accounts and key decision makers")
    newsletter_list_id = db.create_contact_list("Product Newsletter Subscribers", "Weekly updates and product announcements")
    leads_list_id = db.create_contact_list("Inbound Marketing Leads", "Downloaded whitepaper or requested demo")
    print("  [OK] Created 3 contact lists / audience segments")

    # 3. Contacts
    contacts_data = [
        ("sarah.connor@acmetech.io", "Sarah Connor", "Acme Technologies", "+1-555-0101", vip_list_id),
        ("alex.chen@innovate.co", "Alex Chen", "Innovate Cloud", "+1-555-0102", vip_list_id),
        ("elena.rostova@quantumscale.ai", "Elena Rostova", "QuantumScale AI", "+1-555-0103", vip_list_id),
        ("marcus.vance@apexprime.net", "Marcus Vance", "Apex Prime", "+1-555-0104", newsletter_list_id),
        ("david.beck@novacorp.com", "David Beck", "Nova Corp", "+1-555-0105", newsletter_list_id),
        ("rachel.adams@globalcorp.org", "Rachel Adams", "Global Corp", "+1-555-0106", newsletter_list_id),
        ("jordan.lee@hyperstream.dev", "Jordan Lee", "HyperStream Dev", "+1-555-0107", leads_list_id),
        ("maya.patel@zenithsystems.io", "Maya Patel", "Zenith Systems", "+1-555-0108", leads_list_id),
        ("sam.wilson@falconsecurity.com", "Sam Wilson", "Falcon Security", "+1-555-0109", leads_list_id),
    ]

    for email, name, company, phone, list_id in contacts_data:
        cid = db.add_contact(email=email, name=name, company=company, phone=phone)
        db.add_contacts_to_list(list_id, [cid])
    print(f"  [OK] Added {len(contacts_data)} contacts across segments")

    # 4. Smart Rules
    db.add_notification_rule(
        rule_name="High-Priority Executive Alert",
        sender_filter="acmetech.io",
        subject_filter="urgent",
        keyword_filter=None,
        condition_logic="AND",
        action_type="alert"
    )
    db.add_notification_rule(
        rule_name="Auto-Reply to Inbound Quotes",
        sender_filter=None,
        subject_filter="quote",
        keyword_filter="pricing",
        condition_logic="OR",
        action_type="auto_reply",
        action_config={"reply_body": "Thank you for requesting a quote. Our team is preparing your custom proposal.", "is_html": False}
    )
    db.add_notification_rule(
        rule_name="Webhook Notification to Discord/Slack",
        sender_filter=None,
        subject_filter="invoice",
        keyword_filter=None,
        condition_logic="OR",
        action_type="webhook",
        action_config={"webhook_url": "https://httpbin.org/post"}
    )
    print("  [OK] Configured 3 smart automation and notification rules")

    # 5. Scheduled Tasks
    db.add_scheduled_task("Periodic Inbox Monitor (Every 5 mins)", "monitor_inbox", "*/5 * * * *", {"interval_minutes": 5})
    db.add_scheduled_task("Weekly Performance Digest (Monday 09:00)", "weekly_report", "0 9 * * 1", {"day": "monday", "time": "09:00"})
    print("  [OK] Registered persistent background scheduled tasks")

    # 6. Sample Monitored Emails & Sent Log
    db.log_monitored_email(
        sender="sarah.connor@acmetech.io",
        subject="Urgent: Contract renewal terms for Q4",
        body_preview="Hi team, could you please review the attached contract addendum?",
        body_text="Hi team, could you please review the attached contract addendum before our Thursday sync?",
        rule_matches=["High-Priority Executive Alert"],
        message_uid="demo-msg-001"
    )
    db.log_monitored_email(
        sender="procurement@globalcorp.org",
        subject="Request for Pricing and Quote Details",
        body_preview="We are interested in licensing AuraMail for 50 users.",
        body_text="We are interested in licensing AuraMail for 50 users. Please send quote breakdown.",
        rule_matches=["Auto-Reply to Inbound Quotes"],
        message_uid="demo-msg-002"
    )

    # 7. Sample Campaigns
    templates = db.get_templates()
    if templates:
        cid = db.create_campaign(
            name="Q3 Product Announcement & Feature Launch",
            template_id=templates[0]['id'],
            contact_list_id=vip_list_id,
            total_recipients=3,
            batch_size=50,
            delay_seconds=0.5
        )
        # Log simulated sends
        db.update_campaign_progress(cid, sent_delta=3, failed_delta=0)
        db.update_campaign_status(cid, 'completed')
        # Log sends into sent_emails table for dashboard, history, and statistics
        conn = db.get_connection()
        sample_sends = [
            ("sarah.connor@acmetech.io", "Q3 Platform Updates & New Security Features", "sent", None, 1, "tr-001", "date('now', '-4 days')"),
            ("alex.chen@innovate.co", "Welcome to AuraMail Automation Platform", "sent", None, 1, "tr-002", "date('now', '-3 days')"),
            ("elena.rostova@quantumscale.ai", "Your API Key and Dashboard Credentials", "sent", None, 1, "tr-003", "date('now', '-2 days')"),
            ("marcus.vance@apexprime.net", "Weekly Automation Digest & Performance Review", "sent", None, 0, "tr-004", "date('now', '-1 days')"),
            ("david.beck@novacorp.com", "Urgent: Complete your Workspace Verification", "failed", "SMTP 550: Mailbox quota exceeded", 0, "tr-005", "date('now', '-1 days')"),
            ("john.doe@example.com", "Hello John Doe, welcome to Acme Corp!", "sent", None, 1, "tr-006", "datetime('now', '-3 hours')"),
            ("jane.smith@example.com", "Hello Jane Smith, welcome to Tech Solutions!", "sent", None, 1, "tr-007", "datetime('now', '-2 hours')"),
            ("bob.johnson@example.com", "Hello Bob Johnson, welcome to Digital Ventures!", "sent", None, 0, "tr-008", "datetime('now', '-30 minutes')"),
        ]
        for recip, subj, stat, err, opn, trk, tm_expr in sample_sends:
            conn.execute(f'''
                INSERT INTO sent_emails (recipient, subject, status, error_message, is_html, tracking_id, opened, sent_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, {tm_expr})
            ''', (recip, subj, stat, err, trk, opn))
        conn.commit()
        conn.close()

        print("  [OK] Populated sent_emails table with initial sample dispatches")

    db.log_activity('system_seeded', "Populated database with demo enterprise dataset.")
    print("[SUCCESS] Demo seeding complete! The platform is primed and ready.")

if __name__ == '__main__':
    seed()
