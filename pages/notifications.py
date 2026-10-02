"""
Notification Rules Page
Manage automated trigger rules based on incoming sender address, subject keywords, and body phrases.
"""

import streamlit as st
import pandas as pd
import json
from database import EmailDatabase
from config import Config
from utils.helpers import format_datetime, render_badge

def render_notifications():
    st.markdown("### ⚡ Notification & Trigger Rules")
    st.markdown("Configure smart condition filters. When incoming emails match your rule criteria, automated alerts or response workflows are triggered.")

    db = EmailDatabase()

    # Step 1: Create New Rule Form
    with st.expander("➕ Create New Notification Rule", expanded=True):
        with st.form("create_rule_form", clear_on_submit=True):
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                rule_name = st.text_input(
                    "Rule Name *",
                    placeholder="e.g. Job Application Response",
                    help="Descriptive title for identifying this automation rule."
                )
                sender_filter = st.text_input(
                    "Sender Email Filter (optional)",
                    placeholder="e.g. recruiter@company.com or @techcorp.com",
                    help="Match sender email address or domain."
                )
                notification_email = st.text_input(
                    "Notification Email *",
                    value=Config.NOTIFICATION_EMAIL or "",
                    placeholder="e.g. alerts@myportfolio.com",
                    help="Destination address to receive instant alert when this rule triggers."
                )
            with r_col2:
                subject_filter = st.text_input(
                    "Subject Keyword *",
                    placeholder="e.g. Interview",
                    help="Keyword that must appear in the email subject."
                )
                keyword_filter = st.text_input(
                    "Body Keyword (optional)",
                    placeholder="e.g. schedule, offer, technical round",
                    help="Keyword or phrase that must appear in the message body."
                )
                condition_logic = st.selectbox(
                    "Condition Match Logic",
                    ["AND", "OR"],
                    help="'AND' requires all populated filters to match; 'OR' requires any one filter to match."
                )

            submit_rule = st.form_submit_button("💾 Save Notification Rule", type="primary", use_container_width=True)

        if submit_rule:
            if not rule_name or not (subject_filter or keyword_filter or sender_filter):
                st.error("Please provide a Rule Name and at least one filter criterion (Subject Keyword, Body Keyword, or Sender Filter).")
            else:
                rule_id = db.add_notification_rule(
                    rule_name=rule_name,
                    sender_filter=sender_filter if sender_filter else None,
                    subject_filter=subject_filter if subject_filter else None,
                    keyword_filter=keyword_filter if keyword_filter else None,
                    condition_logic=condition_logic,
                    action_type="alert",
                    notification_email=notification_email if notification_email else None
                )
                st.success(f"✓ Notification Rule '{rule_name}' successfully created (ID: {rule_id})!")
                st.rerun()

    st.markdown("---")

    # Step 2: Configured Rules Table with Enable/Disable & Delete
    st.markdown("### 📋 Active Rules Management")
    rules = db.get_all_rules()

    if rules:
        for r in rules:
            with st.container():
                rc1, rc2, rc3, rc4 = st.columns([3, 3, 2, 2])
                with rc1:
                    status_text = "🟢 Active" if r['enabled'] else "⚪ Disabled"
                    st.markdown(f"**{r['rule_name']}** &nbsp; `{status_text}`")
                    st.caption(f"Created: {format_datetime(r.get('created_at'))}")
                with rc2:
                    sub_f = f"Subject: '{r['subject_filter']}'" if r.get('subject_filter') else ""
                    snd_f = f"Sender: '{r['sender_filter']}'" if r.get('sender_filter') else ""
                    bdy_f = f"Body: '{r['keyword_filter']}'" if r.get('keyword_filter') else ""
                    criteria = " • ".join(filter(None, [sub_f, snd_f, bdy_f])) or "Any Message"
                    st.markdown(f"**Filters ({r.get('condition_logic', 'AND')}):** {criteria}")
                    dest = r.get('notification_email') or Config.NOTIFICATION_EMAIL or "Default Alert Address"
                    st.caption(f"Alert To: {dest}")
                with rc3:
                    st.metric("Triggers", f"{r.get('trigger_count', 0)} times")
                with rc4:
                    toggle_btn = "Disable" if r['enabled'] else "Enable"
                    if st.button(toggle_btn, key=f"toggle_rule_{r['id']}"):
                        db.toggle_rule(r['id'])
                        st.rerun()
                    if st.button("🗑️ Delete", key=f"del_rule_{r['id']}"):
                        db.delete_rule(r['id'])
                        st.success(f"Deleted rule '{r['rule_name']}'")
                        st.rerun()
                st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid rgba(148, 163, 184, 0.1);' />", unsafe_allow_html=True)
    else:
        st.info("No notification rules configured yet. Create your first rule above!")

    st.markdown("---")

    # Step 3: Rule Matched Trigger Activity Log
    st.markdown("### 🔔 Rule Matched Activity History")
    monitored = db.get_monitored_emails(limit=50)
    matched_history = []

    for m in monitored:
        rules_raw = m.get('rule_matches')
        if rules_raw:
            try:
                parsed_rules = json.loads(rules_raw) if isinstance(rules_raw, str) else rules_raw
                if parsed_rules and (isinstance(parsed_rules, list) and len(parsed_rules) > 0):
                    rule_names = ", ".join(parsed_rules)
                    matched_history.append({
                        "Rule": rule_names,
                        "Matched Email": f"{m.get('sender')} — {m.get('subject')}",
                        "Notification Status": "SENT" if m.get('notification_sent') else "TRIGGERED",
                        "Timestamp": format_datetime(m.get('received_at'))
                    })
            except Exception:
                pass

    if matched_history:
        st.dataframe(pd.DataFrame(matched_history), use_container_width=True, hide_index=True)
    else:
        st.info("No rule matches recorded yet. Test an incoming message in the **Email Monitoring** tab.")
