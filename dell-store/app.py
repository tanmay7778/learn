import os
import io
import json
import random
import urllib3
from datetime import datetime
import pandas as pd
import requests as http_requests  # renamed to avoid conflict with flask.request
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Product, User, Order, OrderItem, Review, ProductImage
from config import Config

# Suppress SSL warnings (corporate proxy intercepts HTTPS)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
app.config.from_object(Config)

# Image upload config
UPLOAD_FOLDER = os.path.join(app.static_folder, "images", "products")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max

# Create folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
SERIES_FOLDER = os.path.join(app.static_folder, "images", "series")
os.makedirs(SERIES_FOLDER, exist_ok=True)
# Per-series image folders (laptops, desktops, all-in-ones)
for _series in ["inspiron", "vostro", "xps", "alienware", "optiplex", "precision-tower", "inspiron-desktop", "xps-desktop", "inspiron-aio", "optiplex-aio", "xps-aio"]:
    os.makedirs(os.path.join(SERIES_FOLDER, _series), exist_ok=True)
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_FOLDER, exist_ok=True)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================================
# PUBLIC ROUTES
# ==========================================


@app.route("/")
def index():
    featured = Product.query.filter_by(in_stock=True).limit(8).all()
    return render_template("index.html", products=featured)


@app.route("/laptops")
def laptops_page():
    """Laptop series landing page — shows Inspiron, Vostro, XPS, Alienware cards."""
    return render_template("laptops.html")


# Series-specific detail pages (Inspiron, Vostro, XPS, Alienware)
SERIES_INFO = {
    "inspiron": {
        "name": "Inspiron",
        "tagline": "Everyday Performance",
        "hero_desc": "Designed for everyday life — from schoolwork to entertainment, Inspiron laptops deliver reliable performance at an incredible value.",
        "features": [
            {
                "title": "Designed for productivity",
                "desc": "Maximize productivity with state-of-the-art processors, anti-glare displays and multiple ports for easy connection. Connect with confidence using webcams with Temporal Noise Reduction.",
                "image": "feature1.png",
            },
            {
                "title": "Vibrant visuals",
                "desc": "Immerse yourself in stunning clarity with FHD and FHD+ displays. Wide viewing angles and ComfortView Plus reduce blue light to keep your eyes comfortable during long sessions.",
                "image": "feature2.png",
            },
            {
                "title": "All-day battery",
                "desc": "Stay unplugged longer with batteries built for all-day use. ExpressCharge technology gets you back to 80% in just 60 minutes when you need a quick top-up.",
                "image": "feature3.png",
            },
        ],
    },
    "vostro": {
        "name": "Vostro",
        "tagline": "Business Essential",
        "hero_desc": "Purpose-built for small business. Enhanced security features, durable design, and professional-grade performance to help your business thrive.",
        "features": [
            {
                "title": "Built for business",
                "desc": "Hardware TPM 2.0, fingerprint reader, and Dell Optimizer keep your data secure while intelligently optimizing performance based on how you work.",
                "image": "feature1.png",
            },
            {
                "title": "Reliable & durable",
                "desc": "MIL-STD tested for reliability with reinforced hinges, spill-resistant keyboard, and rubberized edges. Built to survive the daily rigors of business life.",
                "image": "feature2.png",
            },
            {
                "title": "Smart connectivity",
                "desc": "Wi-Fi 6E and optional 4G LTE keep you connected everywhere. Multiple USB-C and HDMI ports for seamless multi-monitor setups at your desk.",
                "image": "feature3.png",
            },
        ],
    },
    "xps": {
        "name": "XPS",
        "tagline": "Premium & Ultra-Portable",
        "hero_desc": "Dell's flagship craftsmanship. InfinityEdge displays, premium materials, and cutting-edge performance in a beautifully thin and light design.",
        "features": [
            {
                "title": "Stunning InfinityEdge display",
                "desc": "Edge-to-edge OLED and 3.5K displays with 100% DCI-P3 color accuracy. HDR 500 certified for breathtaking visuals whether you're creating or consuming content.",
                "image": "feature1.png",
            },
            {
                "title": "Crafted with precision",
                "desc": "CNC-machined aluminum and carbon fiber construction. Weighing just 1.17kg, the XPS 13 is ultraportable without compromising on durability or premium feel.",
                "image": "feature2.png",
            },
            {
                "title": "Intel Core Ultra performance",
                "desc": "Latest Intel Core Ultra processors with integrated NPU for AI-accelerated workflows. Up to 32GB LPDDR5x memory for seamless multitasking and creative work.",
                "image": "feature3.png",
            },
        ],
    },
    "alienware": {
        "name": "Alienware",
        "tagline": "Gaming Powerhouse",
        "hero_desc": "Dominate every game with legendary Alienware engineering. Top-tier GPUs, advanced Cryo-Tech cooling, and high-refresh displays built for competitive gaming.",
        "features": [
            {
                "title": "Unmatched gaming power",
                "desc": "Up to NVIDIA RTX 4090 graphics and Intel Core i9 HX processors. Ray tracing, DLSS 3, and 240Hz displays deliver the ultimate competitive advantage.",
                "image": "feature1.png",
            },
            {
                "title": "Cryo-Tech cooling",
                "desc": "Alienware's patented vapor chamber cooling with Element 31 thermal interface material keeps temperatures low during marathon gaming sessions. Zero throttling, maximum FPS.",
                "image": "feature2.png",
            },
            {
                "title": "Iconic design & AlienFX",
                "desc": "Legend 3.0 industrial design with per-key RGB AlienFX lighting. Stadium-inspired rear thermal shelf and customizable lighting zones let you express your style.",
                "image": "feature3.png",
            },
        ],
    },
}


@app.route("/laptops/<series_name>")
def series_page(series_name):
    """Individual series landing page with scroll-reveal features."""
    series_name = series_name.lower()
    if series_name not in SERIES_INFO:
        flash("Series not found!", "error")
        return redirect(url_for("laptops_page"))

    series = SERIES_INFO[series_name]

    # Get products for this series to show count
    product_count = Product.query.filter_by(
        category="laptop", dell_series=series["name"], in_stock=True
    ).count()

    return render_template(
        "series_detail.html",
        series=series,
        series_key=series_name,
        product_count=product_count,
    )


# ==========================================
# DESKTOP SERIES INFO & ROUTES
# ==========================================

