import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Product Performance", page_icon="📦", layout="wide")

from backend.analytics import top_products, product_margin_table
from backend.filters import render_sidebar_filters

st.title("📦 Product Performance")
f = render_sidebar_filters()

selected_categories = st.multiselect(
    "Filter by category (optional)", options=f["categories"], default=[]
)

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Top 10 Products by Revenue")
    df = top_products(f["start_date"], f["end_date"], f["regions"], f["channels"],
                       selected_categories or None, limit=10)
    if df.empty:
        st.info("No data for the selected filters.")
    else:
        fig = px.bar(df.sort_values("revenue"), x="revenue", y="product_name",
                     orientation="h", color="category", text_auto=".2s")
        fig.update_layout(xaxis_title="Revenue ($)", yaxis_title="", height=450)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Units Sold (Top 10)")
    if not df.empty:
        fig2 = px.pie(df, names="product_name", values="units_sold", hole=0.4)
        fig2.update_layout(showlegend=False, height=450)
        fig2.update_traces(textinfo="label+percent")
        st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Full Product Profitability Table")
margin_df = product_margin_table(f["start_date"], f["end_date"], f["regions"], f["channels"])
if margin_df.empty:
    st.info("No data for the selected filters.")
else:
    st.dataframe(
        margin_df.rename(columns={
            "product_name": "Product", "category": "Category", "units_sold": "Units Sold",
            "revenue": "Revenue", "profit": "Profit", "margin_pct": "Margin %"
        }).style.format({"Revenue": "${:,.2f}", "Profit": "${:,.2f}", "Margin %": "{:.1f}%"}),
        use_container_width=True, hide_index=True, height=420,
    )
