import threading
import time
import uuid
from datetime import datetime
from urllib.parse import quote

from config import Config
from database import EmailDatabase
from email_sender import EmailSender
from template_engine import TemplateEngine

class CampaignEngine:
    """Enterprise Campaign Execution Engine with background workers, live throttling, and pause/resume"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CampaignEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config=None, db=None, sender=None):
        if getattr(self, '_initialized', False):
            return
        self.config = config or Config
        self.db = db or EmailDatabase()
        self.sender = sender or EmailSender(config=self.config, db=self.db)
        self.template_engine = TemplateEngine()
        
        # State tracking: campaign_id -> { 'status': 'running'|'paused'|'stopped', 'thread': Thread, 'pause_event': Event }
        self._active_campaigns = {}
        self._lock = threading.Lock()
        self._initialized = True
    
    def start_campaign(self, campaign_id: int) -> dict:
        """Start or resume campaign execution in a dedicated background worker"""
        with self._lock:
            campaign = self.db.get_campaign(campaign_id)
            if not campaign:
                return {'success': False, 'message': f'Campaign #{campaign_id} not found'}
            
            if campaign_id in self._active_campaigns:
                entry = self._active_campaigns[campaign_id]
                if entry['status'] == 'running':
                    return {'success': False, 'message': 'Campaign is already running'}
                elif entry['status'] == 'paused':
                    entry['status'] = 'running'
                    entry['pause_event'].set()
                    self.db.update_campaign_status(campaign_id, 'running')
                    return {'success': True, 'message': 'Campaign resumed successfully'}
            
            # Fetch template
            template = None
            if campaign.get('template_id'):
                template = self.db.get_template(campaign['template_id'])
            
            # Fetch recipients
            recipients = []
            if campaign.get('contact_list_id'):
                recipients = self.db.get_contacts_by_list(campaign['contact_list_id'])
            
            if not recipients:
                return {'success': False, 'message': 'No active recipients found in selected contact list'}
            
            pause_event = threading.Event()
            pause_event.set()  # Not paused initially
            
            state_entry = {
                'status': 'running',
                'pause_event': pause_event,
                'stop_requested': False
            }
            self._active_campaigns[campaign_id] = state_entry
            
            # Update total count if not set
            conn = self.db.get_connection()
            conn.execute('UPDATE campaigns SET total_recipients = ? WHERE id = ?', (len(recipients), campaign_id))
            conn.commit()
            conn.close()
            
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.update_campaign_status(campaign_id, 'running', started_at=now_str)
            self.db.log_activity('campaign_started', f"Campaign '{campaign['name']}' started with {len(recipients)} recipients.")
            
            # Start background thread
            worker = threading.Thread(
                target=self._run_campaign_worker,
                args=(campaign_id, campaign, template, recipients, state_entry),
                daemon=True
            )
            state_entry['thread'] = worker
            worker.start()
            
            return {'success': True, 'message': f"Campaign #{campaign_id} started in background"}

    def pause_campaign(self, campaign_id: int) -> dict:
        """Pause a running campaign"""
        with self._lock:
            if campaign_id in self._active_campaigns:
                entry = self._active_campaigns[campaign_id]
                if entry['status'] == 'running':
                    entry['status'] = 'paused'
                    entry['pause_event'].clear()
                    self.db.update_campaign_status(campaign_id, 'paused')
                    self.db.log_activity('campaign_paused', f"Campaign #{campaign_id} paused by user.")
                    return {'success': True, 'message': 'Campaign paused'}
            return {'success': False, 'message': 'Campaign is not currently running'}

    def resume_campaign(self, campaign_id: int) -> dict:
        """Resume a paused campaign"""
        return self.start_campaign(campaign_id)

    def cancel_campaign(self, campaign_id: int) -> dict:
        """Cancel and stop a campaign"""
        with self._lock:
            if campaign_id in self._active_campaigns:
                entry = self._active_campaigns[campaign_id]
                entry['stop_requested'] = True
                entry['pause_event'].set()  # Unblock if paused so it can exit
                self.db.update_campaign_status(campaign_id, 'cancelled')
                self.db.log_activity('campaign_cancelled', f"Campaign #{campaign_id} cancelled.")
                return {'success': True, 'message': 'Campaign cancellation requested'}
            else:
                self.db.update_campaign_status(campaign_id, 'cancelled')
                return {'success': True, 'message': 'Campaign marked as cancelled'}

    def _run_campaign_worker(self, campaign_id, campaign_meta, template, recipients, state_entry):
        """Worker thread processing each recipient with rate-limiting and pausing"""
        subj_tmpl = template['subject_template'] if template else "Important Update"
        body_tmpl = template['body_html'] if template else "<p>Hello {{ name }},</p><p>We have an update for you.</p>"
        is_html = bool(template and template.get('body_html'))
        
        delay = float(campaign_meta.get('delay_seconds') or self.config.RATE_LIMIT_DELAY)
        batch_size = int(campaign_meta.get('batch_size') or self.config.BATCH_SIZE)
        
        # Check already sent recipients for this campaign to prevent duplicate sends on resume
        existing_logs = self.db.get_campaign_logs(campaign_id, limit=10000)
        sent_emails_set = {log['recipient'].lower() for log in existing_logs if log['status'] == 'sent'}
        
        # Persistent SMTP session for live mode
        server_session = None
        if not self.config.DRY_RUN:
            try:
                server_session = self.sender.connect()
            except Exception as e:
                print(f"[Campaign SMTP Error] Failed to connect: {e}")
        
        try:
            processed_count = 0
            for idx, contact in enumerate(recipients, start=1):
                # 1. Check if stop was requested
                if state_entry.get('stop_requested'):
                    print(f"[Campaign Worker] Campaign #{campaign_id} stopping per user request.")
                    break
                
                # 2. Check if paused
                state_entry['pause_event'].wait()
                if state_entry.get('stop_requested'):
                    break
                
                email_addr = contact['email'].strip().lower()
                
                # Skip if already sent or contact unsubscribed
                if email_addr in sent_emails_set or contact.get('status') == 'unsubscribed':
                    continue
                
                processed_count += 1
                tracking_id = str(uuid.uuid4())
                
                # Build context
                context = {
                    'email': email_addr,
                    'name': contact.get('name') or 'Customer',
                    'company': contact.get('company') or '',
                    'phone': contact.get('phone') or '',
                    'unsubscribe_url': f"{self.config.BASE_URL.rstrip('/')}/unsubscribe?email={quote(email_addr)}"
                }
                
                # Render personalized content
                personalized_subject = self.template_engine.render_string(subj_tmpl, context)
                personalized_body = self.template_engine.render_string(body_tmpl, context)
                
                # Send
                success = self.sender.send_email(
                    to_email=email_addr,
                    subject=personalized_subject,
                    body=personalized_body,
                    html=is_html,
                    tracking_id=tracking_id,
                    server_session=server_session
                )
                
                # Update progress & log recipient
                if success:
                    self.db.update_campaign_progress(campaign_id, sent_delta=1, failed_delta=0)
                    self.db.log_campaign_recipient(
                        campaign_id=campaign_id,
                        recipient=email_addr,
                        subject=personalized_subject,
                        status='sent',
                        tracking_id=tracking_id
                    )
                else:
                    self.db.update_campaign_progress(campaign_id, sent_delta=0, failed_delta=1)
                    self.db.log_campaign_recipient(
                        campaign_id=campaign_id,
                        recipient=email_addr,
                        subject=personalized_subject,
                        status='failed',
                        error_message='SMTP transmission failed',
                        tracking_id=tracking_id
                    )
                
                # Rate Limiting & Throttling
                if idx < len(recipients):
                    time.sleep(delay)
                    if batch_size > 0 and processed_count % batch_size == 0:
                        print(f"[Campaign Batch Pause] Pausing {self.config.BATCH_DELAY}s after batch of {batch_size}...")
                        time.sleep(self.config.BATCH_DELAY)
            
            # Completion
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            final_status = 'cancelled' if state_entry.get('stop_requested') else 'completed'
            self.db.update_campaign_status(campaign_id, final_status, completed_at=now_str)
            self.db.log_activity('campaign_finished', f"Campaign #{campaign_id} finished with status: {final_status}")
            
        finally:
            if server_session:
                try:
                    server_session.quit()
                except:
                    pass
            with self._lock:
                self._active_campaigns.pop(campaign_id, None)