DESKTOP_SERIES_INFO = {
    "optiplex": {
        "name": "OptiPlex",
        "tagline": "Enterprise-Grade Reliability",
        "hero_desc": "The world's most secure and manageable commercial desktops. Built for enterprise deployments with Intel vPro and comprehensive security features.",
        "features": [
            {
                "title": "Enterprise security built-in",
                "desc": "Hardware-based security with Intel vPro, TPM 2.0, and Dell SafeBIOS. Chassis intrusion detection and port lockout keep your business data protected at every level.",
                "image": "feature1.png",
            },
            {
                "title": "Compact & flexible form factors",
                "desc": "From Micro (1.1L) to Tower, choose the form factor that fits your workspace. VESA-mountable micro desktops hide behind monitors for a clutter-free desk.",
                "image": "feature2.png",
            },
            {
                "title": "Built for manageability",
                "desc": "Intel vPro with AMT enables remote management and out-of-band troubleshooting. Dell Client Command Suite provides zero-touch deployment for IT teams.",
                "image": "feature3.png",
            },
        ],
    },
    "xps-desktop": {
        "name": "XPS Desktop",
        "tagline": "Premium Performance",
        "hero_desc": "Uncompromising power meets elegant design. XPS Desktop delivers workstation-class performance for creators, developers, and power users.",
        "features": [
            {
                "title": "Creator-grade power",
                "desc": "Up to Intel Core i9 and NVIDIA RTX 4090 graphics. Handle 8K video editing, 3D rendering, and complex simulations without breaking a sweat.",
                "image": "feature1.png",
            },
            {
                "title": "Elegant minimalist design",
                "desc": "Sleek chassis with premium materials and tool-less interior access. Thoughtful cable management and whisper-quiet thermals keep your workspace pristine.",
                "image": "feature2.png",
            },
            {
                "title": "Expandable & future-proof",
                "desc": "Up to 128GB DDR5 RAM, multiple M.2 NVMe slots, and full-length PCIe 5.0 x16 support. Upgrade components as your needs grow without replacing the system.",
                "image": "feature3.png",
            },
        ],
    },
    "inspiron-desktop": {
        "name": "Inspiron Desktop",
        "tagline": "Everyday Value",
        "hero_desc": "Reliable desktop performance for the whole family. From homework to home entertainment, Inspiron Desktop delivers great value with solid performance.",
        "features": [
            {
                "title": "Perfect for home & family",
                "desc": "Intel Core processors and ample storage handle everyday tasks with ease — browsing, streaming, homework, and light photo editing all run smoothly.",
                "image": "feature1.png",
            },
            {
                "title": "Quiet & compact",
                "desc": "Optimized thermals keep noise levels low during extended use. Compact tower design fits neatly into any home office or living room setup.",
                "image": "feature2.png",
            },
            {
                "title": "Easy connectivity",
                "desc": "Multiple USB ports, HDMI, and SD card reader for all your peripherals. Wi-Fi 6 and Bluetooth 5.2 keep you connected wirelessly throughout your home.",
                "image": "feature3.png",
            },
        ],
    },
    "precision-tower": {
        "name": "Precision Tower",
        "tagline": "Workstation Power",
        "hero_desc": "ISV-certified workstation performance for engineering, data science, and professional applications. Designed for the most demanding workflows.",
        "features": [
            {
                "title": "ISV-certified reliability",
                "desc": "Tested and certified by leading ISVs including Autodesk, SolidWorks, Siemens NX, and ANSYS. Your critical applications run exactly as intended, every time.",
                "image": "feature1.png",
            },
            {
                "title": "Professional GPU options",
                "desc": "NVIDIA RTX A6000 and AMD Radeon Pro graphics with ECC memory. Drive multiple 8K displays and accelerate complex CAD, BIM, and simulation workloads.",
                "image": "feature2.png",
            },
            {
                "title": "Scalable for any workload",
                "desc": "Up to dual Intel Xeon processors, 4TB RAM, and 12 storage bays. Configure for AI/ML training, fluid dynamics, or large-scale data analysis.",
                "image": "feature3.png",
            },
        ],
    },
}


@app.route("/desktops")
def desktops_page():
    """Desktop series landing page — shows OptiPlex, XPS Desktop, Inspiron Desktop, Precision Tower cards."""
    return render_template("desktops.html")


@app.route("/desktops/<series_name>")
def desktop_series_page(series_name):
    """Individual desktop series landing page with scroll-reveal features."""
    series_name = series_name.lower()
    if series_name not in DESKTOP_SERIES_INFO:
        flash("Series not found!", "error")
        return redirect(url_for("desktops_page"))

    series = DESKTOP_SERIES_INFO[series_name]

    product_count = Product.query.filter_by(
        category="desktop", dell_series=series["name"], in_stock=True
    ).count()

    return render_template(
        "series_detail_desktop.html",
        series=series,
        series_key=series_name,
        product_count=product_count,
    )


# ==========================================
# ALL-IN-ONE SERIES INFO & ROUTES
# ==========================================

AIO_SERIES_INFO = {
    "inspiron-aio": {
        "name": "Inspiron AIO",
        "tagline": "Family Entertainment Hub",
        "hero_desc": "A beautiful all-in-one that brings the whole family together. Stunning display, powerful performance, and minimal clutter in one elegant package.",
        "features": [
            {
                "title": "Stunning immersive display",
                "desc": "Up to 27-inch FHD display with narrow bezels and anti-glare coating. Perfect for movie nights, video calls, and creative projects from any viewing angle.",
                "image": "feature1.png",
            },
            {
                "title": "Space-saving elegance",
                "desc": "All the power of a desktop hidden behind a beautiful display. Adjustable stand with cable management keeps your desk clean and your setup minimal.",
                "image": "feature2.png",
            },
            {
                "title": "Built-in entertainment",
                "desc": "Dual speakers with MaxxAudio, FHD webcam with privacy shutter, and pop-up webcam options. Everything you need for streaming, video calls, and music.",
                "image": "feature3.png",
            },
        ],
    },
    "optiplex-aio": {
        "name": "OptiPlex AIO",
        "tagline": "Business All-in-One",
        "hero_desc": "Enterprise-ready all-in-one with space-saving design. Perfect for business environments where desk real estate and IT manageability matter.",
        "features": [
            {
                "title": "Enterprise-ready performance",
                "desc": "Intel Core processors with vPro support and up to 64GB RAM. Handles business applications, virtual meetings, and multitasking with enterprise-grade reliability.",
                "image": "feature1.png",
            },
            {
                "title": "Minimal footprint, maximum productivity",
                "desc": "Replace your desktop tower AND monitor with a single device. VESA-compatible and height-adjustable stand options for ergonomic workspace configurations.",
                "image": "feature2.png",
            },
            {
                "title": "Secure & manageable",
                "desc": "TPM 2.0, Dell SafeBIOS, and Intel vPro for IT fleet management. Camera privacy shutter and optional smart card reader for secure authentication.",
                "image": "feature3.png",
            },
        ],
    },
    "xps-aio": {
        "name": "XPS AIO",
        "tagline": "Premium All-in-One",
        "hero_desc": "Dell's most premium all-in-one experience. A 4K touch display, studio-quality audio, and powerhouse performance in a stunningly thin design.",
        "features": [
            {
                "title": "4K InfinityEdge touch display",
                "desc": "27-inch 4K UHD display with 100% sRGB and factory calibration. Touch-enabled with Dell stylus support for creative workflows and natural interaction.",
                "image": "feature1.png",
            },
            {
                "title": "Studio-quality audio & video",
                "desc": "Quad-speaker design with Waves MaxxAudio. 5MP IR camera with Windows Hello and spatial audio for immersive entertainment and professional video calls.",
                "image": "feature2.png",
            },
            {
                "title": "Artisan craftsmanship",
                "desc": "Machined aluminum chassis just 14.9mm thin. Articulating stand with full tilt/height adjustment. A masterpiece of engineering that elevates any room.",
                "image": "feature3.png",
            },
        ],
    },
}


