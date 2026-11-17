"""
Shared helpers used by app.py routes.

Keeping search / pagination / form parsing here keeps the route functions
short and easier to present: routes decide *what* to do, services do *how*.
"""

from datetime import datetime
from urllib.parse import urlencode

from sqlalchemy import String, cast, or_

from table_meta import TABLES


def parse_value(field, raw):
    """
    HTML forms always send strings.
    Convert them to the correct Python type for the ORM column
    (int, float, date, bool, or leave as text).
    """
    if raw is None:
        return None
    raw = raw.strip() if isinstance(raw, str) else raw
    ftype = field["type"]

    if ftype == "bool":
        return str(raw).lower() in {"1", "true", "on", "yes"}
    if raw == "" or raw is None:
        return None
    if ftype == "number":
        return int(raw)
    if ftype == "float":
        return float(raw)
    if ftype == "date":
        return datetime.strptime(str(raw), "%Y-%m-%d").date()
    return raw


def apply_form(instance, form, fields):
    """
    Copy submitted form fields onto a model instance (create or update).

    Odd case — checkboxes:
    An unchecked HTML checkbox is NOT sent in the POST body at all.
    So for bool fields we check `name in form` instead of reading a value.
    """
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
    """
    Build a SQLAlchemy OR filter across the columns listed in table_meta.

    Why cast(... to String)?
    Some searchable values might be numeric IDs; casting lets LIKE work
    the same way for text and numbers.

    Why return True when q is empty?
    The route can do: if filt is not True: query = query.filter(filt)
    so empty search = no extra WHERE clause.
    """
    if not q or not search_cols:
        return True
    term = f"%{q.strip()}%"
    clauses = []
    for col in search_cols:
        column = getattr(model, col, None)
        if column is not None:
            # MySQL utf8mb4_unicode_ci is usually case-insensitive for LIKE.
            clauses.append(cast(column, String).like(term))
    # Bonus: typing a pure number also matches the primary key.
    if q.strip().isdigit():
        clauses.append(model.id == int(q.strip()))
    return or_(*clauses) if clauses else True


def paginate_query(query, page, per_page):
    # Flask-SQLAlchemy helper: returns page items + total/pages metadata.
    # error_out=False → empty page returns empty list instead of 404.
    return query.paginate(page=page, per_page=per_page, error_out=False)


def pagination_urls(endpoint, page, pages, **params):
    """
    Build Prev/Next links while keeping the current search term (?q=...).
    endpoint is already a full path from url_for(...).
    """
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
    """Used by the Deleted hub page to show a number on each table card."""
    counts = {}
    for key, meta in TABLES.items():
        model = meta["model"]
        counts[key] = model.query.filter(model.deleted_at.isnot(None)).count()
    return counts
