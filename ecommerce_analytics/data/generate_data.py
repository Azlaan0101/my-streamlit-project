"""
Generates a realistic synthetic e-commerce dataset and loads it into a
local SQLite database (data/ecommerce.db).

Run once with:  python data/generate_data.py
"""
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

DB_PATH = Path(__file__).parent / "ecommerce.db"

CATEGORIES = {
    "Electronics": ["Wireless Earbuds", "Smart Watch", "Bluetooth Speaker", "Laptop Stand", "Phone Case", "USB-C Hub"],
    "Apparel": ["Cotton T-Shirt", "Denim Jacket", "Running Shoes", "Hoodie", "Wool Sweater", "Sneakers"],
    "Home & Kitchen": ["Coffee Maker", "Air Fryer", "Cutting Board Set", "Throw Blanket", "Scented Candle", "Blender"],
    "Beauty": ["Face Serum", "Shampoo Bar", "Lip Balm Set", "Perfume", "Makeup Brush Set", "Sunscreen SPF50"],
    "Sports & Outdoors": ["Yoga Mat", "Water Bottle", "Resistance Bands", "Camping Tent", "Hiking Backpack", "Dumbbell Set"],
    "Books": ["Mystery Novel", "Cookbook", "Sci-Fi Anthology", "Self-Help Guide", "History Book", "Children's Story Book"],
}

CHANNELS = ["Organic Search", "Paid Ads", "Social Media", "Email", "Direct", "Referral"]
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
PAYMENT_METHODS = ["Credit Card", "PayPal", "Debit Card", "Apple Pay", "Google Pay"]
STATUSES = ["Delivered", "Delivered", "Delivered", "Delivered", "Shipped", "Cancelled", "Returned"]

FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Jamie", "Avery", "Quinn",
               "Reese", "Skyler", "Dakota", "Rowan", "Emerson", "Finley", "Hayden", "Kendall", "Logan", "Peyton"]
LAST_NAMES = ["Smith", "Johnson", "Lee", "Brown", "Garcia", "Miller", "Davis", "Wilson", "Martinez", "Clark",
              "Rodriguez", "Lewis", "Walker", "Hall", "Young", "King", "Wright", "Scott", "Green", "Baker"]

N_CUSTOMERS = 1200
N_PRODUCTS_PER_ITEM = 1
N_DAYS = 365 * 2  # two years of history
AVG_ORDERS_PER_DAY = 28


def build_products():
    products = []
    pid = 1
    for cat, items in CATEGORIES.items():
        for item in items:
            base_price = round(random.uniform(12, 220), 2)
            cost = round(base_price * random.uniform(0.35, 0.6), 2)
            products.append({
                "product_id": pid,
                "product_name": item,
                "category": cat,
                "price": base_price,
                "cost": cost,
            })
            pid += 1
    return products


def build_customers():
    customers = []
    start = datetime.now() - timedelta(days=N_DAYS + 60)
    for cid in range(1, N_CUSTOMERS + 1):
        signup_offset = random.randint(0, N_DAYS)
        signup_date = start + timedelta(days=signup_offset)
        customers.append({
            "customer_id": cid,
            "first_name": random.choice(FIRST_NAMES),
            "last_name": random.choice(LAST_NAMES),
            "region": random.choices(REGIONS, weights=[35, 28, 20, 10, 7])[0],
            "signup_date": signup_date.strftime("%Y-%m-%d"),
            "acquisition_channel": random.choice(CHANNELS),
        })
    return customers


