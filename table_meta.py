"""
Registry for generic table UI + relation combobox sources.

Field types:
  text | number | float | bool | date | relation

Multilang fields use name_en / name_ar / name_ckb (etc.).
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


def trilang_fields(base, label_en, required=True):
    """Form fields for EN / AR / CKB of one logical column."""
    return [
        {"name": f"{base}_en", "label": f"{label_en} (EN)", "type": "text", "required": required, "i18n": f"field.{base}_en"},
        {"name": f"{base}_ar", "label": f"{label_en} (AR)", "type": "text", "required": required, "i18n": f"field.{base}_ar"},
        {"name": f"{base}_ckb", "label": f"{label_en} (CKB)", "type": "text", "required": required, "i18n": f"field.{base}_ckb"},
    ]


def trilang_search(base):
    return [f"{base}_en", f"{base}_ar", f"{base}_ckb"]


TABLES = {
    "roles": {
        "title": "Roles",
        "title_key": "table.roles",
        "model": Role,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "description", "label": "Description"},
        ],
        "search": trilang_search("name") + trilang_search("description"),
        "fields": trilang_fields("name", "Name") + trilang_fields("description", "Description"),
    },
    "provinces": {
        "title": "Provinces",
        "title_key": "table.provinces",
        "model": Province,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "code", "label": "Code"},
            {"key": "population", "label": "Population"},
        ],
        "search": trilang_search("name") + ["code"],
        "fields": trilang_fields("name", "Name")
        + [
            {"name": "code", "label": "Code", "type": "text", "required": True},
            {"name": "population", "label": "Population", "type": "number", "required": True},
        ],
    },
    "cities": {
        "title": "Cities",
        "title_key": "table.cities",
        "model": City,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "province_name", "label": "Province"},
            {"key": "population", "label": "Population"},
        ],
        "search": trilang_search("name"),
        "fields": trilang_fields("name", "Name")
        + [
            {"name": "province_id", "label": "Province", "type": "relation", "source": "provinces", "required": True},
            {"name": "population", "label": "Population", "type": "number", "required": True},
        ],
    },
    "streets": {
        "title": "Streets",
        "title_key": "table.streets",
        "model": Street,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "city_name", "label": "City"},
            {"key": "postal_code", "label": "Postal Code"},
        ],
        "search": trilang_search("name") + ["postal_code"],
        "fields": trilang_fields("name", "Name")
        + [
            {"name": "city_id", "label": "City", "type": "relation", "source": "cities", "required": True},
            {"name": "postal_code", "label": "Postal Code", "type": "text", "required": True},
        ],
    },
    "posts": {
        "title": "Post Offices",
        "title_key": "table.posts",
        "model": Post,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "city_name", "label": "City"},
            {"key": "street_name", "label": "Street"},
            {"key": "capacity", "label": "Capacity"},
            {"key": "staff_count", "label": "Staff"},
        ],
        "search": trilang_search("name"),
        "fields": trilang_fields("name", "Name")
        + [
            {"name": "city_id", "label": "City", "type": "relation", "source": "cities", "required": True},
            {"name": "street_id", "label": "Street", "type": "relation", "source": "streets", "required": True},
            {"name": "capacity", "label": "Capacity", "type": "number", "required": True},
            {"name": "staff_count", "label": "Staff Count", "type": "number", "required": True},
        ],
    },
    "drivers": {
        "title": "Drivers",
        "title_key": "table.drivers",
        "model": Driver,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "phone", "label": "Phone"},
            {"key": "vehicle_type", "label": "Vehicle"},
            {"key": "deliveries", "label": "Deliveries"},
            {"key": "rating", "label": "Rating"},
            {"key": "years_experience", "label": "Years Exp."},
        ],
        "search": trilang_search("name") + ["phone"] + trilang_search("vehicle_type"),
        "fields": trilang_fields("name", "Name")
        + [
            {"name": "phone", "label": "Phone", "type": "text", "required": True},
        ]
        + trilang_fields("vehicle_type", "Vehicle Type")
        + [
            {"name": "deliveries", "label": "Deliveries", "type": "number", "required": True},
            {"name": "rating", "label": "Rating", "type": "float", "required": True},
            {"name": "years_experience", "label": "Years Experience", "type": "number", "required": True},
        ],
    },
    "merchants": {
        "title": "Merchants",
        "title_key": "table.merchants",
        "model": Merchant,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "city_name", "label": "City"},
            {"key": "phone", "label": "Phone"},
            {"key": "total_orders", "label": "Orders"},
            {"key": "revenue_iqd", "label": "Revenue"},
        ],
        "search": trilang_search("name") + ["phone"],
        "fields": trilang_fields("name", "Name")
        + [
            {"name": "city_id", "label": "City", "type": "relation", "source": "cities", "required": True},
            {"name": "phone", "label": "Phone", "type": "text", "required": True},
            {"name": "total_orders", "label": "Total Orders", "type": "number", "required": True},
            {"name": "revenue", "label": "Revenue (IQD)", "type": "float", "required": True},
        ],
    },
    "admins": {
        "title": "Admins",
        "title_key": "table.admins",
        "model": Admin,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "email", "label": "Email"},
            {"key": "role_name", "label": "Role"},
            {"key": "active", "label": "Active"},
        ],
        "search": trilang_search("name") + ["email"],
        "fields": trilang_fields("name", "Name")
        + [
            {"name": "email", "label": "Email", "type": "text", "required": True},
            {"name": "role_id", "label": "Role", "type": "relation", "source": "roles", "required": True},
            {"name": "active", "label": "Active", "type": "bool", "required": False},
        ],
    },
    "item_types": {
        "title": "Item Types",
        "title_key": "table.item_types",
        "model": ItemType,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "description", "label": "Description"},
        ],
        "search": trilang_search("name") + trilang_search("description"),
        "fields": trilang_fields("name", "Name") + trilang_fields("description", "Description"),
    },
    "items": {
        "title": "Items",
        "title_key": "table.items",
        "model": Item,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "item_type_name", "label": "Item Type"},
            {"key": "merchant_name", "label": "Merchant"},
            {"key": "price_iqd", "label": "Price"},
            {"key": "stock", "label": "Stock"},
        ],
        "search": trilang_search("name"),
        "row_link": "stock_history",
        "fields": trilang_fields("name", "Name")
        + [
            {"name": "item_type_id", "label": "Item Type", "type": "relation", "source": "item_types", "required": True},
            {"name": "merchant_id", "label": "Merchant", "type": "relation", "source": "merchants", "required": True},
            {"name": "price", "label": "Price (IQD)", "type": "float", "required": True},
            {"name": "stock", "label": "Stock", "type": "number", "required": True},
        ],
    },
    "orders": {
        "title": "Orders",
        "title_key": "table.orders",
        "model": Order,
        "special": "orders",
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "merchant_name", "label": "Merchant"},
            {"key": "driver_name", "label": "Driver"},
            {"key": "post_name", "label": "Post"},
            {"key": "city_name", "label": "City"},
            {"key": "street_name", "label": "Street"},
            {"key": "items_summary", "label": "Items"},
            {"key": "total_price_iqd", "label": "Total"},
            {"key": "status", "label": "Status"},
            {"key": "order_date", "label": "Date"},
            {"key": "delivery_days", "label": "Days"},
        ],
        "search": ["status"],
        "fields": [
            {"name": "merchant_id", "label": "Merchant", "type": "relation", "source": "merchants", "required": True},
            {"name": "driver_id", "label": "Driver", "type": "relation", "source": "drivers", "required": True},
            {"name": "post_id", "label": "Post Office", "type": "relation", "source": "posts", "required": True},
            {"name": "city_id", "label": "City", "type": "relation", "source": "cities", "required": True},
            {"name": "street_id", "label": "Street", "type": "relation", "source": "streets", "required": True},
            {"name": "order_date", "label": "Order Date", "type": "date", "required": True},
            {"name": "delivery_days", "label": "Delivery Days", "type": "number", "required": True},
        ],
    },
    "ratings": {
        "title": "Ratings",
        "title_key": "table.ratings",
        "model": Rating,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "item_name", "label": "Item"},
            {"key": "score", "label": "Score"},
            {"key": "comment", "label": "Comment"},
            {"key": "created_at", "label": "Created"},
        ],
        "search": trilang_search("comment"),
        "fields": [
            {"name": "item_id", "label": "Item", "type": "relation", "source": "items", "required": True},
            {"name": "score", "label": "Score (1-5)", "type": "number", "required": True},
        ]
        + trilang_fields("comment", "Comment", required=False),
    },
    "feedbacks": {
        "title": "Feedback",
        "title_key": "table.feedbacks",
        "model": Feedback,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "title", "label": "Title"},
            {"key": "body", "label": "Body"},
            {"key": "created_at", "label": "Created"},
        ],
        "search": trilang_search("title") + trilang_search("body"),
        "fields": trilang_fields("title", "Title") + trilang_fields("body", "Body"),
    },
}

# Combobox sources — label column is resolved live via localized()
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


def nav_tables():
    from i18n import t

    return {
        key: {"title": t(meta.get("title_key", f"table.{key}")), "title_key": meta.get("title_key")}
        for key, meta in TABLES.items()
    }
