"""
Seed script — load sample rows from data/*.py into MySQL.

Run once after configuring .env:
    python seed.py

Re-run anytime to RESET the database back to the sample dataset.
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
    Post,
    Province,
    Street,
)
# These modules are ONLY seed data (lists of dicts), not the live database.
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


def _clear():
    # Delete child tables BEFORE parents, otherwise MySQL foreign-key
    # constraints would block the delete (orders reference items, etc.).
    for model in (
        Order, Item, Admin, Driver, Merchant, Post, Street, City, ItemType, Province
    ):
        model.query.delete()
    db.session.commit()


def seed(reset=True):
    # create_app() gives us a Flask app without starting the web server.
    # app_context() is required so SQLAlchemy knows which app/db to use.
    app = create_app()
    with app.app_context():
        db.create_all()
        if reset:
            _clear()

        if Province.query.count() == 0:
            # bulk_insert_mappings is faster than adding objects one-by-one.
            # Parent tables first, then children that reference them.
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
            db.session.commit()
            print("Seed complete.")
        else:
            print("Data already present — skipped.")


if __name__ == "__main__":
    seed(reset=True)