@app.route("/all-in-ones")
def allinones_page():
    """All-in-One series landing page — shows Inspiron AIO, OptiPlex AIO, XPS AIO cards."""
    return render_template("allinones.html")


@app.route("/all-in-ones/<series_name>")
def aio_series_page(series_name):
    """Individual AIO series landing page with scroll-reveal features."""
    series_name = series_name.lower()
    if series_name not in AIO_SERIES_INFO:
        flash("Series not found!", "error")
        return redirect(url_for("allinones_page"))

    series = AIO_SERIES_INFO[series_name]

    product_count = Product.query.filter_by(
        category="all-in-one", dell_series=series["name"], in_stock=True
    ).count()

    return render_template(
        "series_detail_aio.html",
        series=series,
        series_key=series_name,
        product_count=product_count,
    )




@app.route("/accessories")
def accessories_page():
    """Accessories page — batteries, keyboards, mice, chargers, etc."""
    # Group accessories by subcategory (dell_series field used as subcategory for accessories)
    accessories = Product.query.filter_by(category="accessory", in_stock=True).order_by(Product.dell_series, Product.name).all()
    return render_template("accessories.html", accessories=accessories)



@app.route("/products")
def products():
    category = request.args.get("category", "all")
    sort_by = request.args.get("sort", "name")
    search = request.args.get("search", "")
    series = request.args.get("series", "")

    query = Product.query.filter_by(in_stock=True)

    if category != "all":
        query = query.filter_by(category=category)
    if series:
        query = query.filter_by(dell_series=series)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if sort_by == "price_low":
        query = query.order_by(Product.selling_price.asc())
    elif sort_by == "price_high":
        query = query.order_by(Product.selling_price.desc())
    else:
        query = query.order_by(Product.name)

    all_products = query.all()
    return render_template("products.html", products=all_products, category=category)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    # Get all images for this product (from ProductImage table + legacy image_url)
    product_images = ProductImage.query.filter_by(product_id=product_id).order_by(ProductImage.display_order).all()
    image_urls = [img.image_url for img in product_images]
    # Fallback: if no images in ProductImage table, use the legacy image_url field
    if not image_urls and product.image_url:
        image_urls = [product.image_url]
    return render_template("product_detail.html", product=product, reviews=reviews, product_images=image_urls)


# ==========================================
# CART & CHECKOUT
# ==========================================


@app.route("/cart")
def cart():
    cart_items = session.get("cart", {})
    products_list = []
    total = 0
    for pid, qty in cart_items.items():
        product = Product.query.get(int(pid))
        if product:
            products_list.append({"product": product, "quantity": qty})
            total += product.selling_price * qty
    return render_template("cart.html", cart_items=products_list, total=total)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    cart_data = session.get("cart", {})
    pid = str(product_id)
    cart_data[pid] = cart_data.get(pid, 0) + 1
    session["cart"] = cart_data
    flash("Product added to cart!", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart_data = session.get("cart", {})
    cart_data.pop(str(product_id), None)
    session["cart"] = cart_data
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if request.method == "POST":
        cart_data = session.get("cart", {})
        if not cart_data:
            flash("Cart is empty!", "error")
            return redirect(url_for("cart"))

        total = 0
        order_items_list = []
        for pid, qty in cart_data.items():
            product = Product.query.get(int(pid))
            if product:
                total += product.selling_price * qty
                order_items_list.append((product, qty))

        order = Order(
            user_id=current_user.id,
            total_amount=total,
            shipping_address=request.form.get("address", current_user.address),
        )
        db.session.add(order)
        db.session.flush()

        for product, qty in order_items_list:
            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                price_at_purchase=product.selling_price,
            )
            db.session.add(item)

        db.session.commit()
        session["cart"] = {}
        flash(f"Order #{order.id} placed successfully!", "success")
        return redirect(url_for("index"))

    return render_template("cart.html")


