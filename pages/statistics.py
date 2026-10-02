"""
Statistics Page
Visual analytics, delivery breakdown, daily dispatch volume charts, and performance digests
calculated directly from the SQLite database.
"""

import streamlit as st
import pandas as pd
import altair as alt
from database import EmailDatabase

def render_statistics():
    st.markdown("### 📊 Email System Analytics & Metrics")
    st.markdown("Real-time delivery statistics and volume trends calculated strictly from actual SQLite database records.")

    db = EmailDatabase()
    stats = db.get_email_stats()

    # Top Key Metrics Bar
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emails Processed", f"{stats['total']:,}")
    c2.metric("Successful Deliveries", f"{stats['sent']:,}", delta=f"{stats['success_rate']}% Success Rate")
    c3.metric("Failed Deliveries", f"{stats['failed']:,}", delta="-0.0%" if stats['failed'] == 0 else "Failures", delta_color="inverse")
    c4.metric("Inbox Messages Monitored", f"{stats['monitored']:,}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Rule Alerts Triggered", f"{stats['notifications']:,}")
    c6.metric("Active Contacts in DB", f"{stats['active_contacts']:,}")
    c7.metric("Email Open Conversions", f"{stats['opened']:,}", delta=f"{stats['open_rate']}% Open Rate")
    c8.metric("Click Conversions", f"{stats['clicked']:,}", delta=f"{stats['click_rate']}% Click Rate")

    st.markdown("---")

    # Chart Section
    st.markdown("#### 📈 Dispatch Distribution & Activity Trends")

    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.markdown("**Emails Sent Over Recent Days**")
        daily_stats = stats.get('daily_stats', [])

        if daily_stats:
            daily_df = pd.DataFrame(daily_stats)
            # Melt for stacked bar chart
            melted_df = daily_df.melt(id_vars=['date'], value_vars=['sent', 'failed'], var_name='Type', value_name='Count')
            melted_df['Type'] = melted_df['Type'].replace({'sent': 'Successful', 'failed': 'Failed'})

            chart = alt.Chart(melted_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X('date:T', title='Date', axis=alt.Axis(format='%b %d')),
                y=alt.Y('Count:Q', title='Email Volume'),
                color=alt.Color('Type:N', scale=alt.Scale(domain=['Successful', 'Failed'], range=['#10b981', '#f43f5e'])),
                tooltip=['date:T', 'Type:N', 'Count:Q']
            ).properties(height=320)

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No daily send history logged yet. Send a test email to populate the trend graph.")

    with col_chart2:
        st.markdown("**Successful vs Failed Ratio**")
        sent = stats.get('sent', 0)
        failed = stats.get('failed', 0)

        if sent + failed > 0:
            pie_data = pd.DataFrame({
                "Status": ["Successful", "Failed"],
                "Count": [sent, failed]
            })

            pie_chart = alt.Chart(pie_data).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color("Status:N", scale=alt.Scale(domain=["Successful", "Failed"], range=["#10b981", "#f43f5e"])),
                tooltip=["Status:N", "Count:Q"]
            ).properties(height=320)

            st.altair_chart(pie_chart, use_container_width=True)
        else:
            st.info("Send emails to view delivery ratio breakdown.")

    st.markdown("---")

    # System Health Breakdown Table
    st.markdown("#### 🛡️ Deliverability & System Health Summary")
    health_data = [
        {"Indicator": "Delivery Rate", "Value": f"{stats['delivery_rate']}%", "Standard Benchmark": "> 95.0%", "Health": "Optimal" if stats['delivery_rate'] >= 95 else "Attention Needed"},
        {"Indicator": "Failure Rate", "Value": f"{round(100 - stats['delivery_rate'], 1)}%", "Standard Benchmark": "< 5.0%", "Health": "Optimal" if stats['delivery_rate'] >= 95 else "Check SMTP Config"},
        {"Indicator": "Open Tracking Rate", "Value": f"{stats['open_rate']}%", "Standard Benchmark": "20% – 40%", "Health": "Tracked"},
        {"Indicator": "Click-Through Rate", "Value": f"{stats['click_rate']}%", "Standard Benchmark": "2% – 5%", "Health": "Tracked"},
        {"Indicator": "Active Automation Rules", "Value": str(stats['active_rules']), "Standard Benchmark": ">= 1", "Health": "Configured"}
    ]
    st.dataframe(pd.DataFrame(health_data), use_container_width=True, hide_index=True)
