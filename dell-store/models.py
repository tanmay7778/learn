from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ---- PRODUCT MODEL ----
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # laptop, desktop, all-in-one, accessory
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
    image_url = db.Column(db.String(500))  # Primary/thumbnail image (backward compat)
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
    images = db.relationship("ProductImage", backref="product", lazy=True,
                             order_by="ProductImage.display_order")


# ---- PRODUCT IMAGE MODEL (Multiple images per product) ----
class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)  # Featured image for listing
    display_order = db.Column(db.Integer, default=0)  # Sort order in slider
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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


# ---- SERVICE REQUEST MODEL (replaces service_requests.json) ----
class ServiceRequest(db.Model):
    __tablename__ = "service_requests"

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(20), unique=True, nullable=False)  # SRV-XXXXX
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120))  # Linked to logged-in user
    model = db.Column(db.String(100), nullable=False)  # Dell model name
    issue_description = db.Column(db.Text, nullable=False)
    parts = db.Column(db.Text)  # JSON string of parts list
    total_estimate = db.Column(db.Float, default=0)
    status = db.Column(db.String(30), default="pending")  # pending, in-progress, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---- SERVICE PART MODEL (replaces service_parts.xlsx) ----
class ServicePart(db.Model):
    __tablename__ = "service_parts"

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)  # e.g., "Dell XPS 13 9340"
    part = db.Column(db.String(100), nullable=False)   # e.g., "Battery"
    part_code = db.Column(db.String(30), nullable=False)  # e.g., "BAT-9340"
    price = db.Column(db.Float, nullable=False)        # Part cost in ₹
    labour_charge = db.Column(db.Float, default=0)     # Labour cost in ₹
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite unique constraint (one entry per model+part_code)
    __table_args__ = (
        db.UniqueConstraint("model", "part_code", name="uq_model_part_code"),
    )
