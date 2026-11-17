"""
Seed script — reset MySQL schema and load sample rows from data/*.py.

    python seed.py
"""

from app import create_app
from extensions import db
from models import (
    Admin,
    City,
    Driver,
    Item,
    ItemType,
    Merchant,
    Order,
    OrderItem,
    Post,
    Province,
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
from data.admins import admins
from data.item_types import item_types
from data.items import items
from data.orders import orders
from data.order_items import order_items


def seed():
    app = create_app()
    with app.app_context():
        # Hard reset on the SAME connection (pool-safe):
        # SET FOREIGN_KEY_CHECKS on session A does not apply to drop_all on session B.
        engine = db.engine
        with engine.begin() as conn:
            conn.execute(db.text("SET FOREIGN_KEY_CHECKS=0"))
            # Drop every table that currently exists (old + new schema leftovers).
            rows = conn.execute(db.text("SHOW TABLES")).fetchall()
            for (table_name,) in rows:
                conn.execute(db.text(f"DROP TABLE IF EXISTS `{table_name}`"))
            conn.execute(db.text("SET FOREIGN_KEY_CHECKS=1"))
        db.create_all()

        db.session.bulk_insert_mappings(Role, roles)
        db.session.bulk_insert_mappings(Province, provinces)
        db.session.bulk_insert_mappings(City, cities)
        db.session.bulk_insert_mappings(Street, streets)
        db.session.bulk_insert_mappings(Post, posts)
        db.session.bulk_insert_mappings(Driver, drivers)
        db.session.bulk_insert_mappings(Merchant, merchants)
        db.session.bulk_insert_mappings(Admin, admins)
        db.session.bulk_insert_mappings(ItemType, item_types)
        db.session.bulk_insert_mappings(Item, items)
        db.session.bulk_insert_mappings(Order, orders)
        db.session.bulk_insert_mappings(OrderItem, order_items)
        db.session.commit()

        # Build opening stock-history rows so the history page is not empty.
        # For delivered / in-transit / pending seed orders we log a sale movement.
        history_rows = []
        for oi in order_items:
            order = next(o for o in orders if o["id"] == oi["order_id"])
            if order["status"] == "Cancelled":
                continue
            item = next(i for i in items if i["id"] == oi["item_id"])
            # Approximate: stock_after is current seed stock; before = after + qty
            after = item["stock"]
            before = after + oi["quantity"]
            history_rows.append(
                {
                    "item_id": oi["item_id"],
                    "change_qty": -oi["quantity"],
                    "stock_before": before,
                    "stock_after": after,
                    "reason": "order_sale",
                    "order_id": oi["order_id"],
                    "note": f"Seed order #{oi['order_id']}",
                }
            )
        if history_rows:
            db.session.bulk_insert_mappings(StockHistory, history_rows)
            db.session.commit()

        print("Seed complete (schema reset + sample data + stock history).")


if __name__ == "__main__":
    seed()
