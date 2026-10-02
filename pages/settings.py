"""
Settings & System Diagnostics Page
Exhibits configuration statuses without exposing secrets, runs live connectivity diagnostics,
and displays deployment environment variables.
"""

import streamlit as st
import os
from config import Config
from email_sender import EmailSender
from email_monitor import EmailMonitor
from utils.helpers import mask_secret

def render_settings():
    st.markdown("### ⚙️ System Configuration & Diagnostics")
    st.markdown("Inspect connected email gateways, test SMTP/IMAP protocol connectivity, and review deployment environment variables.")

    # Status Grid (No exposed passwords)
    st.markdown("#### 🔒 Gateway Credentials & Endpoint Status")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**SMTP Outbound Gateway**")
        st.markdown(f"- **Server Host:** `{Config.SMTP_SERVER}`")
        st.markdown(f"- **Port:** `{Config.SMTP_PORT}`")
        st.markdown(f"- **Security:** `{'TLS' if Config.SMTP_USE_TLS else ('SSL' if Config.SMTP_USE_SSL else 'Plaintext')}`")
        st.markdown(f"- **Sending Account:** `{'Configured (' + Config.EMAIL_ADDRESS[:4] + '***@' + Config.EMAIL_ADDRESS.split('@')[-1] + ')' if Config.EMAIL_ADDRESS and '@' in Config.EMAIL_ADDRESS else 'Not Configured'}`")
        st.markdown(f"- **Account Password:** `{mask_secret(Config.EMAIL_PASSWORD)}`")

    with c2:
        st.markdown("**IMAP Inbound Gateway & Storage**")
        st.markdown(f"- **IMAP Host:** `{Config.IMAP_SERVER}`")
        st.markdown(f"- **IMAP Port:** `{Config.IMAP_PORT}`")
        st.markdown(f"- **Security:** `{'SSL Enabled' if Config.IMAP_USE_SSL else 'Standard'}`")
        st.markdown(f"- **Database Engine:** `SQLite (WAL Mode)`")
        st.markdown(f"- **Database File:** `{Config.DB_PATH}` {'✓ Connected' if os.path.exists(Config.DB_PATH) else '(Will Auto-Create)'}")
        st.markdown(f"- **Default Alert Recipient:** `{Config.NOTIFICATION_EMAIL or 'Not Set'}`")

    st.markdown("---")

    # Connection Diagnostic Test Suite
    st.markdown("#### 🧪 Gateway Health & Connectivity Diagnostics")
    st.caption("Verify protocol connectivity, handshake negotiation, and authentication against remote mail servers.")

    test_col1, test_col2 = st.columns(2)
    with test_col1:
        if st.button("🔌 Run Outbound SMTP Health Check", use_container_width=True):
            with st.spinner("Connecting to SMTP server..."):
                sender = EmailSender()
                result = sender.test_connection()
                if result.get('success'):
                    st.success(f"✓ {result.get('message')}")
                else:
                    st.error(f"✕ {result.get('message')}")

    with test_col2:
        if st.button("📡 Run Inbound IMAP Health Check", use_container_width=True):
            with st.spinner("Connecting to IMAP server..."):
                monitor = EmailMonitor()
                result = monitor.test_connection()
                if result.get('success'):
                    st.success(f"✓ {result.get('message')}")
                else:
                    st.error(f"✕ {result.get('message')}")

    st.markdown("---")

    # Environment Variables Reference for Render Deployment
    st.markdown("#### 🌐 Render Cloud Environment Variables Reference")
    st.markdown(
        "When deploying to **Render**, add these key-value pairs in your **Render Service Dashboard → Environment Variables** tab:"
    )

    env_table = [
        {"Variable Name": "SMTP_SERVER", "Example Value": "smtp.gmail.com", "Description": "SMTP server hostname"},
        {"Variable Name": "SMTP_PORT", "Example Value": "587", "Description": "SMTP port (587 for TLS, 465 for SSL)"},
        {"Variable Name": "IMAP_SERVER", "Example Value": "imap.gmail.com", "Description": "IMAP server hostname for monitoring"},
        {"Variable Name": "IMAP_PORT", "Example Value": "993", "Description": "IMAP port (993 for SSL)"},
        {"Variable Name": "EMAIL_ADDRESS", "Example Value": "your_email@gmail.com", "Description": "Sender and inbox email address"},
        {"Variable Name": "EMAIL_PASSWORD", "Example Value": "abcd efgh ijkl mnop", "Description": "Google App Password (16 characters)"},
        {"Variable Name": "NOTIFICATION_EMAIL", "Example Value": "alerts@domain.com", "Description": "Recipient for rule notifications"},
        {"Variable Name": "DRY_RUN", "Example Value": "true", "Description": "Set 'true' for safe demo mode, 'false' for real sending"},
        {"Variable Name": "DB_PATH", "Example Value": "emails.db", "Description": "Path to SQLite database file"}
    ]
    st.dataframe(env_table, use_container_width=True, hide_index=True)
