"""
Single source of truth for the generic table UI.

Instead of writing 10 nearly identical Flask routes / templates, we describe
each entity here (title, model, columns, search fields, form fields).
app.py + table.html then loop over this registry.

Field types used by modal forms: text, number, float, bool, date
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
    Street,
)

TABLES = {
    "provinces": {
        "title": "Provinces",
        "model": Province,
        "columns": ["id", "name", "code", "population"],
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
        "columns": ["id", "name", "province_id", "population"],
        "search": ["name"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "province_id", "label": "Province ID", "type": "number", "required": True},
            {"name": "population", "label": "Population", "type": "number", "required": True},
        ],
    },
    "streets": {
        "title": "Streets",
        "model": Street,
        "columns": ["id", "name", "city_id", "postal_code"],
        "search": ["name", "postal_code"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "city_id", "label": "City ID", "type": "number", "required": True},
            {"name": "postal_code", "label": "Postal Code", "type": "text", "required": True},
        ],
    },
    "posts": {
        "title": "Post Offices",
        "model": Post,
        "columns": ["id", "name", "city_id", "street_id", "capacity", "staff_count"],
        "search": ["name"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "city_id", "label": "City ID", "type": "number", "required": True},
            {"name": "street_id", "label": "Street ID", "type": "number", "required": True},
            {"name": "capacity", "label": "Capacity", "type": "number", "required": True},
            {"name": "staff_count", "label": "Staff Count", "type": "number", "required": True},
        ],
    },
    "drivers": {
        "title": "Drivers",
        "model": Driver,
        "columns": [
            "id", "name", "phone", "post_id", "vehicle_type",
            "deliveries", "rating", "years_experience",
        ],
        "search": ["name", "phone", "vehicle_type"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "phone", "label": "Phone", "type": "text", "required": True},
            {"name": "post_id", "label": "Post ID", "type": "number", "required": True},
            {"name": "vehicle_type", "label": "Vehicle Type", "type": "text", "required": True},
            {"name": "deliveries", "label": "Deliveries", "type": "number", "required": True},
            {"name": "rating", "label": "Rating", "type": "float", "required": True},
            {"name": "years_experience", "label": "Years Experience", "type": "number", "required": True},
        ],
    },
    "merchants": {
        "title": "Merchants",
        "model": Merchant,
        "columns": [
            "id", "name", "city_id", "phone", "category",
            "total_orders", "revenue",
        ],
        "search": ["name", "phone", "category"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "city_id", "label": "City ID", "type": "number", "required": True},
            {"name": "phone", "label": "Phone", "type": "text", "required": True},
            {"name": "category", "label": "Category", "type": "text", "required": True},
            {"name": "total_orders", "label": "Total Orders", "type": "number", "required": True},
            {"name": "revenue", "label": "Revenue", "type": "float", "required": True},
        ],
    },
    "admins": {
        "title": "Admins",
        "model": Admin,
        "columns": ["id", "name", "email", "role", "post_id", "active"],
        "search": ["name", "email", "role"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "text", "required": True},
            {"name": "role", "label": "Role", "type": "text", "required": True},
            {"name": "post_id", "label": "Post ID", "type": "number", "required": True},
            {"name": "active", "label": "Active", "type": "bool", "required": False},
        ],
    },
    "item_types": {
        "title": "Item Types",
        "model": ItemType,
        "columns": ["id", "name", "description", "avg_weight_kg"],
        "search": ["name", "description"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "text", "required": True},
            {"name": "avg_weight_kg", "label": "Avg Weight (kg)", "type": "float", "required": True},
        ],
    },
    "items": {
        "title": "Items",
        "model": Item,
        "columns": [
            "id", "name", "item_type_id", "merchant_id",
            "price", "weight_kg", "stock",
        ],
        "search": ["name"],
        "fields": [
            {"name": "name", "label": "Name", "type": "text", "required": True},
            {"name": "item_type_id", "label": "Item Type ID", "type": "number", "required": True},
            {"name": "merchant_id", "label": "Merchant ID", "type": "number", "required": True},
            {"name": "price", "label": "Price", "type": "float", "required": True},
            {"name": "weight_kg", "label": "Weight (kg)", "type": "float", "required": True},
            {"name": "stock", "label": "Stock", "type": "number", "required": True},
        ],
    },
    "orders": {
        "title": "Orders",
        "model": Order,
        "columns": [
            "id", "merchant_id", "driver_id", "post_id", "city_id",
            "street_id", "item_id", "quantity", "total_price",
            "status", "order_date", "delivery_days",
        ],
        "search": ["status"],
        "fields": [
            {"name": "merchant_id", "label": "Merchant ID", "type": "number", "required": True},
            {"name": "driver_id", "label": "Driver ID", "type": "number", "required": True},
            {"name": "post_id", "label": "Post ID", "type": "number", "required": True},
            {"name": "city_id", "label": "City ID", "type": "number", "required": True},
            {"name": "street_id", "label": "Street ID", "type": "number", "required": True},
            {"name": "item_id", "label": "Item ID", "type": "number", "required": True},
            {"name": "quantity", "label": "Quantity", "type": "number", "required": True},
            {"name": "total_price", "label": "Total Price", "type": "float", "required": True},
            {"name": "status", "label": "Status", "type": "text", "required": True},
            {"name": "order_date", "label": "Order Date", "type": "date", "required": True},
            {"name": "delivery_days", "label": "Delivery Days", "type": "number", "required": True},
        ],
    },
}


def nav_tables():
    """Lightweight dict for the sidebar (titles only — no model objects in templates)."""
    return {key: {"title": meta["title"]} for key, meta in TABLES.items()}
