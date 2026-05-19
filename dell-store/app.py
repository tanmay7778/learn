import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Product, User, Order, OrderItem, Review
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Image upload config
UPLOAD_FOLDER = os.path.join(app.static_folder, "images", "products")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max

# Create upload folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================================
# PUBLIC ROUTES (Customer-Facing)
# ==========================================


@app.route("/")
def index():
    """Home page - featured products."""
    featured = Product.query.filter_by(in_stock=True).limit(8).all()
    return render_template("index.html", products=featured)


@app.route("/products")
def products():
    """Product listing with filters."""
    category = request.args.get("category", "all")
    sort_by = request.args.get("sort", "name")
    search = request.args.get("search", "")

    query = Product.query.filter_by(in_stock=True)

    if category != "all":
        query = query.filter_by(category=category)

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
    """Single product page with specs."""
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    return render_template("product_detail.html", product=product, reviews=reviews)


# ==========================================
# CART & CHECKOUT ROUTES
# ==========================================


@app.route("/cart")
def cart():
    """View shopping cart."""
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
    """Add product to cart."""
    cart_data = session.get("cart", {})
    pid = str(product_id)
    cart_data[pid] = cart_data.get(pid, 0) + 1
    session["cart"] = cart_data
    flash("Product added to cart!", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    """Remove product from cart."""
    cart_data = session.get("cart", {})
    cart_data.pop(str(product_id), None)
    session["cart"] = cart_data
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """Process order."""
    if request.method == "POST":
        cart_data = session.get("cart", {})
        if not cart_data:
            flash("Cart is empty!", "error")
            return redirect(url_for("cart"))

        # Calculate total
        total = 0
        order_items_list = []
        for pid, qty in cart_data.items():
            product = Product.query.get(int(pid))
            if product:
                total += product.selling_price * qty
                order_items_list.append((product, qty))

        # Create order
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            shipping_address=request.form.get("address", current_user.address),
        )
        db.session.add(order)
        db.session.flush()

        # Add order items
        for product, qty in order_items_list:
            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                price_at_purchase=product.selling_price,
            )
            db.session.add(item)

        db.session.commit()
        session["cart"] = {}  # Clear cart

        # TODO: Integrate Razorpay/Stripe payment here
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
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone,
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
# ADMIN ROUTES (Price Management + Image Upload)
# ==========================================


@app.route("/admin")
@login_required
def admin_panel():
    """Admin panel - manage products and prices."""
    if not current_user.is_admin:
        flash("Access denied!", "error")
        return redirect(url_for("index"))

    all_products = Product.query.all()
    return render_template("admin.html", products=all_products)


@app.route("/admin/update-price/<int:product_id>", methods=["POST"])
@login_required
def update_price(product_id):
    """Admin: Update selling price for a product."""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    product = Product.query.get_or_404(product_id)
    new_price = float(request.form["selling_price"])
    product.selling_price = new_price

    # Auto-calculate discount
    if product.dell_mrp and product.dell_mrp > 0:
        product.discount_percent = round((1 - new_price / product.dell_mrp) * 100, 1)

    db.session.commit()
    flash(f"Price updated for {product.name}!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/update-stock/<int:product_id>", methods=["POST"])
@login_required
def update_stock(product_id):
    """Admin: Update stock status."""
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
    """Admin: Upload product image."""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    product = Product.query.get_or_404(product_id)

    if "image" not in request.files:
        flash("No file selected!", "error")
        return redirect(url_for("admin_panel"))

    file = request.files["image"]

    if file.filename == "":
        flash("No file selected!", "error")
        return redirect(url_for("admin_panel"))

    if file and allowed_file(file.filename):
        # Create safe filename: product_id_originalname.ext
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"product_{product_id}.{ext}"
        filename = secure_filename(filename)

        # Save file
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Update product image_url in database
        product.image_url = url_for("static", filename=f"images/products/{filename}")
        db.session.commit()

        flash(f"Image uploaded for {product.name}!", "success")
    else:
        flash("Invalid file type! Use PNG, JPG, JPEG, WEBP, or GIF.", "error")

    return redirect(url_for("admin_panel"))


@app.route("/admin/add-product", methods=["POST"])
@login_required
def add_product():
    """Admin: Manually add a new product."""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    product = Product(
        name=request.form["name"],
        category=request.form["category"],
        dell_series=request.form.get("dell_series", ""),
        processor=request.form.get("processor", ""),
        ram=request.form.get("ram", ""),
        storage=request.form.get("storage", ""),
        display=request.form.get("display", ""),
        graphics=request.form.get("graphics", ""),
        os=request.form.get("os", ""),
        dell_mrp=float(request.form.get("dell_mrp", 0)),
        selling_price=float(request.form.get("selling_price", 0)),
        in_stock=True,
        stock_quantity=int(request.form.get("stock_quantity", 10)),
    )

    # Calculate discount
    if product.dell_mrp and product.dell_mrp > 0:
        product.discount_percent = round((1 - product.selling_price / product.dell_mrp) * 100, 1)

    db.session.add(product)
    db.session.commit()

    flash(f"Product '{product.name}' added successfully!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/scrape", methods=["POST"])
