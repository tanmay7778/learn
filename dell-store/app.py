import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Product, User, Order, OrderItem, Review
from config import Config
import io

app = Flask(__name__)
app.config.from_object(Config)

# Image upload config
UPLOAD_FOLDER = os.path.join(app.static_folder, "images", "products")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max

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
# ADMIN ROUTES (Product Management + Excel Import + Image Upload)
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
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"product_{product_id}.{ext}"
        filename = secure_filename(filename)

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        product.image_url = url_for("static", filename=f"images/products/{filename}")
        db.session.commit()

        flash(f"Image uploaded for {product.name}!", "success")
    else:
        flash("Invalid file type! Use PNG, JPG, JPEG, WEBP, or GIF.", "error")

    return redirect(url_for("admin_panel"))


@app.route("/admin/upload-xlsx", methods=["POST"])
@login_required
def upload_xlsx():
    """Admin: Bulk import products from an Excel (.xlsx) file.

    Expected columns:
        name, category, dell_series, processor, ram, storage, display,
        graphics, os, weight, dell_mrp, selling_price, stock_quantity, image_url

    - 'name' and 'selling_price' are required.
    - 'category' should be: laptop, desktop, or all-in-one.
    - If a product with the same name already exists, it will be UPDATED.
    - If it doesn't exist, a new product will be CREATED.
    """
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    if "xlsx_file" not in request.files:
        flash("No file selected!", "error")
        return redirect(url_for("admin_panel"))

    file = request.files["xlsx_file"]

    if file.filename == "":
        flash("No file selected!", "error")
        return redirect(url_for("admin_panel"))

    if not file.filename.lower().endswith((".xlsx", ".xls")):
        flash("Invalid file! Please upload an .xlsx or .xls file.", "error")
        return redirect(url_for("admin_panel"))

    try:
        # Read Excel file with pandas
        df = pd.read_excel(file, engine="openpyxl")

        # Normalize column names (lowercase, strip spaces)
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        # Validate required columns
        if "name" not in df.columns or "selling_price" not in df.columns:
            flash("Excel must have at least 'name' and 'selling_price' columns!", "error")
            return redirect(url_for("admin_panel"))

        added = 0
        updated = 0

        for _, row in df.iterrows():
            name = str(row.get("name", "")).strip()
            if not name:
                continue  # Skip empty rows

            # Check if product already exists
            existing = Product.query.filter_by(name=name).first()

            # Prepare product data
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

            # Auto-calculate discount
            if product_data["dell_mrp"] > 0:
                product_data["discount_percent"] = round(
                    (1 - product_data["selling_price"] / product_data["dell_mrp"]) * 100, 1
                )
            else:
                product_data["discount_percent"] = 0

            if existing:
                for key, value in product_data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                product = Product(**product_data)
                db.session.add(product)
                added += 1

        db.session.commit()
        flash(f"Excel imported! {added} products added, {updated} products updated.", "success")

    except Exception as e:
        flash(f"Error reading Excel file: {str(e)}", "error")

    return redirect(url_for("admin_panel"))


@app.route("/admin/download-template")
@login_required
def download_template():
    """Admin: Download a sample Excel template for product import."""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    sample_data = {
        "name": ["Dell Inspiron 15 3520", "Dell XPS 13 9340"],
        "category": ["laptop", "laptop"],
        "dell_series": ["Inspiron", "XPS"],
        "processor": ["12th Gen Intel Core i5-1235U", "Intel Core Ultra 7 155H"],
        "ram": ["8 GB DDR4", "16 GB LPDDR5x"],
        "storage": ["512 GB SSD", "512 GB PCIe NVMe SSD"],
        "display": ["15.6 inch FHD (1920x1080)", "13.4 inch FHD+ (1920x1200)"],
        "graphics": ["Intel Iris Xe Graphics", "Intel Arc Graphics"],
        "os": ["Windows 11 Home", "Windows 11 Pro"],
        "weight": ["1.65 kg", "1.17 kg"],
        "dell_mrp": [58990, 149990],
        "selling_price": [54990, 139990],
        "stock_quantity": [15, 5],
        "image_url": ["", ""],
    }

    df = pd.DataFrame(sample_data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="dell_products_template.xlsx",
    )


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

    if product.dell_mrp and product.dell_mrp > 0:
        product.discount_percent = round((1 - product.selling_price / product.dell_mrp) * 100, 1)

    db.session.add(product)
    db.session.commit()

    flash(f"Product '{product.name}' added successfully!", "success")
    return redirect(url_for("admin_panel"))


@app.route("/admin/delete-product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    """Admin: Delete a product."""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    flash(f"Product '{product.name}' deleted.", "success")
    return redirect(url_for("admin_panel"))


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

    # Run the app
    app.run(debug=True, port=5000)
