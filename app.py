import streamlit as st
import plotly.express as px
from pathlib import Path
import subprocess
import sys

st.set_page_config(
    page_title="E-Commerce Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Ensure the database exists (auto-generate on first run, e.g. after fresh deploy) ----
DB_PATH = Path(__file__).parent / "data" / "ecommerce.db"
if not DB_PATH.exists():
    with st.spinner("First run detected — generating the sample database..."):
        subprocess.run([sys.executable, str(Path(__file__).parent / "data" / "generate_data.py")], check=True)

from backend.analytics import get_kpis, revenue_over_time, orders_by_status
from backend.filters import render_sidebar_filters

st.title("🛒 E-Commerce Analytics Dashboard")
st.caption("Synthetic multi-category store · orders, customers, products, and revenue trends")

f = render_sidebar_filters()

kpis = get_kpis(f["start_date"], f["end_date"], f["regions"], f["channels"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Gross Revenue", f"${kpis['gross_revenue']:,.0f}" if kpis['gross_revenue'] else "$0")
col2.metric("Orders", f"{int(kpis['total_orders']):,}")
col3.metric("Unique Customers", f"{int(kpis['unique_customers']):,}")
col4.metric("Avg Order Value", f"${kpis['avg_order_value']:,.2f}" if kpis['avg_order_value'] else "$0")

col5, col6 = st.columns(2)
cancel_rate = (kpis['cancelled_orders'] / kpis['total_orders'] * 100) if kpis['total_orders'] else 0
return_rate = (kpis['returned_orders'] / kpis['total_orders'] * 100) if kpis['total_orders'] else 0
col5.metric("Cancellation Rate", f"{cancel_rate:.1f}%")
col6.metric("Return Rate", f"{return_rate:.1f}%")

st.divider()

left, right = st.columns([2, 1])

with left:
    st.subheader("Revenue Over Time")
    granularity = st.radio("Granularity", ["Daily", "Weekly", "Monthly"], horizontal=True, label_visibility="collapsed")
    gmap = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
    rev_df = revenue_over_time(f["start_date"], f["end_date"], f["regions"], f["channels"], gmap[granularity])
    if rev_df.empty:
        st.info("No revenue data for the selected filters.")
    else:
        fig = px.line(rev_df, x="order_date", y="revenue", markers=True)
        fig.update_layout(xaxis_title="", yaxis_title="Revenue ($)", height=420)
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Orders by Status")
    status_df = orders_by_status(f["start_date"], f["end_date"], f["regions"], f["channels"])
    if status_df.empty:
        st.info("No order data for the selected filters.")
    else:
        fig2 = px.pie(status_df, names="status", values="order_count", hole=0.45)
        fig2.update_layout(height=420)
        st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.markdown(
    "Use the pages in the sidebar for deeper dives: **Sales Analytics**, "
    "**Product Performance**, and **Customer Insights**."
)
