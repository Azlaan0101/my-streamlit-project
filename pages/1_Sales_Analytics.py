import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Sales Analytics", page_icon="📈", layout="wide")

from backend.analytics import revenue_by_category, revenue_by_region, revenue_by_channel, sales_by_weekday
from backend.filters import render_sidebar_filters

st.title("📈 Sales Analytics")
f = render_sidebar_filters()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by Category")
    df = revenue_by_category(f["start_date"], f["end_date"], f["regions"], f["channels"])
    if df.empty:
        st.info("No data for the selected filters.")
    else:
        fig = px.bar(df, x="category", y="revenue", color="category", text_auto=".2s")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Revenue ($)")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Revenue by Region")
    df2 = revenue_by_region(f["start_date"], f["end_date"], f["regions"], f["channels"])
    if df2.empty:
        st.info("No data for the selected filters.")
    else:
        fig2 = px.bar(df2, x="region", y="revenue", color="region", text_auto=".2s")
        fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="Revenue ($)")
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

col3, col4 = st.columns(2)

with col3:
    st.subheader("Revenue & AOV by Channel")
    df3 = revenue_by_channel(f["start_date"], f["end_date"], f["regions"], f["channels"])
    if df3.empty:
        st.info("No data for the selected filters.")
    else:
        fig3 = px.bar(df3, x="channel", y="revenue", color="channel", text_auto=".2s")
        fig3.update_layout(showlegend=False, xaxis_title="", yaxis_title="Revenue ($)")
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(
            df3.rename(columns={"channel": "Channel", "revenue": "Revenue",
                                 "orders": "Orders", "aov": "Avg Order Value"}),
            use_container_width=True, hide_index=True,
        )

with col4:
    st.subheader("Revenue by Day of Week")
    df4 = sales_by_weekday(f["start_date"], f["end_date"], f["regions"], f["channels"])
    if df4.empty:
        st.info("No data for the selected filters.")
    else:
        fig4 = px.bar(df4, x="weekday", y="revenue")
        fig4.update_layout(xaxis_title="", yaxis_title="Revenue ($)")
        st.plotly_chart(fig4, use_container_width=True)
