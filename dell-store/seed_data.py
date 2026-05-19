"""Seed script to populate the database with sample Dell products.
Run this ONCE after starting the app: python seed_data.py
"""

from app import app
from models import db, Product, User
from werkzeug.security import generate_password_hash


# Sample Dell products (using working placeholder images)
SAMPLE_PRODUCTS = [
    # ===== LAPTOPS =====
    {
        "name": "Dell Inspiron 15 3520",
        "category": "laptop",
        "dell_series": "Inspiron",
        "processor": "12th Gen Intel Core i5-1235U",
        "ram": "8 GB DDR4",
        "storage": "512 GB SSD",
        "display": "15.6 inch FHD (1920x1080) Anti-Glare",
        "graphics": "Intel Iris Xe Graphics",
        "os": "Windows 11 Home",
        "weight": "1.65 kg",
        "dell_mrp": 58990.0,
        "selling_price": 54990.0,
        "image_url": "https://placehold.co/300x200/0076CE/ffffff?text=Inspiron+15+3520",
        "dell_url": "https://www.dell.com/en-in/shop/laptops/inspiron-15-3520/spd/inspiron-15-3520-laptop",
        "in_stock": True,
        "stock_quantity": 15,
    },
    {
        "name": "Dell Inspiron 14 5430",
        "category": "laptop",
        "dell_series": "Inspiron",
        "processor": "13th Gen Intel Core i7-1360P",
        "ram": "16 GB LPDDR5",
        "storage": "512 GB SSD",
        "display": "14 inch FHD+ (1920x1200) IPS",
        "graphics": "Intel Iris Xe Graphics",
        "os": "Windows 11 Home",
        "weight": "1.44 kg",
        "dell_mrp": 78990.0,
        "selling_price": 72990.0,
        "image_url": "https://placehold.co/300x200/0076CE/ffffff?text=Inspiron+14+5430",
        "dell_url": "https://www.dell.com/en-in/shop/laptops/inspiron-14-5430/spd/inspiron-14-5430-laptop",
        "in_stock": True,
        "stock_quantity": 10,
    },
    {
        "name": "Dell XPS 13 9340",
        "category": "laptop",
        "dell_series": "XPS",
        "processor": "Intel Core Ultra 7 155H",
        "ram": "16 GB LPDDR5x",
        "storage": "512 GB PCIe NVMe SSD",
        "display": "13.4 inch FHD+ (1920x1200) InfinityEdge",
        "graphics": "Intel Arc Graphics",
        "os": "Windows 11 Pro",
        "weight": "1.17 kg",
        "dell_mrp": 149990.0,
        "selling_price": 139990.0,
        "image_url": "https://placehold.co/300x200/003366/ffffff?text=XPS+13+9340",
        "dell_url": "https://www.dell.com/en-in/shop/laptops/dell-xps-13/spd/xps-13-9340-laptop",
        "in_stock": True,
        "stock_quantity": 5,
    },
    {
        "name": "Dell XPS 15 9530",
        "category": "laptop",
        "dell_series": "XPS",
        "processor": "13th Gen Intel Core i9-13900H",
        "ram": "32 GB DDR5",
        "storage": "1 TB PCIe NVMe SSD",
        "display": "15.6 inch 3.5K OLED (3456x2160)",
        "graphics": "NVIDIA GeForce RTX 4060 6GB",
        "os": "Windows 11 Pro",
        "weight": "1.86 kg",
        "dell_mrp": 249990.0,
        "selling_price": 234990.0,
        "image_url": "https://placehold.co/300x200/003366/ffffff?text=XPS+15+9530",
        "dell_url": "https://www.dell.com/en-in/shop/laptops/dell-xps-15/spd/xps-15-9530-laptop",
        "in_stock": True,
        "stock_quantity": 3,
    },
    {
        "name": "Dell Latitude 5540",
        "category": "laptop",
        "dell_series": "Latitude",
        "processor": "13th Gen Intel Core i5-1345U",
        "ram": "16 GB DDR4",
        "storage": "256 GB SSD",
        "display": "15.6 inch FHD (1920x1080) IPS Anti-Glare",
        "graphics": "Intel Iris Xe Graphics",
        "os": "Windows 11 Pro",
        "weight": "1.57 kg",
        "dell_mrp": 92990.0,
        "selling_price": 85990.0,
        "image_url": "https://placehold.co/300x200/004080/ffffff?text=Latitude+5540",
        "dell_url": "https://www.dell.com/en-in/shop/business-laptops/latitude-5540/spd/latitude-15-5540-laptop",
        "in_stock": True,
        "stock_quantity": 8,
    },
    {
        "name": "Dell Vostro 3520",
        "category": "laptop",
        "dell_series": "Vostro",
        "processor": "12th Gen Intel Core i3-1215U",
        "ram": "8 GB DDR4",
        "storage": "256 GB SSD",
        "display": "15.6 inch FHD (1920x1080)",
        "graphics": "Intel UHD Graphics",
        "os": "Windows 11 Home",
        "weight": "1.66 kg",
        "dell_mrp": 42990.0,
        "selling_price": 38990.0,
        "image_url": "https://placehold.co/300x200/004080/ffffff?text=Vostro+3520",
        "dell_url": "https://www.dell.com/en-in/shop/business-laptops/vostro-3520/spd/vostro-15-3520-laptop",
        "in_stock": True,
        "stock_quantity": 20,
    },
    # ===== DESKTOPS =====
    {
        "name": "Dell OptiPlex 7010 Tower",
        "category": "desktop",
        "dell_series": "OptiPlex",
        "processor": "13th Gen Intel Core i7-13700",
        "ram": "16 GB DDR5",
        "storage": "512 GB PCIe NVMe SSD",
        "display": "Monitor not included",
        "graphics": "Intel UHD Graphics 770",
        "os": "Windows 11 Pro",
        "weight": "7.3 kg",
        "dell_mrp": 89990.0,
        "selling_price": 82990.0,
        "image_url": "https://placehold.co/300x200/1a1a2e/ffffff?text=OptiPlex+7010",
        "dell_url": "https://www.dell.com/en-in/shop/desktops/optiplex-7010-tower/spd/optiplex-7010-tower",
        "in_stock": True,
        "stock_quantity": 6,
    },
    {
        "name": "Dell OptiPlex 3000 SFF",
        "category": "desktop",
        "dell_series": "OptiPlex",
        "processor": "12th Gen Intel Core i5-12500",
        "ram": "8 GB DDR4",
        "storage": "256 GB SSD",
        "display": "Monitor not included",
        "graphics": "Intel UHD Graphics 770",
        "os": "Windows 11 Pro",
        "weight": "4.8 kg",
        "dell_mrp": 58990.0,
        "selling_price": 52990.0,
        "image_url": "https://placehold.co/300x200/1a1a2e/ffffff?text=OptiPlex+3000",
        "dell_url": "https://www.dell.com/en-in/shop/desktops/optiplex-3000-sff/spd/optiplex-3000-sff",
        "in_stock": True,
        "stock_quantity": 12,
    },
    {
        "name": "Dell XPS Desktop 8960",
        "category": "desktop",
        "dell_series": "XPS",
        "processor": "13th Gen Intel Core i7-13700K",
        "ram": "32 GB DDR5",
        "storage": "1 TB SSD + 2 TB HDD",
        "display": "Monitor not included",
        "graphics": "NVIDIA GeForce RTX 4070 12GB",
        "os": "Windows 11 Home",
        "weight": "13.2 kg",
        "dell_mrp": 189990.0,
        "selling_price": 179990.0,
        "image_url": "https://placehold.co/300x200/003366/ffffff?text=XPS+Desktop+8960",
        "dell_url": "https://www.dell.com/en-in/shop/desktops/xps-desktop-8960/spd/xps-8960-desktop",
        "in_stock": True,
        "stock_quantity": 4,
    },
    {
        "name": "Dell Inspiron 3020 Tower",
        "category": "desktop",
        "dell_series": "Inspiron",
        "processor": "13th Gen Intel Core i5-13400",
        "ram": "8 GB DDR4",
        "storage": "512 GB SSD",
        "display": "Monitor not included",
        "graphics": "Intel UHD Graphics 730",
        "os": "Windows 11 Home",
        "weight": "6.1 kg",
        "dell_mrp": 52990.0,
        "selling_price": 47990.0,
        "image_url": "https://placehold.co/300x200/0076CE/ffffff?text=Inspiron+3020",
        "dell_url": "https://www.dell.com/en-in/shop/desktops/inspiron-3020-tower/spd/inspiron-3020-tower",
        "in_stock": True,
        "stock_quantity": 10,
    },
    # ===== ALL-IN-ONES =====
    {
        "name": "Dell Inspiron 24 5420 All-in-One",
        "category": "all-in-one",
        "dell_series": "Inspiron",
        "processor": "13th Gen Intel Core i5-1335U",
        "ram": "8 GB DDR4",
        "storage": "512 GB SSD",
        "display": "23.8 inch FHD (1920x1080) IPS Touchscreen",
        "graphics": "Intel Iris Xe Graphics",
        "os": "Windows 11 Home",
        "weight": "5.4 kg",
        "dell_mrp": 72990.0,
        "selling_price": 67990.0,
        "image_url": "https://placehold.co/300x200/005a9e/ffffff?text=Inspiron+24+AIO",
        "dell_url": "https://www.dell.com/en-in/shop/desktops/inspiron-24-5420-aio/spd/inspiron-24-5420-aio",
        "in_stock": True,
        "stock_quantity": 7,
    },
    {
        "name": "Dell Inspiron 27 7720 All-in-One",
        "category": "all-in-one",
        "dell_series": "Inspiron",
        "processor": "13th Gen Intel Core i7-1355U",
        "ram": "16 GB DDR4",
        "storage": "1 TB SSD",
        "display": "27 inch QHD (2560x1440) IPS Touchscreen",
        "graphics": "NVIDIA GeForce MX550 2GB",
        "os": "Windows 11 Home",
        "weight": "7.7 kg",
        "dell_mrp": 109990.0,
        "selling_price": 99990.0,
        "image_url": "https://placehold.co/300x200/005a9e/ffffff?text=Inspiron+27+AIO",
        "dell_url": "https://www.dell.com/en-in/shop/desktops/inspiron-27-7720-aio/spd/inspiron-27-7720-aio",
        "in_stock": True,
        "stock_quantity": 5,
    },
    {
        "name": "Dell OptiPlex 7410 All-in-One",
        "category": "all-in-one",
        "dell_series": "OptiPlex",
        "processor": "13th Gen Intel Core i5-13500T",
        "ram": "16 GB DDR5",
        "storage": "512 GB SSD",
        "display": "23.8 inch FHD (1920x1080) IPS Anti-Glare",
        "graphics": "Intel UHD Graphics 770",
        "os": "Windows 11 Pro",
        "weight": "6.2 kg",
        "dell_mrp": 98990.0,
        "selling_price": 91990.0,
        "image_url": "https://placehold.co/300x200/1a1a2e/ffffff?text=OptiPlex+7410+AIO",
        "dell_url": "https://www.dell.com/en-in/shop/desktops/optiplex-7410-aio/spd/optiplex-7410-aio",
        "in_stock": True,
        "stock_quantity": 6,
    },
]


