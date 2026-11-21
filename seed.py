"""
Seed script — reset MySQL schema and load sample rows from data/*.py,
then generate at least 500 varied orders (+ line items + stock history).

    python seed.py
"""

from __future__ import annotations

import random
from collections import defaultdict
from datetime import date, datetime, timedelta

from app import create_app
from extensions import db
from models import (
    Admin,
    City,
    Driver,
    Feedback,
    Item,
    ItemType,
    Merchant,
    Order,
    OrderItem,
    Post,
    Province,
    Rating,
    Role,
    StockHistory,
    Street,
)
from data.roles import roles
from data.provinces import provinces
from data.cities import cities
from data.streets import streets
from data.posts import posts
from data.drivers import drivers
from data.merchants import merchants
from data.admins import DEFAULT_ADMIN_PASSWORD, admins
from data.item_types import item_types
from data.items import items
from data.feedbacks import feedbacks
from i18n.db_names import expand_row
from auth import hash_password

# Reproducible “random” data every time you seed.
RNG = random.Random(42)
ORDER_COUNT = 520
STATUSES = ["Delivered", "Delivered", "Delivered", "In Transit", "Pending", "Cancelled"]
# Spread across the last ~18 months up to today so dashboard date filters always hit data.
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=540)


def _index_by_city(rows, city_key="city_id"):
    by_city = defaultdict(list)
    for row in rows:
        by_city[row[city_key]].append(row)
    return by_city


def generate_orders(count: int = ORDER_COUNT):
    """
    Build varied order headers + line items.
    Picks city-consistent street/post when possible; mixes merchants, drivers,
    statuses, dates, and 1–4 items per order.
    """
    streets_by_city = _index_by_city(streets)
    posts_by_city = _index_by_city(posts)
    item_by_id = {i["id"]: i for i in items}
    all_city_ids = [c["id"] for c in cities]

    order_rows = []
    order_item_rows = []
    # Track stock deductions for non-cancelled orders (item_id -> qty sold)
    sold = defaultdict(int)
    line_id = 1

    for order_id in range(1, count + 1):
        city_id = RNG.choice(all_city_ids)
        city_streets = streets_by_city.get(city_id) or streets
        city_posts = posts_by_city.get(city_id) or posts
        street = RNG.choice(city_streets)
        post = RNG.choice(city_posts)
        # Prefer merchant in same city when available
        city_merchants = [m for m in merchants if m["city_id"] == city_id] or merchants
        merchant = RNG.choice(city_merchants)
        driver = RNG.choice(drivers)
        status = RNG.choice(STATUSES)
        span = (END_DATE - START_DATE).days
        order_date = START_DATE + timedelta(days=RNG.randint(0, span))
        delivery_days = 0 if status == "Cancelled" else RNG.randint(1, 6)

        # 1–4 distinct items per order
        n_lines = RNG.randint(1, 4)
        chosen_items = RNG.sample(items, k=min(n_lines, len(items)))
        total = 0.0
        for item in chosen_items:
            qty = RNG.randint(1, 5)
            unit = float(item["price"])
            line_total = unit * qty
            total += line_total
            order_item_rows.append(
                {
                    "id": line_id,
                    "order_id": order_id,
                    "item_id": item["id"],
                    "quantity": qty,
                    "unit_price": unit,
                    "line_total": line_total,
                }
            )
            line_id += 1
            if status != "Cancelled":
                sold[item["id"]] += qty

        order_rows.append(
            {
                "id": order_id,
                "merchant_id": merchant["id"],
                "driver_id": driver["id"],
                "post_id": post["id"],
                "city_id": city_id,
                "street_id": street["id"],
                "total_price": total,
                "status": status,
                "order_date": order_date.isoformat(),
                "delivery_days": delivery_days,
            }
        )

    # Apply sold qty to a mutable stock map (starting from seed item stock)
    stock_left = {i["id"]: i["stock"] for i in items}
    for item_id, qty in sold.items():
        stock_left[item_id] = max(0, stock_left[item_id] - qty)

    # Merchant aggregates from generated orders
    merchant_stats = defaultdict(lambda: {"orders": 0, "revenue": 0.0})
    for o in order_rows:
        if o["status"] == "Cancelled":
            continue
        merchant_stats[o["merchant_id"]]["orders"] += 1
        merchant_stats[o["merchant_id"]]["revenue"] += o["total_price"]

    updated_merchants = []
    for m in merchants:
        stats = merchant_stats.get(m["id"], {"orders": 0, "revenue": 0.0})
        updated_merchants.append(
            {
                **m,
                "total_orders": stats["orders"],
                "revenue": round(stats["revenue"], 2),
            }
        )

    updated_items = []
    for i in items:
        updated_items.append({**i, "stock": stock_left[i["id"]]})

    return order_rows, order_item_rows, updated_items, updated_merchants, sold


RATING_COMMENTS = [
    "Excellent quality",
    "Good value for money",
    "As described",
    "Packaging could be better",
    "Fast dispatch",
    "Would buy again",
    "Average experience",
    "Not what I expected",
    "Perfect for gifts",
    "Solid product",
]


