# Dell Store — Deployment Guide (Going Live)

> Step-by-step instructions to deploy the Dell Authorized Store website to production.

---

## Architecture Overview

```
Your Laptop (local dev)
    ↓ git push
GitHub Repository (source code)
    ↓ auto-deploy webhook
Render Web Service (Flask app + gunicorn)
    ↔ Render PostgreSQL (database)
    ↔ Cloudinary CDN (product images)
    ↔ Groq API (service chatbot LLM)
```

| Platform | Purpose | Cost |
|----------|---------|------|
| GitHub | Source code hosting + version control | Free |
| Render | Flask app hosting + PostgreSQL database | Free tier available |
| Cloudinary | Product image storage + CDN delivery | Free (25GB storage, 25GB bandwidth/mo) |
| Groq | LLM API for service chatbot | Free (30 RPM, 14,400 RPD) |

---

## Prerequisites

- [ ] Python 3.10+ installed locally
- [ ] Git installed
- [ ] GitHub account
- [ ] Render account (https://render.com)
- [ ] Cloudinary account (https://cloudinary.com)
- [ ] Groq account (https://console.groq.com)

---

## Step 1: Fix the Procfile

Rename `Procfile.py` to `Procfile` (no extension). Render requires this exact filename.

```bash
# In your project folder:
mv Procfile.py Procfile
```

The file content should be (no change needed):
```
web: gunicorn app:app
```

---

## Step 2: Prepare Static Images

You need 44 static images committed to Git. Create/place them in:

```
static/images/series/
├── inspiron/
│   ├── hero.png          ← Series card + homepage slider
│   ├── feature1.png      ← Series detail page section 1
│   ├── feature2.png      ← Series detail page section 2
│   └── feature3.png      ← Series detail page section 3
├── vostro/
│   ├── hero.png
│   ├── feature1.png, feature2.png, feature3.png
├── xps/
│   ├── hero.png
│   ├── feature1.png, feature2.png, feature3.png
├── alienware/
│   ├── hero.png
│   ├── feature1.png, feature2.png, feature3.png
├── optiplex/
│   ├── hero.png
│   ├── feature1.png, feature2.png, feature3.png
├── xps-desktop/
│   ├── hero.png
│   ├── feature1.png, feature2.png, feature3.png
├── inspiron-desktop/
│   ├── hero.png
│   ├── feature1.png, feature2.png, feature3.png
├── precision-tower/
│   ├── hero.png
│   ├── feature1.png, feature2.png, feature3.png
├── inspiron-aio/
│   ├── hero.png
│   ├── feature1.png, feature2.png, feature3.png
├── optiplex-aio/
│   ├── hero.png
│   ├── feature1.png, feature2.png, feature3.png
└── xps-aio/
    ├── hero.png
    ├── feature1.png, feature2.png, feature3.png
```

**Where to get these images:**
- Download from Dell India product pages (https://www.dell.com/en-in)
- Use official Dell press kit images
- Or create placeholder images (minimum 600x400px, PNG/WebP)

---

## Step 3: Set Up GitHub Repository

```bash
# 1. Initialize git in your project folder
cd dell-store
git init

# 2. Verify .gitignore is correct (should exclude .env, *.db, __pycache__)
cat .gitignore

# 3. Stage all files
git add .

# 4. Commit
git commit -m "Initial commit: Dell Store with Cloudinary integration"

# 5. Create a new repo on GitHub (https://github.com/new)
#    Name: dell-store (or your choice)
#    Visibility: Private (recommended — has API keys references)

# 6. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/dell-store.git
git branch -M main
git push -u origin main
```

---

## Step 4: Set Up Cloudinary (Image Storage)

1. **Sign up**: https://cloudinary.com/users/register_free
2. **Go to Dashboard**: https://console.cloudinary.com/settings/api-keys
3. **Copy these 3 values** (you'll need them in Step 6):
   - Cloud Name (e.g., `dxyz1abc2`)
   - API Key (e.g., `123456789012345`)
   - API Secret (e.g., `abcDEF_ghiJKL-mnoPQR`)

> **Note**: Never commit these values to Git. They go in Render's environment variables.

---

## Step 5: Set Up Groq (LLM for Chatbot)

1. **Sign up**: https://console.groq.com
2. **Go to API Keys**: https://console.groq.com/keys
3. **Create a new key** → Copy it (starts with `gsk_...`)

> The free tier gives you 30 requests/minute and 14,400 requests/day — more than enough for a small store.

---

## Step 6: Deploy on Render

### 6a. Create PostgreSQL Database

1. Go to https://dashboard.render.com
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: `dell-store-db`
   - **Region**: Singapore (closest to India) or Mumbai if available
   - **Plan**: Free (90-day limit) or Starter ($7/mo for persistent)
4. Click **Create Database**
5. Wait for it to provision → Copy the **Internal Database URL** (starts with `postgresql://`)

### 6b. Create Web Service

1. Click **New** → **Web Service**
2. Connect your GitHub repo (`dell-store`)
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `dell-store` (or your choice) |
| **Region** | Same as database |
| **Branch** | `main` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Plan** | Free (or Starter $7/mo for always-on) |

4. **Environment Variables** — Add all of these:

| Key | Value | Source |
|-----|-------|--------|
| `SECRET_KEY` | *(generate: `python -c "import secrets; print(secrets.token_hex(32))"`)* | You generate locally |
| `DATABASE_URL` | *(paste Internal Database URL from Step 6a)* | Render PostgreSQL |
| `GROQ_API_KEY` | `gsk_your_key_here` | Step 5 |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Default |
| `CLOUDINARY_CLOUD_NAME` | *(from Step 4)* | Cloudinary Dashboard |
| `CLOUDINARY_API_KEY` | *(from Step 4)* | Cloudinary Dashboard |
| `CLOUDINARY_API_SECRET` | *(from Step 4)* | Cloudinary Dashboard |
| `PYTHON_VERSION` | `3.11.0` | Render Python version |

5. Click **Create Web Service**
6. Wait for the first deploy to complete (2-5 minutes)

### 6c. Initialize the Database

After the first deploy succeeds:

1. Go to your Web Service on Render Dashboard
2. Click **Shell** tab (or use Render CLI)
3. Run:

```bash
python -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('Tables created!')
"
```

4. Seed the admin user and default data:

```bash
python seed_data.py
```

---

## Step 7: Verify Deployment

1. **Visit your site**: `https://dell-store.onrender.com` (your URL from Render dashboard)
2. **Test these flows**:

| Test | Expected Result |
|------|-----------------|
| Homepage loads | Hero slider + featured products visible |
| `/products` page | Product grid with placeholder images |
| `/login` with `admin@dellstore.com` / `admin123` | Login success, Admin link appears |
| `/admin` → Upload image for a product | Image uploads to Cloudinary, URL saved |
| `/admin` → Upload Excel with products | Products added to database |
| `/service` → Chat with bot | Groq LLM responds with repair estimates |
| Series pages (`/laptops/inspiron`) | Hero + feature images display |

3. **Check Cloudinary Dashboard**: Uploaded images should appear under `dell-store/products/` folder

---

## Step 8: Add Products via Excel

1. Login as admin → Go to `/admin`
2. Download the Excel template (or create your own with these columns):

| Column | Required | Example |
|--------|----------|---------|
| `name` | Yes | Dell Inspiron 15 3520 |
| `category` | Yes | laptop / desktop / all-in-one / accessory |
| `dell_series` | No | Inspiron / XPS / Vostro / Alienware |
| `processor` | No | 12th Gen Intel Core i5-1235U |
| `ram` | No | 8 GB DDR4 |
| `storage` | No | 512 GB SSD |
| `display` | No | 15.6 inch FHD |
| `graphics` | No | Intel Iris Xe |
| `os` | No | Windows 11 Home |
| `weight` | No | 1.65 kg |
| `dell_mrp` | No | 58990 |
| `selling_price` | Yes | 54990 |
| `stock_quantity` | No | 15 (default: 10) |
| `image_url` | No | Cloudinary/external URL |

3. For `image_url` column — use **Cloudinary URLs** (recommended):
   - Upload images manually to Cloudinary Media Library
   - Copy the URL and paste in Excel
   - Or leave blank and upload images later via Admin panel

---

## Step 9: Custom Domain (Optional)

1. Buy a domain (e.g., `yourdellstore.in`) from GoDaddy/Namecheap/Google Domains
2. In Render Dashboard → your Web Service → **Settings** → **Custom Domains**
3. Add your domain
4. Update DNS records at your registrar:
   - Type: `CNAME`
   - Name: `www` (or `@` for root)
   - Value: `dell-store.onrender.com` (your Render URL)
5. Wait 5-30 minutes for DNS propagation
6. Render auto-provisions free SSL (HTTPS)

---

## Step 10: Post-Launch Checklist

- [ ] Change admin password (currently `admin123` — insecure!)
- [ ] Remove/update placeholder phone number and email in `base.html`
- [ ] Update store address in footer
- [ ] Upload real product images via admin panel
- [ ] Upload service parts Excel with actual pricing
- [ ] Test the full purchase flow (add to cart → checkout)
- [ ] Set up Render auto-deploy (should be on by default — every `git push` triggers redeploy)
- [ ] Monitor Cloudinary usage (25GB/month free bandwidth)
- [ ] Monitor Groq usage (30 RPM limit)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'dotenv'` | Run `pip install -r requirements.txt` locally |
| Site shows 500 error on Render | Check Render Logs tab for the actual error |
| Images not showing after redeploy | Admin-uploaded images should be on Cloudinary. If using local disk, they're lost — re-upload |
| Database empty after redeploy | Render Free PostgreSQL persists. If using SQLite, it's lost — use PostgreSQL |
| Groq chatbot not responding | Check `GROQ_API_KEY` is set correctly in Render environment |
| Cloudinary upload fails | Verify all 3 Cloudinary env vars are set correctly |
| `RuntimeError: SECRET_KEY must be set` | Add `SECRET_KEY` to Render environment variables |

---

## Costs Summary (Monthly)

| Service | Free Tier Limit | Paid Tier (if needed) |
|---------|-----------------|----------------------|
| Render Web Service | 750 hours/month, sleeps after 15min inactivity | $7/mo (always-on) |
| Render PostgreSQL | 90 days free, then expires | $7/mo (Starter) |
| Cloudinary | 25GB storage + 25GB bandwidth | $89/mo (Plus) — unlikely needed |
| Groq LLM | 30 RPM, 14,400 RPD | Free is sufficient for small store |
| GitHub | Unlimited private repos | Free |
| **Total (free tier)** | | **₹0/month** |
| **Total (always-on)** | | **~₹1,200/month ($14)** |

---

## File → Platform Mapping (Quick Reference)

```
┌─────────────────────────────────────────────────────────────────┐
│ GITHUB REPOSITORY (all code files via git push)                 │
├─────────────────────────────────────────────────────────────────┤
│ app.py, config.py, models.py, seed_data.py, scraper.py         │
│ create_parts_excel.py, Procfile, requirements.txt, .gitignore  │
│ templates/*.html                                                │
│ static/css/style.css, static/js/main.js                        │
│ static/images/series/**/*.png (44 static images)               │
│ data/service_parts.xlsx, .env.example, DEPLOYMENT_GUIDE.md     │
└──────────────────────────────┬──────────────────────────────────┘
                               │ auto-deploy
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ RENDER WEB SERVICE (runs Flask + gunicorn)                      │
├─────────────────────────────────────────────────────────────────┤
│ Environment Variables:                                          │
│   SECRET_KEY, DATABASE_URL, GROQ_API_KEY, GROQ_MODEL,          │
│   CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY,                    │
│   CLOUDINARY_API_SECRET, PYTHON_VERSION                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
┌──────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ RENDER POSTGRESQL│ │   CLOUDINARY    │ │    GROQ API     │
│                  │ │                 │ │                 │
│ Products table   │ │ Product images  │ │ Service chatbot │
│ Users table      │ │ (persistent,    │ │ (LLM inference) │
│ Orders table     │ │  CDN-delivered) │ │                 │
│ Reviews table    │ │                 │ │                 │
│ Service requests │ │ dell-store/     │ │ llama-3.3-70b   │
│ Service parts    │ │   products/     │ │                 │
│ Product images   │ │                 │ │                 │
│ (metadata only)  │ │                 │ │                 │
└──────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Never Upload / Never Commit

| File | Reason |
|------|--------|
| `.env` | Contains real API keys and secrets |
| `*.db` (SQLite files) | Local dev database — production uses PostgreSQL |
| `__pycache__/` | Python bytecode — auto-generated |
| `venv/` | Virtual environment — install from requirements.txt |
| `static/images/products/*` | Admin-uploaded images — these go to Cloudinary |

---

*Guide created for the Dell Authorized Store project. Last updated: July 2025.*
