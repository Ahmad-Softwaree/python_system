"""
Shared helpers: forms, search, pagination, IQD formatting, joined display rows, stock.
"""

from datetime import datetime
from urllib.parse import urlencode

from sqlalchemy import String, cast, or_

from extensions import db
from models import Item, OrderItem, StockHistory, ORDER_STATUSES
from table_meta import TABLES


def format_iqd(value):
    """Format a number as Iraqi Dinar, e.g. 450000 → '450,000 IQD'."""
    try:
        return f"{float(value):,.0f} IQD"
    except (TypeError, ValueError):
        return "0 IQD"


def parse_value(field, raw):
    if raw is None:
        return None
    raw = raw.strip() if isinstance(raw, str) else raw
    ftype = field["type"]

    if ftype == "bool":
        return str(raw).lower() in {"1", "true", "on", "yes"}
    if raw == "" or raw is None:
        return None
    if ftype in ("number", "relation"):
        return int(raw)
    if ftype == "float":
        return float(raw)
    if ftype == "date":
        return datetime.strptime(str(raw), "%Y-%m-%d").date()
    return raw


def apply_form(instance, form, fields):
    """Copy form fields onto a model (skips order multi-item lines)."""
    for field in fields:
        name = field["name"]
        if name not in form and field["type"] != "bool":
            continue
        if field["type"] == "bool":
            setattr(instance, name, name in form)
        else:
            value = parse_value(field, form.get(name, ""))
            if value is None and field.get("required"):
                raise ValueError(f"{field['label']} is required")
            setattr(instance, name, value)
    return instance


def search_filter(model, search_cols, q):
    if not q or not search_cols:
        return True
    term = f"%{q.strip()}%"
    clauses = []
    for col in search_cols:
        column = getattr(model, col, None)
        if column is not None:
            clauses.append(cast(column, String).like(term))
    if q.strip().isdigit():
        clauses.append(model.id == int(q.strip()))
    return or_(*clauses) if clauses else True


def paginate_query(query, page, per_page):
    return query.paginate(page=page, per_page=per_page, error_out=False)


def pagination_urls(endpoint, page, pages, **params):
    def link(p):
        query = {k: v for k, v in params.items() if v not in (None, "")}
        query["page"] = p
        return f"{endpoint}?{urlencode(query)}"

    return {
        "page": page,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
        "prev_url": link(page - 1) if page > 1 else None,
        "next_url": link(page + 1) if page < pages else None,
    }


def deleted_counts():
    counts = {}
    for key, meta in TABLES.items():
        model = meta["model"]
        counts[key] = model.query.filter(model.deleted_at.isnot(None)).count()
    return counts


def enrich_row(table_name, obj):
    """
    Build a display dict with joined names (city_name, role_name, …)
    instead of raw foreign-key ids.
    """
    d = obj.to_dict()
    d["_raw"] = obj.to_dict()  # for edit forms (ids still needed)

    if table_name == "cities":
        d["province_name"] = obj.province.name if obj.province else "—"
    elif table_name == "streets":
        d["city_name"] = obj.city.name if obj.city else "—"
    elif table_name == "posts":
        d["city_name"] = obj.city.name if obj.city else "—"
        d["street_name"] = obj.street.name if obj.street else "—"
    elif table_name == "merchants":
        d["city_name"] = obj.city.name if obj.city else "—"
        d["revenue_iqd"] = format_iqd(obj.revenue)
    elif table_name == "admins":
        d["role_name"] = obj.role_rel.name if obj.role_rel else "—"
    elif table_name == "items":
        d["item_type_name"] = obj.item_type.name if obj.item_type else "—"
        d["merchant_name"] = obj.merchant.name if obj.merchant else "—"
        d["price_iqd"] = format_iqd(obj.price)
    elif table_name == "orders":
        d["merchant_name"] = obj.merchant.name if obj.merchant else "—"
        d["driver_name"] = obj.driver.name if obj.driver else "—"
        d["post_name"] = obj.post.name if obj.post else "—"
        d["city_name"] = obj.city.name if obj.city else "—"
        d["street_name"] = obj.street.name if obj.street else "—"
        parts = []
        for oi in obj.items or []:
            name = oi.item.name if oi.item else f"#{oi.item_id}"
            parts.append(f"{name} ×{oi.quantity}")
        d["items_summary"] = ", ".join(parts) if parts else "—"
        d["total_price_iqd"] = format_iqd(obj.total_price)
    elif table_name == "ratings":
        d["item_name"] = obj.item.name if obj.item else "—"

    if "deleted_at" in d and d["deleted_at"]:
        pass
    return d


def adjust_stock(item, change_qty, reason, order_id=None, note=""):
    """
    Change item.stock and append a StockHistory row.
    change_qty: negative to subtract, positive to restore.
    """
    before = item.stock
    after = before + change_qty
    if after < 0:
        raise ValueError(f"Not enough stock for '{item.name}' (have {before}, need {-change_qty})")
    item.stock = after
    db.session.add(
        StockHistory(
            item_id=item.id,
            change_qty=change_qty,
            stock_before=before,
            stock_after=after,
            reason=reason,
            order_id=order_id,
            note=note,
        )
    )


def apply_order_items(order, lines, reason="order_sale"):
    """
    lines = list of {item_id, quantity}
    Creates OrderItem rows, computes total, subtracts stock.
    """
    if not lines:
        raise ValueError("Add at least one item to the order")

    # Ensure order.id exists before writing stock history with order_id.
    db.session.flush()

    total = 0.0
    for line in lines:
        item = Item.query.get(line["item_id"])
        if not item or item.deleted_at is not None:
            raise ValueError(f"Item #{line['item_id']} not found")
        qty = int(line["quantity"])
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        unit = float(item.price)
        line_total = unit * qty
        total += line_total
        db.session.add(
            OrderItem(
                order=order,
                item_id=item.id,
                quantity=qty,
                unit_price=unit,
                line_total=line_total,
            )
        )
        adjust_stock(
            item,
            -qty,
            reason=reason,
            order_id=order.id,
            note=f"Order sale of {qty}",
        )

    order.total_price = total


def restore_order_stock(order, reason="order_cancel"):
    """Put stock back when an order is cancelled."""
    for oi in order.items:
        item = Item.query.get(oi.item_id)
        if item:
            adjust_stock(
                item,
                oi.quantity,
                reason=reason,
                order_id=order.id,
                note=f"Restored from order #{order.id}",
            )


def subtract_order_stock(order, reason="order_sale"):
    """Subtract stock again (e.g. un-cancel)."""
    for oi in order.items:
        item = Item.query.get(oi.item_id)
        if item:
            adjust_stock(
                item,
                -oi.quantity,
                reason=reason,
                order_id=order.id,
                note=f"Re-applied order #{order.id}",
            )


def parse_order_item_lines(form):
    """
    Read repeated fields item_id[] and quantity[] from the order form.
    """
    item_ids = form.getlist("item_id[]")
    qtys = form.getlist("quantity[]")
    lines = []
    for iid, qty in zip(item_ids, qtys):
        if not iid:
            continue
        lines.append({"item_id": int(iid), "quantity": int(qty or 0)})
    return lines


def set_order_status(order, new_status):
    if new_status not in ORDER_STATUSES:
        raise ValueError("Invalid status")
    old = order.status
    if old == new_status:
        return
    if new_status == "Cancelled" and old != "Cancelled":
        restore_order_stock(order)
    elif old == "Cancelled" and new_status != "Cancelled":
        subtract_order_stock(order)
    order.status = new_status
