"""
Dashboard report charts — filtered business reports (not one-button-per-lecture-chart).

Each report returns several charts with different chart types.
Filters: province, city, merchant, driver, status, date range / presets.
"""

from __future__ import annotations

import base64
import io
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from models import City, Driver, Item, ItemType, Merchant, Order, OrderItem, Post, Province

sns.set_theme(style="whitegrid", palette="viridis")
COLORS = ["#0d7377", "#14919b", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#264653", "#457b9d"]


def _to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def resolve_date_range(filters: dict):
    """
    Apply preset (today/week/month/year) or explicit date_from / date_to.
    Preset wins when provided.
    """
    today = date.today()
    preset = (filters.get("preset") or "").strip().lower()
    date_from = _parse_date(filters.get("date_from"))
    date_to = _parse_date(filters.get("date_to"))

    # Rolling windows (not only calendar periods) so seed/demo data still shows up.
    if preset == "today":
        return today, today
    if preset == "week":
        return today - timedelta(days=6), today
    if preset == "month":
        return today - timedelta(days=29), today
    if preset == "year":
        return today - timedelta(days=364), today
    return date_from, date_to


def _filtered_orders(filters: dict):
    """Load active orders with optional filters applied in SQL."""
    query = Order.query.filter(Order.deleted_at.is_(None))

    province_id = filters.get("province_id")
    city_id = filters.get("city_id")
    merchant_id = filters.get("merchant_id")
    driver_id = filters.get("driver_id")
    post_id = filters.get("post_id")
    status = (filters.get("status") or "").strip()
    date_from, date_to = resolve_date_range(filters)

    if city_id:
        query = query.filter(Order.city_id == int(city_id))
    elif province_id:
        city_ids = [
            c.id for c in City.query.filter(
                City.deleted_at.is_(None),
                City.province_id == int(province_id),
            ).all()
        ]
        if not city_ids:
            return []
        query = query.filter(Order.city_id.in_(city_ids))

    if merchant_id:
        query = query.filter(Order.merchant_id == int(merchant_id))
    if driver_id:
        query = query.filter(Order.driver_id == int(driver_id))
    if post_id:
        query = query.filter(Order.post_id == int(post_id))
    if status:
        query = query.filter(Order.status == status)
    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)

    return query.order_by(Order.order_date.asc()).all()


def _lookups():
    cities = {c.id: c for c in City.query.filter(City.deleted_at.is_(None)).all()}
    provinces = {p.id: p for p in Province.query.filter(Province.deleted_at.is_(None)).all()}
    merchants = {m.id: m for m in Merchant.query.filter(Merchant.deleted_at.is_(None)).all()}
    drivers = {d.id: d for d in Driver.query.filter(Driver.deleted_at.is_(None)).all()}
    posts = {p.id: p for p in Post.query.filter(Post.deleted_at.is_(None)).all()}
    items = {i.id: i for i in Item.query.filter(Item.deleted_at.is_(None)).all()}
    item_types = {t.id: t for t in ItemType.query.filter(ItemType.deleted_at.is_(None)).all()}
    return cities, provinces, merchants, drivers, posts, items, item_types


def _empty_chart(message):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.axis("off")
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, color="#5f7375")
    return _to_base64(fig)


def _top_n(counter: Counter, n=12):
    return counter.most_common(n)


def _bar(labels, values, title, ylabel, color=COLORS[0], horizontal=False):
    if not labels:
        return _empty_chart("No data for this filter")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    if horizontal:
        ax.barh(labels[::-1], values[::-1], color=color)
        ax.set_xlabel(ylabel)
    else:
        ax.bar(labels, values, color=color)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=35)
    ax.set_title(title)
    fig.tight_layout()
    return _to_base64(fig)


def _pie(labels, values, title, donut=False):
    if not labels:
        return _empty_chart("No data for this filter")
    fig, ax = plt.subplots(figsize=(6.5, 5))
    wedges, *_ = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        colors=COLORS[: max(len(labels), 1)],
        startangle=90,
        pctdistance=0.75 if donut else 0.6,
    )
    if donut:
        ax.add_artist(plt.Circle((0, 0), 0.50, fc="white"))
        ax.text(0, 0, f"{sum(values)}\norders", ha="center", va="center", fontsize=10, fontweight="bold")
    ax.set_title(title)
    fig.tight_layout()
    return _to_base64(fig)


