"""
Shared sidebar filter widget so every page has consistent date/region/channel
filtering without duplicating code.
"""
from datetime import datetime, timedelta
import streamlit as st
from backend.analytics import get_filter_options


def render_sidebar_filters():
    opts = get_filter_options()
    min_date = datetime.strptime(opts["min_date"], "%Y-%m-%d").date()
    max_date = datetime.strptime(opts["max_date"], "%Y-%m-%d").date()
    default_start = max(min_date, max_date - timedelta(days=90))

    st.sidebar.header("Filters")
    date_range = st.sidebar.date_input(
        "Date range",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, max_date

    regions = st.sidebar.multiselect("Region", options=opts["regions"], default=[])
    channels = st.sidebar.multiselect("Acquisition channel", options=opts["channels"], default=[])

    st.sidebar.caption("Leave a filter empty to include all values.")

    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "regions": regions or None,
        "channels": channels or None,
        "categories": opts["categories"],
    }
