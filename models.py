"""
ORM models = Python classes that map 1:1 to MySQL tables.
Text fields that users see use trilang columns: *_en / *_ar / *_ckb
(like enName / arName / ckbName in camelCase APIs).
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


def _trilang_dict(obj, base):
    return {
        f"{base}_en": getattr(obj, f"{base}_en", None),
        f"{base}_ar": getattr(obj, f"{base}_ar", None),
        f"{base}_ckb": getattr(obj, f"{base}_ckb", None),
    }


class Role(SoftDeleteMixin, db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False, default="")
    name_ckb = db.Column(db.String(100), nullable=False, default="")
    description_en = db.Column(db.String(255), nullable=False, default="")
    description_ar = db.Column(db.String(255), nullable=False, default="")
    description_ckb = db.Column(db.String(255), nullable=False, default="")

    admins = db.relationship("Admin", back_populates="role_rel", lazy="dynamic")

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "description": localized(self, "description"),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "name"))
        d.update(_trilang_dict(self, "description"))
        return d


class Province(SoftDeleteMixin, db.Model):
    __tablename__ = "provinces"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False, default="")
    name_ckb = db.Column(db.String(100), nullable=False, default="")
    code = db.Column(db.String(20), nullable=False)
    population = db.Column(db.Integer, nullable=False, default=0)

    cities = db.relationship("City", back_populates="province", lazy="dynamic")

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "code": self.code,
            "population": self.population,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "name"))
        return d


class City(SoftDeleteMixin, db.Model):
    __tablename__ = "cities"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False, default="")
    name_ckb = db.Column(db.String(100), nullable=False, default="")
    province_id = db.Column(db.Integer, db.ForeignKey("provinces.id"), nullable=False)
    population = db.Column(db.Integer, nullable=False, default=0)

    province = db.relationship("Province", back_populates="cities")

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "province_id": self.province_id,
            "population": self.population,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "name"))
        return d


class Street(SoftDeleteMixin, db.Model):
    __tablename__ = "streets"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(120), nullable=False)
    name_ar = db.Column(db.String(120), nullable=False, default="")
    name_ckb = db.Column(db.String(120), nullable=False, default="")
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)

    city = db.relationship("City")

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "city_id": self.city_id,
            "postal_code": self.postal_code,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "name"))
        return d


class Post(SoftDeleteMixin, db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(120), nullable=False)
    name_ar = db.Column(db.String(120), nullable=False, default="")
    name_ckb = db.Column(db.String(120), nullable=False, default="")
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    street_id = db.Column(db.Integer, db.ForeignKey("streets.id"), nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=0)
    staff_count = db.Column(db.Integer, nullable=False, default=0)

    city = db.relationship("City")
    street = db.relationship("Street")

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "city_id": self.city_id,
            "street_id": self.street_id,
            "capacity": self.capacity,
            "staff_count": self.staff_count,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "name"))
        return d


class Driver(SoftDeleteMixin, db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(120), nullable=False)
    name_ar = db.Column(db.String(120), nullable=False, default="")
    name_ckb = db.Column(db.String(120), nullable=False, default="")
    phone = db.Column(db.String(30), nullable=False)
    vehicle_type_en = db.Column(db.String(50), nullable=False, default="")
    vehicle_type_ar = db.Column(db.String(50), nullable=False, default="")
    vehicle_type_ckb = db.Column(db.String(50), nullable=False, default="")
    deliveries = db.Column(db.Integer, nullable=False, default=0)
    rating = db.Column(db.Float, nullable=False, default=0)
    years_experience = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "phone": self.phone,
            "vehicle_type": localized(self, "vehicle_type"),
            "deliveries": self.deliveries,
            "rating": self.rating,
            "years_experience": self.years_experience,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "name"))
        d.update(_trilang_dict(self, "vehicle_type"))
        return d


class Merchant(SoftDeleteMixin, db.Model):
    __tablename__ = "merchants"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(120), nullable=False)
    name_ar = db.Column(db.String(120), nullable=False, default="")
    name_ckb = db.Column(db.String(120), nullable=False, default="")
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    total_orders = db.Column(db.Integer, nullable=False, default=0)
    revenue = db.Column(db.Float, nullable=False, default=0)

    city = db.relationship("City")

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "city_id": self.city_id,
            "phone": self.phone,
            "total_orders": self.total_orders,
            "revenue": self.revenue,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "name"))
        return d


class Admin(SoftDeleteMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(120), nullable=False)
    name_ar = db.Column(db.String(120), nullable=False, default="")
    name_ckb = db.Column(db.String(120), nullable=False, default="")
    email = db.Column(db.String(120), nullable=False)
    # Never store plaintext — use set_password() / auth.hash_password()
    password_hash = db.Column(db.String(255), nullable=False, default="")
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    role_rel = db.relationship("Role", back_populates="admins")

    def set_password(self, plain: str):
        from auth import hash_password

        self.password_hash = hash_password(plain)

    def check_password(self, plain: str) -> bool:
        from auth import verify_password

        return verify_password(self.password_hash, plain)

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "email": self.email,
            "role_id": self.role_id,
            "active": self.active,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            # password_hash intentionally omitted from API / tables
        }
        d.update(_trilang_dict(self, "name"))
        return d


class ItemType(SoftDeleteMixin, db.Model):
    __tablename__ = "item_types"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False, default="")
    name_ckb = db.Column(db.String(100), nullable=False, default="")
    description_en = db.Column(db.String(255), nullable=False, default="")
    description_ar = db.Column(db.String(255), nullable=False, default="")
    description_ckb = db.Column(db.String(255), nullable=False, default="")

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "description": localized(self, "description"),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "name"))
        d.update(_trilang_dict(self, "description"))
        return d


class Item(SoftDeleteMixin, db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(120), nullable=False)
    name_ar = db.Column(db.String(120), nullable=False, default="")
    name_ckb = db.Column(db.String(120), nullable=False, default="")
    item_type_id = db.Column(db.Integer, db.ForeignKey("item_types.id"), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchants.id"), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)

    item_type = db.relationship("ItemType")
    merchant = db.relationship("Merchant")
    stock_history = db.relationship("StockHistory", back_populates="item", lazy="dynamic")
    ratings = db.relationship("Rating", back_populates="item", lazy="dynamic")

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "name": localized(self, "name"),
            "item_type_id": self.item_type_id,
            "merchant_id": self.merchant_id,
            "price": self.price,
            "stock": self.stock,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "name"))
        return d


class Rating(SoftDeleteMixin, db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=5)
    comment_en = db.Column(db.String(255), nullable=False, default="")
    comment_ar = db.Column(db.String(255), nullable=False, default="")
    comment_ckb = db.Column(db.String(255), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    item = db.relationship("Item", back_populates="ratings")

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "item_id": self.item_id,
            "score": self.score,
            "comment": localized(self, "comment"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "comment"))
        return d


class Feedback(SoftDeleteMixin, db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    title_en = db.Column(db.String(150), nullable=False)
    title_ar = db.Column(db.String(150), nullable=False, default="")
    title_ckb = db.Column(db.String(150), nullable=False, default="")
    body_en = db.Column(db.Text, nullable=False, default="")
    body_ar = db.Column(db.Text, nullable=False, default="")
    body_ckb = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        from i18n import localized

        d = {
            "id": self.id,
            "title": localized(self, "title"),
            "body": localized(self, "body"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        d.update(_trilang_dict(self, "title"))
        d.update(_trilang_dict(self, "body"))
        return d


class Order(SoftDeleteMixin, db.Model):
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
