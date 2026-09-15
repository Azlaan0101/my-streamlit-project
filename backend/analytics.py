"""
Backend: analytics / business logic layer.

Every function returns a pandas DataFrame (or scalar) ready for the
Streamlit frontend to plot or display. No Streamlit UI code lives here,
so this module could just as easily sit behind a REST API instead.
"""
import pandas as pd
import streamlit as st
from backend.database import run_query


# ---------- Filters helper ----------

def get_filter_options():
    regions = run_query("SELECT DISTINCT region FROM orders ORDER BY region")["region"].tolist()
    channels = run_query("SELECT DISTINCT channel FROM orders ORDER BY channel")["channel"].tolist()
    categories = run_query("SELECT DISTINCT category FROM products ORDER BY category")["category"].tolist()
    min_max = run_query("SELECT MIN(order_date) AS min_d, MAX(order_date) AS max_d FROM orders")
    return {
        "regions": regions,
        "channels": channels,
        "categories": categories,
        "min_date": min_max["min_d"].iloc[0],
        "max_date": min_max["max_d"].iloc[0],
    }


def _where_clause(start_date, end_date, regions, channels, alias="o"):
    clauses = [f"{alias}.order_date BETWEEN ? AND ?"]
    params = [start_date, end_date]
    if regions:
        clauses.append(f"{alias}.region IN ({','.join('?' * len(regions))})")
        params.extend(regions)
    if channels:
        clauses.append(f"{alias}.channel IN ({','.join('?' * len(channels))})")
        params.extend(channels)
    return " AND ".join(clauses), params


# ---------- KPI / Overview ----------

@st.cache_data(ttl=600)
def get_kpis(start_date, end_date, regions=None, channels=None):
    where, params = _where_clause(start_date, end_date, regions, channels)
    df = run_query(f"""
        SELECT
            COUNT(DISTINCT o.order_id) AS total_orders,
            COUNT(DISTINCT o.customer_id) AS unique_customers,
            SUM(o.order_total) AS gross_revenue,
            AVG(o.order_total) AS avg_order_value,
            SUM(CASE WHEN o.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
            SUM(CASE WHEN o.status = 'Returned' THEN 1 ELSE 0 END) AS returned_orders
        FROM orders o
        WHERE {where}
    """, tuple(params))
    return df.iloc[0]


@st.cache_data(ttl=600)
def revenue_over_time(start_date, end_date, regions=None, channels=None, granularity="D"):
    where, params = _where_clause(start_date, end_date, regions, channels)
    df = run_query(f"""
        SELECT o.order_date, o.order_total, o.status
        FROM orders o
        WHERE {where}
    """, tuple(params))
    if df.empty:
        return df
    df["order_date"] = pd.to_datetime(df["order_date"])
    df = df[df["status"] != "Cancelled"]
    grouped = (
        df.set_index("order_date")
        .resample(granularity)["order_total"]
        .sum()
        .reset_index()
        .rename(columns={"order_total": "revenue"})
    )
    return grouped


@st.cache_data(ttl=600)
def orders_by_status(start_date, end_date, regions=None, channels=None):
    where, params = _where_clause(start_date, end_date, regions, channels)
    return run_query(f"""
        SELECT status, COUNT(*) AS order_count
        FROM orders o
        WHERE {where}
        GROUP BY status
        ORDER BY order_count DESC
    """, tuple(params))


# ---------- Sales analytics ----------

@st.cache_data(ttl=600)
def revenue_by_category(start_date, end_date, regions=None, channels=None):
    where, params = _where_clause(start_date, end_date, regions, channels)
    return run_query(f"""
        SELECT p.category, SUM(oi.line_total) AS revenue, SUM(oi.quantity) AS units_sold
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE {where} AND o.status != 'Cancelled'
        GROUP BY p.category
        ORDER BY revenue DESC
    """, tuple(params))


@st.cache_data(ttl=600)
def revenue_by_region(start_date, end_date, regions=None, channels=None):
    where, params = _where_clause(start_date, end_date, regions, channels)
    return run_query(f"""
        SELECT o.region, SUM(o.order_total) AS revenue, COUNT(DISTINCT o.order_id) AS orders
        FROM orders o
        WHERE {where} AND o.status != 'Cancelled'
        GROUP BY o.region
        ORDER BY revenue DESC
    """, tuple(params))


@st.cache_data(ttl=600)
def revenue_by_channel(start_date, end_date, regions=None, channels=None):
    where, params = _where_clause(start_date, end_date, regions, channels)
    return run_query(f"""
        SELECT o.channel, SUM(o.order_total) AS revenue, COUNT(DISTINCT o.order_id) AS orders,
               AVG(o.order_total) AS aov
        FROM orders o
        WHERE {where} AND o.status != 'Cancelled'
        GROUP BY o.channel
        ORDER BY revenue DESC
    """, tuple(params))


