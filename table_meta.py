"""
Registry for generic table UI + relation combobox sources.

Field types:
  text | number | float | bool | date | relation

Multilang fields use name_en / name_ar / name_ckb (etc.).
Column/field labels use label_key → t(label_key) at render time.
"""

from models import (
    Admin,
    City,
    Driver,
    Feedback,
    Item,
    ItemType,
    Merchant,
    Order,
    Post,
    Province,
    Rating,
    Role,
    Street,
)


def trilang_fields(base, label_key_base, required=True):
    """Form fields for EN / AR / CKB of one logical column."""
    return [
        {
            "name": f"{base}_en",
            "label": f"{base}_en",
            "type": "text",
            "required": required,
            "label_key": f"field.{base}_en",
        },
        {
            "name": f"{base}_ar",
            "label": f"{base}_ar",
            "type": "text",
            "required": required,
            "label_key": f"field.{base}_ar",
        },
        {
            "name": f"{base}_ckb",
            "label": f"{base}_ckb",
            "type": "text",
            "required": required,
            "label_key": f"field.{base}_ckb",
        },
    ]


def trilang_search(base):
    return [f"{base}_en", f"{base}_ar", f"{base}_ckb"]


def col(key, label_key):
    return {"key": key, "label_key": label_key}


def field(name, label_key, ftype, required=True, **extra):
    d = {"name": name, "label_key": label_key, "type": ftype, "required": required}
    d.update(extra)
    return d