def _line(labels, values, title, ylabel, fill=False):
    if not labels:
        return _empty_chart("No data for this filter")
    fig, ax = plt.subplots(figsize=(8, 4))
    if fill:
        ax.fill_between(labels, values, alpha=0.35, color=COLORS[2])
    ax.plot(labels, values, marker="o", color=COLORS[0], linewidth=2)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    return _to_base64(fig)


def _summary(orders):
    revenue = sum(o.total_price for o in orders if o.status != "Cancelled")
    delivered = sum(1 for o in orders if o.status == "Delivered")
    return {
        "orders": len(orders),
        "delivered": delivered,
        "cancelled": sum(1 for o in orders if o.status == "Cancelled"),
        "revenue": f"{revenue:,.0f} IQD",
        "avg_delivery_days": (
            round(
                np.mean([o.delivery_days for o in orders if o.delivery_days > 0]),
                2,
            )
            if any(o.delivery_days > 0 for o in orders)
            else 0
        ),
    }


def build_orders_report(filters: dict):
    """Orders Report: by city (bar), merchant (h-bar), driver (pie), status (donut), trend (line)."""
    orders = _filtered_orders(filters)
    cities, _, merchants, drivers, *_ = _lookups()
    summary = _summary(orders)

    by_city = Counter(cities.get(o.city_id).name if cities.get(o.city_id) else f"#{o.city_id}" for o in orders)
    by_merchant = Counter(
        merchants.get(o.merchant_id).name if merchants.get(o.merchant_id) else f"#{o.merchant_id}"
        for o in orders
    )
    by_driver = Counter(
        drivers.get(o.driver_id).name if drivers.get(o.driver_id) else f"#{o.driver_id}"
        for o in orders
    )
    by_status = Counter(o.status for o in orders)

    # Daily trend
    by_day = defaultdict(int)
    for o in orders:
        by_day[o.order_date.isoformat()] += 1
    day_labels = sorted(by_day.keys())
    day_values = [by_day[d] for d in day_labels]
    # If too many days, aggregate by month
    if len(day_labels) > 45:
        by_month = defaultdict(int)
        for d, v in by_day.items():
            by_month[d[:7]] += v
        day_labels = sorted(by_month.keys())
        day_values = [by_month[m] for m in day_labels]
        trend_title = "Orders Over Time (Monthly Line)"
    else:
        trend_title = "Orders Over Time (Daily Line)"

    city_top = _top_n(by_city)
    merchant_top = _top_n(by_merchant)
    driver_top = _top_n(by_driver, 10)

    charts = [
        {
            "title": "Orders by City (Bar)",
            "lecture": "Compare order volume across delivery cities",
            "image": _bar([k for k, _ in city_top], [v for _, v in city_top], "Orders by City", "Orders"),
        },
        {
            "title": "Orders by Merchant (Horizontal Bar)",
            "lecture": "Top merchants by number of orders",
            "image": _bar(
                [k for k, _ in merchant_top],
                [v for _, v in merchant_top],
                "Orders by Merchant",
                "Orders",
                color=COLORS[4],
                horizontal=True,
            ),
        },
        {
            "title": "Orders by Driver (Pie)",
            "lecture": "Share of orders handled by each driver",
            "image": _pie([k for k, _ in driver_top], [v for _, v in driver_top], "Orders by Driver"),
        },
        {
            "title": "Orders by Status (Donut)",
            "lecture": "Pending / In Transit / Delivered / Cancelled mix",
            "image": _pie(list(by_status.keys()), list(by_status.values()), "Order Status Mix", donut=True),
        },
        {
            "title": trend_title,
            "lecture": "How order volume changes over the selected period",
            "image": _line(day_labels, day_values, trend_title, "Orders", fill=True),
        },
    ]
    return {
        "key": "orders",
        "title": "Orders Report",
        "description": "Order volume by city, merchant, driver, status and time.",
        "summary": summary,
        "charts": charts,
    }