def seed_database():
    """Populate the database with sample products."""
    with app.app_context():
        db.create_all()

        # Check if data already exists
        existing = Product.query.count()
        if existing > 0:
            print(f"Database already has {existing} products. Deleting and re-seeding...")
            Product.query.delete()
            db.session.commit()

        # Add products
        for product_data in SAMPLE_PRODUCTS:
            # Auto-calculate discount
            dell_mrp = product_data["dell_mrp"]
            selling_price = product_data["selling_price"]
            discount = round((1 - selling_price / dell_mrp) * 100, 1) if dell_mrp > 0 else 0

            product = Product(
                **product_data,
                discount_percent=discount,
            )
            db.session.add(product)

        # Create admin user if not exists
        if not User.query.filter_by(email="admin@dellstore.com").first():
            admin = User(
                name="Admin",
                email="admin@dellstore.com",
                password_hash=generate_password_hash("admin123"),
                is_admin=True,
            )
            db.session.add(admin)

        db.session.commit()
        print(f"Successfully added {len(SAMPLE_PRODUCTS)} products!")
        print("  - 6 Laptops (Inspiron, XPS, Latitude, Vostro)")
        print("  - 4 Desktops (OptiPlex, XPS, Inspiron)")
        print("  - 3 All-in-Ones (Inspiron, OptiPlex)")
        print("\nAdmin login: admin@dellstore.com / admin123")


if __name__ == "__main__":
    seed_database()