@st.cache_data(ttl=600)
def sales_by_weekday(start_date, end_date, regions=None, channels=None):
    where, params = _where_clause(start_date, end_date, regions, channels)
    df = run_query(f"""
        SELECT o.order_date, o.order_total
        FROM orders o
        WHERE {where} AND o.status != 'Cancelled'
    """, tuple(params))
    if df.empty:
        return df
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["weekday"] = df["order_date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grouped = df.groupby("weekday")["order_total"].sum().reindex(order).reset_index()
    grouped.columns = ["weekday", "revenue"]
    return grouped


# ---------- Product performance ----------

@st.cache_data(ttl=600)
def top_products(start_date, end_date, regions=None, channels=None, categories=None, limit=10):
    where, params = _where_clause(start_date, end_date, regions, channels)
    cat_clause = ""
    if categories:
        cat_clause = f" AND p.category IN ({','.join('?' * len(categories))})"
        params = params + categories
    df = run_query(f"""
        SELECT p.product_name, p.category,
               SUM(oi.quantity) AS units_sold,
               SUM(oi.line_total) AS revenue,
               SUM(oi.line_total - (p.cost * oi.quantity)) AS profit
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE {where} AND o.status != 'Cancelled' {cat_clause}
        GROUP BY p.product_id
        ORDER BY revenue DESC
        LIMIT ?
    """, tuple(params) + (limit,))
    return df


@st.cache_data(ttl=600)
def product_margin_table(start_date, end_date, regions=None, channels=None):
    where, params = _where_clause(start_date, end_date, regions, channels)
    df = run_query(f"""
        SELECT p.product_name, p.category,
               SUM(oi.quantity) AS units_sold,
               SUM(oi.line_total) AS revenue,
               SUM(oi.line_total - (p.cost * oi.quantity)) AS profit
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE {where} AND o.status != 'Cancelled'
        GROUP BY p.product_id
        ORDER BY profit DESC
    """, tuple(params))
    if not df.empty:
        df["margin_pct"] = (df["profit"] / df["revenue"] * 100).round(1)
    return df


# ---------- Customer insights ----------

@st.cache_data(ttl=600)
def customer_segments(start_date, end_date, regions=None, channels=None):
    """RFM-style segmentation: new / returning / VIP by order count in the period."""
    where, params = _where_clause(start_date, end_date, regions, channels)
    df = run_query(f"""
        SELECT o.customer_id, COUNT(*) AS order_count, SUM(o.order_total) AS total_spent
        FROM orders o
        WHERE {where} AND o.status != 'Cancelled'
        GROUP BY o.customer_id
    """, tuple(params))
    if df.empty:
        return df

    def segment(row):
        if row["order_count"] == 1:
            return "One-time"
        elif row["order_count"] <= 3:
            return "Returning"
        else:
            return "VIP"

    df["segment"] = df.apply(segment, axis=1)
    summary = df.groupby("segment").agg(
        customers=("customer_id", "count"),
        revenue=("total_spent", "sum"),
        avg_spent=("total_spent", "mean"),
    ).reset_index()
    return summary


@st.cache_data(ttl=600)
def top_customers(start_date, end_date, regions=None, channels=None, limit=10):
    where, params = _where_clause(start_date, end_date, regions, channels)
    return run_query(f"""
        SELECT c.first_name || ' ' || c.last_name AS customer_name, c.region,
               COUNT(o.order_id) AS orders, SUM(o.order_total) AS total_spent
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE {where} AND o.status != 'Cancelled'
        GROUP BY o.customer_id
        ORDER BY total_spent DESC
        LIMIT ?
    """, tuple(params) + (limit,))


@st.cache_data(ttl=600)
def new_customers_over_time(start_date, end_date, granularity="D"):
    df = run_query("SELECT customer_id, signup_date FROM customers")
    if df.empty:
        return df
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    mask = (df["signup_date"] >= start_date) & (df["signup_date"] <= end_date)
    df = df[mask]
    grouped = (
        df.set_index("signup_date")
        .resample(granularity)["customer_id"]
        .count()
        .reset_index()
        .rename(columns={"customer_id": "new_customers"})
    )
    return grouped


@st.cache_data(ttl=600)
def monthly_cohort_retention():
    """Cohort retention matrix: % of each signup-month cohort still ordering in later months."""
    orders = run_query("SELECT customer_id, order_date FROM orders WHERE status != 'Cancelled'")
    customers = run_query("SELECT customer_id, signup_date FROM customers")
    if orders.empty or customers.empty:
        return pd.DataFrame()

    orders["order_date"] = pd.to_datetime(orders["order_date"])
    customers["signup_date"] = pd.to_datetime(customers["signup_date"])
    merged = orders.merge(customers, on="customer_id")
    merged["cohort_month"] = merged["signup_date"].dt.to_period("M")
    merged["order_month"] = merged["order_date"].dt.to_period("M")
    merged["period_number"] = (merged["order_month"] - merged["cohort_month"]).apply(lambda x: x.n)
    merged = merged[merged["period_number"] >= 0]

    cohort_sizes = merged.groupby("cohort_month")["customer_id"].nunique()
    cohort_data = merged.groupby(["cohort_month", "period_number"])["customer_id"].nunique().reset_index()
    cohort_pivot = cohort_data.pivot(index="cohort_month", columns="period_number", values="customer_id")
    retention = cohort_pivot.divide(cohort_sizes, axis=0).round(3) * 100

    # keep it readable: most recent 12 cohorts, first 6 periods
    retention = retention.tail(12).iloc[:, :6]
    retention.index = retention.index.astype(str)
    return retention