def build_revenue_report(filters: dict):
    """Revenue Report: by province, city, merchant, monthly area."""
    orders = [o for o in _filtered_orders(filters) if o.status != "Cancelled"]
    cities, provinces, merchants, *_ = _lookups()
    summary = _summary(orders)

    by_province = defaultdict(float)
    by_city = defaultdict(float)
    by_merchant = defaultdict(float)
    by_month = defaultdict(float)

    for o in orders:
        city = cities.get(o.city_id)
        prov_name = provinces.get(city.province_id).name if city and provinces.get(city.province_id) else "Unknown"
        by_province[prov_name] += o.total_price
        by_city[city.name if city else f"#{o.city_id}"] += o.total_price
        m = merchants.get(o.merchant_id)
        by_merchant[m.name if m else f"#{o.merchant_id}"] += o.total_price
        by_month[o.order_date.strftime("%Y-%m")] += o.total_price

    prov_items = sorted(by_province.items(), key=lambda x: x[1], reverse=True)
    city_items = sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:12]
    merchant_items = sorted(by_merchant.items(), key=lambda x: x[1], reverse=True)[:12]
    month_labels = sorted(by_month.keys())
    month_values = [by_month[m] for m in month_labels]

    charts = [
        {
            "title": "Revenue by Province (Bar)",
            "lecture": "Which provinces generate the most IQD revenue",
            "image": _bar(
                [k for k, _ in prov_items],
                [v for _, v in prov_items],
                "Revenue by Province (IQD)",
                "IQD",
                color=COLORS[1],
            ),
        },
        {
            "title": "Revenue by City (Horizontal Bar)",
            "lecture": "Top cities by revenue",
            "image": _bar(
                [k for k, _ in city_items],
                [v for _, v in city_items],
                "Revenue by City (IQD)",
                "IQD",
                color=COLORS[5],
                horizontal=True,
            ),
        },
        {
            "title": "Revenue by Merchant (Pie)",
            "lecture": "Revenue share of top merchants",
            "image": _pie(
                [k for k, _ in merchant_items[:8]],
                [v for _, v in merchant_items[:8]],
                "Revenue by Merchant",
            ),
        },
        {
            "title": "Monthly Revenue (Area)",
            "lecture": "Revenue trend over months in IQD",
            "image": _line(month_labels, month_values, "Monthly Revenue (IQD)", "IQD", fill=True),
        },
    ]
    return {
        "key": "revenue",
        "title": "Revenue Report",
        "description": "IQD revenue by province, city, merchant and month (cancelled excluded).",
        "summary": summary,
        "charts": charts,
    }


def build_delivery_report(filters: dict):
    """Delivery performance: avg days by city, status mix, delivery days histogram."""
    orders = _filtered_orders(filters)
    cities, *_ = _lookups()
    summary = _summary(orders)

    days_by_city = defaultdict(list)
    for o in orders:
        if o.delivery_days > 0:
            name = cities.get(o.city_id).name if cities.get(o.city_id) else f"#{o.city_id}"
            days_by_city[name].append(o.delivery_days)

    avg_items = sorted(
        ((name, float(np.mean(vals))) for name, vals in days_by_city.items()),
        key=lambda x: x[1],
        reverse=True,
    )[:12]

    by_status = Counter(o.status for o in orders)
    all_days = [o.delivery_days for o in orders if o.delivery_days > 0]

    # Histogram of delivery days
    if all_days:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(all_days, bins=min(10, max(all_days)), color=COLORS[0], edgecolor="white")
        ax.set_title("Delivery Days Distribution (Histogram)")
        ax.set_xlabel("Days")
        ax.set_ylabel("Orders")
        fig.tight_layout()
        hist_img = _to_base64(fig)
    else:
        hist_img = _empty_chart("No delivery-day data")

    # Box-like bar of avg delivery by city
    charts = [
        {
            "title": "Avg Delivery Days by City (Bar)",
            "lecture": "Where deliveries take longer on average",
            "image": _bar(
                [k for k, _ in avg_items],
                [v for _, v in avg_items],
                "Average Delivery Days by City",
                "Days",
                color=COLORS[6],
            ),
        },
        {
            "title": "Status Mix (Donut)",
            "lecture": "Operational health of the filtered orders",
            "image": _pie(list(by_status.keys()), list(by_status.values()), "Delivery Status Mix", donut=True),
        },
        {
            "title": "Delivery Days Distribution (Histogram)",
            "lecture": "How delivery durations are spread",
            "image": hist_img,
        },
    ]
    return {
        "key": "delivery",
        "title": "Delivery Report",
        "description": "Delivery speed and status health for the filtered period.",
        "summary": summary,
        "charts": charts,
    }


