"""
Registry for generic table UI + relation combobox sources.

Field types:
  text | number | float | bool | date | relation

relation fields use a searchable combobox (type-to-filter, then select).
"""

from models import (
    Admin,
    City,
    Driver,
    Item,
    ItemType,
    Merchant,
    Order,
    Post,
    Province,
    Role,
    Street,
)

TABLES = {
    "roles": {
        "title": "Roles",
        "model": Role,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "description", "label": "Description"},
        ],
        "search": ["name", "description"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "text", "required": True},
        ],
    },
    "provinces": {
        "title": "Provinces",
        "model": Province,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "code", "label": "Code"},
            {"key": "population", "label": "Population"},
        ],
        "search": ["name", "code"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "code", "label": "Code", "type": "text", "required": True},
            {"name": "population", "label": "Population", "type": "number", "required": True},
        ],
    },
    "cities": {
        "title": "Cities",
        "model": City,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "province_name", "label": "Province"},
            {"key": "population", "label": "Population"},
        ],
        "search": ["name"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "province_id", "label": "Province", "type": "relation", "source": "provinces", "required": True},
            {"name": "population", "label": "Population", "type": "number", "required": True},
        ],
    },
    "streets": {
        "title": "Streets",
        "model": Street,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "city_name", "label": "City"},
            {"key": "postal_code", "label": "Postal Code"},
        ],
        "search": ["name", "postal_code"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "city_id", "label": "City", "type": "relation", "source": "cities", "required": True},
            {"name": "postal_code", "label": "Postal Code", "type": "text", "required": True},
        ],
    },
    "posts": {
        "title": "Post Offices",
        "model": Post,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "city_name", "label": "City"},
            {"key": "street_name", "label": "Street"},
            {"key": "capacity", "label": "Capacity"},
            {"key": "staff_count", "label": "Staff"},
        ],
        "search": ["name"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "city_id", "label": "City", "type": "relation", "source": "cities", "required": True},
            {"name": "street_id", "label": "Street", "type": "relation", "source": "streets", "required": True},
            {"name": "capacity", "label": "Capacity", "type": "number", "required": True},
            {"name": "staff_count", "label": "Staff Count", "type": "number", "required": True},
        ],
    },
    "drivers": {
        "title": "Drivers",
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
        "search": ["name", "phone", "vehicle_type"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "phone", "label": "Phone", "type": "text", "required": True},
            {"name": "vehicle_type", "label": "Vehicle Type", "type": "text", "required": True},
            {"name": "deliveries", "label": "Deliveries", "type": "number", "required": True},
            {"name": "rating", "label": "Rating", "type": "float", "required": True},
            {"name": "years_experience", "label": "Years Experience", "type": "number", "required": True},
        ],
    },
    "merchants": {
        "title": "Merchants",
        "model": Merchant,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "city_name", "label": "City"},
            {"key": "phone", "label": "Phone"},
            {"key": "total_orders", "label": "Orders"},
            {"key": "revenue_iqd", "label": "Revenue"},
        ],
        "search": ["name", "phone"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "city_id", "label": "City", "type": "relation", "source": "cities", "required": True},
            {"name": "phone", "label": "Phone", "type": "text", "required": True},
            {"name": "total_orders", "label": "Total Orders", "type": "number", "required": True},
            {"name": "revenue", "label": "Revenue (IQD)", "type": "float", "required": True},
        ],
    },
    "admins": {
        "title": "Admins",
        "model": Admin,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "email", "label": "Email"},
            {"key": "role_name", "label": "Role"},
            {"key": "active", "label": "Active"},
        ],
        "search": ["name", "email"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "text", "required": True},
            {"name": "role_id", "label": "Role", "type": "relation", "source": "roles", "required": True},
            {"name": "active", "label": "Active", "type": "bool", "required": False},
        ],
    },
    "item_types": {
        "title": "Item Types",
        "model": ItemType,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "description", "label": "Description"},
        ],
        "search": ["name", "description"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "text", "required": True},
        ],
    },
    "items": {
        "title": "Items",
        "model": Item,
        "view_columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "item_type_name", "label": "Item Type"},
            {"key": "merchant_name", "label": "Merchant"},
            {"key": "price_iqd", "label": "Price"},
            {"key": "stock", "label": "Stock"},
        ],
        "search": ["name"],
        "row_link": "stock_history",  # clicking a row opens stock history
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "item_type_id", "label": "Item Type", "type": "relation", "source": "item_types", "required": True},
            {"name": "merchant_id", "label": "Merchant", "type": "relation", "source": "merchants", "required": True},
            {"name": "price", "label": "Price (IQD)", "type": "float", "required": True},
            {"name": "stock", "label": "Stock", "type": "number", "required": True},
        ],
    },
    "orders": {
        "title": "Orders",
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
}

# Used by /api/options/<source>
OPTION_SOURCES = {
    "roles": (Role, "name"),
    "provinces": (Province, "name"),
    "cities": (City, "name"),
    "streets": (Street, "name"),
    "posts": (Post, "name"),
    "drivers": (Driver, "name"),
    "merchants": (Merchant, "name"),
    "item_types": (ItemType, "name"),
    "items": (Item, "name"),
}


def nav_tables():
    return {key: {"title": meta["title"]} for key, meta in TABLES.items()}
