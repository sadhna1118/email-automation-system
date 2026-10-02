"""
Send Single Email Page
Allows composing and dispatching one-off transactional or personalized emails.
"""

import streamlit as st
from config import Config
from database import EmailDatabase
from email_sender import EmailSender
from utils.validation import validate_single_email

def render_send_email():
    st.markdown("### ✉️ Send Single Email")
    st.markdown("Compose and transmit an individual email with automated address validation and SQLite audit tracking.")

    sender = EmailSender()
    db = EmailDatabase()

    # Pre-fill shortcuts for live interview demonstration
    with st.expander("⚡ Quick Fill Demo Presets", expanded=False):
        c1, c2 = st.columns(2)
        if c1.button("Preset: Interview Follow-up"):
            st.session_state['single_recipient'] = "interviewer@company.com"
            st.session_state['single_subject'] = "Thank You for the Interview — Sadhna"
            st.session_state['single_message'] = (
                "Dear Hiring Team,\n\n"
                "Thank you for the opportunity to discuss the Python Engineer role today. "
                "I enjoyed sharing the architecture of my Email Automation System with you.\n\n"
                "Looking forward to hearing from you!\n\nBest regards,\nSadhna"
            )
        if c2.button("Preset: System Notification"):
            st.session_state['single_recipient'] = Config.NOTIFICATION_EMAIL or "admin@company.com"
            st.session_state['single_subject'] = "AuraMail Alert: Daily Health Status OK"
            st.session_state['single_message'] = (
                "Hello Administrator,\n\n"
                "All email automation services are operating smoothly with 100% deliverability.\n\n"
                "Automation Daemon: Active\nDatabase: SQLite WAL Mode\n\nRegards,\nAutomation System"
            )

    # Form inputs
    with st.form("single_email_form", clear_on_submit=False):
        recipient = st.text_input(
            "Recipient Email *",
            value=st.session_state.get('single_recipient', ''),
            placeholder="e.g. client@example.com",
            help="Enter a valid email address. Synthetic and RFC checks will be executed automatically."
        )

        subject = st.text_input(
            "Subject *",
            value=st.session_state.get('single_subject', ''),
            placeholder="e.g. Project Update & Milestone Status"
        )

        message = st.text_area(
            "Message Body *",
            value=st.session_state.get('single_message', ''),
            placeholder="Type your message content here...",
            height=200
        )

        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            send_as_html = st.checkbox("Format as Rich HTML Email", value=True, help="Renders HTML tags and styled responsive containers.")
        with col_opt2:
            st.caption(f"**Current Sending Mode:** {'🟡 Dry-Run Simulation' if Config.DRY_RUN else '🟢 Live SMTP Network'}")

        submitted = st.form_submit_button("🚀 Send Email", use_container_width=True)

    if submitted:
        # 1. Validation
        if not recipient or not subject or not message:
            st.error("Please fill in all required fields (Recipient, Subject, Message).")
            return

        val = validate_single_email(recipient)
        if not val['valid']:
            st.error(f"✕ Invalid Recipient Email Address: {val.get('reason', 'Format violation')}")
            return

        if val.get('is_disposable'):
            st.warning("⚠️ Warning: Recipient domain appears to be a disposable or temporary email address.")

        # 2. Dispatching Email
        with st.spinner("Transmitting email via SMTP engine..."):
            try:
                success = sender.send_email(
                    to_email=val['email'],
                    subject=subject,
                    body=message,
                    html=send_as_html
                )

                if success:
                    st.success("✅ Email sent successfully.")
                    if Config.DRY_RUN:
                        st.info("ℹ️ Sent in Simulation (Dry-Run) mode and recorded to SQLite database.")
                    else:
                        st.info(f"Delivered to {val['email']} via {Config.SMTP_SERVER}:{Config.SMTP_PORT}.")
                else:
                    st.error("✕ Failed to send email. Check configuration or SMTP credentials.")
            except Exception as e:
                st.error(f"✕ SMTP Dispatch Error: {str(e)}")

    # Recent Single Emails Table
    st.markdown("---")
    st.markdown("#### 📜 Recent Single Dispatches")
    recent = db.get_recent_sent_emails(limit=5)
    if recent:
        st.dataframe(
            [
                {
                    "Recipient": r['recipient'],
                    "Subject": r['subject'],
                    "Status": (r['status'] or 'SENT').upper(),
                    "Sent At": r['sent_at'],
                    "Error": r.get('error_message') or "None"
                }
                for r in recent
            ],
            use_container_width=True,
            hide_index=True
        )
