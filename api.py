import os
import json
import base64
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import Config
from database import EmailDatabase
from email_sender import EmailSender
from email_monitor import EmailMonitor
from template_engine import TemplateEngine
from validator import EmailValidator
from campaign_engine import CampaignEngine
from scheduler import EmailScheduler

# 1x1 Transparent GIF bytes for email open tracking
TRANSPARENT_GIF_BYTES = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")

# Core singletons
db = EmailDatabase()
sender = EmailSender(config=Config, db=db)
monitor = EmailMonitor(config=Config, db=db, sender=sender)
template_engine = TemplateEngine()
campaign_engine = CampaignEngine(config=Config, db=db, sender=sender)
scheduler = EmailScheduler(config=Config, db=db, sender=sender, monitor=monitor)

# Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    existing = db.get_templates()
    if not existing:
        for key, tmpl in TemplateEngine.BUILT_IN_TEMPLATES.items():
            db.save_template(
                name=tmpl['name'],
                subject_template=tmpl['subject'],
                body_html=tmpl['body_html'],
                body_text=tmpl['body_text'],
                category=tmpl['category'],
                variables=tmpl['variables']
            )
    scheduler.start_background()
    yield
    # Shutdown
    scheduler.stop_background()
    monitor.stop_background_daemon()

app = FastAPI(
    title="Email Automation & Intelligence Platform API",
    description="Enterprise REST API for Bulk Sending, IMAP Monitoring, Template Studio, and Analytics",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for local development and integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Pydantic Models ----------------- #

class SendSingleRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    html: bool = False
    cc: Optional[str] = None
    bcc: Optional[str] = None
    reply_to: Optional[str] = None

class TemplateCreateRequest(BaseModel):
    name: str
    subject_template: str
    body_html: str
    body_text: Optional[str] = None
    category: str = "general"
    variables: Optional[List[str]] = None

class TemplatePreviewRequest(BaseModel):
    subject_template: str
    body_html: str
    context: Optional[dict] = None

class SpamCheckRequest(BaseModel):
    subject: str
    body: str

class ContactCreateRequest(BaseModel):
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[List[str]] = None
    list_id: Optional[int] = None

class ContactListCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class CampaignCreateRequest(BaseModel):
    name: str
    template_id: int
    contact_list_id: int
    batch_size: int = 50
    delay_seconds: float = 1.0

class RuleCreateRequest(BaseModel):
    rule_name: str
    sender_filter: Optional[str] = None
    subject_filter: Optional[str] = None
    keyword_filter: Optional[str] = None
    condition_logic: str = "AND"
    action_type: str = "alert"
    action_config: Optional[dict] = None

class SettingsUpdateRequest(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_use_ssl: bool = False
    smtp_use_tls: bool = True
    imap_server: str
    imap_port: int
    imap_use_ssl: bool = True
    email_address: str
    email_password: Optional[str] = None
    sender_name: Optional[str] = None
    notification_email: Optional[str] = None
    dry_run: bool = True
    rate_limit_delay: float = 1.0
    batch_size: int = 50
    tracking_enabled: bool = True
    webhook_url: Optional[str] = None

class SimulateIncomingRequest(BaseModel):
    sender: str
    subject: str
    body: str

# ----------------- Dashboard & Analytics ----------------- #

@app.get("/api/stats")
def get_stats():
    """Get system-wide analytics, counts, and 7-day volume trends"""
    stats = db.get_email_stats()
    stats['monitor_running'] = monitor.is_running()
    stats['dry_run'] = Config.DRY_RUN
    return stats

@app.get("/api/activities")
def get_activities(limit: int = 30):
    """Get recent system audit logs"""
    return db.get_activity_logs(limit=limit)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": Config.to_dict(),
        "monitor_running": monitor.is_running()
    }

# ----------------- Composer & Single Send ----------------- #

@app.post("/api/send-single")
def send_single(req: SendSingleRequest):
    """Send a single email message with validation and tracking"""
    cc_list = [c.strip() for c in req.cc.split(',')] if req.cc else None
    bcc_list = [b.strip() for b in req.bcc.split(',')] if req.bcc else None
    
    success = sender.send_email(
        to_email=req.to_email,
        subject=req.subject,
        body=req.body,
        html=req.html,
        cc=cc_list,
        bcc=bcc_list,
        reply_to=req.reply_to
    )
    
    if success:
        db.log_activity('single_email_sent', f"Sent email to {req.to_email}: {req.subject}")
        return {"success": True, "message": f"Email sent successfully to {req.to_email}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to send email. Check SMTP logs.")

# ----------------- Templates & Spam Studio ----------------- #

@app.get("/api/templates")
def list_templates(category: Optional[str] = None):
    return db.get_templates(category=category)

@app.get("/api/templates/{template_id}")
def get_template(template_id: int):
    t = db.get_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t

@app.post("/api/templates")
def save_template(req: TemplateCreateRequest):
    tid = db.save_template(
        name=req.name,
        subject_template=req.subject_template,
        body_html=req.body_html,
        body_text=req.body_text,
        category=req.category,
        variables=req.variables
    )
    db.log_activity('template_saved', f"Saved template '{req.name}'")
    return {"success": True, "template_id": tid, "message": "Template saved successfully"}

@app.delete("/api/templates/{template_id}")
def delete_template(template_id: int):
    db.delete_template(template_id)
    db.log_activity('template_deleted', f"Deleted template #{template_id}")
    return {"success": True, "message": "Template deleted"}

@app.post("/api/templates/preview")
def preview_template(req: TemplatePreviewRequest):
    sample_context = {
        'name': 'Alex Johnson',
        'email': 'alex@example.com',
        'company': 'Acme Corporation',
        'login_url': f"{Config.BASE_URL}",
        'support_email': Config.NOTIFICATION_EMAIL or 'support@example.com',
        'unsubscribe_url': f"{Config.BASE_URL}/unsubscribe?email=alex@example.com",
        'update_title': 'AI Automation Engine 2.0 Live',
        'update_description': 'Experience blazing fast email workflows with real-time analytics.',
        'invoice_number': 'INV-2026-894',
        'amount': '129.00',
        'date': 'September 02, 2026',
        'item_description': 'Enterprise Automation Plan',
        'alert_title': 'High Priority Server Trigger',
        'severity': 'HIGH',
        'timestamp': '2026-09-02 21:00 UTC',
        'details': 'Condition rule match triggered immediate notification.',
        'event_title': 'Live Deliverability & Workflow Masterclass',
        'speaker': 'Engineering Leadership',
        'date_time': 'Thursday, Sep 10 at 2:00 PM EST'
    }
    if req.context:
        sample_context.update(req.context)
        
    rendered_subject = template_engine.render_string(req.subject_template, sample_context)
    rendered_html = template_engine.render_string(req.body_html, sample_context)
    return {
        "subject": rendered_subject,
        "html": rendered_html
    }

@app.post("/api/templates/spam-check")
def analyze_spam(req: SpamCheckRequest):
    return template_engine.analyze_spam_score(req.subject, req.body)

# ----------------- Contacts & CSV Manager ----------------- #

@app.get("/api/contacts")
def list_contacts(search: Optional[str] = None, status: str = "active", limit: int = 100, offset: int = 0):
    contacts = db.get_contacts(search=search, status=status, limit=limit, offset=offset)
    total = db.count_contacts(status=status)
    return {"contacts": contacts, "total": total}

@app.post("/api/contacts")
def create_contact(req: ContactCreateRequest):
    cid = db.add_contact(
        email=req.email,
        name=req.name,
        company=req.company,
        phone=req.phone,
        tags=req.tags
    )
    if req.list_id:
        db.add_contacts_to_list(req.list_id, [cid])
    return {"success": True, "contact_id": cid, "message": "Contact added"}

@app.get("/api/contact-lists")
def list_contact_lists():
    return db.get_contact_lists()

@app.post("/api/contact-lists")
def create_contact_list(req: ContactListCreateRequest):
    lid = db.create_contact_list(name=req.name, description=req.description)
    return {"success": True, "list_id": lid, "message": "Contact list created"}

@app.post("/api/contacts/import-csv")
async def import_csv(file: UploadFile = File(...), list_name: Optional[str] = Form(None), target_list_id: Optional[int] = Form(None)):
    """Upload and parse CSV, save contacts, and optionally attach to list"""
    content = await file.read()
    text = content.decode('utf-8-sig', errors='ignore')
    
    parsed = EmailValidator.parse_csv(text, is_raw_text=True)
    if 'error' in parsed:
        raise HTTPException(status_code=400, detail=parsed['error'])
    
    list_id = target_list_id
    if not list_id and list_name:
        list_id = db.create_contact_list(list_name, description=f"Imported from {file.filename}")
    
    added_ids = []
    for row in parsed['valid_rows']:
        cid = db.add_contact(
            email=row['email'],
            name=row.get('name'),
            company=row.get('company'),
            phone=row.get('phone')
        )
        if cid:
            added_ids.append(cid)
    
    if list_id and added_ids:
        db.add_contacts_to_list(list_id, added_ids)
    
    db.log_activity('csv_imported', f"Imported {len(added_ids)} contacts from '{file.filename}'", {
        'total_rows': parsed['total_rows'],
        'duplicates_removed': parsed['duplicates_removed'],
        'invalid_rows_count': len(parsed['invalid_rows'])
    })
    
    return {
        "success": True,
        "valid_count": len(added_ids),
        "invalid_count": len(parsed['invalid_rows']),
        "duplicates_removed": parsed['duplicates_removed'],
        "invalid_rows": parsed['invalid_rows'][:20],
        "list_id": list_id
    }

# ----------------- Campaign Manager ----------------- #

@app.get("/api/campaigns")
def list_campaigns():
    return db.get_campaigns()

@app.get("/api/campaigns/{campaign_id}")
def get_campaign(campaign_id: int):
    c = db.get_campaign(campaign_id)
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return c

@app.get("/api/campaigns/{campaign_id}/logs")
def get_campaign_logs(campaign_id: int, limit: int = 100):
    return db.get_campaign_logs(campaign_id, limit=limit)

@app.post("/api/campaigns")
def create_campaign(req: CampaignCreateRequest):
    cid = db.create_campaign(
        name=req.name,
        template_id=req.template_id,
        contact_list_id=req.contact_list_id,
        batch_size=req.batch_size,
        delay_seconds=req.delay_seconds
    )
    db.log_activity('campaign_created', f"Created campaign '{req.name}'")
    return {"success": True, "campaign_id": cid, "message": "Campaign created successfully"}

@app.post("/api/campaigns/{campaign_id}/start")
def start_campaign(campaign_id: int):
    res = campaign_engine.start_campaign(campaign_id)
    if not res['success']:
        raise HTTPException(status_code=400, detail=res['message'])
    return res

@app.post("/api/campaigns/{campaign_id}/pause")
def pause_campaign(campaign_id: int):
    res = campaign_engine.pause_campaign(campaign_id)
    return res

@app.post("/api/campaigns/{campaign_id}/resume")
def resume_campaign(campaign_id: int):
    res = campaign_engine.resume_campaign(campaign_id)
    return res

@app.post("/api/campaigns/{campaign_id}/cancel")
def cancel_campaign(campaign_id: int):
    res = campaign_engine.cancel_campaign(campaign_id)
    return res

# ----------------- Inbox & Smart Rules ----------------- #

@app.get("/api/inbox")
def get_inbox_emails(limit: int = 50):
    return db.get_monitored_emails(limit=limit)

@app.post("/api/inbox/check-now")
def check_inbox_now():
    """Trigger immediate IMAP check"""
    count = monitor.monitor_inbox()
    return {"success": True, "processed_count": count, "message": f"Processed {count} new emails"}

@app.post("/api/inbox/simulate")
def simulate_email(req: SimulateIncomingRequest):
    """Simulate an incoming email for testing rules and auto-replies"""
    res = monitor.simulate_incoming_email(req.sender, req.subject, req.body)
    return {"success": True, "details": res}

@app.get("/api/rules")
def list_rules():
    return db.get_all_rules()

@app.post("/api/rules")
def add_rule(req: RuleCreateRequest):
    rid = db.add_notification_rule(
        rule_name=req.rule_name,
        sender_filter=req.sender_filter,
        subject_filter=req.subject_filter,
        keyword_filter=req.keyword_filter,
        condition_logic=req.condition_logic,
        action_type=req.action_type,
        action_config=req.action_config
    )
    db.log_activity('rule_created', f"Created rule '{req.rule_name}'")
    return {"success": True, "rule_id": rid, "message": "Notification rule added"}

@app.post("/api/rules/{rule_id}/toggle")
def toggle_rule(rule_id: int):
    db.toggle_rule(rule_id)
    return {"success": True, "message": "Rule toggled"}

@app.delete("/api/rules/{rule_id}")
def delete_rule(rule_id: int):
    db.delete_rule(rule_id)
    db.log_activity('rule_deleted', f"Deleted rule #{rule_id}")
    return {"success": True, "message": "Rule deleted"}

# ----------------- Scheduler Endpoints ----------------- #

@app.get("/api/scheduler")
def list_schedules():
    return db.get_scheduled_tasks()

@app.post("/api/scheduler")
def add_schedule(task_name: str = Form(...), task_type: str = Form(...), schedule_expr: str = Form(...), params: Optional[str] = Form(None)):
    parsed_params = json.loads(params) if params else None
    tid = db.add_scheduled_task(task_name, task_type, schedule_expr, parsed_params)
    return {"success": True, "task_id": tid, "message": "Scheduled task added"}

@app.post("/api/scheduler/{task_id}/toggle")
def toggle_schedule(task_id: int):
    db.toggle_scheduled_task(task_id)
    return {"success": True, "message": "Task toggled"}

# ----------------- Settings & Diagnostics ----------------- #

@app.get("/api/settings")
def get_settings():
    return Config.to_dict()

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    Config.SMTP_SERVER = req.smtp_server
    Config.SMTP_PORT = req.smtp_port
    Config.SMTP_USE_SSL = req.smtp_use_ssl
    Config.SMTP_USE_TLS = req.smtp_use_tls
    Config.IMAP_SERVER = req.imap_server
    Config.IMAP_PORT = req.imap_port
    Config.IMAP_USE_SSL = req.imap_use_ssl
    Config.EMAIL_ADDRESS = req.email_address
    if req.email_password:
        Config.EMAIL_PASSWORD = req.email_password
    Config.SENDER_NAME = req.sender_name or Config.SENDER_NAME
    Config.NOTIFICATION_EMAIL = req.notification_email or Config.NOTIFICATION_EMAIL
    Config.DRY_RUN = req.dry_run
    Config.RATE_LIMIT_DELAY = req.rate_limit_delay
    Config.BATCH_SIZE = req.batch_size
    Config.TRACKING_ENABLED = req.tracking_enabled
    Config.WEBHOOK_URL = req.webhook_url or Config.WEBHOOK_URL
    
    db.log_activity('settings_updated', "System configuration settings updated")
    return {"success": True, "message": "Settings updated successfully", "settings": Config.to_dict()}

@app.post("/api/settings/test-smtp")
def test_smtp():
    return sender.test_connection()

@app.post("/api/settings/test-imap")
def test_imap():
    return monitor.test_connection()

# ----------------- Tracking & Unsubscribe Endpoints ----------------- #

@app.get("/track/open/{tracking_id}")
def track_open(tracking_id: str):
    """Open tracking transparent 1x1 GIF"""
    db.record_open_tracking(tracking_id)
    return Response(content=TRANSPARENT_GIF_BYTES, media_type="image/gif")

@app.get("/track/click/{tracking_id}")
def track_click(tracking_id: str, url: str = Query(...)):
    """Click tracking redirect endpoint"""
    db.record_click_tracking(tracking_id)
    return RedirectResponse(url=url, status_code=302)

@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_page(email: Optional[str] = None):
    """User-facing unsubscribe confirmation page"""
    if email:
        db.unsubscribe_contact(email)
        db.log_activity('contact_unsubscribed', f"Contact '{email}' clicked unsubscribe.")
    
    email_display = email or "your email address"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Unsubscribed Successfully</title>
  <style>
    body {{ background: #0f172a; color: #f8fafc; font-family: system-ui, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 40px; text-align: center; max-width: 480px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
    h1 {{ color: #10b981; font-size: 24px; margin-bottom: 12px; }}
    p {{ color: #94a3b8; line-height: 1.6; }}
    .badge {{ background: #0f172a; border: 1px solid #334155; padding: 6px 14px; border-radius: 6px; color: #cbd5e1; font-family: monospace; display: inline-block; margin: 10px 0; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>✓ Unsubscribed</h1>
    <p>You have been successfully removed from our mailing list for:</p>
    <div class="badge">{email_display}</div>
    <p>You will no longer receive marketing or campaign emails from this sender.</p>
  </div>
</body>
</html>"""

# ----------------- Static Frontend Mounting ----------------- #

web_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    def serve_dashboard():
        index_file = os.path.join(web_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                return f.read()
        return "<h1>Dashboard is loading...</h1>"