@login_required
def trigger_scrape():
    """Admin: Manually trigger Dell scraping."""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        from scraper import DellScraper
        scrape_dell_products()
        flash("Scraping complete! New products added.", "success")
    except ImportError:
        flash("Scraper not available (Selenium/Chrome not installed).", "error")

    return redirect(url_for("admin_panel"))


# ==========================================
# SCRAPING SCHEDULER (lazy import)
# ==========================================


def scrape_dell_products():
    """Background job: Scrape Dell and update database."""
    from scraper import DellScraper

    scraper = DellScraper()
    categories = {
        "laptop": "/shop/laptops/new",
        "desktop": "/shop/desktops-all-in-one/new",
        "all-in-one": "/shop/desktops-all-in-one/all-in-one",
    }

    with app.app_context():
        for category, url in categories.items():
            products_list = scraper.scrape_category(url)

            for prod_data in products_list:
                # Check if product already exists
                existing = Product.query.filter_by(dell_url=prod_data.get("dell_url")).first()

                if existing:
                    # Update specs (keep your price)
                    existing.dell_mrp = prod_data.get("dell_mrp", existing.dell_mrp)
                    existing.image_url = prod_data.get("image_url", existing.image_url)
                else:
                    # Scrape full details for new product
                    detail = scraper.scrape_product_detail(prod_data["dell_url"])

                    new_product = Product(
                        name=detail.get("name", prod_data.get("name", "Unknown")),
                        category=category,
                        processor=detail.get("processor", ""),
                        ram=detail.get("ram", ""),
                        storage=detail.get("storage", ""),
                        display=detail.get("display", ""),
                        graphics=detail.get("graphics", ""),
                        os=detail.get("os", ""),
                        weight=detail.get("weight", ""),
                        dell_mrp=prod_data.get("dell_mrp", 0),
                        selling_price=prod_data.get("dell_mrp", 0),  # Default: same as Dell
                        image_url=detail.get("image_url", ""),
                        dell_url=prod_data.get("dell_url", ""),
                        in_stock=True,
                        stock_quantity=10,
                    )
                    db.session.add(new_product)

            db.session.commit()


# ==========================================
# API ENDPOINTS (for AJAX calls)
# ==========================================


@app.route("/api/products")
def api_products():
    """JSON API for product listing."""
    category = request.args.get("category", "all")
    query = Product.query.filter_by(in_stock=True)

    if category != "all":
        query = query.filter_by(category=category)

    all_products = query.all()
    return jsonify(
        [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "selling_price": p.selling_price,
                "dell_mrp": p.dell_mrp,
                "image_url": p.image_url,
                "processor": p.processor,
                "ram": p.ram,
                "storage": p.storage,
            }
            for p in all_products
        ]
    )


# ==========================================
# AUTO-SEED: Populate sample data if DB is empty
# ==========================================


