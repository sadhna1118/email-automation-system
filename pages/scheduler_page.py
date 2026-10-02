"""
Email Scheduler Page
Configure and manage persistent automated tasks (Single Email, Bulk Email, Email Monitoring, Weekly Report).
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from database import EmailDatabase
from scheduler import EmailScheduler
from utils.helpers import format_datetime

def get_scheduler_instance():
    """Get or create singleton EmailScheduler in Streamlit session state"""
    if 'scheduler_instance' not in st.session_state:
        st.session_state['scheduler_instance'] = EmailScheduler()
    return st.session_state['scheduler_instance']

def render_scheduler_page():
    st.markdown("### ⏱️ Automated Task Scheduler")
    st.markdown("Set recurring timers and schedules for automated email dispatches, periodic inbox checks, and weekly performance digests.")

    db = EmailDatabase()
    scheduler = get_scheduler_instance()
    is_active = scheduler.is_running()

    # Daemon Status Card
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(
            f"**Scheduler Engine Status:** {'🟢 ACTIVE (Background daemon running)' if is_active else '⚪ IDLE (Paused)'}. "
            "Jobs are executed according to configured schedules."
        )
    with col2:
        if is_active:
            if st.button("⏹️ Pause Scheduler", use_container_width=True):
                scheduler.stop_background()
                st.rerun()
        else:
            if st.button("▶️ Start Scheduler", type="primary", use_container_width=True):
                scheduler.start_background()
                st.rerun()

    st.markdown("---")

    # Step 1: Add New Scheduled Task Form
    with st.expander("➕ Configure New Scheduled Task", expanded=True):
        with st.form("new_schedule_form", clear_on_submit=True):
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                task_name = st.text_input("Task Name *", placeholder="e.g. Daily Marketing Blast or Hourly Monitor")
                task_type = st.selectbox(
                    "Task Type *",
                    ["Single Email", "Bulk Email", "Email Monitoring", "Weekly Report"]
                )
                schedule_freq = st.selectbox(
                    "Frequency *",
                    ["Daily", "Weekly", "Specific Time / Interval"]
                )
            with t_col2:
                time_str = st.text_input(
                    "Execution Time (HH:MM in 24hr format) or Interval",
                    value="09:00",
                    help="e.g. '09:00', '18:30', or '5' for interval in minutes."
                )

                # Dynamic parameters based on task type
                params = {}
                if task_type == "Single Email":
                    s_to = st.text_input("Recipient Email", placeholder="recipient@example.com")
                    s_sub = st.text_input("Subject", placeholder="Daily Status Check")
                    s_body = st.text_area("Body", placeholder="Automated periodic message...")
                    params = {"to_email": s_to, "subject": s_sub, "body": s_body, "time": time_str}

                elif task_type == "Bulk Email":
                    csv_p = st.text_input("CSV File Path", value="data/sample_recipients.csv")
                    b_sub = st.text_input("Subject Template", value="Daily update for {name}")
                    b_body = st.text_area("Body Template", value="Hi {name}, hope you have a great day at {company}!")
                    params = {"csv_file": csv_p, "subject_template": b_sub, "body_template": b_body, "time": time_str}

                elif task_type == "Email Monitoring":
                    st.caption("Periodically connects to IMAP to fetch unseen emails and process rules.")
                    params = {"interval_minutes": 5, "time": time_str}

                elif task_type == "Weekly Report":
                    rep_day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
                    params = {"day": rep_day.lower(), "time": time_str}

            submit_task = st.form_submit_button("📅 Schedule Task", type="primary", use_container_width=True)

        if submit_task:
            if not task_name:
                st.error("Please enter a Task Name.")
            else:
                schedule_expr = f"{schedule_freq} at {time_str}"
                
                # Approximate next run calculation
                now = datetime.now()
                next_run_calc = (now + timedelta(days=1)).strftime("%Y-%m-%d ") + time_str + ":00"

                task_id = db.add_scheduled_task(
                    task_name=task_name,
                    task_type=task_type,
                    schedule_expr=schedule_expr,
                    params=params
                )
                db.update_task_execution(task_id, next_run=next_run_calc)

                # Reload into scheduler memory if active
                if is_active:
                    scheduler.load_db_tasks()

                st.success(f"✓ Task '{task_name}' successfully scheduled (ID: {task_id})!")
                st.rerun()

    st.markdown("---")

    # Step 2: Scheduled Tasks Table with Enable, Disable, and Delete Buttons
    st.markdown("### 📋 Scheduled Tasks")
    tasks = db.get_scheduled_tasks()

    if tasks:
        for t in tasks:
            with st.container():
                tc1, tc2, tc3, tc4, tc5 = st.columns([3, 2, 2, 2, 2])
                with tc1:
                    status_dot = "🟢 Active" if t['enabled'] else "⚪ Disabled"
                    st.markdown(f"**{t['task_name']}**")
                    st.caption(f"Type: `{t['task_type']}` • {status_dot}")
                with tc2:
                    st.markdown(f"**Schedule:** {t['schedule_expr']}")
                with tc3:
                    st.caption("Next Run")
                    st.write(t.get('next_run') or "Scheduled")
                with tc4:
                    st.caption("Last Run")
                    st.write(t.get('last_run') or "Never")
                with tc5:
                    b_toggle = "Disable" if t['enabled'] else "Enable"
                    if st.button(b_toggle, key=f"toggle_t_{t['id']}"):
                        db.toggle_scheduled_task(t['id'])
                        if is_active:
                            scheduler.load_db_tasks()
                        st.rerun()
                    if st.button("🗑️ Delete", key=f"del_t_{t['id']}"):
                        db.delete_scheduled_task(t['id'])
                        if is_active:
                            scheduler.load_db_tasks()
                        st.success(f"Deleted task '{t['task_name']}'")
                        st.rerun()
                st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid rgba(148, 163, 184, 0.1);' />", unsafe_allow_html=True)
    else:
        st.info("No scheduled tasks found. Add a scheduled automation job above.")