# ==========================================
# AUTH ROUTES
# ==========================================


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form.get("phone", "")

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "error")
            return redirect(url_for("register"))

        user = User(
            name=name, email=email,
            password_hash=generate_password_hash(password), phone=phone,
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created!", "success")
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid credentials!", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# ==========================================
# ADMIN ROUTES (Products + Excel + Images)
# ==========================================


@app.route("/admin")
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash("Access denied!", "error")
        return redirect(url_for("index"))
    all_products = Product.query.all()
    return render_template("admin.html", products=all_products)


@app.route("/admin/update-price/<int:product_id>", methods=["POST"])
@login_required
def update_price(product_id):
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    product = Product.query.get_or_404(product_id)
    new_price = float(request.form["selling_price"])
    product.selling_price = new_price
    if product.dell_mrp and product.dell_mrp > 0:
        product.discount_percent = round((1 - new_price / product.dell_mrp) * 100, 1)
    db.session.commit()
    flash(f"Price updated for {product.name}!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/update-stock/<int:product_id>", methods=["POST"])
@login_required
def update_stock(product_id):
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    product = Product.query.get_or_404(product_id)
    product.stock_quantity = int(request.form["quantity"])
    product.in_stock = product.stock_quantity > 0
    db.session.commit()
    return redirect(url_for("admin_panel"))


@app.route("/admin/upload-image/<int:product_id>", methods=["POST"])
@login_required
def upload_image(product_id):
    """Upload one or multiple images for a product (stored in ProductImage table)."""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    product = Product.query.get_or_404(product_id)

    files = request.files.getlist("image")
    if not files or all(f.filename == "" for f in files):
        flash("No files selected!", "error")
        return redirect(url_for("admin_panel"))

    # Get current max display_order for this product
    max_order = db.session.query(db.func.max(ProductImage.display_order)).filter_by(product_id=product_id).scalar() or 0
    uploaded_count = 0

    for file in files:
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            # Unique filename: product_<id>_<timestamp>_<index>.<ext>
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = secure_filename(f"product_{product_id}_{timestamp}_{uploaded_count}.{ext}")
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            img_url = url_for("static", filename=f"images/products/{filename}")
            max_order += 1

            # Check if this is the first image (make it primary)
            is_first = (ProductImage.query.filter_by(product_id=product_id).count() == 0 and uploaded_count == 0)

            img_record = ProductImage(
                product_id=product_id,
                image_url=img_url,
                is_primary=is_first,
                display_order=max_order,
            )
            db.session.add(img_record)

            # Also set the product's thumbnail (first uploaded image)
            if is_first or not product.image_url:
                product.image_url = img_url

            uploaded_count += 1

    if uploaded_count > 0:
        db.session.commit()
        flash(f"{uploaded_count} image(s) uploaded for {product.name}!", "success")
    else:
        flash("No valid image files found!", "error")

    return redirect(url_for("admin_panel"))


@app.route("/admin/delete-image/<int:image_id>", methods=["POST"])
@login_required
def delete_image(image_id):
    """Delete a specific product image."""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    img = ProductImage.query.get_or_404(image_id)
    product = img.product

    # Try to delete the file from disk
    if img.image_url:
        # Convert URL path to filesystem path
        relative_path = img.image_url.replace("/static/", "")
        file_path = os.path.join(app.static_folder, relative_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    # If this was the primary image, reassign primary
    was_primary = img.is_primary
    db.session.delete(img)
    db.session.commit()

    if was_primary:
        # Set next image as primary
        next_img = ProductImage.query.filter_by(product_id=product.id).order_by(ProductImage.display_order).first()
        if next_img:
            next_img.is_primary = True
            product.image_url = next_img.image_url
        else:
            product.image_url = None
        db.session.commit()

    flash("Image deleted.", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/set-primary-image/<int:image_id>", methods=["POST"])
@login_required
def set_primary_image(image_id):
    """Set a specific image as the primary/thumbnail image."""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    img = ProductImage.query.get_or_404(image_id)
    product = img.product

    # Unset all primary flags for this product
    ProductImage.query.filter_by(product_id=product.id).update({"is_primary": False})
    img.is_primary = True
    product.image_url = img.image_url
    db.session.commit()

    flash("Primary image updated!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/upload-xlsx", methods=["POST"])
@login_required
def upload_xlsx():
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    if "xlsx_file" not in request.files:
        flash("No file selected!", "error")
        return redirect(url_for("admin_panel"))

    file = request.files["xlsx_file"]
    if file.filename == "" or not file.filename.lower().endswith((".xlsx", ".xls")):
        flash("Invalid file! Upload .xlsx or .xls.", "error")
        return redirect(url_for("admin_panel"))

    try:
        df = pd.read_excel(file, engine="openpyxl")
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        if "name" not in df.columns or "selling_price" not in df.columns:
            flash("Excel must have 'name' and 'selling_price' columns!", "error")
            return redirect(url_for("admin_panel"))

        added = 0
        updated = 0

        for _, row in df.iterrows():
            name = str(row.get("name", "")).strip()
            if not name:
                continue

            existing = Product.query.filter_by(name=name).first()
            product_data = {
                "name": name,
                "category": str(row.get("category", "laptop")).strip().lower(),
                "dell_series": str(row.get("dell_series", "")).strip() if pd.notna(row.get("dell_series")) else "",
                "processor": str(row.get("processor", "")).strip() if pd.notna(row.get("processor")) else "",
                "ram": str(row.get("ram", "")).strip() if pd.notna(row.get("ram")) else "",
                "storage": str(row.get("storage", "")).strip() if pd.notna(row.get("storage")) else "",
                "display": str(row.get("display", "")).strip() if pd.notna(row.get("display")) else "",
                "graphics": str(row.get("graphics", "")).strip() if pd.notna(row.get("graphics")) else "",
                "os": str(row.get("os", "")).strip() if pd.notna(row.get("os")) else "",
                "weight": str(row.get("weight", "")).strip() if pd.notna(row.get("weight")) else "",
                "dell_mrp": float(row.get("dell_mrp", 0)) if pd.notna(row.get("dell_mrp")) else 0,
                "selling_price": float(row.get("selling_price", 0)) if pd.notna(row.get("selling_price")) else 0,
                "stock_quantity": int(row.get("stock_quantity", 10)) if pd.notna(row.get("stock_quantity")) else 10,
                "image_url": str(row.get("image_url", "")).strip() if pd.notna(row.get("image_url")) else "",
                "in_stock": True,
            }
            if product_data["dell_mrp"] > 0:
                product_data["discount_percent"] = round(
                    (1 - product_data["selling_price"] / product_data["dell_mrp"]) * 100, 1)
            else:
                product_data["discount_percent"] = 0

            if existing:
                for key, value in product_data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                db.session.add(Product(**product_data))
                added += 1

        db.session.commit()
        flash(f"Excel imported! {added} added, {updated} updated.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")

    return redirect(url_for("admin_panel"))


@app.route("/admin/download-template")
@login_required
def download_template():
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    sample_data = {
        "name": ["Dell Inspiron 15 3520", "Dell XPS 13 9340", "Dell 65W USB-C Adapter", "Dell Pro Wireless Keyboard KB5221W"],
        "category": ["laptop", "laptop", "accessory", "accessory"],
        "dell_series": ["Inspiron", "XPS", "Charger", "Keyboard"],
        "processor": ["12th Gen Intel Core i5-1235U", "Intel Core Ultra 7 155H", "65W USB-C Power Delivery, compact design", "Wireless 2.4GHz, programmable keys, full-size"],
        "ram": ["8 GB DDR4", "16 GB LPDDR5x", "", ""],
        "storage": ["512 GB SSD", "512 GB PCIe NVMe SSD", "", ""],
        "display": ["15.6 inch FHD", "13.4 inch FHD+", "", ""],
        "graphics": ["Intel Iris Xe", "Intel Arc", "", ""],
        "os": ["Windows 11 Home", "Windows 11 Pro", "", ""],
        "weight": ["1.65 kg", "1.17 kg", "0.3 kg", "0.5 kg"],
        "dell_mrp": [58990, 149990, 3499, 4999],
        "selling_price": [54990, 139990, 2999, 4499],
        "stock_quantity": [15, 5, 50, 30],
        "image_url": ["", "", "", ""],
    }
    df = pd.DataFrame(sample_data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name="dell_products_template.xlsx")


@app.route("/admin/add-product", methods=["POST"])
@login_required
def add_product():
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    product = Product(
        name=request.form["name"], category=request.form["category"],
        dell_series=request.form.get("dell_series", ""),
        processor=request.form.get("processor", ""),
        ram=request.form.get("ram", ""), storage=request.form.get("storage", ""),
        display=request.form.get("display", ""), graphics=request.form.get("graphics", ""),
        os=request.form.get("os", ""),
        dell_mrp=float(request.form.get("dell_mrp", 0)),
        selling_price=float(request.form.get("selling_price", 0)),
        in_stock=True, stock_quantity=int(request.form.get("stock_quantity", 10)),
    )
    if product.dell_mrp and product.dell_mrp > 0:
        product.discount_percent = round((1 - product.selling_price / product.dell_mrp) * 100, 1)
    db.session.add(product)
    db.session.commit()
    flash(f"Product '{product.name}' added!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/delete-product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{product.name}' deleted.", "success")
    return redirect(url_for("admin_panel"))


# ==========================================
# ADMIN: VIEW ORDERS
# ==========================================


@app.route("/admin/orders")
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash("Access denied!", "error")
        return redirect(url_for("index"))
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin_orders.html", orders=orders)


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    order = Order.query.get_or_404(order_id)
    order.status = request.form["status"]
    db.session.commit()
    flash(f"Order #{order.id} status updated to '{order.status}'.", "success")
    return redirect(url_for("admin_orders"))


# ==========================================
# ADMIN: VIEW SERVICE REQUESTS
# ==========================================


@app.route("/admin/service-requests")
@login_required
def admin_service_requests():
    if not current_user.is_admin:
        flash("Access denied!", "error")
        return redirect(url_for("index"))
    requests_path = os.path.join(DATA_FOLDER, "service_requests.json")
    service_requests = []
    if os.path.exists(requests_path):
        try:
            with open(requests_path, "r") as f:
                service_requests = json.load(f)
        except (json.JSONDecodeError, IOError):
            service_requests = []
    service_requests.reverse()
    return render_template("admin_service_requests.html", requests=service_requests)


@app.route("/admin/service-requests/<request_id>/status", methods=["POST"])
@login_required
def update_service_status(request_id):
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    requests_path = os.path.join(DATA_FOLDER, "service_requests.json")
    new_status = request.form["status"]
    if os.path.exists(requests_path):
        with open(requests_path, "r") as f:
            all_requests = json.load(f)
        for req in all_requests:
            if req["request_id"] == request_id:
                req["status"] = new_status
                break
        with open(requests_path, "w") as f:
            json.dump(all_requests, f, indent=2)
    flash(f"Service request {request_id} updated to '{new_status}'.", "success")
    return redirect(url_for("admin_service_requests"))


# ==========================================
# SERVICE CHATBOT — LLM INTEGRATION
# ==========================================

PARTS_EXCEL_PATH = os.path.join(DATA_FOLDER, "service_parts.xlsx")

# Domain-locked system prompt
SERVICE_SYSTEM_PROMPT = """You are a Dell Laptop Service Assistant for an authorized Dell service center.

YOUR ROLE:
- Help customers get repair estimates for Dell laptops
- Look up part prices and labour charges from the parts database
- Guide customers to submit service requests
- Answer questions about Dell laptop repairs, warranty, and service timelines

STRICT RULES:
1. ONLY answer questions related to Dell laptop/desktop repairs, parts, service, and warranty.
2. If asked about anything unrelated (politics, coding, recipes, other brands, general knowledge), politely say: "I'm a Dell service assistant and can only help with Dell product repairs and service requests. How can I help you with your Dell device?"
3. NEVER make up part prices. Only quote prices from the PARTS DATABASE provided below.
4. If a model or part is not in the database, say "I don't have pricing for that specific model/part. Please contact our service desk for a custom quote."
5. Always include labour charges when giving estimates.
6. Be friendly, professional, and concise.
7. When you provide an estimate, format it clearly with part cost + labour = total.
8. Suggest submitting a service request after providing an estimate.

SERVICE INFO:
- Typical repair time: 2-5 business days
- Warranty repairs: Free if under Dell warranty (1 year standard)
- Walk-in hours: Mon-Sat, 10 AM - 8 PM
- Emergency/same-day service available for additional ₹500

PARTS DATABASE:
{parts_data}

CONVERSATION STYLE:
- Greet warmly on first message
- Ask which Dell model they have if not specified
- Be specific with pricing (always in ₹)
- Use simple language, avoid jargon
- End estimates with "Would you like me to book a service request for this?"
"""


def _create_default_parts_excel():
    """Auto-generate service_parts.xlsx if missing or corrupted."""
    parts = [
        ("Dell Inspiron 15 3520", "Screen/Display", "LCD-3520", 4500, 800),
        ("Dell Inspiron 15 3520", "Keyboard", "KB-3520", 1800, 500),
        ("Dell Inspiron 15 3520", "Battery", "BAT-3520", 3200, 400),
        ("Dell Inspiron 15 3520", "Motherboard", "MB-3520", 12500, 1500),
        ("Dell Inspiron 15 3520", "RAM (8GB DDR4)", "RAM8-3520", 2200, 300),
        ("Dell Inspiron 15 3520", "SSD (512GB)", "SSD512-3520", 3500, 400),
        ("Dell Inspiron 15 3520", "Charger/Adapter", "CHG-3520", 1500, 0),
        ("Dell Inspiron 15 3520", "Touchpad", "TP-3520", 1200, 600),
        ("Dell Inspiron 15 3520", "Fan/Cooling", "FAN-3520", 900, 500),
        ("Dell Inspiron 15 3520", "Hinge", "HNG-3520", 1100, 700),
        ("Dell Inspiron 14 5430", "Screen/Display", "LCD-5430", 6500, 800),
        ("Dell Inspiron 14 5430", "Keyboard", "KB-5430", 2200, 500),
        ("Dell Inspiron 14 5430", "Battery", "BAT-5430", 4000, 400),
        ("Dell Inspiron 14 5430", "Motherboard", "MB-5430", 16000, 1500),
        ("Dell Inspiron 14 5430", "RAM (16GB LPDDR5)", "RAM16-5430", 4500, 300),
        ("Dell Inspiron 14 5430", "SSD (512GB)", "SSD512-5430", 3500, 400),
        ("Dell Inspiron 14 5430", "Charger/Adapter", "CHG-5430", 1800, 0),
        ("Dell Inspiron 14 5430", "Fan/Cooling", "FAN-5430", 1100, 500),
        ("Dell XPS 13 9340", "Screen/Display", "LCD-9340", 12000, 1000),
        ("Dell XPS 13 9340", "Keyboard", "KB-9340", 3500, 600),
        ("Dell XPS 13 9340", "Battery", "BAT-9340", 5500, 500),
        ("Dell XPS 13 9340", "Motherboard", "MB-9340", 28000, 2000),
        ("Dell XPS 13 9340", "RAM (16GB LPDDR5x)", "RAM16-9340", 5500, 300),
        ("Dell XPS 13 9340", "SSD (512GB NVMe)", "SSD512-9340", 4500, 400),
        ("Dell XPS 13 9340", "Charger (USB-C)", "CHG-9340", 2500, 0),
        ("Dell XPS 13 9340", "Fan/Cooling", "FAN-9340", 1500, 600),
        ("Dell XPS 15 9530", "Screen/Display (OLED)", "LCD-9530", 18000, 1200),
        ("Dell XPS 15 9530", "Keyboard", "KB-9530", 3800, 600),
        ("Dell XPS 15 9530", "Battery", "BAT-9530", 6500, 500),
        ("Dell XPS 15 9530", "Motherboard", "MB-9530", 35000, 2500),
        ("Dell XPS 15 9530", "SSD (1TB NVMe)", "SSD1T-9530", 7500, 400),
        ("Dell XPS 15 9530", "GPU (RTX 4060)", "GPU-9530", 22000, 2000),
        ("Dell XPS 15 9530", "Fan/Cooling", "FAN-9530", 1800, 600),
        ("Dell Latitude 5540", "Screen/Display", "LCD-5540", 5500, 800),
        ("Dell Latitude 5540", "Keyboard", "KB-5540", 2000, 500),
        ("Dell Latitude 5540", "Battery", "BAT-5540", 3800, 400),
        ("Dell Latitude 5540", "Motherboard", "MB-5540", 18000, 1500),
        ("Dell Latitude 5540", "RAM (16GB DDR4)", "RAM16-5540", 3500, 300),
        ("Dell Latitude 5540", "Charger/Adapter", "CHG-5540", 1600, 0),
        ("Dell Latitude 5540", "Fan/Cooling", "FAN-5540", 1000, 500),
        ("Dell Vostro 3520", "Screen/Display", "LCD-V3520", 4000, 800),
        ("Dell Vostro 3520", "Keyboard", "KB-V3520", 1500, 500),
        ("Dell Vostro 3520", "Battery", "BAT-V3520", 2800, 400),
        ("Dell Vostro 3520", "Motherboard", "MB-V3520", 10000, 1500),
        ("Dell Vostro 3520", "RAM (8GB DDR4)", "RAM8-V3520", 2000, 300),
        ("Dell Vostro 3520", "SSD (256GB)", "SSD256-V3520", 2200, 400),
        ("Dell Vostro 3520", "Charger/Adapter", "CHG-V3520", 1200, 0),
        ("Dell Vostro 3520", "Fan/Cooling", "FAN-V3520", 800, 500),
    ]
    df = pd.DataFrame(parts, columns=["model", "part", "part_code", "price", "labour_charge"])
    df.to_excel(PARTS_EXCEL_PATH, index=False, engine="openpyxl")
    print(f"Auto-created service_parts.xlsx with {len(df)} parts")
    return df


def load_parts_data():
    """Load service parts from Excel. Auto-creates if missing/corrupted."""
    try:
        if not os.path.exists(PARTS_EXCEL_PATH) or os.path.getsize(PARTS_EXCEL_PATH) < 100:
            return _create_default_parts_excel()
        return pd.read_excel(PARTS_EXCEL_PATH, engine="openpyxl")
    except Exception:
        return _create_default_parts_excel()


def get_parts_context():
    """Format parts data as text for LLM context."""
    df = load_parts_data()
    if df.empty:
        return "No parts data available."
    lines = []
    current_model = ""
    for _, row in df.iterrows():
        if row["model"] != current_model:
            current_model = row["model"]
            lines.append(f"\n{current_model}:")
        lines.append(f"  - {row['part']} (Code: {row['part_code']}): Part ₹{int(row['price'])} + Labour ₹{int(row['labour_charge'])} = Total ₹{int(row['price'] + row['labour_charge'])}")
    return "\n".join(lines)


# ==========================================
# LLM PROVIDER: DATABRICKS FOUNDATION MODELS
# ==========================================


def call_databricks_api(messages, parts_context):
    """
    Call Databricks Foundation Model API (OpenAI-compatible format).
    Works on corporate network — calls your own Databricks workspace.
    Free pay-per-token models: databricks-meta-llama-3-3-70b-instruct
    """
    host = app.config.get("DATABRICKS_HOST", "")
    token = app.config.get("DATABRICKS_TOKEN", "")
    model = app.config.get("DATABRICKS_MODEL", "databricks-meta-llama-3-3-70b-instruct")

    if not host or not token or token == "YOUR_DATABRICKS_TOKEN_HERE":
        return None, "Databricks not configured. Set DATABRICKS_HOST and DATABRICKS_TOKEN in config.py"

    # Build system prompt with parts data
    system_prompt = SERVICE_SYSTEM_PROMPT.format(parts_data=parts_context)

    # Format messages in OpenAI chat format
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        role = msg["role"] if msg["role"] in ("user", "assistant") else "assistant"
        api_messages.append({"role": role, "content": msg["content"]})

    # Databricks serving endpoint URL (OpenAI-compatible)
    url = f"{host.rstrip('/')}/serving-endpoints/{model}/invocations"

    payload = {
        "messages": api_messages,
        "max_tokens": 1024,
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = http_requests.post(url, json=payload, headers=headers, timeout=60, verify=False)
        response_text = response.text.strip()

        if not response_text:
            return None, f"Empty response from Databricks (HTTP {response.status_code})"

        # Check for HTML (proxy intercept)
        if response_text.startswith("<!") or response_text.startswith("<html"):
            return None, f"Proxy blocked Databricks API. Preview: {response_text[:100]}"

        try:
            data = response.json()
        except json.JSONDecodeError:
            return None, f"Invalid JSON from Databricks (HTTP {response.status_code}): {response_text[:150]}"

        if response.status_code == 200:
            # OpenAI-compatible response format
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", ""), None
            return None, "Empty response from Databricks (no choices)"
        else:
            error_msg = data.get("error", {}).get("message", "") or data.get("message", "") or response_text[:200]
            return None, f"Databricks API error ({response.status_code}): {error_msg}"

    except http_requests.exceptions.Timeout:
        return None, "Databricks request timed out (60s). Try again."
    except http_requests.exceptions.ConnectionError as e:
        return None, f"Cannot reach Databricks workspace. Check DATABRICKS_HOST in config.py. ({str(e)[:80]})"
    except Exception as e:
        return None, f"Databricks connection error: {str(e)}"


# ==========================================
# LLM PROVIDER: GOOGLE GEMINI (backup)
# ==========================================


def call_gemini_api(messages, parts_context):
    """
    Call Google Gemini API (free tier).
    Blocked on Capgemini corporate network — use as backup on personal WiFi.
    """
    api_key = app.config.get("GEMINI_API_KEY", "")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        return None, "Gemini API key not configured."

    system_instruction = SERVICE_SYSTEM_PROMPT.format(parts_data=parts_context)

    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {"temperature": 0.7, "topP": 0.9, "maxOutputTokens": 1024},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    }

    try:
        response = http_requests.post(url, json=payload, timeout=30, verify=False)
        content_type = response.headers.get("Content-Type", "")
        response_text = response.text.strip()

        if not response_text:
            return None, "Empty response from Gemini"
        if "text/html" in content_type or response_text.startswith("<!"):
            return None, "Gemini blocked by proxy (HTML returned)"

        try:
            data = response.json()
        except json.JSONDecodeError:
            return None, f"Invalid JSON from Gemini: {response_text[:100]}"

        if response.status_code == 200:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", ""), None
            return None, "Empty Gemini response (no candidates)"
        else:
            error_detail = data.get("error", {}).get("message", response_text[:150])
            return None, f"Gemini error ({response.status_code}): {error_detail}"

    except http_requests.exceptions.Timeout:
        return None, "Gemini request timed out."
    except Exception as e:
        return None, f"Gemini connection error: {str(e)}"


# ==========================================
# LOCAL FALLBACK CHATBOT (no API needed)
# ==========================================

# Part keyword aliases for fuzzy matching
PART_KEYWORDS = {
    "screen": "Screen/Display",
    "display": "Screen/Display",
    "lcd": "Screen/Display",
    "monitor": "Screen/Display",
    "oled": "Screen/Display",
    "keyboard": "Keyboard",
    "kb": "Keyboard",
    "keys": "Keyboard",
    "battery": "Battery",
    "bat": "Battery",
    "charging": "Battery",
    "motherboard": "Motherboard",
    "mobo": "Motherboard",
    "mainboard": "Motherboard",
    "ram": "RAM",
    "memory": "RAM",
    "ssd": "SSD",
    "storage": "SSD",
    "hard drive": "SSD",
    "harddrive": "SSD",
    "disk": "SSD",
    "charger": "Charger",
    "adapter": "Charger",
    "power": "Charger",
    "touchpad": "Touchpad",
    "trackpad": "Touchpad",
    "fan": "Fan/Cooling",
    "cooling": "Fan/Cooling",
    "heating": "Fan/Cooling",
    "overheat": "Fan/Cooling",
    "hot": "Fan/Cooling",
    "hinge": "Hinge",
    "gpu": "GPU",
    "graphics": "GPU",
}

# Model keyword aliases for fuzzy matching
MODEL_KEYWORDS = {
    "inspiron 15": "Dell Inspiron 15 3520",
    "inspiron 3520": "Dell Inspiron 15 3520",
    "3520": "Dell Inspiron 15 3520",
    "inspiron 14": "Dell Inspiron 14 5430",
    "inspiron 5430": "Dell Inspiron 14 5430",
    "5430": "Dell Inspiron 14 5430",
    "xps 13": "Dell XPS 13 9340",
    "xps 9340": "Dell XPS 13 9340",
    "9340": "Dell XPS 13 9340",
    "xps 15": "Dell XPS 15 9530",
    "xps 9530": "Dell XPS 15 9530",
    "9530": "Dell XPS 15 9530",
    "latitude": "Dell Latitude 5540",
    "latitude 5540": "Dell Latitude 5540",
    "5540": "Dell Latitude 5540",
    "vostro": "Dell Vostro 3520",
    "vostro 3520": "Dell Vostro 3520",
}


def call_local_bot(messages):
    """
    Rule-based fallback chatbot — works 100% offline.
    Parses user messages for model + part keywords and returns pricing from Excel.
    """
    df = load_parts_data()
    if df.empty:
        return "Sorry, I couldn't load the parts database. Please try again later."

    # Get the latest user message
    user_msg = messages[-1]["content"].lower() if messages else ""

    # Check for greetings (first message or explicit greeting)
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "namaste"]
    if len(messages) <= 1 or any(user_msg.strip() == g for g in greetings):
        if any(user_msg.strip() == g or user_msg.strip().startswith(g) for g in greetings):
            return (
                "👋 Hello! Welcome to Dell Authorized Service Center.\n\n"
                "I can help you get repair estimates for your Dell device. "
                "Here are the models I have pricing for:\n\n"
                "1. Dell Inspiron 15 3520\n"
                "2. Dell Inspiron 14 5430\n"
                "3. Dell XPS 13 9340\n"
                "4. Dell XPS 15 9530\n"
                "5. Dell Latitude 5540\n"
                "6. Dell Vostro 3520\n\n"
                "Please tell me your **model** and what **part** needs repair, "
                "and I'll give you an instant estimate!\n\n"
                "Example: \"I need a battery replacement for my Inspiron 3520\""
            )

    # Try to find model in the message (check longer phrases first)
    detected_model = None
    sorted_keys = sorted(MODEL_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_keys:
        if keyword in user_msg:
            detected_model = MODEL_KEYWORDS[keyword]
            break

    # Also check full model names from the dataframe
    if not detected_model:
        for model_name in df["model"].unique():
            if model_name.lower() in user_msg:
                detected_model = model_name
                break

    # Check conversation history for model context
    if not detected_model:
        for msg in reversed(messages[:-1]):
            msg_lower = msg["content"].lower()
            for keyword in sorted_keys:
                if keyword in msg_lower:
                    detected_model = MODEL_KEYWORDS[keyword]
                    break
            if detected_model:
                break
            for model_name in df["model"].unique():
                if model_name.lower() in msg_lower:
                    detected_model = model_name
                    break
            if detected_model:
                break

    # Try to find part in the message
    detected_part_key = None
    sorted_part_keys = sorted(PART_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_part_keys:
        if keyword in user_msg:
            detected_part_key = PART_KEYWORDS[keyword]
            break

    # Handle "all parts" / "price list" requests
    if any(phrase in user_msg for phrase in ["all parts", "price list", "all prices", "full list", "what parts", "available parts"]):
        if detected_model:
            model_parts = df[df["model"] == detected_model]
            if model_parts.empty:
                return f"I don't have pricing data for {detected_model}. Please contact our service desk."
            lines = [f"📋 **Parts & Pricing for {detected_model}:**\n"]
            for _, row in model_parts.iterrows():
                total = int(row["price"] + row["labour_charge"])
                lines.append(f"• {row['part']}: ₹{int(row['price'])} + Labour ₹{int(row['labour_charge'])} = **₹{total}**")
            lines.append("\n💡 Tell me which part you need and I can give you a detailed estimate!")
            lines.append("Would you like to book a service request for any of these?")
            return "\n".join(lines)
        else:
            return (
                "I'd be happy to show you our parts pricing! Which model do you have?\n\n"
                "1. Dell Inspiron 15 3520\n"
                "2. Dell Inspiron 14 5430\n"
                "3. Dell XPS 13 9340\n"
                "4. Dell XPS 15 9530\n"
                "5. Dell Latitude 5540\n"
                "6. Dell Vostro 3520\n\n"
                "Just type the model name or number."
            )

    # Handle warranty questions
    if any(w in user_msg for w in ["warranty", "guarantee", "free repair", "covered"]):
        return (
            "📋 **Dell Warranty Information:**\n\n"
            "• Standard Dell warranty: **1 year** from purchase date\n"
            "• If your device is under warranty, repairs are **FREE** (parts + labour)\n"
            "• Extended warranty (Dell Premium Support): Up to 4 years\n"
            "• Accidental damage is NOT covered under standard warranty\n\n"
            "To check your warranty status, you'll need your Dell Service Tag "
            "(found on the bottom of your laptop).\n\n"
            "Is your device under warranty, or would you like a paid repair estimate?"
        )

    # Handle service timing questions
    if any(w in user_msg for w in ["how long", "time", "days", "when", "ready", "duration"]):
        return (
            "⏱️ **Service Timelines:**\n\n"
            "• Standard repair: **2-5 business days**\n"
            "• Screen/Display replacement: 1-2 days\n"
            "• Battery replacement: Same day\n"
            "• Motherboard repair: 3-5 days\n"
            "• Emergency/same-day service: Available for additional ₹500\n\n"
            "🕐 Walk-in hours: Mon-Sat, 10 AM - 8 PM\n\n"
            "Would you like to know the cost for a specific repair?"
        )

    # Handle service request / booking
    if any(w in user_msg for w in ["book", "submit", "request", "appointment", "schedule"]):
        return (
            "📝 **To submit a service request**, please provide:\n\n"
            "1. Your **name**\n"
            "2. Your **phone number**\n"
            "3. Your Dell **model**\n"
            "4. **Issue description** (which part needs repair)\n\n"
            "You can also visit us directly:\n"
            "🕐 Walk-in hours: Mon-Sat, 10 AM - 8 PM\n\n"
            "Or tell me your model and issue, and I'll prepare an estimate first!"
        )

    # If we have both model and part — give the estimate
    if detected_model and detected_part_key:
        # Find matching rows (fuzzy match on part name)
        model_parts = df[df["model"] == detected_model]
        matching = model_parts[model_parts["part"].str.lower().str.contains(detected_part_key.lower().split("/")[0])]

        if matching.empty:
            # Try broader match
            matching = model_parts[model_parts["part"].str.lower().str.contains(detected_part_key.lower().split("(")[0].strip().lower())]

        if not matching.empty:
            row = matching.iloc[0]
            part_cost = int(row["price"])
            labour = int(row["labour_charge"])
            total = part_cost + labour
            return (
                f"🔧 **Repair Estimate for {detected_model}**\n\n"
                f"**Part:** {row['part']} (Code: {row['part_code']})\n"
                f"**Part Cost:** ₹{part_cost:,}\n"
                f"**Labour Charge:** ₹{labour:,}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"**Total Estimate:** ₹{total:,}\n\n"
                f"⏱️ Estimated time: 2-5 business days\n"
                f"📍 Walk-in: Mon-Sat, 10 AM - 8 PM\n\n"
                f"Would you like me to book a service request for this repair?"
            )
        else:
            return (
                f"I don't have specific pricing for that part on the {detected_model}. "
                f"Here are the parts I have for this model:\n\n" +
                "\n".join(f"• {row['part']}" for _, row in model_parts.iterrows()) +
                "\n\nWhich one do you need?"
            )

    # If we have model but no part
    if detected_model and not detected_part_key:
        model_parts = df[df["model"] == detected_model]
        if model_parts.empty:
            return f"I don't have pricing data for {detected_model}. Please contact our service desk for a quote."
        return (
            f"Great! I can help with the **{detected_model}**. 👍\n\n"
            f"What part needs repair? Here's what I have pricing for:\n\n" +
            "\n".join(f"• {row['part']}" for _, row in model_parts.iterrows()) +
            "\n\nJust tell me which part you need replaced or repaired!"
        )

    # If we have part but no model
    if detected_part_key and not detected_model:
        return (
            f"I can help with a **{detected_part_key.split('/')[0]}** replacement! "
            f"Which Dell model do you have?\n\n"
            "1. Dell Inspiron 15 3520\n"
            "2. Dell Inspiron 14 5430\n"
            "3. Dell XPS 13 9340\n"
            "4. Dell XPS 15 9530\n"
            "5. Dell Latitude 5540\n"
            "6. Dell Vostro 3520\n\n"
            "Just type the model name or number."
        )

    # Handle "thank you" / goodbye
    if any(w in user_msg for w in ["thank", "thanks", "bye", "goodbye", "ok done"]):
        return (
            "You're welcome! 😊 Happy to help.\n\n"
            "If you need anything else — repair estimates, warranty info, or want to book a service — "
            "just come back anytime!\n\n"
            "🕐 Walk-in: Mon-Sat, 10 AM - 8 PM\n"
            "📞 For urgent queries, call our service desk."
        )

    # Default fallback — couldn't understand
    return (
        "I'm your Dell Service Assistant and I can help with:\n\n"
        "🔧 **Repair estimates** — Tell me your model + part (e.g., \"battery for XPS 13\")\n"
        "📋 **Parts list** — Say \"show all parts for Inspiron 3520\"\n"
        "📝 **Service booking** — Say \"book a service request\"\n"
        "🛡️ **Warranty info** — Ask about warranty coverage\n"
        "⏱️ **Repair timelines** — Ask \"how long does repair take?\"\n\n"
        "**Supported models:** Inspiron 15 3520, Inspiron 14 5430, XPS 13 9340, "
        "XPS 15 9530, Latitude 5540, Vostro 3520\n\n"
        "How can I help you today?"
    )


# ==========================================
# LLM ROUTER — tries provider, falls back to local bot
# ==========================================


def call_llm(messages, parts_context):
    """
    Route to the configured LLM provider.
    If LLM fails, automatically falls back to local rule-based bot.
    Set LLM_PROVIDER in config.py: "databricks" or "gemini"
    """
    provider = app.config.get("LLM_PROVIDER", "databricks").lower()

    # Try primary provider
    reply, error = None, None
    if provider == "databricks":
        reply, error = call_databricks_api(messages, parts_context)
    elif provider == "gemini":
        reply, error = call_gemini_api(messages, parts_context)
    else:
        error = f"Unknown LLM_PROVIDER: '{provider}'"

    # If primary succeeded, return it
    if reply and not error:
        return reply, None

    # Try the OTHER provider as secondary fallback
    secondary_reply, secondary_error = None, None
    if provider == "databricks":
        secondary_reply, secondary_error = call_gemini_api(messages, parts_context)
    elif provider == "gemini":
        secondary_reply, secondary_error = call_databricks_api(messages, parts_context)

    if secondary_reply and not secondary_error:
        return secondary_reply, None

    # Both LLMs failed — use local rule-based bot (always works)
    local_reply = call_local_bot(messages)
    return local_reply, None


# ==========================================
# SERVICE CHATBOT ROUTES
# ==========================================


@app.route("/service")
def service_page():
    session.pop("chat_history", None)
    return render_template("service.html")


@app.route("/service/chat", methods=["POST"])
def service_chat():
    """Handle chat messages — routes to LLM with local fallback."""
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "No message provided"}), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    chat_history = session.get("chat_history", [])
    chat_history.append({"role": "user", "content": user_message})

    parts_context = get_parts_context()

    # Call LLM (with automatic fallback to local bot)
    reply, error = call_llm(chat_history, parts_context)

    # This shouldn't happen anymore since local bot always works,
    # but just in case:
    if not reply:
        reply = call_local_bot(chat_history)

    chat_history.append({"role": "assistant", "content": reply})

    if len(chat_history) > 20:
        chat_history = chat_history[-20:]

    session["chat_history"] = chat_history
    return jsonify({"reply": reply})


@app.route("/service/chat/reset", methods=["POST"])
def service_chat_reset():
    session.pop("chat_history", None)
    return jsonify({"success": True})


# Legacy routes (backward compatibility)
@app.route("/service/parts")
def service_parts():
    model = request.args.get("model", "")
    df = load_parts_data()
    if df.empty or not model:
        return jsonify({"parts": []})
    model_parts = df[df["model"] == model]
    parts = [
        {"part": row["part"], "part_code": row["part_code"],
         "price": float(row["price"]), "labour_charge": float(row["labour_charge"])}
        for _, row in model_parts.iterrows()
    ]
    return jsonify({"parts": parts})


@app.route("/service/submit", methods=["POST"])
def service_submit():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400

    request_id = f"SRV-{random.randint(10000, 99999)}"
    requests_path = os.path.join(DATA_FOLDER, "service_requests.json")

    service_request = {
        "request_id": request_id,
        "customer_name": data.get("name", ""),
        "customer_phone": data.get("phone", ""),
        "issue_description": data.get("issue", ""),
        "model": data.get("model", ""),
        "parts": data.get("parts", []),
        "total_estimate": data.get("total_estimate", 0),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }

    existing = []
    if os.path.exists(requests_path):
        try:
            with open(requests_path, "r") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []

    existing.append(service_request)
    with open(requests_path, "w") as f:
        json.dump(existing, f, indent=2)

    return jsonify({"success": True, "request_id": request_id})


# ==========================================
# API ENDPOINTS
# ==========================================


@app.route("/api/products")
def api_products():
    category = request.args.get("category", "all")
    query = Product.query.filter_by(in_stock=True)
    if category != "all":
        query = query.filter_by(category=category)
    all_products = query.all()
    return jsonify([
        {"id": p.id, "name": p.name, "category": p.category,
         "selling_price": p.selling_price, "dell_mrp": p.dell_mrp,
         "image_url": p.image_url, "processor": p.processor,
         "ram": p.ram, "storage": p.storage}
        for p in all_products
    ])


# ==========================================
# APP STARTUP
# ==========================================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email="admin@dellstore.com").first():
            admin = User(
                name="Admin", email="admin@dellstore.com",
                password_hash=generate_password_hash("admin123"), is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True, port=5000)