def build_inventory_report(filters: dict):
    """
    Inventory / sales report from order line items in the filtered order set.
    Also shows current stock levels (not date-filtered — live stock).
    """
    orders = _filtered_orders(filters)
    order_ids = [o.id for o in orders]
    _, _, _, _, _, items, item_types = _lookups()
    summary = _summary(orders)

    qty_by_item = Counter()
    revenue_by_type = defaultdict(float)
    if order_ids:
        lines = OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).all()
        # Exclude lines belonging only to cancelled? Use order status map
        status_by_order = {o.id: o.status for o in orders}
        for line in lines:
            if status_by_order.get(line.order_id) == "Cancelled":
                continue
            qty_by_item[line.item_id] += line.quantity
            item = items.get(line.item_id)
            if item:
                tname = item_types.get(item.item_type_id).name if item_types.get(item.item_type_id) else "Other"
                revenue_by_type[tname] += line.line_total

    top_items = qty_by_item.most_common(12)
    item_labels = [
        (items.get(i).name if items.get(i) else f"#{i}") for i, _ in top_items
    ]
    item_values = [v for _, v in top_items]

    type_items = sorted(revenue_by_type.items(), key=lambda x: x[1], reverse=True)

    # Current stock (live)
    stock_sorted = sorted(
        [(i.name, i.stock) for i in items.values()],
        key=lambda x: x[1],
    )[:12]  # lowest stock first — useful operationally

    charts = [
        {
            "title": "Top Sold Items (Horizontal Bar)",
            "lecture": "Units sold in the filtered orders",
            "image": _bar(item_labels, item_values, "Top Sold Items (Qty)", "Qty", color=COLORS[2], horizontal=True),
        },
        {
            "title": "Sales by Item Type (Pie)",
            "lecture": "Revenue share by category (IQD)",
            "image": _pie(
                [k for k, _ in type_items],
                [v for _, v in type_items],
                "Sales by Item Type",
            ),
        },
        {
            "title": "Lowest Stock Items (Bar)",
            "lecture": "Live stock levels — watch what may run out",
            "image": _bar(
                [k for k, _ in stock_sorted],
                [v for _, v in stock_sorted],
                "Lowest Current Stock",
                "Stock",
                color=COLORS[5],
                horizontal=True,
            ),
        },
    ]
    return {
        "key": "inventory",
        "title": "Inventory & Sales Report",
        "description": "What sold in the filtered period, plus current low-stock items.",
        "summary": summary,
        "charts": charts,
    }


REPORT_BUILDERS = {
    "orders": build_orders_report,
    "revenue": build_revenue_report,
    "delivery": build_delivery_report,
    "inventory": build_inventory_report,
}

REPORT_CATALOG = [
    {"key": "orders", "label": "Orders Report", "description": "Orders by city, merchant, driver, status & time"},
    {"key": "revenue", "label": "Revenue Report", "description": "IQD revenue by province, city, merchant & month"},
    {"key": "delivery", "label": "Delivery Report", "description": "Delivery speed and status health"},
    {"key": "inventory", "label": "Inventory Report", "description": "Top sold items, categories & low stock"},
]


def get_report_catalog():
    return REPORT_CATALOG


def build_report(key: str, filters: dict | None = None):
    builder = REPORT_BUILDERS.get(key)
    if not builder:
        return None
    return builder(filters or {})
