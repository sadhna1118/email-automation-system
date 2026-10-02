"""
Email History Page
Audits all sent emails with real-time filtering by status, date range, recipient keyword search,
and dynamic CSV export.
"""

import streamlit as st
import pandas as pd
from database import EmailDatabase
from utils.helpers import format_datetime

def render_history():
    st.markdown("### 📜 Sent Email History & Audit Log")
    st.markdown("Search, inspect, and export all email dispatches logged by the system into SQLite.")

    db = EmailDatabase()

    # Filters and Search Bar
    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
    with f1:
        search_query = st.text_input("🔍 Search Recipient or Subject", placeholder="e.g. acme or @gmail.com")
    with f2:
        status_filter = st.selectbox("Status Filter", ["All", "SUCCESS", "FAILED"])
    with f3:
        start_date = st.date_input("Start Date", value=None)
    with f4:
        end_date = st.date_input("End Date", value=None)

    # Query DB with filters
    history_records = db.get_email_history(
        limit=500,
        status=status_filter if status_filter != "All" else None,
        search=search_query if search_query else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None
    )

    if not history_records:
        st.info("No email records match your filter criteria.")
        return

    # Prepare DataFrame
    formatted_data = []
    for r in history_records:
        raw_status = (r.get('status') or 'sent').lower()
        if raw_status in ('sent', 'success'):
            status_disp = "SUCCESS"
        elif raw_status in ('failed', 'error'):
            status_disp = "FAILED"
        else:
            status_disp = "PENDING"

        formatted_data.append({
            "ID": r.get('id'),
            "Recipient": r.get('recipient'),
            "Subject": r.get('subject'),
            "Status": status_disp,
            "Timestamp": format_datetime(r.get('sent_at')),
            "Error Message": r.get('error_message') or "None",
            "Opened": "✓ Yes" if r.get('opened') else "No",
            "Clicked": "✓ Yes" if r.get('clicked') else "No"
        })

    df = pd.DataFrame(formatted_data)

    # Summary metrics above table
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matching Records", f"{len(df)}")
    m2.metric("Successful", f"{len(df[df['Status'] == 'SUCCESS'])}")
    m3.metric("Failed", f"{len(df[df['Status'] == 'FAILED'])}")
    m4.metric("Opens Tracked", f"{len(df[df['Opened'] == '✓ Yes'])}")

    st.markdown("---")

    # CSV Export Button
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export History to CSV",
        data=csv_bytes,
        file_name="sent_email_history.csv",
        mime="text/csv",
        help="Download filtered email records as a CSV file."
    )

    # Render Table
    st.dataframe(
        df[['Recipient', 'Subject', 'Status', 'Timestamp', 'Error Message', 'Opened', 'Clicked']],
        use_container_width=True,
        hide_index=True
    )
