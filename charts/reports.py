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

import pandas as pd

from i18n import localized, t
from models import City, Driver, Item, ItemType, Merchant, Order, OrderItem, Post, Province, Rating

sns.set_theme(style="whitegrid", palette="viridis")
# Prefer fonts that can render Arabic / Kurdish in chart titles
plt.rcParams["font.sans-serif"] = ["Segoe UI", "Tahoma", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
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


def _empty_chart(message=None):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.axis("off")
    ax.text(0.5, 0.5, message or t("report.empty.no_data"), ha="center", va="center", fontsize=12, color="#5f7375")
    return _to_base64(fig)


def _top_n(counter: Counter, n=12):
    return counter.most_common(n)


def _bar(labels, values, title, ylabel, color=COLORS[0], horizontal=False):
    if not labels:
        return _empty_chart()
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
        return _empty_chart()
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
        return _empty_chart()
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
    cancelled = sum(1 for o in orders if o.status == "Cancelled")
    avg_days = (
        round(np.mean([o.delivery_days for o in orders if o.delivery_days > 0]), 2)
        if any(o.delivery_days > 0 for o in orders)
        else 0
    )
    revenue_txt = f"{revenue:,.0f} IQD"
    return {
        "orders": len(orders),
        "delivered": delivered,
        "cancelled": cancelled,
        "revenue": revenue_txt,
        "avg_delivery_days": avg_days,
        "cards": [
            {"label": t("report.summary.orders"), "value": len(orders)},
            {"label": t("report.summary.delivered"), "value": delivered},
            {"label": t("report.summary.cancelled"), "value": cancelled},
            {"label": t("report.summary.revenue"), "value": revenue_txt},
            {"label": t("report.summary.avg_days"), "value": avg_days},
        ],
    }


def build_orders_report(filters: dict):
    """Orders Report: by city (bar), merchant (h-bar), driver (pie), status (donut), trend (line)."""
    orders = _filtered_orders(filters)
    cities, _, merchants, drivers, *_ = _lookups()
    summary = _summary(orders)

    by_city = Counter(localized(cities[o.city_id]) if cities.get(o.city_id) else f"#{o.city_id}" for o in orders)
    by_merchant = Counter(
        localized(merchants[o.merchant_id]) if merchants.get(o.merchant_id) else f"#{o.merchant_id}"
        for o in orders
    )
    by_driver = Counter(
        localized(drivers[o.driver_id]) if drivers.get(o.driver_id) else f"#{o.driver_id}"
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
        trend_title = t("report.chart.orders_trend_monthly")
        trend_mpl = trend_title
    else:
        trend_title = t("report.chart.orders_trend_daily")
        trend_mpl = trend_title

    city_top = _top_n(by_city)
    merchant_top = _top_n(by_merchant)
    driver_top = _top_n(by_driver, 10)

    charts = [
        {
            "title": t("report.chart.orders_by_city"),
            "lecture": t("report.lecture.volume_city"),
            "image": _bar(
                [k for k, _ in city_top],
                [v for _, v in city_top],
                t("report.mpl.orders_by_city"),
                t("report.axis.orders"),
            ),
        },
        {
            "title": t("report.chart.orders_by_merchant"),
            "lecture": t("report.lecture.which_merchants"),
            "image": _bar(
                [k for k, _ in merchant_top],
                [v for _, v in merchant_top],
                t("report.mpl.orders_by_merchant"),
                t("report.axis.orders"),
                color=COLORS[4],
                horizontal=True,
            ),
        },
        {
            "title": t("report.chart.orders_by_driver"),
            "lecture": t("report.lecture.driver_share"),
            "image": _pie(
                [k for k, _ in driver_top],
                [v for _, v in driver_top],
                t("report.mpl.orders_by_driver"),
            ),
        },
        {
            "title": t("report.chart.orders_by_status"),
            "lecture": t("report.lecture.status_mix"),
            "image": _pie(
                list(by_status.keys()),
                list(by_status.values()),
                t("report.mpl.orders_by_status"),
                donut=True,
            ),
        },
        {
            "title": trend_title,
            "lecture": t("report.lecture.trend"),
            "image": _line(day_labels, day_values, trend_mpl, t("report.axis.orders"), fill=True),
        },
    ]
    return {
        "key": "orders",
        "title": t("report.orders.title"),
        "description": t("report.orders.desc_long"),
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
        prov_name = localized(provinces[city.province_id]) if city and provinces.get(city.province_id) else "Unknown"
        by_province[prov_name] += o.total_price
        by_city[localized(city) if city else f"#{o.city_id}"] += o.total_price
        m = merchants.get(o.merchant_id)
        by_merchant[localized(m) if m else f"#{o.merchant_id}"] += o.total_price
        by_month[o.order_date.strftime("%Y-%m")] += o.total_price

    prov_items = sorted(by_province.items(), key=lambda x: x[1], reverse=True)
    city_items = sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:12]
    merchant_items = sorted(by_merchant.items(), key=lambda x: x[1], reverse=True)[:12]
    month_labels = sorted(by_month.keys())
    month_values = [by_month[m] for m in month_labels]

    charts = [
        {
            "title": t("report.chart.revenue_by_province"),
            "lecture": t("report.lecture.revenue_province"),
            "image": _bar(
                [k for k, _ in prov_items],
                [v for _, v in prov_items],
                t("report.mpl.revenue_province"),
                t("report.axis.iqd"),
                color=COLORS[1],
            ),
        },
        {
            "title": t("report.chart.revenue_by_city"),
            "lecture": t("report.lecture.revenue_city"),
            "image": _bar(
                [k for k, _ in city_items],
                [v for _, v in city_items],
                t("report.mpl.revenue_city"),
                t("report.axis.iqd"),
                color=COLORS[5],
                horizontal=True,
            ),
        },
        {
            "title": t("report.chart.revenue_by_merchant"),
            "lecture": t("report.lecture.revenue_merchant"),
            "image": _pie(
                [k for k, _ in merchant_items[:8]],
                [v for _, v in merchant_items[:8]],
                t("report.mpl.revenue_merchant"),
            ),
        },
        {
            "title": t("report.chart.monthly_revenue"),
            "lecture": t("report.lecture.monthly_revenue"),
            "image": _line(
                month_labels,
                month_values,
                t("report.mpl.monthly_revenue"),
                t("report.axis.iqd"),
                fill=True,
            ),
        },
    ]
    return {
        "key": "revenue",
        "title": t("report.revenue.title"),
        "description": t("report.revenue.desc_long"),
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
            name = localized(cities[o.city_id]) if cities.get(o.city_id) else f"#{o.city_id}"
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
        ax.set_title(t("report.mpl.delivery_hist"))
        ax.set_xlabel(t("report.axis.days"))
        ax.set_ylabel(t("report.axis.orders"))
        fig.tight_layout()
        hist_img = _to_base64(fig)
    else:
        hist_img = _empty_chart()

    charts = [
        {
            "title": t("report.chart.avg_delivery_city"),
            "lecture": t("report.lecture.avg_days"),
            "image": _bar(
                [k for k, _ in avg_items],
                [v for _, v in avg_items],
                t("report.mpl.avg_delivery"),
                t("report.axis.days"),
                color=COLORS[6],
            ),
        },
        {
            "title": t("report.chart.status_mix"),
            "lecture": t("report.lecture.status_health"),
            "image": _pie(
                list(by_status.keys()),
                list(by_status.values()),
                t("report.mpl.status_mix"),
                donut=True,
            ),
        },
        {
            "title": t("report.chart.delivery_hist"),
            "lecture": t("report.lecture.days_spread"),
            "image": hist_img,
        },
    ]
    return {
        "key": "delivery",
        "title": t("report.delivery.title"),
        "description": t("report.delivery.desc_long"),
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
                tname = localized(item_types[item.item_type_id]) if item_types.get(item.item_type_id) else "Other"
                revenue_by_type[tname] += line.line_total

    top_items = qty_by_item.most_common(12)
    item_labels = [
        (localized(items[i]) if items.get(i) else f"#{i}") for i, _ in top_items
    ]
    item_values = [v for _, v in top_items]

    type_items = sorted(revenue_by_type.items(), key=lambda x: x[1], reverse=True)

    # Current stock (live)
    stock_sorted = sorted(
        [(localized(i), i.stock) for i in items.values()],
        key=lambda x: x[1],
    )[:12]  # lowest stock first — useful operationally

    charts = [
        {
            "title": t("report.chart.top_sold"),
            "lecture": t("report.lecture.top_qty"),
            "image": _bar(
                item_labels,
                item_values,
                t("report.mpl.top_sold"),
                t("report.axis.qty"),
                color=COLORS[2],
                horizontal=True,
            ),
        },
        {
            "title": t("report.chart.sales_by_type"),
            "lecture": t("report.lecture.type_share"),
            "image": _pie(
                [k for k, _ in type_items],
                [v for _, v in type_items],
                t("report.mpl.sales_type"),
            ),
        },
        {
            "title": t("report.chart.low_stock"),
            "lecture": t("report.lecture.restock"),
            "image": _bar(
                [k for k, _ in stock_sorted],
                [v for _, v in stock_sorted],
                t("report.mpl.low_stock"),
                t("report.axis.stock"),
                color=COLORS[5],
                horizontal=True,
            ),
        },
    ]
    return {
        "key": "inventory",
        "title": t("report.inventory.title"),
        "description": t("report.inventory.desc_long"),
        "summary": summary,
        "charts": charts,
    }


def build_ratings_report(filters: dict):
    """Item ratings report: average by item, score distribution, top/bottom rated."""
    orders = _filtered_orders(filters)
    _, _, _, _, _, items, _ = _lookups()

    ratings = Rating.query.filter(Rating.deleted_at.is_(None)).all()
    if not ratings:
        empty = _empty_chart()
        return {
            "key": "ratings",
            "title": t("report.ratings.title"),
            "description": t("report.ratings.desc_long"),
            "summary": {
                "cards": [
                    {"label": t("report.summary.ratings"), "value": 0},
                    {"label": t("report.summary.avg_score"), "value": "-"},
                    {"label": t("report.summary.items_rated"), "value": 0},
                    {"label": t("report.summary.orders_filter"), "value": len(orders)},
                ]
            },
            "charts": [
                {
                    "title": t("report.chart.no_ratings"),
                    "lecture": t("report.lecture.add_ratings"),
                    "image": empty,
                },
            ],
        }

    scores_by_item = defaultdict(list)
    all_scores = []
    for r in ratings:
        scores_by_item[r.item_id].append(r.score)
        all_scores.append(r.score)

    avg_by_item = {
        item_id: float(np.mean(vals)) for item_id, vals in scores_by_item.items()
    }
    avg_sorted = sorted(avg_by_item.items(), key=lambda x: x[1], reverse=True)
    top = avg_sorted[:10]
    bottom = list(reversed(avg_sorted[-10:])) if len(avg_sorted) >= 2 else avg_sorted

    score_counts = Counter(all_scores)
    score_labels = [str(s) for s in range(1, 6)]
    score_values = [score_counts.get(s, 0) for s in range(1, 6)]
    avg_score = round(float(np.mean(all_scores)), 2)

    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.bar(score_labels, score_values, color=COLORS[0])
    ax.set_title(t("report.mpl.score_dist"))
    ax.set_xlabel(t("report.axis.stars"))
    ax.set_ylabel(t("report.axis.count"))
    fig.tight_layout()
    dist_img = _to_base64(fig)

    charts = [
        {
            "title": t("report.chart.top_rated"),
            "lecture": t("report.lecture.top_rated"),
            "image": _bar(
                [localized(items[i]) if items.get(i) else f"#{i}" for i, _ in top],
                [v for _, v in top],
                t("report.mpl.top_rated"),
                t("report.axis.avg_rating"),
                color=COLORS[3],
                horizontal=True,
            ),
        },
        {
            "title": t("report.chart.low_rated"),
            "lecture": t("report.lecture.low_rated"),
            "image": _bar(
                [localized(items[i]) if items.get(i) else f"#{i}" for i, _ in bottom],
                [v for _, v in bottom],
                t("report.mpl.low_rated"),
                t("report.axis.avg_rating"),
                color=COLORS[5],
                horizontal=True,
            ),
        },
        {
            "title": t("report.chart.score_dist"),
            "lecture": t("report.lecture.stars"),
            "image": dist_img,
        },
        {
            "title": t("report.chart.score_share"),
            "lecture": t("report.lecture.star_share"),
            "image": _pie(score_labels, score_values, t("report.mpl.score_share"), donut=True),
        },
    ]
    return {
        "key": "ratings",
        "title": t("report.ratings.title"),
        "description": t("report.ratings.desc_avg", avg=avg_score, count=len(all_scores)),
        "summary": {
            "cards": [
                {"label": t("report.summary.ratings"), "value": len(all_scores)},
                {"label": t("report.summary.avg_score"), "value": f"{avg_score}/5"},
                {"label": t("report.summary.items_rated"), "value": len(avg_by_item)},
                {"label": t("report.summary.five_star"), "value": score_counts.get(5, 0)},
                {"label": t("report.summary.orders_filter"), "value": len(orders)},
            ]
        },
        "charts": charts,
    }


def build_correlations_report(filters: dict):
    """
    Heatmap report connecting per-item:
    avg_rating, sell_price (IQD), quantity sold, order_lines, revenue.
    """
    orders = [o for o in _filtered_orders(filters) if o.status != "Cancelled"]
    order_ids = [o.id for o in orders]
    _, _, _, _, _, items, _ = _lookups()

    qty_by_item = defaultdict(int)
    revenue_by_item = defaultdict(float)
    orders_by_item = defaultdict(set)
    if order_ids:
        lines = OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).all()
        for line in lines:
            qty_by_item[line.item_id] += line.quantity
            revenue_by_item[line.item_id] += line.line_total
            orders_by_item[line.item_id].add(line.order_id)

    ratings = Rating.query.filter(Rating.deleted_at.is_(None)).all()
    scores_by_item = defaultdict(list)
    for r in ratings:
        scores_by_item[r.item_id].append(r.score)

    rows = []
    for item_id, item in items.items():
        scores = scores_by_item.get(item_id) or []
        rows.append(
            {
                "item": localized(item),
                "avg_rating": float(np.mean(scores)) if scores else np.nan,
                "sell_price": float(item.price),
                "quantity_sold": int(qty_by_item.get(item_id, 0)),
                "order_count": len(orders_by_item.get(item_id, set())),
                "revenue": float(revenue_by_item.get(item_id, 0.0)),
                "rating_count": len(scores),
            }
        )

    df = pd.DataFrame(rows)
    metric_cols = ["avg_rating", "sell_price", "quantity_sold", "order_count", "revenue"]
    corr = df[metric_cols].corr()

    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="viridis",
        square=True,
        ax=ax,
        vmin=-1,
        vmax=1,
        linewidths=0.5,
    )
    ax.set_title(t("report.mpl.corr"))
    fig.tight_layout()
    corr_img = _to_base64(fig)

    plot_df = df.dropna(subset=["avg_rating"]).copy()
    if plot_df.empty:
        plot_df = df.copy()
    plot_df = plot_df.sort_values("quantity_sold", ascending=False).head(12)
    heat_cols = ["avg_rating", "sell_price", "quantity_sold", "order_count", "revenue"]
    matrix = plot_df.set_index("item")[heat_cols].astype(float)
    norm = (matrix - matrix.min()) / (matrix.max() - matrix.min()).replace(0, 1)

    fig2, ax2 = plt.subplots(figsize=(8.5, 5.5))
    sns.heatmap(norm, annot=True, fmt=".2f", cmap="YlGnBu", ax=ax2, linewidths=0.4)
    ax2.set_title(t("report.mpl.items_heat"))
    ax2.set_xlabel(t("report.axis.metric"))
    ax2.set_ylabel(t("report.axis.item"))
    fig2.tight_layout()
    items_heat_img = _to_base64(fig2)

    scatter_df = df.dropna(subset=["avg_rating"])
    if not scatter_df.empty:
        fig3, ax3 = plt.subplots(figsize=(7.5, 4.5))
        sizes = (scatter_df["quantity_sold"].clip(lower=1) ** 0.7) * 8
        ax3.scatter(
            scatter_df["sell_price"],
            scatter_df["avg_rating"],
            s=sizes,
            c=COLORS[1],
            alpha=0.65,
            edgecolors=COLORS[0],
        )
        ax3.set_title(t("report.mpl.price_rating"))
        ax3.set_xlabel(t("report.axis.sell_price"))
        ax3.set_ylabel(t("report.axis.avg_rating"))
        fig3.tight_layout()
        scatter_img = _to_base64(fig3)
    else:
        scatter_img = _empty_chart(t("report.empty.need_ratings"))

    rated = int(df["avg_rating"].notna().sum())
    return {
        "key": "correlations",
        "title": t("report.correlations.title"),
        "description": t("report.correlations.desc_long"),
        "summary": {
            "cards": [
                {"label": t("report.summary.items"), "value": len(df)},
                {"label": t("report.summary.with_ratings"), "value": rated},
                {"label": t("report.summary.orders_filter"), "value": len(orders)},
                {"label": t("report.summary.qty_sold"), "value": int(df["quantity_sold"].sum())},
                {"label": t("report.summary.revenue"), "value": f"{df['revenue'].sum():,.0f} IQD"},
            ]
        },
        "charts": [
            {
                "title": t("report.chart.corr_heat"),
                "lecture": t("report.lecture.pearson"),
                "image": corr_img,
            },
            {
                "title": t("report.chart.items_heat"),
                "lecture": t("report.lecture.normalized"),
                "image": items_heat_img,
            },
            {
                "title": t("report.chart.price_rating"),
                "lecture": t("report.lecture.bubble"),
                "image": scatter_img,
            },
        ],
    }


REPORT_BUILDERS = {
    "orders": build_orders_report,
    "revenue": build_revenue_report,
    "delivery": build_delivery_report,
    "inventory": build_inventory_report,
    "ratings": build_ratings_report,
    "correlations": build_correlations_report,
}

REPORT_KEYS = ["orders", "revenue", "delivery", "inventory", "ratings", "correlations"]


def get_report_catalog():
    return [
        {
            "key": key,
            "label": t(f"report.{key}.label"),
            "description": t(f"report.{key}.description"),
        }
        for key in REPORT_KEYS
    ]


def build_report(key: str, filters: dict | None = None):
    builder = REPORT_BUILDERS.get(key)
    if not builder:
        return None
    report = builder(filters or {})
    # Educational source-peek: which Python builder drew these charts
    source_key = f"report.{key}"
    report["source_key"] = source_key
    for chart in report.get("charts") or []:
        chart.setdefault("source_key", source_key)
    return report