def seed_sample_products():
    """Insert sample Dell products if database is empty."""
    if Product.query.count() > 0:
        return  # Already has products

    print("Database empty — auto-seeding sample products...")

    sample_products = [
        # LAPTOPS
        {"name": "Dell Inspiron 15 3520", "category": "laptop", "dell_series": "Inspiron", "processor": "12th Gen Intel Core i5-1235U", "ram": "8 GB DDR4", "storage": "512 GB SSD", "display": "15.6 inch FHD (1920x1080) Anti-Glare", "graphics": "Intel Iris Xe Graphics", "os": "Windows 11 Home", "weight": "1.65 kg", "dell_mrp": 58990.0, "selling_price": 54990.0, "image_url": "https://placehold.co/300x200/0076CE/ffffff?text=Inspiron+15+3520", "dell_url": "https://www.dell.com/en-in/shop/laptops/inspiron-15-3520/spd/inspiron-15-3520-laptop", "in_stock": True, "stock_quantity": 15},
        {"name": "Dell Inspiron 14 5430", "category": "laptop", "dell_series": "Inspiron", "processor": "13th Gen Intel Core i7-1360P", "ram": "16 GB LPDDR5", "storage": "512 GB SSD", "display": "14 inch FHD+ (1920x1200) IPS", "graphics": "Intel Iris Xe Graphics", "os": "Windows 11 Home", "weight": "1.44 kg", "dell_mrp": 78990.0, "selling_price": 72990.0, "image_url": "https://placehold.co/300x200/0076CE/ffffff?text=Inspiron+14+5430", "dell_url": "https://www.dell.com/en-in/shop/laptops/inspiron-14-5430/spd/inspiron-14-5430-laptop", "in_stock": True, "stock_quantity": 10},
        {"name": "Dell XPS 13 9340", "category": "laptop", "dell_series": "XPS", "processor": "Intel Core Ultra 7 155H", "ram": "16 GB LPDDR5x", "storage": "512 GB PCIe NVMe SSD", "display": "13.4 inch FHD+ (1920x1200) InfinityEdge", "graphics": "Intel Arc Graphics", "os": "Windows 11 Pro", "weight": "1.17 kg", "dell_mrp": 149990.0, "selling_price": 139990.0, "image_url": "https://placehold.co/300x200/003366/ffffff?text=XPS+13+9340", "dell_url": "https://www.dell.com/en-in/shop/laptops/dell-xps-13/spd/xps-13-9340-laptop", "in_stock": True, "stock_quantity": 5},
        {"name": "Dell XPS 15 9530", "category": "laptop", "dell_series": "XPS", "processor": "13th Gen Intel Core i9-13900H", "ram": "32 GB DDR5", "storage": "1 TB PCIe NVMe SSD", "display": "15.6 inch 3.5K OLED (3456x2160)", "graphics": "NVIDIA GeForce RTX 4060 6GB", "os": "Windows 11 Pro", "weight": "1.86 kg", "dell_mrp": 249990.0, "selling_price": 234990.0, "image_url": "https://placehold.co/300x200/003366/ffffff?text=XPS+15+9530", "dell_url": "https://www.dell.com/en-in/shop/laptops/dell-xps-15/spd/xps-15-9530-laptop", "in_stock": True, "stock_quantity": 3},
        {"name": "Dell Latitude 5540", "category": "laptop", "dell_series": "Latitude", "processor": "13th Gen Intel Core i5-1345U", "ram": "16 GB DDR4", "storage": "256 GB SSD", "display": "15.6 inch FHD (1920x1080) IPS Anti-Glare", "graphics": "Intel Iris Xe Graphics", "os": "Windows 11 Pro", "weight": "1.57 kg", "dell_mrp": 92990.0, "selling_price": 85990.0, "image_url": "https://placehold.co/300x200/004080/ffffff?text=Latitude+5540", "dell_url": "https://www.dell.com/en-in/shop/business-laptops/latitude-5540/spd/latitude-15-5540-laptop", "in_stock": True, "stock_quantity": 8},
        {"name": "Dell Vostro 3520", "category": "laptop", "dell_series": "Vostro", "processor": "12th Gen Intel Core i3-1215U", "ram": "8 GB DDR4", "storage": "256 GB SSD", "display": "15.6 inch FHD (1920x1080)", "graphics": "Intel UHD Graphics", "os": "Windows 11 Home", "weight": "1.66 kg", "dell_mrp": 42990.0, "selling_price": 38990.0, "image_url": "https://placehold.co/300x200/004080/ffffff?text=Vostro+3520", "dell_url": "https://www.dell.com/en-in/shop/business-laptops/vostro-3520/spd/vostro-15-3520-laptop", "in_stock": True, "stock_quantity": 20},
        # DESKTOPS
        {"name": "Dell OptiPlex 7010 Tower", "category": "desktop", "dell_series": "OptiPlex", "processor": "13th Gen Intel Core i7-13700", "ram": "16 GB DDR5", "storage": "512 GB PCIe NVMe SSD", "display": "Monitor not included", "graphics": "Intel UHD Graphics 770", "os": "Windows 11 Pro", "weight": "7.3 kg", "dell_mrp": 89990.0, "selling_price": 82990.0, "image_url": "https://placehold.co/300x200/1a1a2e/ffffff?text=OptiPlex+7010", "dell_url": "https://www.dell.com/en-in/shop/desktops/optiplex-7010-tower/spd/optiplex-7010-tower", "in_stock": True, "stock_quantity": 6},
        {"name": "Dell OptiPlex 3000 SFF", "category": "desktop", "dell_series": "OptiPlex", "processor": "12th Gen Intel Core i5-12500", "ram": "8 GB DDR4", "storage": "256 GB SSD", "display": "Monitor not included", "graphics": "Intel UHD Graphics 770", "os": "Windows 11 Pro", "weight": "4.8 kg", "dell_mrp": 58990.0, "selling_price": 52990.0, "image_url": "https://placehold.co/300x200/1a1a2e/ffffff?text=OptiPlex+3000", "dell_url": "https://www.dell.com/en-in/shop/desktops/optiplex-3000-sff/spd/optiplex-3000-sff", "in_stock": True, "stock_quantity": 12},
        {"name": "Dell XPS Desktop 8960", "category": "desktop", "dell_series": "XPS", "processor": "13th Gen Intel Core i7-13700K", "ram": "32 GB DDR5", "storage": "1 TB SSD + 2 TB HDD", "display": "Monitor not included", "graphics": "NVIDIA GeForce RTX 4070 12GB", "os": "Windows 11 Home", "weight": "13.2 kg", "dell_mrp": 189990.0, "selling_price": 179990.0, "image_url": "https://placehold.co/300x200/003366/ffffff?text=XPS+Desktop+8960", "dell_url": "https://www.dell.com/en-in/shop/desktops/xps-desktop-8960/spd/xps-8960-desktop", "in_stock": True, "stock_quantity": 4},
        {"name": "Dell Inspiron 3020 Tower", "category": "desktop", "dell_series": "Inspiron", "processor": "13th Gen Intel Core i5-13400", "ram": "8 GB DDR4", "storage": "512 GB SSD", "display": "Monitor not included", "graphics": "Intel UHD Graphics 730", "os": "Windows 11 Home", "weight": "6.1 kg", "dell_mrp": 52990.0, "selling_price": 47990.0, "image_url": "https://placehold.co/300x200/0076CE/ffffff?text=Inspiron+3020", "dell_url": "https://www.dell.com/en-in/shop/desktops/inspiron-3020-tower/spd/inspiron-3020-tower", "in_stock": True, "stock_quantity": 10},
        # ALL-IN-ONES
        {"name": "Dell Inspiron 24 5420 All-in-One", "category": "all-in-one", "dell_series": "Inspiron", "processor": "13th Gen Intel Core i5-1335U", "ram": "8 GB DDR4", "storage": "512 GB SSD", "display": "23.8 inch FHD (1920x1080) IPS Touchscreen", "graphics": "Intel Iris Xe Graphics", "os": "Windows 11 Home", "weight": "5.4 kg", "dell_mrp": 72990.0, "selling_price": 67990.0, "image_url": "https://placehold.co/300x200/005a9e/ffffff?text=Inspiron+24+AIO", "dell_url": "https://www.dell.com/en-in/shop/desktops/inspiron-24-5420-aio/spd/inspiron-24-5420-aio", "in_stock": True, "stock_quantity": 7},
        {"name": "Dell Inspiron 27 7720 All-in-One", "category": "all-in-one", "dell_series": "Inspiron", "processor": "13th Gen Intel Core i7-1355U", "ram": "16 GB DDR4", "storage": "1 TB SSD", "display": "27 inch QHD (2560x1440) IPS Touchscreen", "graphics": "NVIDIA GeForce MX550 2GB", "os": "Windows 11 Home", "weight": "7.7 kg", "dell_mrp": 109990.0, "selling_price": 99990.0, "image_url": "https://placehold.co/300x200/005a9e/ffffff?text=Inspiron+27+AIO", "dell_url": "https://www.dell.com/en-in/shop/desktops/inspiron-27-7720-aio/spd/inspiron-27-7720-aio", "in_stock": True, "stock_quantity": 5},
        {"name": "Dell OptiPlex 7410 All-in-One", "category": "all-in-one", "dell_series": "OptiPlex", "processor": "13th Gen Intel Core i5-13500T", "ram": "16 GB DDR5", "storage": "512 GB SSD", "display": "23.8 inch FHD (1920x1080) IPS Anti-Glare", "graphics": "Intel UHD Graphics 770", "os": "Windows 11 Pro", "weight": "6.2 kg", "dell_mrp": 98990.0, "selling_price": 91990.0, "image_url": "https://placehold.co/300x200/1a1a2e/ffffff?text=OptiPlex+7410+AIO", "dell_url": "https://www.dell.com/en-in/shop/desktops/optiplex-7410-aio/spd/optiplex-7410-aio", "in_stock": True, "stock_quantity": 6},
    ]

    for prod_data in sample_products:
        dell_mrp = prod_data["dell_mrp"]
        selling_price = prod_data["selling_price"]
        discount = round((1 - selling_price / dell_mrp) * 100, 1) if dell_mrp > 0 else 0

        product = Product(**prod_data, discount_percent=discount)
        db.session.add(product)

    db.session.commit()
    print(f"Auto-seeded {len(sample_products)} products successfully!")


# ==========================================
# APP STARTUP
# ==========================================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables

        # Create default admin user
        if not User.query.filter_by(email="admin@dellstore.com").first():
            admin = User(
                name="Admin",
                email="admin@dellstore.com",
                password_hash=generate_password_hash("admin123"),
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()

        # Auto-seed products if database is empty
        seed_sample_products()

    # Run the app (no scraper scheduler unless Selenium is installed)
    app.run(debug=True, port=5000)
