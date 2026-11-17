"""
Generate lecture chart types as base64 PNG images for the dashboard.

Odd / important choices for presentation:
1) matplotlib.use("Agg")
   "Agg" is a non-GUI backend. On a web server we must NOT open plot windows;
   we only render images into memory.

2) Charts read from MySQL (active rows only), not from data/*.py
   so soft-deleted records disappear from the dashboard automatically.

3) Each figure is encoded as base64 and embedded in HTML
   (<img src="data:image/png;base64,...">). No chart files are written to disk.
"""

import base64
import io
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")  # headless backend for Flask (no desktop window)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from models import (
    City,
    Driver,
    Item,
    ItemType,
    Merchant,
    Order,
    Post,
    Province,
)

sns.set_theme(style="whitegrid", palette="viridis")
COLORS = ["#0d7377", "#14919b", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#264653", "#457b9d"]

# Module-level lists filled by _load_active() before charts run.
# Using simple dict lists keeps chart functions easy to read in class.
cities = []
drivers = []
item_types = []
items = []
merchants = []
orders = []
posts = []
provinces = []


def _load_active():
    """Pull non-deleted rows from MySQL into the module-level lists above."""
    global cities, drivers, item_types, items, merchants, orders, posts, provinces
    cities = [r.to_dict() for r in City.query.filter(City.deleted_at.is_(None)).all()]
    drivers = [r.to_dict() for r in Driver.query.filter(Driver.deleted_at.is_(None)).all()]
    item_types = [r.to_dict() for r in ItemType.query.filter(ItemType.deleted_at.is_(None)).all()]
    items = [r.to_dict() for r in Item.query.filter(Item.deleted_at.is_(None)).all()]
    merchants = [r.to_dict() for r in Merchant.query.filter(Merchant.deleted_at.is_(None)).all()]
    orders = [r.to_dict() for r in Order.query.filter(Order.deleted_at.is_(None)).all()]
    posts = [r.to_dict() for r in Post.query.filter(Post.deleted_at.is_(None)).all()]
    provinces = [r.to_dict() for r in Province.query.filter(Province.deleted_at.is_(None)).all()]


def _to_base64(fig):
    """Save figure to an in-memory PNG buffer → base64 string for the template."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110, facecolor="white")
    plt.close(fig)  # free memory; important when drawing many charts per request
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _city_name(city_id):
    return next(c["name"] for c in cities if c["id"] == city_id)


def _province_for_city(city_id):
    city = next(c for c in cities if c["id"] == city_id)
    return next(p["name"] for p in provinces if p["id"] == city["province_id"])


def _item_type_name(item_id):
    item = next(i for i in items if i["id"] == item_id)
    return next(t["name"] for t in item_types if t["id"] == item["item_type_id"])


def chart_bar_orders_by_city():
    """Bar chart — orders per city."""
    counts = Counter(_city_name(o["city_id"]) for o in orders)
    labels = list(counts.keys())
    values = list(counts.values())

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(labels, values, color=COLORS[0])
    ax.set_title("Orders by City (Bar Chart)")
    ax.set_ylabel("Order Count")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    return {
        "title": "Bar Chart — Orders by City",
        "lecture": "Bar chart compares categories",
        "image": _to_base64(fig),
    }


def chart_grouped_bar_posts():
    """Grouped bar — post capacity vs staff."""
    names = [p["name"].replace(" Post", "").replace(" Central", "")[:12] for p in posts[:8]]
    capacity = [p["capacity"] for p in posts[:8]]
    staff = [p["staff_count"] * 10 for p in posts[:8]]  # scale for visibility

    x = np.arange(len(names))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - width / 2, capacity, width, label="Capacity", color=COLORS[0])
    ax.bar(x + width / 2, staff, width, label="Staff ×10", color=COLORS[4])
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=35, ha="right")
    ax.set_title("Post Offices: Capacity vs Staff (Grouped Bar)")
    ax.legend()
    fig.tight_layout()
    return {
        "title": "Grouped Bar — Posts Capacity vs Staff",
        "lecture": "Grouped bars compare related measures",
        "image": _to_base64(fig),
    }


def chart_horizontal_bar_drivers():
    """Horizontal bar — top drivers by deliveries."""
    sorted_drivers = sorted(drivers, key=lambda d: d["deliveries"], reverse=True)[:10]
    names = [d["name"] for d in sorted_drivers]
    values = [d["deliveries"] for d in sorted_drivers]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(names[::-1], values[::-1], color=COLORS[1])
    ax.set_title("Top Drivers by Deliveries (Horizontal Bar)")
    ax.set_xlabel("Deliveries")
    fig.tight_layout()
    return {
        "title": "Horizontal Bar — Top Drivers",
        "lecture": "Bar/horizontal bar for category comparison",
        "image": _to_base64(fig),
    }


def chart_pie_item_types():
    """Pie chart — item type share from orders."""
    counts = Counter(_item_type_name(o["item_id"]) for o in orders)
    labels = list(counts.keys())
    values = list(counts.values())

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.pie(values, labels=labels, autopct="%1.1f%%", colors=COLORS[: len(labels)], startangle=90)
    ax.set_title("Orders by Item Type (Pie Chart)")
    fig.tight_layout()
    return {
        "title": "Pie Chart — Item Types",
        "lecture": "Pie shows share of each category in a whole",
        "image": _to_base64(fig),
    }


def chart_donut_status():
    """Donut chart — order status distribution."""
    counts = Counter(o["status"] for o in orders)
    labels = list(counts.keys())
    values = list(counts.values())

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct="%1.1f%%",
        colors=COLORS[: len(labels)], startangle=90,
        pctdistance=0.75,
    )
    centre = plt.Circle((0, 0), 0.50, fc="white")
    ax.add_artist(centre)
    ax.set_title("Order Status (Donut Chart)")
    ax.text(0, 0, f"{sum(values)}\norders", ha="center", va="center", fontsize=11, fontweight="bold")
    fig.tight_layout()
    return {
        "title": "Donut Chart — Order Status",
        "lecture": "Donut is a pie with a hole for totals",
        "image": _to_base64(fig),
    }


def chart_line_orders_over_time():
    """Line chart — orders per month."""
    months = defaultdict(int)
    for o in orders:
        months[o["order_date"][:7]] += 1
    labels = sorted(months.keys())
    values = [months[m] for m in labels]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(labels, values, marker="o", color=COLORS[0], linewidth=2)
    ax.set_title("Orders Over Time (Line Chart)")
    ax.set_ylabel("Orders")
    ax.set_xlabel("Month")
    fig.tight_layout()
    return {
        "title": "Line Chart — Orders Over Time",
        "lecture": "Line shows trend over time",
        "image": _to_base64(fig),
    }


def chart_area_monthly_revenue():
    """Area chart — monthly revenue volume."""
    months = defaultdict(float)
    for o in orders:
        months[o["order_date"][:7]] += o["total_price"]
    labels = sorted(months.keys())
    values = [months[m] for m in labels]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.fill_between(labels, values, alpha=0.5, color=COLORS[2])
    ax.plot(labels, values, color=COLORS[0], linewidth=2)
    ax.set_title("Monthly Revenue (Area Chart)")
    ax.set_ylabel("Revenue ($)")
    fig.tight_layout()
    return {
        "title": "Area Chart — Monthly Revenue",
        "lecture": "Area stresses magnitude over time",
        "image": _to_base64(fig),
    }


def chart_histogram_order_values():
    """Histogram — distribution of order values."""
    values = [o["total_price"] for o in orders]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(values, bins=10, color=COLORS[0], edgecolor="white")
    ax.set_title("Order Value Distribution (Histogram)")
    ax.set_xlabel("Order Value ($)")
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    return {
        "title": "Histogram — Order Values",
        "lecture": "Histogram shows how values are spread out",
        "image": _to_base64(fig),
    }


def chart_scatter_drivers():
    """Scatter — deliveries vs rating for drivers."""
    x = [d["deliveries"] for d in drivers]
    y = [d["rating"] for d in drivers]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(x, y, c=COLORS[0], alpha=0.75, s=60)
    ax.set_title("Driver Deliveries vs Rating (Scatter)")
    ax.set_xlabel("Deliveries")
    ax.set_ylabel("Rating")
    fig.tight_layout()
    return {
        "title": "Scatter — Drivers Deliveries vs Rating",
        "lecture": "Scatter shows relationship between two numeric variables",
        "image": _to_base64(fig),
    }


def chart_scatter_trend():
    """Scatter with trend line — merchant orders vs revenue."""
    x = np.array([m["total_orders"] for m in merchants], dtype=float)
    y = np.array([m["revenue"] for m in merchants], dtype=float)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(x, y, c=COLORS[5], alpha=0.8, s=70)
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, p(xs), color=COLORS[0], linewidth=2, label="Trend line")
    ax.set_title("Merchant Orders vs Revenue (Scatter + Trend)")
    ax.set_xlabel("Total Orders")
    ax.set_ylabel("Revenue ($)")
    ax.legend()
    fig.tight_layout()
    return {
        "title": "Scatter + Trend — Merchants",
        "lecture": "Scatter with trend line adds a fitted line",
        "image": _to_base64(fig),
    }


def chart_bubble_merchants():
    """Bubble chart — merchants: orders, revenue, stock proxy."""
    x = [m["total_orders"] for m in merchants]
    y = [m["revenue"] for m in merchants]
    sizes = [max(m["revenue"] / 80, 40) for m in merchants]
    labels = [m["name"][:10] for m in merchants]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(x, y, s=sizes, c=COLORS[1], alpha=0.55, edgecolors=COLORS[0])
    for i, label in enumerate(labels):
        ax.annotate(label, (x[i], y[i]), fontsize=7, ha="center")
    ax.set_title("Merchants Bubble (Orders × Revenue × Size)")
    ax.set_xlabel("Total Orders")
    ax.set_ylabel("Revenue ($)")
    fig.tight_layout()
    return {
        "title": "Bubble Chart — Merchants",
        "lecture": "Bubble uses size for a third variable",
        "image": _to_base64(fig),
    }


def chart_box_by_province():
    """Box plot — order values by province."""
    rows = []
    for o in orders:
        rows.append({"province": _province_for_city(o["city_id"]), "total_price": o["total_price"]})
    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.boxplot(data=df, x="province", y="total_price", hue="province", ax=ax, palette="viridis", legend=False)
    ax.set_title("Order Value by Province (Box Plot)")
    ax.set_ylabel("Order Value ($)")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    return {
        "title": "Box Plot — Order Value by Province",
        "lecture": "Box shows median, quartiles and outliers",
        "image": _to_base64(fig),
    }


def chart_violin_delivery_days():
    """Violin plot — delivery days by city (top cities)."""
    top_cities = [c for c, _ in Counter(o["city_id"] for o in orders).most_common(5)]
    rows = [
        {"city": _city_name(o["city_id"]), "delivery_days": o["delivery_days"]}
        for o in orders if o["city_id"] in top_cities and o["delivery_days"] > 0
    ]
    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.violinplot(data=df, x="city", y="delivery_days", hue="city", ax=ax, palette="viridis", legend=False)
    ax.set_title("Delivery Days by City (Violin Plot)")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    return {
        "title": "Violin Plot — Delivery Days by City",
        "lecture": "Violin shows full distribution shape",
        "image": _to_base64(fig),
    }


def chart_heatmap_correlation():
    """Heatmap — correlation of numeric order/driver-related fields."""
    df = pd.DataFrame([
        {
            "quantity": o["quantity"],
            "total_price": o["total_price"],
            "delivery_days": o["delivery_days"],
            "item_price": next(i["price"] for i in items if i["id"] == o["item_id"]),
            "item_weight": next(i["weight_kg"] for i in items if i["id"] == o["item_id"]),
        }
        for o in orders
    ])
    corr = df.corr()

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(corr, annot=True, cmap="viridis", fmt=".2f", ax=ax, square=True)
    ax.set_title("Order Fields Correlation (Heatmap)")
    fig.tight_layout()
    return {
        "title": "Heatmap — Order Field Correlations",
        "lecture": "Heatmap shows correlations as colours",
        "image": _to_base64(fig),
    }


def chart_count_plot_status():
    """Count plot — orders per status."""
    df = pd.DataFrame(orders)

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.countplot(data=df, x="status", hue="status", ax=ax, palette="viridis", order=df["status"].value_counts().index, legend=False)
    ax.set_title("Orders per Status (Count Plot)")
    ax.set_ylabel("Count")
    fig.tight_layout()
    return {
        "title": "Count Plot — Order Status",
        "lecture": "Count plot counts observations per group",
        "image": _to_base64(fig),
    }


def chart_kde_order_values():
    """KDE density plot — order value probability density."""
    values = [o["total_price"] for o in orders]

    fig, ax = plt.subplots(figsize=(7, 4))
    sns.kdeplot(values, fill=True, color=COLORS[0], ax=ax)
    ax.set_title("Order Value Density (KDE)")
    ax.set_xlabel("Order Value ($)")
    fig.tight_layout()
    return {
        "title": "Density Plot (KDE) — Order Values",
        "lecture": "KDE is a smooth estimate of probability density",
        "image": _to_base64(fig),
    }


def chart_radar_provinces():
    """Radar/polar chart — province performance measures."""
    metrics = ["orders", "revenue", "avg_delivery", "drivers_proxy"]
    province_stats = {}
    for p in provinces:
        p_cities = {c["id"] for c in cities if c["province_id"] == p["id"]}
        p_orders = [o for o in orders if o["city_id"] in p_cities]
        p_posts = [po for po in posts if po["city_id"] in p_cities]
        province_stats[p["name"]] = {
            "orders": len(p_orders),
            "revenue": sum(o["total_price"] for o in p_orders),
            "avg_delivery": (
                np.mean([o["delivery_days"] for o in p_orders if o["delivery_days"] > 0])
                if p_orders else 0
            ),
            "drivers_proxy": sum(po["staff_count"] for po in p_posts),
        }

    # Normalize each metric to 0–1
    maxes = {m: max(s[m] for s in province_stats.values()) or 1 for m in metrics}
    selected = list(province_stats.keys())[:4]

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    for i, name in enumerate(selected):
        vals = [province_stats[name][m] / maxes[m] for m in metrics]
        vals += vals[:1]
        ax.plot(angles, vals, label=name, color=COLORS[i], linewidth=2)
        ax.fill(angles, vals, color=COLORS[i], alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(["Orders", "Revenue", "Avg Delivery", "Staff"])
    ax.set_title("Province Performance (Radar Chart)")
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1))
    fig.tight_layout()
    return {
        "title": "Radar Chart — Province Performance",
        "lecture": "Radar compares regions on several measures",
        "image": _to_base64(fig),
    }


def build_all_charts():
    """Return all lecture charts for the dashboard."""
    _load_active()
    return [
        chart_bar_orders_by_city(),
        chart_grouped_bar_posts(),
        chart_horizontal_bar_drivers(),
        chart_pie_item_types(),
        chart_donut_status(),
        chart_line_orders_over_time(),
        chart_area_monthly_revenue(),
        chart_histogram_order_values(),
        chart_scatter_drivers(),
        chart_scatter_trend(),
        chart_bubble_merchants(),
        chart_box_by_province(),
        chart_violin_delivery_days(),
        chart_heatmap_correlation(),
        chart_count_plot_status(),
        chart_kde_order_values(),
        chart_radar_provinces(),
    ]
