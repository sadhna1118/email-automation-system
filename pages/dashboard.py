"""
Dashboard Page View
Displays key metric cards, recent email activity, and quick system overview.
"""

import streamlit as st
import pandas as pd
from database import EmailDatabase
from config import Config
from utils.helpers import render_badge, format_datetime

def render_dashboard():
    db = EmailDatabase()
    stats = db.get_email_stats()

    st.markdown("### 📊 System Overview & Performance")
    
    # Mode banner if in Dry-Run
    if Config.DRY_RUN:
        st.info("ℹ️ **Simulation Mode (Dry-Run) is Active:** Emails and monitoring can be safely tested and simulated without contacting live SMTP/IMAP servers. To enable live sending, update `.env` or Settings.")

    # 6 Key Metric Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Total Emails Sent",
            value=f"{stats.get('total', 0):,}",
            delta=f"{stats.get('sent', 0)} Delivered"
        )
        st.metric(
            label="Monitored Emails",
            value=f"{stats.get('monitored', 0):,}",
            delta="Inbox Watcher"
        )

    with col2:
        st.metric(
            label="Successful Emails",
            value=f"{stats.get('sent', 0):,}",
            delta=f"{stats.get('success_rate', 100.0)}% Success Rate"
        )
        st.metric(
            label="Active Notification Rules",
            value=f"{stats.get('active_rules', 0):,}",
            delta="Smart Triggers"
        )

    with col3:
        st.metric(
            label="Failed Emails",
            value=f"{stats.get('failed', 0):,}",
            delta="-0.0%" if stats.get('failed', 0) == 0 else "Needs Review",
            delta_color="inverse"
        )
        st.metric(
            label="Scheduled Tasks",
            value=f"{stats.get('active_scheduled_tasks', 0):,}",
            delta="Automated Jobs"
        )

    st.markdown("---")

    # Recent Email Activity Table
    st.markdown("### 🕒 Recent Email Activity")
    recent_emails = db.get_recent_sent_emails(limit=10)

    if recent_emails:
        activity_data = []
        for em in recent_emails:
            raw_status = em.get('status', 'pending')
            # Normalize status for presentation
            if raw_status in ('sent', 'success'):
                disp_status = "SUCCESS"
            elif raw_status in ('failed', 'error'):
                disp_status = "FAILED"
            else:
                disp_status = "PENDING"

            activity_data.append({
                "Recipient": em.get('recipient'),
                "Subject": em.get('subject'),
                "Status": disp_status,
                "Sent At": format_datetime(em.get('sent_at')),
                "Opened": "✓ Yes" if em.get('opened') else "—",
                "Error": em.get('error_message') or "None"
            })

        df = pd.DataFrame(activity_data)
        
        # Display styled dataframe
        st.dataframe(
            df[['Recipient', 'Subject', 'Status', 'Sent At', 'Error']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No sent email activity logged yet. Use the **Send Email** or **Bulk Email** tab to get started!")

    # Quick Action Cards
    st.markdown("---")
    st.markdown("### ⚡ Quick Navigation")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("✉️ Send Single Email", use_container_width=True):
            st.session_state['selected_page'] = "Send Email"
            st.rerun()
    with q2:
        if st.button("📁 Bulk Campaign", use_container_width=True):
            st.session_state['selected_page'] = "Bulk Email"
            st.rerun()
    with q3:
        if st.button("📥 Inbox Monitor", use_container_width=True):
            st.session_state['selected_page'] = "Email Monitoring"
            st.rerun()
    with q4:
        if st.button("⏱️ Task Scheduler", use_container_width=True):
            st.session_state['selected_page'] = "Scheduler"
            st.rerun()
