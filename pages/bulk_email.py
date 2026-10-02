"""
Bulk Email Automation Page
Uploads CSV, validates recipient schemas, renders live personalized templates, and runs throttled bulk dispatch.
"""

import streamlit as st
import pandas as pd
import time
import os
import uuid
from config import Config
from database import EmailDatabase
from email_sender import EmailSender
from validator import EmailValidator
from template_engine import TemplateEngine

def render_bulk_email():
    st.markdown("### 📁 Bulk Email Automation")
    st.markdown("Upload a recipient CSV, customize dynamic variable placeholders, preview rendered outputs, and run a safe batch broadcast.")

    sender = EmailSender()
    db = EmailDatabase()
    engine = TemplateEngine()

    # Step 1: Upload or Load CSV
    st.markdown("#### 1. Recipient List (CSV)")
    c1, c2 = st.columns([3, 1])
    with c1:
        uploaded_file = st.file_uploader(
            "Upload Recipient CSV File",
            type=["csv"],
            help="Upload a CSV with an 'email' column, plus optional columns like 'name', 'company', etc."
        )
    with c2:
        st.write("")
        st.write("")
        use_sample = st.button("📄 Load Demo CSV", help="Loads data/sample_recipients.csv immediately for testing")

    csv_text = None
    if uploaded_file is not None:
        csv_text = uploaded_file.getvalue().decode('utf-8-sig', errors='ignore')
        st.session_state['bulk_csv_text'] = csv_text
    elif use_sample or 'bulk_csv_text' in st.session_state:
        if use_sample:
            sample_path = os.path.join("data", "sample_recipients.csv")
            if not os.path.exists(sample_path):
                sample_path = "sample_recipients.csv"
            if os.path.exists(sample_path):
                with open(sample_path, "r", encoding="utf-8-sig") as f:
                    csv_text = f.read()
                    st.session_state['bulk_csv_text'] = csv_text
        else:
            csv_text = st.session_state.get('bulk_csv_text')
    else:
        # Preload sample dataset by default so the entire UI, preview, and send buttons are ready
        sample_path = os.path.join("data", "sample_recipients.csv")
        if not os.path.exists(sample_path):
            sample_path = "sample_recipients.csv"
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8-sig") as f:
                csv_text = f.read()
                st.session_state['bulk_csv_text'] = csv_text

    if not csv_text:
        st.info("👆 Please upload a CSV file or click **'Load Demo CSV'** to begin.")
        return

    # Parse and Validate CSV
    parsed = EmailValidator.parse_csv(csv_text, is_raw_text=True)

    if 'error' in parsed:
        st.error(f"✕ CSV Parsing Error: {parsed['error']}")
        return

    valid_rows = parsed['valid_rows']
    invalid_rows = parsed['invalid_rows']
    total_count = parsed['total_rows']

    # Show recipient counts breakdown
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Rows in CSV", f"{total_count}")
    m2.metric("Valid Recipients", f"{len(valid_rows)}", delta="Ready to Send")
    m3.metric("Invalid Emails", f"{len(invalid_rows)}", delta="Filtered Out" if len(invalid_rows) > 0 else "0", delta_color="inverse")
    m4.metric("Duplicates Removed", f"{parsed.get('duplicates_removed', 0)}")

    if invalid_rows:
        with st.expander("⚠️ View Filtered / Invalid Rows", expanded=False):
            st.dataframe(pd.DataFrame(invalid_rows), use_container_width=True)

    if not valid_rows:
        st.error("No valid email addresses found in the uploaded file.")
        return

    st.markdown("---")

    # Step 2: Subject & Message Templates
    st.markdown("#### 2. Compose Template & Dynamic Personalization")
    detected_cols = [f"{{{col}}}" for col in parsed.get('columns', [])]
    st.caption(f"**Available Placeholder Tags:** `{'`, `'.join(detected_cols)}`")

    default_subject = "Hello {name}, welcome to {company}!"
    default_message = "Dear {name},\n\nThis is an automated email regarding {company}.\n\nRegards,\nSadhna"

    subject_template = st.text_input(
        "Subject Template *",
        value=default_subject,
        help="Use placeholders like {name} and {company} matching your CSV columns."
    )

    message_template = st.text_area(
        "Message Template *",
        value=default_message,
        height=180,
        help="Placeholders will be replaced automatically for every recipient row."
    )

    # Step 3: Live Personalization Preview
    st.markdown("#### 3. Live Personalization Preview")
    preview_tabs = st.tabs([f"Recipient #{i+1} ({row.get('name', 'Contact')})" for i, row in enumerate(valid_rows[:3])])

    for i, tab in enumerate(preview_tabs):
        with tab:
            row = valid_rows[i]
            rendered_sub = engine.render_string(subject_template, row)
            rendered_body = engine.render_string(message_template, row)
            st.markdown(f"**To:** `{row['email']}`")
            st.markdown(f"**Personalized Subject:** `{rendered_sub}`")
            st.markdown("**Personalized Body Preview:**")
            st.code(rendered_body, language="text")

    st.markdown("---")

    # Step 4: Safety & Throttling Settings
    st.markdown("#### 4. Safe Sending & Throttling Controls")
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        delay = st.slider(
            "Delay Between Emails (seconds)",
            min_value=0.1,
            max_value=5.0,
            value=float(Config.RATE_LIMIT_DELAY),
            step=0.1,
            help="Adds a delay between sends to respect SMTP provider limits and avoid spam flags."
        )
    with c_s2:
        is_html = st.checkbox("Format Body as HTML", value=False)
        st.caption(f"**Execution Mode:** {'🟡 Dry-Run (Simulation)' if Config.DRY_RUN else '🟢 Live SMTP Network'}")

    # Step 5: Start Bulk Sending with Progress Bar
    st.markdown("---")
    if st.button("🚀 Start Bulk Email", type="primary", use_container_width=True):
        progress_bar = st.progress(0, text="Initializing batch dispatcher...")
        status_text = st.empty()
        
        success_count = 0
        failed_count = 0
        total_recipients = len(valid_rows)

        # Batch connect if live
        server_session = None
        if not Config.DRY_RUN:
            try:
                server_session = sender.connect()
            except Exception as e:
                st.error(f"Could not connect to SMTP server: {e}")
                return

        try:
            for idx, row in enumerate(valid_rows):
                to_email = row['email']
                p_subject = engine.render_string(subject_template, row)
                p_body = engine.render_string(message_template, row)
                tracking_id = str(uuid.uuid4())

                # Send
                status_text.text(f"Dispatching [{idx + 1}/{total_recipients}]: {to_email}...")
                ok = sender.send_email(
                    to_email=to_email,
                    subject=p_subject,
                    body=p_body,
                    html=is_html,
                    tracking_id=tracking_id,
                    server_session=server_session
                )

                if ok:
                    success_count += 1
                else:
                    failed_count += 1

                # Update progress: 0% -> 100%
                percent_complete = int(((idx + 1) / total_recipients) * 100)
                progress_bar.progress(
                    percent_complete,
                    text=f"Progress: {percent_complete}% ({idx + 1}/{total_recipients}) • Sent: {success_count} • Failed: {failed_count}"
                )

                # Delay between sends for rate limiting
                if idx < total_recipients - 1:
                    time.sleep(delay)

        finally:
            if server_session:
                try:
                    server_session.quit()
                except Exception:
                    pass

        status_text.empty()
        st.success(f"🎉 Bulk Email Campaign Completed!")

        # After completion show summary cards
        r1, r2, r3 = st.columns(3)
        r1.metric("Total Processed", f"{total_recipients}")
        r2.metric("Successful", f"{success_count}", delta=f"{int(success_count/total_recipients*100)}% Success")
        r3.metric("Failed", f"{failed_count}", delta="Errors" if failed_count > 0 else "None", delta_color="inverse")

        st.info("Every recipient result has been securely recorded to the SQLite database. Check the **Email History** tab to view the full audit log.")