TABLES = {
    "roles": {
        "title_key": "table.roles",
        "model": Role,
        "view_columns": [col("id", "col.id"), col("name", "col.name"), col("description", "col.description")],
        "search": trilang_search("name") + trilang_search("description"),
        "fields": trilang_fields("name", "name") + trilang_fields("description", "description"),
    },
    "provinces": {
        "title_key": "table.provinces",
        "model": Province,
        "view_columns": [
            col("id", "col.id"),
            col("name", "col.name"),
            col("code", "col.code"),
            col("population", "col.population"),
        ],
        "search": trilang_search("name") + ["code"],
        "fields": trilang_fields("name", "name")
        + [
            field("code", "col.code", "text"),
            field("population", "col.population", "number"),
        ],
    },
    "cities": {
        "title_key": "table.cities",
        "model": City,
        "view_columns": [
            col("id", "col.id"),
            col("name", "col.name"),
            col("province_name", "col.province"),
            col("population", "col.population"),
        ],
        "search": trilang_search("name"),
        "fields": trilang_fields("name", "name")
        + [
            field("province_id", "col.province", "relation", source="provinces"),
            field("population", "col.population", "number"),
        ],
    },
    "streets": {
        "title_key": "table.streets",
        "model": Street,
        "view_columns": [
            col("id", "col.id"),
            col("name", "col.name"),
            col("city_name", "col.city"),
            col("postal_code", "col.postal_code"),
        ],
        "search": trilang_search("name") + ["postal_code"],
        "fields": trilang_fields("name", "name")
        + [
            field("city_id", "col.city", "relation", source="cities"),
            field("postal_code", "col.postal_code", "text"),
        ],
    },
    "posts": {
        "title_key": "table.posts",
        "model": Post,
        "view_columns": [
            col("id", "col.id"),
            col("name", "col.name"),
            col("city_name", "col.city"),
            col("street_name", "col.street"),
            col("capacity", "col.capacity"),
            col("staff_count", "col.staff"),
        ],
        "search": trilang_search("name"),
        "fields": trilang_fields("name", "name")
        + [
            field("city_id", "col.city", "relation", source="cities"),
            field("street_id", "col.street", "relation", source="streets"),
            field("capacity", "col.capacity", "number"),
            field("staff_count", "col.staff_count", "number"),
        ],
    },
    "drivers": {
        "title_key": "table.drivers",
        "model": Driver,
        "view_columns": [
            col("id", "col.id"),
            col("name", "col.name"),
            col("phone", "col.phone"),
            col("vehicle_type", "col.vehicle"),
            col("deliveries", "col.deliveries"),
            col("rating", "col.rating"),
            col("years_experience", "col.years_exp"),
        ],
        "search": trilang_search("name") + ["phone"] + trilang_search("vehicle_type"),
        "fields": trilang_fields("name", "name")
        + [field("phone", "col.phone", "text")]
        + trilang_fields("vehicle_type", "vehicle_type")
        + [
            field("deliveries", "col.deliveries", "number"),
            field("rating", "col.rating", "float"),
            field("years_experience", "col.years_experience", "number"),
        ],
    },
    "merchants": {
        "title_key": "table.merchants",
        "model": Merchant,
        "view_columns": [
            col("id", "col.id"),
            col("name", "col.name"),
            col("city_name", "col.city"),
            col("phone", "col.phone"),
            col("total_orders", "col.orders"),
            col("revenue_iqd", "col.revenue"),
        ],
        "search": trilang_search("name") + ["phone"],
        "fields": trilang_fields("name", "name")
        + [
            field("city_id", "col.city", "relation", source="cities"),
            field("phone", "col.phone", "text"),
            field("total_orders", "col.total_orders", "number"),
            field("revenue", "col.revenue_iqd", "float"),
        ],
    },
    "admins": {
        "title_key": "table.admins",
        "model": Admin,
        "view_columns": [
            col("id", "col.id"),
            col("name", "col.name"),
            col("email", "col.email"),
            col("role_name", "col.role"),
            col("active", "col.active"),
        ],
        "search": trilang_search("name") + ["email"],
        "fields": trilang_fields("name", "name")
        + [
            field("email", "col.email", "text"),
            {
                "name": "password",
                "label": "Password",
                "type": "password",
                "required": True,
                "label_key": "col.password",
            },
            field("role_id", "col.role", "relation", source="roles"),
            field("active", "col.active", "bool", required=False),
        ],
    },
    "item_types": {
        "title_key": "table.item_types",
        "model": ItemType,
        "view_columns": [col("id", "col.id"), col("name", "col.name"), col("description", "col.description")],
        "search": trilang_search("name") + trilang_search("description"),
        "fields": trilang_fields("name", "name") + trilang_fields("description", "description"),
    },
    "items": {
        "title_key": "table.items",
        "model": Item,
        "view_columns": [
            col("id", "col.id"),
            col("name", "col.name"),
            col("item_type_name", "col.item_type"),
            col("merchant_name", "col.merchant"),
            col("price_iqd", "col.price"),
            col("stock", "col.stock"),
        ],
        "search": trilang_search("name"),
        "row_link": "stock_history",
        "fields": trilang_fields("name", "name")
        + [
            field("item_type_id", "col.item_type", "relation", source="item_types"),
            field("merchant_id", "col.merchant", "relation", source="merchants"),
            field("price", "col.price_iqd", "float"),
            field("stock", "col.stock", "number"),
        ],
    },
    "orders": {
        "title_key": "table.orders",
        "model": Order,
        "special": "orders",
        "view_columns": [
            col("id", "col.id"),
            col("merchant_name", "col.merchant"),
            col("driver_name", "col.driver"),
            col("post_name", "col.post"),
            col("city_name", "col.city"),
            col("street_name", "col.street"),
            col("items_summary", "col.items"),
            col("total_price_iqd", "col.total"),
            col("status", "col.status"),
            col("order_date", "col.date"),
            col("delivery_days", "col.days"),
        ],
        "search": ["status"],
        "fields": [
            field("merchant_id", "col.merchant", "relation", source="merchants"),
            field("driver_id", "col.driver", "relation", source="drivers"),
            field("post_id", "col.post_office", "relation", source="posts"),
            field("city_id", "col.city", "relation", source="cities"),
            field("street_id", "col.street", "relation", source="streets"),
            field("order_date", "col.order_date", "date"),
            field("delivery_days", "col.delivery_days", "number"),
        ],
    },
    "ratings": {
        "title_key": "table.ratings",
        "model": Rating,
        "view_columns": [
            col("id", "col.id"),
            col("item_name", "col.item"),
            col("score", "col.score"),
            col("comment", "col.comment"),
            col("created_at", "col.created"),
        ],
        "search": trilang_search("comment"),
        "fields": [
            field("item_id", "col.item", "relation", source="items"),
            field("score", "col.score_1_5", "number"),
        ]
        + trilang_fields("comment", "comment", required=False),
    },
    "feedbacks": {
        "title_key": "table.feedbacks",
        "model": Feedback,
        "view_columns": [
            col("id", "col.id"),
            col("title", "col.title"),
            col("body", "col.body"),
            col("created_at", "col.created"),
        ],
        "search": trilang_search("title") + trilang_search("body"),
        "fields": trilang_fields("title", "title") + trilang_fields("body", "body"),
    },
}

OPTION_SOURCES = {
    "roles": Role,
    "provinces": Province,
    "cities": City,
    "streets": Street,
    "posts": Post,
    "drivers": Driver,
    "merchants": Merchant,
    "item_types": ItemType,
    "items": Item,
}


def translate_columns(columns):
    from i18n import t

    out = []
    for c in columns:
        item = dict(c)
        key = item.get("label_key")
        item["label"] = t(key) if key else item.get("label", item.get("key", ""))
        out.append(item)
    return out


def translate_fields(fields):
    from i18n import t

    out = []
    for f in fields:
        item = dict(f)
        key = item.get("label_key") or item.get("i18n")
        item["label"] = t(key) if key else item.get("label", item.get("name", ""))
        out.append(item)
    return out


def nav_tables():
    from i18n import t

    return {
        key: {"title": t(meta.get("title_key", f"table.{key}")), "title_key": meta.get("title_key")}
        for key, meta in TABLES.items()
    }
