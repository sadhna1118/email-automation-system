"""
Email Monitoring Page
Displays live IMAP status, background daemon controls, latest monitored incoming emails,
and an interactive rule-matching test simulator for demonstrations.
"""

import streamlit as st
import pandas as pd
import json
from config import Config
from database import EmailDatabase
from email_monitor import EmailMonitor
from utils.helpers import format_datetime, render_badge

def get_monitor_instance():
    """Get or create singleton EmailMonitor in Streamlit session state"""
    if 'email_monitor_instance' not in st.session_state:
        st.session_state['email_monitor_instance'] = EmailMonitor()
    return st.session_state['email_monitor_instance']

def render_monitoring():
    st.markdown("### 📥 Email Monitoring & IMAP Watcher")
    st.markdown("Continuously monitor incoming inbox messages, evaluate intelligent notification rules, and trigger automated alerts or replies.")

    monitor = get_monitor_instance()
    db = EmailDatabase()

    # Connection and Daemon Status
    is_running = monitor.is_running()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="IMAP Server",
            value=Config.IMAP_SERVER,
            delta=f"Port {Config.IMAP_PORT} • SSL {'Enabled' if Config.IMAP_USE_SSL else 'Off'}"
        )
    with col2:
        st.metric(
            label="Connection Mode",
            value="Dry-Run (Simulated)" if Config.DRY_RUN else "Live Network",
            delta="Safe Interview Mode" if Config.DRY_RUN else "Production IMAP"
        )
    with col3:
        status_label = "RUNNING" if is_running else "STOPPED"
        st.metric(
            label="Monitoring Status",
            value=status_label,
            delta="Daemon Active" if is_running else "Daemon Idle",
            delta_color="normal" if is_running else "off"
        )

    # Action Buttons: Start, Stop, Refresh
    st.markdown("---")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("▶️ Start Monitoring", disabled=is_running, use_container_width=True):
            monitor.start_background_daemon()
            st.success("Background inbox monitoring daemon started.")
            st.rerun()
    with b2:
        if st.button("⏹️ Stop Monitoring", disabled=not is_running, use_container_width=True):
            monitor.stop_background_daemon()
            st.warning("Background inbox monitoring daemon stopped.")
            st.rerun()
    with b3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    with b4:
        if st.button("⚡ Check Inbox Now", use_container_width=True):
            with st.spinner("Polling inbox for unseen emails..."):
                count = monitor.monitor_inbox()
                st.info(f"Inbox poll complete. Found {count} new message(s).")
                st.rerun()

    # Live Interview Demo Feature: Simulate Incoming Email
    st.markdown("---")
    with st.expander("🧪 Interview Live Demo: Simulate Incoming Email", expanded=False):
        st.markdown(
            "Use this simulation tool during an interview to showcase how incoming emails trigger "
            "rules, alert notifications, and auto-replies in real time."
        )
        sim_c1, sim_c2 = st.columns(2)
        with sim_c1:
            sim_sender = st.text_input("Sender", value="recruiter@techcorp.com")
            sim_subject = st.text_input("Subject", value="Interview Invitation: Python Engineering Role")
        with sim_c2:
            sim_body = st.text_area(
                "Body Content",
                value="Hi Sadhna,\n\nWe were impressed with your application and would like to schedule an Interview with you this week.\n\nBest,\nHR Team",
                height=110
            )

        if st.button("📨 Process Incoming Test Message", type="secondary"):
            with st.spinner("Processing email through smart rules engine..."):
                res = monitor.simulate_incoming_email(
                    sender=sim_sender,
                    subject=sim_subject,
                    body=sim_body
                )
                matched = res.get('matched_rules', [])
                actions = res.get('actions_taken', [])
                if matched:
                    st.success(f"🎯 Matched {len(matched)} Rule(s): **{', '.join(matched)}**")
                    if actions:
                        st.info(f"⚡ Actions Executed: {', '.join(actions)}")
                else:
                    st.info("✓ Email received and logged. No active notification rules matched criteria.")
                st.rerun()

    # Latest Monitored Emails Table
    st.markdown("---")
    st.markdown("### 📋 Latest Monitored Emails")
    monitored = db.get_monitored_emails(limit=25)

    if monitored:
        rows = []
        for m in monitored:
            rules_raw = m.get('rule_matches')
            rules_str = "None"
            if rules_raw:
                try:
                    parsed_rules = json.loads(rules_raw) if isinstance(rules_raw, str) else rules_raw
                    rules_str = ", ".join(parsed_rules) if isinstance(parsed_rules, list) and parsed_rules else str(parsed_rules)
                except Exception:
                    rules_str = str(rules_raw)

            notify_status = "SENT" if m.get('notification_sent') else ("MATCHED" if rules_str != "None" else "NORMAL")

            rows.append({
                "Sender": m.get('sender'),
                "Subject": m.get('subject'),
                "Received Time": format_datetime(m.get('received_at')),
                "Matched Rule": rules_str,
                "Notification Status": notify_status,
                "Preview": (m.get('body_preview') or '')[:120]
            })

        df = pd.DataFrame(rows)
        st.dataframe(
            df[['Sender', 'Subject', 'Received Time', 'Matched Rule', 'Notification Status', 'Preview']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No incoming emails monitored yet. Click **'Check Inbox Now'** or test with the **'Simulate Incoming Email'** tool above.")
