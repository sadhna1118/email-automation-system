import re
from jinja2 import Environment, BaseLoader, TemplateSyntaxError

class TemplateEngine:
    """Enterprise Template Engine with Jinja2 support, Pre-built HTML templates, and Spam Analyzer"""
    
    # 6 Built-in High-Converting Responsive HTML Templates
    BUILT_IN_TEMPLATES = {
        'welcome_onboarding': {
            'name': 'Modern SaaS Welcome & Onboarding',
            'category': 'onboarding',
            'subject': 'Welcome to {{ company|default("our platform") }}, {{ name|default("there") }}! 🚀',
            'variables': ['name', 'company', 'login_url', 'support_email', 'unsubscribe_url'],
            'body_html': """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to {{ company|default('Our Platform') }}</title>
  <style>
    body { margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0; }
    .wrapper { width: 100%; max-width: 600px; margin: 40px auto; background: #1e293b; border-radius: 16px; overflow: hidden; border: 1px solid #334155; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }
    .header { background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); padding: 40px 30px; text-align: center; }
    .header h1 { margin: 0; font-size: 28px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
    .content { padding: 36px 30px; line-height: 1.6; }
    .content h2 { color: #f8fafc; font-size: 20px; margin-top: 0; }
    .content p { color: #cbd5e1; font-size: 15px; margin-bottom: 20px; }
    .feature-card { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 16px 20px; margin-bottom: 14px; }
    .feature-title { font-weight: 600; color: #818cf8; font-size: 15px; margin-bottom: 4px; }
    .feature-desc { color: #94a3b8; font-size: 13px; margin: 0; }
    .cta-container { text-align: center; margin: 35px 0 20px; }
    .cta-button { display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: #ffffff !important; font-weight: 700; font-size: 15px; text-decoration: none; padding: 14px 34px; border-radius: 8px; box-shadow: 0 4px 14px rgba(99,102,241,0.4); }
    .footer { background: #0f172a; padding: 24px 30px; text-align: center; border-top: 1px solid #334155; }
    .footer p { color: #64748b; font-size: 12px; margin: 6px 0; }
    .footer a { color: #818cf8; text-decoration: none; }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>🚀 Welcome aboard, {{ name|default('Friend') }}!</h1>
    </div>
    <div class="content">
      <h2>We're thrilled to have you with us at {{ company|default('our team') }}.</h2>
      <p>Your account is ready and activated. To help you get the absolute most out of our automation tools, we've prepared 3 quick steps to get you up and running in minutes:</p>
      
      <div class="feature-card">
        <div class="feature-title">1. Connect Your Inbox</div>
        <div class="feature-desc">Configure SMTP & IMAP credentials to start sending and monitoring messages.</div>
      </div>
      
      <div class="feature-card">
        <div class="feature-title">2. Set Up Smart Notification Rules</div>
        <div class="feature-desc">Receive real-time alerts or trigger automated workflows when key emails arrive.</div>
      </div>
      
      <div class="feature-card">
        <div class="feature-title">3. Launch Your First Campaign</div>
        <div class="feature-desc">Import your audience CSV and send personalized high-converting campaigns.</div>
      </div>
      
      <div class="cta-container">
        <a href="{{ login_url|default('http://localhost:8000') }}" class="cta-button">Go to Your Dashboard &rarr;</a>
      </div>
      
      <p style="font-size: 13px; color: #94a3b8; text-align: center;">Have questions? Reach us anytime at <a href="mailto:{{ support_email|default('support@example.com') }}" style="color: #818cf8;">{{ support_email|default('support@example.com') }}</a></p>
    </div>
    <div class="footer">
      <p>&copy; 2026 {{ company|default('Email Automation System') }}. All rights reserved.</p>
      <p><a href="{{ unsubscribe_url|default('#') }}">Unsubscribe</a> &bull; <a href="#">Privacy Policy</a> &bull; <a href="#">Security</a></p>
    </div>
  </div>
</body>
</html>""",
            'body_text': """Welcome aboard, {{ name|default('Friend') }}!

We're thrilled to have you with us at {{ company|default('our team') }}.

Here are 3 quick steps to get started:
1. Connect Your Inbox (Configure SMTP & IMAP credentials)
2. Set Up Smart Notification Rules
3. Launch Your First Campaign

Visit your dashboard: {{ login_url|default('http://localhost:8000') }}
Support: {{ support_email|default('support@example.com') }}

To unsubscribe, visit: {{ unsubscribe_url|default('#') }}"""
        },

        'newsletter_announcement': {
            'name': 'Product Update & Newsletter',
            'category': 'marketing',
            'subject': '✨ Major Updates & New Features for {{ name|default("You") }}',
            'variables': ['name', 'company', 'update_title', 'update_description', 'cta_url', 'unsubscribe_url'],
            'body_html': """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Product Announcement</title>
  <style>
    body { margin: 0; padding: 0; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #f1f5f9; }
    .container { max-width: 600px; margin: 30px auto; background: #111827; border-radius: 16px; border: 1px solid #1f2937; overflow: hidden; }
    .badge { display: inline-block; padding: 4px 12px; background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 9999px; font-size: 12px; font-weight: 600; margin-bottom: 12px; }
    .hero { padding: 40px 30px 20px; text-align: center; }
    .hero h1 { font-size: 26px; color: #ffffff; margin: 0 0 12px; font-weight: 800; }
    .hero p { color: #9ca3af; font-size: 16px; margin: 0; }
    .body-content { padding: 20px 30px 30px; }
    .highlight-box { background: #1f2937; border-left: 4px solid #3b82f6; padding: 20px; border-radius: 0 10px 10px 0; margin: 24px 0; }
    .cta-btn { display: inline-block; background: #2563eb; color: #ffffff !important; padding: 14px 30px; border-radius: 8px; font-weight: 600; text-decoration: none; }
    .footer { padding: 20px; text-align: center; color: #6b7280; font-size: 12px; border-top: 1px solid #1f2937; }
  </style>
</head>
<body>
  <div class="container">
    <div class="hero">
      <div class="badge">PRODUCT ANNOUNCEMENT</div>
      <h1>{{ update_title|default('Exciting New Enhancements Are Live') }}</h1>
      <p>Hello {{ name|default('Valued Customer') }}, check out what we just shipped for you.</p>
    </div>
    <div class="body-content">
      <div class="highlight-box">
        <h3 style="margin-top:0; color:#60a5fa;">What's New in This Release</h3>
        <p style="color:#d1d5db; font-size:14px; margin:0;">{{ update_description|default('We have upgraded our platform with AI-powered analytics, high-speed bulk sending engines, and real-time inbox rule triggers.') }}</p>
      </div>
      <div style="text-align: center; margin: 30px 0;">
        <a href="{{ cta_url|default('http://localhost:8000') }}" class="cta-btn">Explore Features Now &rarr;</a>
      </div>
    </div>
    <div class="footer">
      <p>Sent to {{ name|default('you') }} because you subscribed to updates from {{ company|default('our platform') }}.</p>
      <p><a href="{{ unsubscribe_url|default('#') }}" style="color:#9ca3af;">Unsubscribe</a></p>
    </div>
  </div>
</body>
</html>""",
            'body_text': """Product Announcement: {{ update_title|default('Exciting New Enhancements Are Live') }}

Hello {{ name|default('Valued Customer') }},

{{ update_description|default('We have upgraded our platform with AI-powered analytics, high-speed bulk sending engines, and real-time inbox rule triggers.') }}

Explore the updates: {{ cta_url|default('http://localhost:8000') }}

Unsubscribe: {{ unsubscribe_url|default('#') }}"""
        },

        'transactional_invoice': {
            'name': 'Transactional Invoice / Receipt',
            'category': 'transactional',
            'subject': 'Receipt #{{ invoice_number|default("INV-2026-001") }} from {{ company|default("Our Service") }}',
            'variables': ['name', 'company', 'invoice_number', 'amount', 'date', 'item_description', 'download_url'],
            'body_html': """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Payment Receipt</title>
  <style>
    body { background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1e293b; margin: 0; padding: 20px; }
    .box { max-width: 580px; margin: auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 36px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .receipt-header { display: flex; justify-content: space-between; border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; }
    .table { width: 100%; border-collapse: collapse; margin: 24px 0; }
    .table th { text-align: left; padding: 10px; background: #f8fafc; color: #64748b; font-size: 13px; text-transform: uppercase; }
    .table td { padding: 14px 10px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }
    .total-row td { font-weight: 700; font-size: 16px; color: #0f172a; border-top: 2px solid #e2e8f0; }
    .btn { display: inline-block; background: #0f172a; color: #ffffff !important; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 600; }
  </style>
</head>
<body>
  <div class="box">
    <div style="text-align: center; margin-bottom: 20px;">
      <h2 style="margin: 0; color: #0f172a;">Payment Confirmation</h2>
      <p style="color: #64748b; font-size: 14px; margin: 4px 0 0;">Invoice #{{ invoice_number|default('INV-2026-001') }}</p>
    </div>
    <p>Hi {{ name|default('Customer') }},</p>
    <p style="color: #475569; font-size: 14px;">Thank you for your payment. Here is the receipt for your recent transaction on {{ date|default('Today') }}:</p>
    <table class="table">
      <thead>
        <tr>
          <th>Description</th>
          <th style="text-align: right;">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ item_description|default('Pro Automation Subscription - Monthly') }}</td>
          <td style="text-align: right;">${{ amount|default('49.00') }}</td>
        </tr>
        <tr class="total-row">
          <td>Total Paid</td>
          <td style="text-align: right;">${{ amount|default('49.00') }}</td>
        </tr>
      </tbody>
    </table>
    <div style="text-align: center; margin-top: 28px;">
      <a href="{{ download_url|default('#') }}" class="btn">Download PDF Receipt</a>
    </div>
    <p style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 30px;">{{ company|default('Email Automation System') }} &bull; Billing Support</p>
  </div>
</body>
</html>""",
            'body_text': """Payment Receipt: Invoice #{{ invoice_number|default('INV-2026-001') }}

Hi {{ name|default('Customer') }},

Thank you for your payment.
Item: {{ item_description|default('Pro Automation Subscription') }}
Total Paid: ${{ amount|default('49.00') }}
Date: {{ date|default('Today') }}

Download receipt: {{ download_url|default('#') }}"""
        },

        'system_alert': {
            'name': 'Critical Incident / System Alert',
            'category': 'alerts',
            'subject': '🚨 ALERT: {{ alert_title|default("System Event Triggered") }}',
            'variables': ['name', 'alert_title', 'severity', 'timestamp', 'details', 'action_url'],
            'body_html': """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>System Alert</title>
  <style>
    body { background-color: #18181b; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #f4f4f5; margin: 0; padding: 20px; }
    .card { max-width: 560px; margin: auto; background: #27272a; border-radius: 12px; border: 1px solid #ef4444; overflow: hidden; }
    .banner { background: #ef4444; color: #ffffff; padding: 18px 24px; font-weight: 700; font-size: 18px; }
    .body { padding: 24px; font-size: 14px; line-height: 1.6; }
    .metric-grid { background: #18181b; border: 1px solid #3f3f46; border-radius: 8px; padding: 14px; margin: 16px 0; }
    .metric-row { display: flex; justify-content: space-between; margin-bottom: 6px; }
    .metric-label { color: #a1a1aa; }
    .metric-val { color: #ffffff; font-weight: 600; }
    .action-btn { display: inline-block; background: #ef4444; color: #ffffff !important; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <div class="banner">⚠️ System Notification: {{ alert_title|default('High Priority Trigger') }}</div>
    <div class="body">
      <p>Hello {{ name|default('Administrator') }},</p>
      <p>Our automated monitoring system detected the following condition:</p>
      <div class="metric-grid">
        <div class="metric-row"><span class="metric-label">Severity:</span> <span class="metric-val" style="color:#ef4444;">{{ severity|default('HIGH') }}</span></div>
        <div class="metric-row"><span class="metric-label">Detected At:</span> <span class="metric-val">{{ timestamp|default('Just now') }}</span></div>
        <div class="metric-row"><span class="metric-label">Details:</span> <span class="metric-val">{{ details|default('Condition rule match triggered immediate notification.') }}</span></div>
      </div>
      <div style="text-align: center; margin-top: 24px;">
        <a href="{{ action_url|default('http://localhost:8000') }}" class="action-btn">Inspect in Control Center &rarr;</a>
      </div>
    </div>
  </div>
</body>
</html>""",
            'body_text': """ALERT: {{ alert_title|default('High Priority Trigger') }}

Hello {{ name|default('Administrator') }},

Severity: {{ severity|default('HIGH') }}
Detected At: {{ timestamp|default('Just now') }}
Details: {{ details|default('Condition rule match triggered immediate notification.') }}

Control Center: {{ action_url|default('http://localhost:8000') }}"""
        },

        'customer_feedback': {
            'name': 'Customer Feedback & NPS Survey',
            'category': 'feedback',
            'subject': 'How was your experience with {{ company|default("us") }}, {{ name|default("there") }}? ⭐',
            'variables': ['name', 'company', 'survey_url', 'unsubscribe_url'],
            'body_html': """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Quick Feedback</title>
  <style>
    body { background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: #e2e8f0; margin: 0; padding: 20px; }
    .box { max-width: 580px; margin: auto; background: #1e293b; border-radius: 16px; padding: 36px 30px; text-align: center; border: 1px solid #334155; }
    .rating-row { display: flex; justify-content: center; gap: 8px; margin: 28px 0; }
    .rating-btn { width: 42px; height: 42px; line-height: 42px; border-radius: 8px; background: #0f172a; border: 1px solid #475569; color: #f8fafc; font-weight: 700; text-decoration: none; display: inline-block; }
    .rating-btn:hover { background: #6366f1; border-color: #6366f1; }
  </style>
</head>
<body>
  <div class="box">
    <h2 style="color: #f8fafc; margin-top: 0;">We value your opinion, {{ name|default('Friend') }}!</h2>
    <p style="color: #94a3b8; font-size: 15px;">How likely are you to recommend {{ company|default('our automation platform') }} to a colleague or friend?</p>
    <div class="rating-row">
      <a href="{{ survey_url|default('#') }}?score=1" class="rating-btn">1</a>
      <a href="{{ survey_url|default('#') }}?score=2" class="rating-btn">2</a>
      <a href="{{ survey_url|default('#') }}?score=3" class="rating-btn">3</a>
      <a href="{{ survey_url|default('#') }}?score=4" class="rating-btn">4</a>
      <a href="{{ survey_url|default('#') }}?score=5" class="rating-btn">5</a>
      <a href="{{ survey_url|default('#') }}?score=6" class="rating-btn">6</a>
      <a href="{{ survey_url|default('#') }}?score=7" class="rating-btn">7</a>
      <a href="{{ survey_url|default('#') }}?score=8" class="rating-btn">8</a>
      <a href="{{ survey_url|default('#') }}?score=9" class="rating-btn">9</a>
      <a href="{{ survey_url|default('#') }}?score=10" class="rating-btn" style="background:#6366f1; border-color:#6366f1;">10</a>
    </div>
    <p style="color: #64748b; font-size: 12px; margin-top: 30px;"><a href="{{ unsubscribe_url|default('#') }}" style="color: #64748b;">Unsubscribe from surveys</a></p>
  </div>
</body>
</html>""",
            'body_text': """Hi {{ name|default('Friend') }},

How likely are you to recommend {{ company|default('us') }} on a scale of 1-10?
Take the 30-second survey: {{ survey_url|default('http://localhost:8000') }}

Unsubscribe: {{ unsubscribe_url|default('#') }}"""
        },

        'webinar_invite': {
            'name': 'Event & Webinar Invitation',
            'category': 'events',
            'subject': '🎟️ You\'re Invited: {{ event_title|default("Live Automation Masterclass") }}',
            'variables': ['name', 'event_title', 'speaker', 'date_time', 'register_url', 'unsubscribe_url'],
            'body_html': """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Event Invitation</title>
  <style>
    body { background-color: #030712; font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: #f9fafb; margin: 0; padding: 20px; }
    .card { max-width: 580px; margin: auto; background: #111827; border-radius: 16px; border: 1px solid #1f2937; overflow: hidden; }
    .hero-img { background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 36px 24px; text-align: center; }
    .content { padding: 30px; }
    .date-card { background: #1f2937; border-radius: 10px; padding: 16px; margin: 20px 0; border: 1px solid #374151; }
    .btn { display: inline-block; background: #10b981; color: #ffffff !important; padding: 14px 32px; border-radius: 8px; font-weight: 700; text-decoration: none; }
  </style>
</head>
<body>
  <div class="card">
    <div class="hero-img">
      <h1 style="margin: 0; font-size: 24px; color: #ffffff;">{{ event_title|default('Live Automation Masterclass') }}</h1>
    </div>
    <div class="content">
      <p>Hi {{ name|default('there') }},</p>
      <p style="color: #9ca3af;">Join us for an exclusive live session with <strong>{{ speaker|default('Industry Experts') }}</strong> on scaling email workflows and high-deliverability campaigns.</p>
      <div class="date-card">
        <div style="color: #10b981; font-weight: 600; font-size: 14px;">📅 DATE & TIME</div>
        <div style="font-size: 18px; font-weight: 700; margin-top: 4px;">{{ date_time|default('Thursday, 3:00 PM EST') }}</div>
      </div>
      <div style="text-align: center; margin: 30px 0;">
        <a href="{{ register_url|default('http://localhost:8000') }}" class="btn">Reserve Free Seat &rarr;</a>
      </div>
    </div>
  </div>
</body>
</html>""",
            'body_text': """You're Invited: {{ event_title|default('Live Automation Masterclass') }}

Hi {{ name|default('there') }},

Speaker: {{ speaker|default('Industry Experts') }}
Date & Time: {{ date_time|default('Thursday, 3:00 PM EST') }}

Reserve your free seat: {{ register_url|default('http://localhost:8000') }}"""
        }
    }

    # Spam Trigger Keywords & Patterns
    SPAM_KEYWORDS = [
        '100% free', '100% satisfied', 'act now', 'apply now', 'as seen on', 'bad credit',
        'bargain', 'be your own boss', 'best price', 'big bucks', 'billion dollars', 'bonus',
        'buy direct', 'call now', 'cancel at any time', 'cash bonus', 'cash prize', 'casino',
        'certified', 'cheap', 'claim', 'clearance', 'click below', 'click here now', 'click here',
        'congratulations', 'credit card offers', 'cures', 'deal', 'dear friend', 'direct email',
        'direct marketing', 'discount', 'double your income', 'earn extra cash', 'earn money',
        'eliminate debt', 'exclusive deal', 'expect to earn', 'extra income', 'fast cash',
        'financial freedom', 'free consultation', 'free gift', 'free info', 'free membership',
        'free sample', 'free trial', 'free', 'get out of debt', 'get paid', 'giveaway',
        'guaranteed', 'hidden assets', 'income from home', 'increase sales', 'instant',
        'investment', 'join millions', 'limited time', 'lowest price', 'make money',
        'millionaire', 'miracle', 'money back', 'mortgage', 'multi-level marketing',
        'no catch', 'no cost', 'no credit check', 'no experience', 'no fees', 'no gimmick',
        'no hidden costs', 'no obligation', 'no purchase necessary', 'no risk', 'no strings attached',
        'not spam', 'now only', 'obligation', 'off shore', 'offer', 'once in a lifetime',
        'one time', 'online marketing', 'open immediately', 'opportunity', 'order now',
        'passwords', 'pennies a day', 'potential earnings', 'prize', 'promise', 'pure profit',
        'refinance', 'refund', 'removal', 'reverses aging', 'risk free', 'save big', 'save money',
        'score', 'see for yourself', 'sent in compliance', 'special promotion', 'stainless steel',
        'stock alert', 'stop snoring', 'terms and conditions', 'this isn\'t spam', 'time limited',
        'unlimited', 'unsolicited', 'urgent', 'valuable', 'viagra', 'vicodin', 'warranty',
        'weight loss', 'while supplies last', 'win', 'winner', 'winning', 'work from home',
        'you have been selected', 'your income'
    ]

    def __init__(self):
        self.jinja_env = Environment(loader=BaseLoader())

    def render_string(self, template_str: str, context: dict) -> str:
        """
        Safely render template string using Jinja2 with bracket fallback
        """
        if not template_str:
            return ""
        
        rendered = template_str
        # 1. Try Jinja2 rendering
        try:
            template = self.jinja_env.from_string(rendered)
            rendered = template.render(**context)
        except Exception:
            pass
        
        # 2. Substitute any remaining single bracket {name} tokens
        for k, v in context.items():
            rendered = rendered.replace(f"{{{k}}}", str(v))
        return rendered



    def analyze_spam_score(self, subject: str, body: str) -> dict:
        """
        Analyze email content for spam risk and return score, breakdown, and suggestions.
        Score: 0 (Ultra Safe) to 100 (High Risk Spam)
        """
        score = 0
        reasons = []
        recommendations = []
        found_keywords = []
        
        text_content = f"{subject} {body}".lower()
        
        # 1. Spam keyword check
        for kw in self.SPAM_KEYWORDS:
            # Word boundary matching
            pattern = r'\b' + re.escape(kw) + r'\b'
            matches = re.findall(pattern, text_content)
            if matches:
                found_keywords.append(kw)
                score += min(len(matches) * 5, 20)
        
        if found_keywords:
            reasons.append(f"Found {len(found_keywords)} trigger phrase(s): {', '.join(found_keywords[:5])}")
            recommendations.append("Replace high-pressure sales and hype phrases with neutral, professional language.")
        
        # 2. Subject line ALL-CAPS check
        if subject:
            alpha_chars = [c for c in subject if c.isalpha()]
            if alpha_chars:
                caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                if caps_ratio > 0.4 and len(alpha_chars) > 6:
                    score += 25
                    reasons.append(f"Excessive ALL-CAPS in subject line ({int(caps_ratio*100)}%)")
                    recommendations.append("Use standard sentence casing for subject lines.")
        
        # 3. Exclamation marks check
        exclamation_count = subject.count('!') + body.count('!')
        if exclamation_count > 4:
            score += min(exclamation_count * 2, 20)
            reasons.append(f"Multiple exclamation marks ({exclamation_count})")
            recommendations.append("Reduce exclamation marks to 1 or none.")
            
        # 4. Multiple $$$ signs
        dollar_count = subject.count('$') + body.count('$')
        if dollar_count > 3:
            score += 15
            reasons.append(f"Multiple currency symbols (${dollar_count})")
            recommendations.append("Avoid excessive currency signs.")
            
        # 5. Missing Unsubscribe link check
        if 'unsubscribe' not in text_content:
            score += 15
            reasons.append("Missing 'Unsubscribe' link / footer (CAN-SPAM / GDPR risk)")
            recommendations.append("Always include an explicit Unsubscribe link in the footer.")
            
        # 6. Subject length
        if len(subject.strip()) < 4:
            score += 10
            reasons.append("Subject line is too short")
        elif len(subject.strip()) > 90:
            score += 10
            reasons.append("Subject line is too long (> 90 chars)")
            
        # Normalize score
        final_score = min(max(score, 0), 100)
        
        if final_score < 25:
            verdict = 'Safe (Excellent Deliverability)'
            status = 'safe'
        elif final_score < 55:
            verdict = 'Moderate Risk (Minor Improvements Needed)'
            status = 'warning'
        else:
            verdict = 'High Spam Risk (Likely to trigger junk filters)'
            status = 'danger'
            
        return {
            'score': final_score,
            'verdict': verdict,
            'status': status,
            'found_keywords': found_keywords,
            'reasons': reasons,
            'recommendations': recommendations
        }