def build_orders(products, customers):
    orders = []
    order_items = []
    order_id = 1
    item_id = 1
    today = datetime.now()

    # weight customers so some are repeat buyers (power law-ish)
    customer_weights = [random.paretovariate(1.5) for _ in customers]

    for day_offset in range(N_DAYS, 0, -1):
        order_date = today - timedelta(days=day_offset)
        # weekly seasonality: weekends slightly higher, plus a growth trend + holiday bump in Nov/Dec
        weekday_factor = 1.25 if order_date.weekday() >= 5 else 1.0
        growth_factor = 0.6 + 0.4 * ((N_DAYS - day_offset) / N_DAYS)  # gradual growth over time
        holiday_factor = 1.8 if order_date.month in (11, 12) else 1.0
        n_orders_today = max(1, int(random.gauss(AVG_ORDERS_PER_DAY, 6) * weekday_factor * growth_factor * holiday_factor))

        for _ in range(n_orders_today):
            cust = random.choices(customers, weights=customer_weights, k=1)[0]
            status = random.choice(STATUSES)
            n_items = random.choices([1, 2, 3, 4], weights=[50, 30, 15, 5])[0]
            chosen_products = random.sample(products, k=min(n_items, len(products)))

            order_total = 0.0
            item_rows = []
            for p in chosen_products:
                qty = random.choices([1, 2, 3], weights=[70, 22, 8])[0]
                discount_pct = random.choices([0, 0, 0, 10, 15, 20], weights=[50, 15, 10, 10, 10, 5])[0]
                unit_price = round(p["price"] * (1 - discount_pct / 100), 2)
                line_total = round(unit_price * qty, 2)
                order_total += line_total
                item_rows.append({
                    "order_item_id": item_id,
                    "order_id": order_id,
                    "product_id": p["product_id"],
                    "quantity": qty,
                    "unit_price": unit_price,
                    "discount_pct": discount_pct,
                    "line_total": line_total,
                })
                item_id += 1

            orders.append({
                "order_id": order_id,
                "customer_id": cust["customer_id"],
                "order_date": order_date.strftime("%Y-%m-%d"),
                "channel": random.choice(CHANNELS),
                "region": cust["region"],
                "payment_method": random.choice(PAYMENT_METHODS),
                "status": status,
                "order_total": round(order_total, 2),
            })
            order_items.extend(item_rows)
            order_id += 1

    return orders, order_items


def load_into_sqlite(products, customers, orders, order_items):
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE products (
        product_id INTEGER PRIMARY KEY, product_name TEXT, category TEXT,
        price REAL, cost REAL)""")
    cur.execute("""CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT,
        region TEXT, signup_date TEXT, acquisition_channel TEXT)""")
    cur.execute("""CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT,
        channel TEXT, region TEXT, payment_method TEXT, status TEXT, order_total REAL)""")
    cur.execute("""CREATE TABLE order_items (
        order_item_id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER,
        quantity INTEGER, unit_price REAL, discount_pct INTEGER, line_total REAL)""")

    cur.executemany(
        "INSERT INTO products VALUES (:product_id,:product_name,:category,:price,:cost)", products)
    cur.executemany(
        "INSERT INTO customers VALUES (:customer_id,:first_name,:last_name,:region,:signup_date,:acquisition_channel)",
        customers)
    cur.executemany(
        "INSERT INTO orders VALUES (:order_id,:customer_id,:order_date,:channel,:region,:payment_method,:status,:order_total)",
        orders)
    cur.executemany(
        "INSERT INTO order_items VALUES (:order_item_id,:order_id,:product_id,:quantity,:unit_price,:discount_pct,:line_total)",
        order_items)

    for stmt in [
        "CREATE INDEX idx_orders_date ON orders(order_date)",
        "CREATE INDEX idx_orders_customer ON orders(customer_id)",
        "CREATE INDEX idx_items_order ON order_items(order_id)",
        "CREATE INDEX idx_items_product ON order_items(product_id)",
    ]:
        cur.execute(stmt)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("Generating products...")
    products = build_products()
    print("Generating customers...")
    customers = build_customers()
    print("Generating orders + order items (this may take a moment)...")
    orders, order_items = build_orders(products, customers)
    print(f"Loading {len(products)} products, {len(customers)} customers, "
          f"{len(orders)} orders, {len(order_items)} order items into SQLite...")
    load_into_sqlite(products, customers, orders, order_items)
    print(f"Done. Database written to {DB_PATH}")