def generate_ratings(count: int = 400):
    """Many item ratings (1–5) so the Ratings / Heatmap reports have enough data."""
    rows = []
    for i in range(1, count + 1):
        item = RNG.choice(items)
        # Slight bias toward higher scores (more realistic reviews)
        score = RNG.choices([1, 2, 3, 4, 5], weights=[5, 8, 18, 32, 37], k=1)[0]
        created = datetime.utcnow() - timedelta(days=RNG.randint(0, 400), hours=RNG.randint(0, 23))
        rows.append(
            expand_row(
                {
                    "id": i,
                    "item_id": item["id"],
                    "score": score,
                    "comment": RNG.choice(RATING_COMMENTS),
                    "created_at": created,
                },
                ("comment",),
            )
        )
    return rows


def seed():
    app = create_app()
    with app.app_context():
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(db.text("SET FOREIGN_KEY_CHECKS=0"))
            rows = conn.execute(db.text("SHOW TABLES")).fetchall()
            for (table_name,) in rows:
                conn.execute(db.text(f"DROP TABLE IF EXISTS `{table_name}`"))
            conn.execute(db.text("SET FOREIGN_KEY_CHECKS=1"))
        db.create_all()

        order_rows, order_item_rows, updated_items, updated_merchants, sold = generate_orders()
        rating_rows = generate_ratings(400)

        role_rows = [expand_row(r, ("name", "description")) for r in roles]
        province_rows = [expand_row(r, ("name",)) for r in provinces]
        city_rows = [expand_row(r, ("name",)) for r in cities]
        street_rows = [expand_row(r, ("name",)) for r in streets]
        post_rows = [expand_row(r, ("name",)) for r in posts]
        driver_rows = [expand_row(r, ("name", "vehicle_type")) for r in drivers]
        merchant_rows = [expand_row(r, ("name",)) for r in updated_merchants]
        # Hash passwords before insert — never store plaintext in MySQL
        admin_rows = []
        for r in admins:
            row = expand_row(r, ("name",))
            plain = row.pop("password", None) or DEFAULT_ADMIN_PASSWORD
            row["password_hash"] = hash_password(plain)
            admin_rows.append(row)
        item_type_rows = [expand_row(r, ("name", "description")) for r in item_types]
        item_rows = [expand_row(r, ("name",)) for r in updated_items]
        feedback_rows = [
            {
                **expand_row(fb, ("title", "body")),
                "created_at": datetime.utcnow() - timedelta(days=RNG.randint(0, 200)),
            }
            for fb in feedbacks
        ]

        db.session.bulk_insert_mappings(Role, role_rows)
        db.session.bulk_insert_mappings(Province, province_rows)
        db.session.bulk_insert_mappings(City, city_rows)
        db.session.bulk_insert_mappings(Street, street_rows)
        db.session.bulk_insert_mappings(Post, post_rows)
        db.session.bulk_insert_mappings(Driver, driver_rows)
        db.session.bulk_insert_mappings(Merchant, merchant_rows)
        db.session.bulk_insert_mappings(Admin, admin_rows)
        db.session.bulk_insert_mappings(ItemType, item_type_rows)
        db.session.bulk_insert_mappings(Item, item_rows)
        db.session.bulk_insert_mappings(Order, order_rows)
        db.session.bulk_insert_mappings(OrderItem, order_item_rows)
        db.session.bulk_insert_mappings(Rating, rating_rows)
        db.session.bulk_insert_mappings(Feedback, feedback_rows)
        db.session.commit()

        # Stock history: one sale row per non-cancelled line item
        history_rows = []
        running = {i["id"]: i["stock"] + sold.get(i["id"], 0) for i in item_rows}
        for oi in order_item_rows:
            order = next(o for o in order_rows if o["id"] == oi["order_id"])
            if order["status"] == "Cancelled":
                continue
            item_id = oi["item_id"]
            before = running[item_id]
            after = before - oi["quantity"]
            running[item_id] = after
            history_rows.append(
                {
                    "item_id": item_id,
                    "change_qty": -oi["quantity"],
                    "stock_before": before,
                    "stock_after": after,
                    "reason": "order_sale",
                    "order_id": oi["order_id"],
                    "note": f"Seed order #{oi['order_id']}",
                }
            )

        if history_rows:
            chunk = 500
            for i in range(0, len(history_rows), chunk):
                db.session.bulk_insert_mappings(StockHistory, history_rows[i : i + chunk])
            db.session.commit()

        print(
            f"Seed complete: {len(order_rows)} orders, "
            f"{len(order_item_rows)} order lines, "
            f"{len(history_rows)} stock-history rows, "
            f"{len(rating_rows)} ratings, "
            f"{len(feedbacks)} feedbacks, "
            f"{len(admin_rows)} admins (passwords hashed)."
        )
        print(f"Login demo: ahmed@postal.iq  /  {DEFAULT_ADMIN_PASSWORD}")


if __name__ == "__main__":
    seed()
