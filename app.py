"""
Email Automation & Notification System — Master Streamlit Web Application
A professional enterprise-grade platform for transactional dispatch, bulk personalized campaigns,
IMAP inbox intelligence, rule-based notifications, and background task scheduling.
"""

import streamlit as st
import os
import sys

# Ensure root workspace is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config import Config
from database import EmailDatabase
from utils.helpers import load_custom_css, render_header

# Import modular page views
from pages.dashboard import render_dashboard
from pages.send_email import render_send_email
from pages.bulk_email import render_bulk_email
from pages.monitoring import render_monitoring
from pages.notifications import render_notifications
from pages.scheduler_page import render_scheduler_page
from pages.history import render_history
from pages.statistics import render_statistics
from pages.settings import render_settings

# Page Configuration
st.set_page_config(
    page_title="Email Automation & Notification System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize SQLite Database & Tables
    EmailDatabase()

    # Inject SaaS Custom Styling
    load_custom_css()

    # Render Header Banner
    render_header(
        title="Email Automation & Notification System",
        subtitle="Automate • Personalize • Monitor • Schedule"
    )

    # Sidebar Navigation Menu Items
    menu_options = [
        "Dashboard",
        "Send Email",
        "Bulk Email",
        "Email Monitoring",
        "Notification Rules",
        "Scheduler",
        "Email History",
        "Statistics",
        "Settings"
    ]

    menu_icons = {
        "Dashboard": "📊",
        "Send Email": "✉️",
        "Bulk Email": "📁",
        "Email Monitoring": "📥",
        "Notification Rules": "⚡",
        "Scheduler": "⏱️",
        "Email History": "📜",
        "Statistics": "📈",
        "Settings": "⚙️"
    }

    # Initialize session state for selected page if not present
    if 'selected_page' not in st.session_state:
        st.session_state['selected_page'] = "Dashboard"

    with st.sidebar:
        st.markdown("""
        <div style="padding: 10px 0 16px 0; border-bottom: 1px solid rgba(148, 163, 184, 0.15); margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 800; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
                <span>⚡ AuraMail Pro</span>
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Enterprise Email Automation OS</div>
        </div>
        """, unsafe_allow_html=True)

        st.caption("NAVIGATION")

        # Page selection via radio
        selected = st.radio(
            label="Navigation",
            options=menu_options,
            index=menu_options.index(st.session_state['selected_page']) if st.session_state['selected_page'] in menu_options else 0,
            format_func=lambda opt: f"{menu_icons.get(opt, '•')} {opt}",
            label_visibility="collapsed"
        )
        st.session_state['selected_page'] = selected

        st.markdown("---")
        st.caption("GATEWAY STATUS")

        # Mode Badge
        if Config.DRY_RUN:
            st.markdown(
                '<div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #fbbf24;">'
                '🟡 <b>SIMULATION MODE</b><br/><span style="color: #94a3b8; font-size: 11px;">Safe dry-run testing active</span>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #34d399;">'
                '🟢 <b>LIVE SMTP / IMAP</b><br/><span style="color: #94a3b8; font-size: 11px;">Production dispatch enabled</span>'
                '</div>',
                unsafe_allow_html=True
            )

        st.markdown(f"""
        <div style="font-size: 11px; color: #64748b; margin-top: 14px; line-height: 1.6;">
            <b>SMTP:</b> {Config.SMTP_SERVER}:{Config.SMTP_PORT}<br/>
            <b>IMAP:</b> {Config.IMAP_SERVER}:{Config.IMAP_PORT}<br/>
            <b>Database:</b> SQLite WAL Mode
        </div>
        """, unsafe_allow_html=True)

    # Route to selected page
    current_page = st.session_state['selected_page']

    if current_page == "Dashboard":
        render_dashboard()
    elif current_page == "Send Email":
        render_send_email()
    elif current_page == "Bulk Email":
        render_bulk_email()
    elif current_page == "Email Monitoring":
        render_monitoring()
    elif current_page == "Notification Rules":
        render_notifications()
    elif current_page == "Scheduler":
        render_scheduler_page()
    elif current_page == "Email History":
        render_history()
    elif current_page == "Statistics":
        render_statistics()
    elif current_page == "Settings":
        render_settings()

if __name__ == '__main__':
    main()
