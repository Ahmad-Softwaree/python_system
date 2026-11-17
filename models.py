"""
ORM models = Python classes that map 1:1 to MySQL tables.
Uses Flask-SQLAlchemy (no raw SQL in the app layer).
"""

from datetime import datetime, date

from extensions import db


class SoftDeleteMixin:
    """Soft delete: set deleted_at instead of removing the MySQL row."""

    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()

    def restore(self):
        self.deleted_at = None

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class Role(SoftDeleteMixin, db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")

    admins = db.relationship("Admin", back_populates="role_rel", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Province(SoftDeleteMixin, db.Model):
    __tablename__ = "provinces"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    population = db.Column(db.Integer, nullable=False, default=0)

    cities = db.relationship("City", back_populates="province", lazy="dynamic")

    def to_dict(self):
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
    vehicle_type = db.Column(db.String(50), nullable=False)
    deliveries = db.Column(db.Integer, nullable=False, default=0)
    rating = db.Column(db.Float, nullable=False, default=0)
    years_experience = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
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
    total_orders = db.Column(db.Integer, nullable=False, default=0)
    revenue = db.Column(db.Float, nullable=False, default=0)

    city = db.relationship("City")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "city_id": self.city_id,
            "phone": self.phone,
            "total_orders": self.total_orders,
            "revenue": self.revenue,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Admin(SoftDeleteMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    role_rel = db.relationship("Role", back_populates="admins")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role_id": self.role_id,
            "active": self.active,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class ItemType(SoftDeleteMixin, db.Model):
    __tablename__ = "item_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Item(SoftDeleteMixin, db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    item_type_id = db.Column(db.Integer, db.ForeignKey("item_types.id"), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchants.id"), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0)  # stored as IQD
    stock = db.Column(db.Integer, nullable=False, default=0)

    item_type = db.relationship("ItemType")
    merchant = db.relationship("Merchant")
    stock_history = db.relationship("StockHistory", back_populates="item", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "item_type_id": self.item_type_id,
            "merchant_id": self.merchant_id,
            "price": self.price,
            "stock": self.stock,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Order(SoftDeleteMixin, db.Model):
    """
    One order can have MANY items via order_items.
    item_id/quantity were removed from this table on purpose.
    """

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchants.id"), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    street_id = db.Column(db.Integer, db.ForeignKey("streets.id"), nullable=False)
    total_price = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(40), nullable=False, default="Pending")
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    delivery_days = db.Column(db.Integer, nullable=False, default=0)

    merchant = db.relationship("Merchant")
    driver = db.relationship("Driver")
    post = db.relationship("Post")
    city = db.relationship("City")
    street = db.relationship("Street")
    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "driver_id": self.driver_id,
            "post_id": self.post_id,
            "city_id": self.city_id,
            "street_id": self.street_id,
            "total_price": self.total_price,
            "status": self.status,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "delivery_days": self.delivery_days,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "order_items": [
                {
                    "item_id": oi.item_id,
                    "quantity": oi.quantity,
                    "unit_price": oi.unit_price,
                    "line_total": oi.line_total,
                }
                for oi in (self.items or [])
            ],
        }


class OrderItem(db.Model):
    """Line items for an order (many items per order)."""

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0)
    line_total = db.Column(db.Float, nullable=False, default=0)

    order = db.relationship("Order", back_populates="items")
    item = db.relationship("Item")


class StockHistory(db.Model):
    """
    Read-only stock movement log for each item.
    change_qty is negative when stock is sold / reserved for an order.
    """

    __tablename__ = "stock_history"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    change_qty = db.Column(db.Integer, nullable=False)
    stock_before = db.Column(db.Integer, nullable=False)
    stock_after = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(80), nullable=False, default="adjustment")
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    note = db.Column(db.String(255), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    item = db.relationship("Item", back_populates="stock_history")
    order = db.relationship("Order")

    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "change_qty": self.change_qty,
            "stock_before": self.stock_before,
            "stock_after": self.stock_after,
            "reason": self.reason,
            "order_id": self.order_id,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


ORDER_STATUSES = ["Pending", "In Transit", "Delivered", "Cancelled"]
