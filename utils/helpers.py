"""
UI Helpers, Custom CSS, and Data Formatting Utilities for Email Automation Dashboard
"""

import streamlit as st
from datetime import datetime

def load_custom_css():
    """Inject custom enterprise SaaS CSS styling into Streamlit application"""
    st.markdown("""
    <style>
    /* Import modern typography */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main container spacing */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }

    /* Custom Header Banner */
    .app-header-box {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), 0 0 20px -5px rgba(99, 102, 241, 0.15);
    }
    
    .app-title {
        font-size: 26px;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .app-subtitle {
        font-size: 14px;
        color: #94a3b8;
        font-weight: 500;
        margin-top: 4px;
        letter-spacing: 0.2px;
    }

    /* Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 14px;
        padding: 18px 20px;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        backdrop-filter: blur(8px);
    }

    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 8px 20px -6px rgba(99, 102, 241, 0.2);
    }

    .metric-title {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #94a3b8;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.1;
    }

    .metric-desc {
        font-size: 12px;
        color: #64748b;
        margin-top: 6px;
    }

    /* Status Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .badge-success {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .badge-failed {
        background: rgba(244, 63, 94, 0.15);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.3);
    }

    .badge-pending {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .badge-running {
        background: rgba(6, 182, 212, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }

    .badge-stopped {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.3);
    }

    /* Code & Mono */
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Polished Card Container */
    .card-container {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }

    /* Action Callout */
    .info-callout {
        background: rgba(99, 102, 241, 0.08);
        border-left: 4px solid #6366f1;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 12px 0;
        font-size: 13px;
        color: #cbd5e1;
    }
    </style>
    """, unsafe_allow_html=True)

def render_header(title="Email Automation & Notification System", subtitle="Automate • Personalize • Monitor • Schedule"):
    """Render top application brand banner"""
    st.markdown(f"""
    <div class="app-header-box">
        <h1 class="app-title">⚡ {title}</h1>
        <div class="app-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_badge(status: str) -> str:
    """Generate HTML string for standard status badge"""
    st_upper = (status or 'PENDING').upper()
    if st_upper in ('SENT', 'SUCCESS', 'ACTIVE', 'ENABLED', 'DELIVERED', 'COMPLETED'):
        return f'<span class="badge badge-success">✓ {st_upper}</span>'
    elif st_upper in ('FAILED', 'ERROR', 'DISABLED'):
        return f'<span class="badge badge-failed">✕ {st_upper}</span>'
    elif st_upper in ('RUNNING', 'LIVE'):
        return f'<span class="badge badge-running">● {st_upper}</span>'
    elif st_upper in ('STOPPED', 'PAUSED'):
        return f'<span class="badge badge-stopped">■ {st_upper}</span>'
    else:
        return f'<span class="badge badge-pending">⏱ {st_upper}</span>'

def mask_secret(value: str) -> str:
    """Return a masked secret string or 'Configured ✓'"""
    if not value:
        return "Not Set"
    return "Configured ✓"

def format_datetime(dt_str: str) -> str:
    """Safely format database timestamp for presentation"""
    if not dt_str:
        return "—"
    try:
        # If timestamp is ISO or standard SQL format
        clean_str = str(dt_str).replace('T', ' ')
        dt = datetime.strptime(clean_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%b %d, %Y • %I:%M %p")
    except Exception:
        return str(dt_str)
