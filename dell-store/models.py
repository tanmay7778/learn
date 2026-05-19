from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ---- PRODUCT MODEL ----
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # laptop, desktop, all-in-one
    dell_series = db.Column(db.String(50))  # Inspiron, XPS, Latitude, OptiPlex, Vostro

    # Specs (scraped from Dell)
    processor = db.Column(db.String(100))
    ram = db.Column(db.String(50))
    storage = db.Column(db.String(100))
    display = db.Column(db.String(100))
    graphics = db.Column(db.String(100))
    os = db.Column(db.String(50))
    weight = db.Column(db.String(30))
    ports = db.Column(db.Text)

    # Pricing (YOU set this)
    dell_mrp = db.Column(db.Float)  # Dell's listed price (scraped)
    selling_price = db.Column(db.Float)  # YOUR price
    discount_percent = db.Column(db.Float)  # Auto-calculated

    # Images & links
    image_url = db.Column(db.String(500))
    dell_url = db.Column(db.String(500))  # Original Dell page

    # Stock
    in_stock = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=0)

    # Timestamps
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order_items = db.relationship("OrderItem", backref="product", lazy=True)
    reviews = db.relationship("Review", backref="product", lazy=True)


# ---- USER MODEL ----
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", backref="user", lazy=True)
    reviews = db.relationship("Review", backref="user", lazy=True)


# ---- ORDER MODEL ----
class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="pending")  # pending, confirmed, shipped, delivered
    payment_id = db.Column(db.String(100))  # Razorpay/Stripe payment ID
    payment_status = db.Column(db.String(30), default="unpaid")
    shipping_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True)


# ---- ORDER ITEMS ----
class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_at_purchase = db.Column(db.Float, nullable=False)


# ---- REVIEW MODEL ----
class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
