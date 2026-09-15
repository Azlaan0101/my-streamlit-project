import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Customer Insights", page_icon="👥", layout="wide")

from backend.analytics import customer_segments, top_customers, new_customers_over_time, monthly_cohort_retention
from backend.filters import render_sidebar_filters

st.title("👥 Customer Insights")
f = render_sidebar_filters()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Customer Segments")
    seg_df = customer_segments(f["start_date"], f["end_date"], f["regions"], f["channels"])
    if seg_df.empty:
        st.info("No data for the selected filters.")
    else:
        fig = px.pie(seg_df, names="segment", values="customers", hole=0.45,
                     color="segment",
                     color_discrete_map={"One-time": "#93c5fd", "Returning": "#3b82f6", "VIP": "#1e3a8a"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            seg_df.rename(columns={"segment": "Segment", "customers": "Customers",
                                    "revenue": "Revenue", "avg_spent": "Avg Spend"})
            .style.format({"Revenue": "${:,.0f}", "Avg Spend": "${:,.2f}"}),
            use_container_width=True, hide_index=True,
        )

with col2:
    st.subheader("New Customer Signups Over Time")
    new_df = new_customers_over_time(f["start_date"], f["end_date"], "W")
    if new_df.empty:
        st.info("No signups in this range.")
    else:
        fig2 = px.area(new_df, x="signup_date", y="new_customers")
        fig2.update_layout(xaxis_title="", yaxis_title="New Customers")
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader("Top 10 Customers by Spend")
top_df = top_customers(f["start_date"], f["end_date"], f["regions"], f["channels"], limit=10)
if top_df.empty:
    st.info("No data for the selected filters.")
else:
    st.dataframe(
        top_df.rename(columns={"customer_name": "Customer", "region": "Region",
                                "orders": "Orders", "total_spent": "Total Spent"})
        .style.format({"Total Spent": "${:,.2f}"}),
        use_container_width=True, hide_index=True,
    )

st.divider()

st.subheader("Monthly Cohort Retention (%)")
st.caption("Of customers who signed up in a given month, what % placed an order N months later.")
cohort_df = monthly_cohort_retention()
if cohort_df.empty:
    st.info("Not enough data to build cohorts yet.")
else:
    st.dataframe(
        cohort_df.style.background_gradient(cmap="Blues", axis=None).format("{:.0f}%", na_rep="—"),
        use_container_width=True,
    )
