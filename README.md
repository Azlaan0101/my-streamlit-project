# E-Commerce Analytics Dashboard

A full-stack analytics app built with **Python + Streamlit**, backed by a **SQLite** database
and a synthetic dataset (~19k orders / 1,200 customers / 36 products / 2 years of history).

## Architecture

```
ecommerce_analytics/
├── app.py                  # Frontend entry point — Overview / KPI page
├── pages/                  # Frontend — additional Streamlit pages (auto-routed)
│   ├── 1_Sales_Analytics.py
│   ├── 2_Product_Performance.py
│   └── 3_Customer_Insights.py
├── backend/                # Backend — all SQL + business logic, no UI code
│   ├── database.py         # SQLite connection layer
│   ├── analytics.py        # Cached query functions (KPIs, cohorts, segments...)
│   └── filters.py          # Shared sidebar filter widget
├── data/
│   ├── generate_data.py    # Synthetic data generator (run once to seed the DB)
│   └── ecommerce.db        # Generated SQLite database (gitignored, auto-built)
├── .streamlit/config.toml  # Theme
├── requirements.txt
└── Dockerfile
```

**Why this split:** Streamlit runs frontend and backend in the same Python process, but the
`backend/` package is written with no Streamlit UI calls (except `st.cache_data` for
performance) — every function just takes filters and returns a DataFrame. That means the same
`backend/analytics.py` could be dropped behind a FastAPI endpoint later without rewriting logic.

## Features

- **Overview**: revenue trend, KPIs (revenue, orders, AOV, cancellation/return rate), order status breakdown
- **Sales Analytics**: revenue by category, region, channel, day-of-week, channel AOV comparison
- **Product Performance**: top products by revenue, units sold, full profitability/margin table
- **Customer Insights**: RFM-style segments (one-time / returning / VIP), top spenders, signup growth, monthly cohort retention heatmap
- Global sidebar filters (date range, region, channel) shared across every page
- Query results cached with `st.cache_data` so switching filters/pages stays fast

## Run locally

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate the sample database (only needed once — app.py also auto-generates
#    it on first launch if it's missing)
python data/generate_data.py

# 4. Launch the app
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

### Using your own data instead of the synthetic dataset

Replace the contents of `data/ecommerce.db` by pointing `generate_data.py`'s `load_into_sqlite`
step at your own CSVs/exports, keeping the same four tables (`products`, `customers`, `orders`,
`order_items`) and column names — the rest of the app needs no changes. For a real production
data source, swap `backend/database.py`'s `sqlite3.connect(...)` for a connection to Postgres/
MySQL/Snowflake/etc. (e.g. via `sqlalchemy`); every function in `analytics.py` uses plain SQL
strings and will work unchanged against another SQL engine with minor syntax tweaks.

---

## Deployment

### Option A — Streamlit Community Cloud (free, easiest)

1. Push this folder to a **public or private GitHub repo**.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **"New app"**, select the repo/branch, and set the main file path to `app.py`.
4. Deploy. `app.py` auto-generates `data/ecommerce.db` on first boot if it isn't already
   committed, so no extra setup step is required.
5. Every push to the connected branch auto-redeploys.

> Tip: commit `data/ecommerce.db` to the repo (or run `generate_data.py` once and commit the
> file) so the first page load is instant instead of waiting on data generation.

### Option B — Docker (any cloud: Render, Fly.io, AWS/GCP/Azure, a VPS)

```bash
# Build
docker build -t ecommerce-analytics .

# Run locally to test
docker run -p 8501:8501 ecommerce-analytics
```

Then push the image to a registry and deploy it on your platform of choice:

- **Render**: "New Web Service" → connect repo → it detects the Dockerfile automatically.
- **Fly.io**: `fly launch` (detects the Dockerfile), then `fly deploy`.
- **AWS App Runner / GCP Cloud Run / Azure Container Apps**: push the image to
  ECR/Artifact Registry/ACR, then point the service at it. All three support the
  `streamlit run ... --server.port=$PORT` pattern; Cloud Run in particular requires
  reading the `PORT` env var — swap the Dockerfile's hardcoded `8501` for `${PORT:-8501}`
  if deploying there.

### Option C — A plain VM / EC2 / Droplet

```bash
sudo apt update && sudo apt install -y python3-pip
pip3 install -r requirements.txt
python3 data/generate_data.py
# Run persistently with a process manager:
nohup streamlit run app.py --server.port=80 --server.address=0.0.0.0 &
```

For production, put this behind Nginx (reverse proxy + TLS via Let's Encrypt) rather than
exposing Streamlit's dev server directly on port 80/443, and run it under `systemd` or `pm2`
instead of `nohup` so it restarts on crash/reboot.

## Notes on the synthetic data

`data/generate_data.py` generates two years of orders with: weekly seasonality (higher weekend
volume), a gradual growth trend, a Nov/Dec holiday demand spike, realistic discounting, and a
Pareto-distributed mix of one-time vs. repeat customers so cohort/segment charts look like a
real store rather than uniform noise. Re-run the script any time to regenerate with a new seed
(edit `random.seed(42)` at the top of the file).
