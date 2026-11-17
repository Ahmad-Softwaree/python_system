"""
ORM models = Python classes that map 1:1 to MySQL tables.

We use Flask-SQLAlchemy (ORM) instead of writing raw SQL strings.
Each class becomes a table; each attribute becomes a column.
"""

from datetime import datetime, date

from extensions import db


class SoftDeleteMixin:
    """
    Soft delete pattern (important for the presentation):

    - Normal "Delete" in the UI does NOT remove the MySQL row.
    - It sets deleted_at = current timestamp.
    - Active pages only show rows where deleted_at IS NULL.
    - Deleted pages show rows where deleted_at IS NOT NULL.
    - Restore sets deleted_at back to NULL.

    Mixin = a small class we inherit so every model gets the same behaviour
    without copy-pasting these three methods into every table class.
    """

    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()

    def restore(self):
        self.deleted_at = None

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class Province(SoftDeleteMixin, db.Model):
    __tablename__ = "provinces"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    population = db.Column(db.Integer, nullable=False, default=0)

    # Relationship: one province has many cities (ORM-level link, not a DB column).
    cities = db.relationship("City", back_populates="province", lazy="dynamic")

    def to_dict(self):
        # Templates and charts prefer plain dicts / JSON, not ORM objects.
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "population": self.population,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class City(SoftDeleteMixin, db.Model):
    __tablename__ = "cities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Foreign key → provinces.id (referential integrity in MySQL).
    province_id = db.Column(db.Integer, db.ForeignKey("provinces.id"), nullable=False)
    population = db.Column(db.Integer, nullable=False, default=0)

    province = db.relationship("Province", back_populates="cities")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "province_id": self.province_id,
            "population": self.population,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Street(SoftDeleteMixin, db.Model):
    __tablename__ = "streets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)

    city = db.relationship("City")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "city_id": self.city_id,
            "postal_code": self.postal_code,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Post(SoftDeleteMixin, db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    street_id = db.Column(db.Integer, db.ForeignKey("streets.id"), nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=0)
    staff_count = db.Column(db.Integer, nullable=False, default=0)

    city = db.relationship("City")
    street = db.relationship("Street")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "city_id": self.city_id,
            "street_id": self.street_id,
            "capacity": self.capacity,
            "staff_count": self.staff_count,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Driver(SoftDeleteMixin, db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    deliveries = db.Column(db.Integer, nullable=False, default=0)
    rating = db.Column(db.Float, nullable=False, default=0)
    years_experience = db.Column(db.Integer, nullable=False, default=0)

    post = db.relationship("Post")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "post_id": self.post_id,
            "vehicle_type": self.vehicle_type,
            "deliveries": self.deliveries,
            "rating": self.rating,
            "years_experience": self.years_experience,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Merchant(SoftDeleteMixin, db.Model):
    __tablename__ = "merchants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    total_orders = db.Column(db.Integer, nullable=False, default=0)
    revenue = db.Column(db.Float, nullable=False, default=0)

    city = db.relationship("City")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "city_id": self.city_id,
            "phone": self.phone,
            "category": self.category,
            "total_orders": self.total_orders,
            "revenue": self.revenue,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Admin(SoftDeleteMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    post = db.relationship("Post")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "post_id": self.post_id,
            "active": self.active,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class ItemType(SoftDeleteMixin, db.Model):
    __tablename__ = "item_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")
    avg_weight_kg = db.Column(db.Float, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "avg_weight_kg": self.avg_weight_kg,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Item(SoftDeleteMixin, db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    item_type_id = db.Column(db.Integer, db.ForeignKey("item_types.id"), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchants.id"), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0)
    weight_kg = db.Column(db.Float, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)

    item_type = db.relationship("ItemType")
    merchant = db.relationship("Merchant")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "item_type_id": self.item_type_id,
            "merchant_id": self.merchant_id,
            "price": self.price,
            "weight_kg": self.weight_kg,
            "stock": self.stock,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Order(SoftDeleteMixin, db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchants.id"), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    street_id = db.Column(db.Integer, db.ForeignKey("streets.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(40), nullable=False, default="Pending")
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    delivery_days = db.Column(db.Integer, nullable=False, default=0)

    merchant = db.relationship("Merchant")
    driver = db.relationship("Driver")
    post = db.relationship("Post")
    city = db.relationship("City")
    street = db.relationship("Street")
    item = db.relationship("Item")

    def to_dict(self):
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "driver_id": self.driver_id,
            "post_id": self.post_id,
            "city_id": self.city_id,
            "street_id": self.street_id,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "total_price": self.total_price,
            "status": self.status,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "delivery_days": self.delivery_days,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
