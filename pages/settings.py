"""
Settings & System Diagnostics Page
Exhibits configuration statuses, allows updating credentials and live/simulation modes,
runs live protocol diagnostics, and displays deployment environment variables.
"""

import streamlit as st
import os
from config import Config
from email_sender import EmailSender
from email_monitor import EmailMonitor
from utils.helpers import mask_secret

def update_env_file(key_values: dict):
    """Update or append keys in .env file and update Config class in-memory"""
    env_path = ".env"
    existing_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    updated_keys = set()
    new_lines = []
    for line in existing_lines:
        line_stripped = line.strip()
        if "=" in line_stripped and not line_stripped.startswith("#"):
            k = line_stripped.split("=", 1)[0].strip()
            if k in key_values:
                new_lines.append(f"{k}={key_values[k]}\n")
                updated_keys.add(k)
                continue
        new_lines.append(line)

    for k, v in key_values.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Update in-memory Config class
    if 'EMAIL_ADDRESS' in key_values:
        Config.EMAIL_ADDRESS = key_values['EMAIL_ADDRESS']
    if 'EMAIL_PASSWORD' in key_values:
        Config.EMAIL_PASSWORD = key_values['EMAIL_PASSWORD']
    if 'NOTIFICATION_EMAIL' in key_values:
        Config.NOTIFICATION_EMAIL = key_values['NOTIFICATION_EMAIL']
    if 'DRY_RUN' in key_values:
        Config.DRY_RUN = str(key_values['DRY_RUN']).lower() in ('true', '1', 'yes')

def render_settings():
    st.markdown("### ⚙️ System Configuration & Diagnostics")
    st.markdown("Inspect connected email gateways, configure credentials, switch operational modes, and test protocol connectivity.")

    # Status Grid
    st.markdown("#### 🔒 Gateway Credentials & Status")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Outbound SMTP Gateway**")
        st.markdown(f"- **Server:** `{Config.SMTP_SERVER}:{Config.SMTP_PORT}`")
        st.markdown(f"- **Encryption:** `{'TLS (Port 587)' if Config.SMTP_USE_TLS else 'SSL (Port 465)'}`")
        st.markdown(f"- **Sender Account:** `{Config.EMAIL_ADDRESS or 'Not Set'}`")
        st.markdown(f"- **Account Password:** `{mask_secret(Config.EMAIL_PASSWORD)}`")

    with c2:
        st.markdown("**Inbound IMAP Gateway & Storage**")
        st.markdown(f"- **IMAP Server:** `{Config.IMAP_SERVER}:{Config.IMAP_PORT}`")
        st.markdown(f"- **Database:** `SQLite WAL Mode ({Config.DB_PATH})` {'✓ Connected' if os.path.exists(Config.DB_PATH) else ''}")
        st.markdown(f"- **Alert Recipient:** `{Config.NOTIFICATION_EMAIL or 'Not Set'}`")
        st.markdown(f"- **Active Mode:** `{'🟡 Simulation (Dry-Run)' if Config.DRY_RUN else '🟢 Live Production (Real SMTP)'}`")

    st.markdown("---")

    # Interactive Setup Form
    with st.expander("📝 Update Credentials & Mode (Live vs Simulation)", expanded=True):
        st.markdown("Configure your sending email address, Google App Password, and choose whether to send real emails or run in safe simulation mode.")
        with st.form("settings_update_form"):
            s_mode = st.radio(
                "Execution Mode *",
                ["🟡 Simulation Mode (Safe demo without contacting SMTP/IMAP)", "🟢 Live Production Mode (Send real emails to inboxes)"],
                index=0 if Config.DRY_RUN else 1,
                help="Simulation mode is safe for interviews. Live mode sends real emails through Gmail/Outlook."
            )

            col_acc1, col_acc2 = st.columns(2)
            with col_acc1:
                new_email = st.text_input(
                    "Gmail / Sender Email",
                    value=Config.EMAIL_ADDRESS if Config.EMAIL_ADDRESS != "your_email@gmail.com" else "",
                    placeholder="e.g. your_name@gmail.com",
                    help="Your Google email address."
                )
            with col_acc2:
                new_password = st.text_input(
                    "Google 16-Character App Password",
                    value=Config.EMAIL_PASSWORD if "your_app_password" not in Config.EMAIL_PASSWORD else "",
                    type="password",
                    placeholder="e.g. abcd efgh ijkl mnop",
                    help="Generate at: myaccount.google.com/apppasswords"
                )

            new_notify = st.text_input(
                "Notification Alert Recipient Email",
                value=Config.NOTIFICATION_EMAIL if Config.NOTIFICATION_EMAIL != "alerts@yourdomain.com" else "",
                placeholder="e.g. alerts@company.com"
            )

            save_btn = st.form_submit_button("💾 Save & Apply Configuration", type="primary", use_container_width=True)

        if save_btn:
            is_dry = "Simulation Mode" in s_mode
            updates = {
                "DRY_RUN": "true" if is_dry else "false",
                "EMAIL_ADDRESS": new_email.strip() if new_email.strip() else Config.EMAIL_ADDRESS,
                "EMAIL_PASSWORD": new_password.strip() if new_password.strip() else Config.EMAIL_PASSWORD,
                "NOTIFICATION_EMAIL": new_notify.strip() if new_notify.strip() else Config.NOTIFICATION_EMAIL
            }
            update_env_file(updates)
            st.success(f"✓ Configuration successfully saved! Active Mode: {'Simulation (Dry-Run)' if is_dry else 'Live Network'}")
            st.rerun()

    st.markdown("---")

    # Gateway Health Checks
    st.markdown("#### 🧪 Gateway Health & Connectivity Diagnostics")
    st.caption("Perform live protocol handshakes against remote mail servers to verify internet connectivity and credentials.")

    test_col1, test_col2 = st.columns(2)
    with test_col1:
        if st.button("🔌 Run Outbound SMTP Health Check", use_container_width=True):
            with st.spinner("Executing SMTP handshake against smtp.gmail.com:587..."):
                sender = EmailSender()
                result = sender.test_connection(force_live=True)
                if result.get('success'):
                    st.success(f"✓ {result.get('message')}")
                else:
                    st.error(f"✕ {result.get('message')}")

    with test_col2:
        if st.button("📡 Run Inbound IMAP Health Check", use_container_width=True):
            with st.spinner("Executing IMAP handshake against imap.gmail.com:993..."):
                monitor = EmailMonitor()
                result = monitor.test_connection(force_live=True)
                if result.get('success'):
                    st.success(f"✓ {result.get('message')}")
                else:
                    st.error(f"✕ {result.get('message')}")

    st.markdown("---")

    # Render Environment Variables Reference
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
