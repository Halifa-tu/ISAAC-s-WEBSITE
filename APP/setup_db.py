"""
LandMark Realty — One-time database setup script
Run this ONCE to create all tables and insert Isaac's details.
Usage: python setup_db.py
"""

import json, re, os
from urllib import request as urlreq
from werkzeug.security import generate_password_hash

# ── Your Neon database URL ─────────────────────────
DATABASE_URL = "postgresql://neondb_owner:npg_D2Zuhakv8YNK@ep-damp-darkness-amse7s7j-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# ── Agent / Business Details ───────────────────────
AGENT = {
    "agent_name":    "Isaac Teye",
    "agent_phone":   "0249315662",
    "agent_email":   "iisaacteye@gmail.com",
    "agent_wa":      "233249315662",
    "agent_bio":     "With years of experience in Ghana's real estate market, I help families, professionals, and investors find the right property at the right price. Whether you're buying, renting, or investing, I'm here to make the process smooth and stress-free.",
    "business_name": "LandMark Realty",
}

ADMIN_EMAIL    = "iisaacteye@gmail.com"
ADMIN_PASSWORD = "agent2024"   # ← Change this to your preferred password
ADMIN_NAME     = "Isaac Teye"

# ──────────────────────────────────────────────────

from urllib.parse import urlparse
import base64

def _api_url():
    parsed = urlparse(DATABASE_URL)
    host   = parsed.hostname
    return f"https://{host}/sql"

def _creds():
    parsed = urlparse(DATABASE_URL)
    return parsed.username, parsed.password

def run(sql, params=None):
    api_url  = _api_url()
    username, password = _creds()

    if params:
        counter = [0]
        def replacer(_):
            counter[0] += 1
            return f'${counter[0]}'
        sql = re.sub(r'%s', replacer, sql)

    payload = json.dumps({
        "query":  sql,
        "params": [str(p) if p is not None else None for p in (params or [])]
    }).encode('utf-8')

    creds   = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Basic {creds}",
        "Neon-Connection-String": DATABASE_URL,
    }
    req = urlreq.Request(api_url, data=payload, headers=headers, method='POST')
    with urlreq.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode())
    rows   = data.get('rows', [])
    fields = data.get('fields', [])
    if not fields: return []
    col_names = [f['name'] for f in fields]
    return [dict(zip(col_names, row)) for row in rows]

def one(sql, params=None):
    rows = run(sql, params)
    return rows[0] if rows else None

def val(sql, params=None):
    row = one(sql, params)
    return list(row.values())[0] if row else 0

print("🔌 Connecting to Neon database...")

# ── 1. Create tables ───────────────────────────────
print("📦 Creating tables...")
tables = [
    """CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)""",
    """CREATE TABLE IF NOT EXISTS admin_users (
        id SERIAL PRIMARY KEY, full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE, password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin', reset_token TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS listings (
        id SERIAL PRIMARY KEY, type TEXT NOT NULL DEFAULT 'house',
        title TEXT NOT NULL, description TEXT, price TEXT,
        location TEXT, bedrooms INTEGER, bathrooms INTEGER,
        size TEXT, land_use TEXT, land_docs TEXT,
        status TEXT NOT NULL DEFAULT 'available',
        featured INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS listing_images (
        id SERIAL PRIMARY KEY, listing_id INTEGER NOT NULL,
        filename TEXT NOT NULL, sort_order INTEGER NOT NULL DEFAULT 0)""",
    """CREATE TABLE IF NOT EXISTS property_requests (
        id SERIAL PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL,
        email TEXT, type TEXT, location TEXT, budget TEXT,
        bedrooms TEXT, purpose TEXT, urgency TEXT, land_size TEXT,
        land_use TEXT, land_docs TEXT, details TEXT, admin_reply TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY, name TEXT NOT NULL, phone TEXT,
        email TEXT, subject TEXT, body TEXT NOT NULL,
        admin_reply TEXT, created_at TIMESTAMP NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS reviews (
        id SERIAL PRIMARY KEY, name TEXT NOT NULL, location TEXT,
        rating INTEGER NOT NULL DEFAULT 5, body TEXT NOT NULL,
        approved INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT NOW())""",
]
for t in tables:
    run(t)
    print("  ✅", t.split('\n')[0].strip()[:60])

# ── 2. Insert agent settings ───────────────────────
print("\n👤 Inserting agent details...")
for k, v in AGENT.items():
    run("INSERT INTO settings (key,value) VALUES (%s,%s) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value", (k, v))
    print(f"  ✅ {k}: {v[:50]}")

# ── 3. Create admin account ────────────────────────
print("\n🔐 Setting up admin account...")
existing = one("SELECT id FROM admin_users WHERE email = %s", (ADMIN_EMAIL,))
if existing:
    run("UPDATE admin_users SET full_name=%s, password=%s WHERE email=%s",
        (ADMIN_NAME, generate_password_hash(ADMIN_PASSWORD), ADMIN_EMAIL))
    print(f"  ✅ Updated admin: {ADMIN_EMAIL}")
else:
    run("INSERT INTO admin_users (full_name,email,password,role) VALUES (%s,%s,%s,%s)",
        (ADMIN_NAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD), 'superadmin'))
    print(f"  ✅ Created admin: {ADMIN_EMAIL}")

# ── 4. Seed sample listings (only if empty) ────────
listing_count = val("SELECT COUNT(*) FROM listings")
if listing_count == 0:
    print("\n🏠 Adding sample listings...")
    samples = [
        ('house','Elegant 4-Bedroom Family Home','Spacious modern home with open-plan living, fitted kitchen, master en-suite, and a large garden. Located in a serene, secure neighbourhood.','GHS 850,000','East Legon, Accra',4,3,'320 sqm',None,None,'available',1),
        ('room','Self-Contained Studio Room','Neat tiled self-contained room with private bath, kitchenette, and 24/7 water and electricity. Perfect for a working professional.','GHS 1,200/mo','Tema, Community 25',1,1,'45 sqm',None,None,'available',0),
        ('land','Prime Residential Plot','Fenced, gated 1-acre plot with Indenture, Site Plan, and Land Search Report ready for handover.','GHS 400,000','Kasoa, Central Region',None,None,'1 acre','Residential','Indenture, Site Plan','available',1),
        ('house','Modern 3-Bedroom Townhouse','Newly built townhouse with solar panels, CCTV security, covered parking and backup water supply.','GHS 620,000','Tema, Community 18',3,2,'220 sqm',None,None,'available',0),
        ('room','Furnished 2-Bedroom Apartment','Fully furnished apartment with AC, washing machine, DSTV, and WiFi included in rent.','GHS 4,500/mo','Airport Residential, Accra',2,2,'90 sqm',None,None,'available',1),
        ('land','Commercial Land — Main Road','Half-acre commercial land on a busy road. Ideal for shops, offices, or mixed-use development.','GHS 750,000','Spintex Road, Accra',None,None,'0.5 acre','Commercial','Indenture','available',0),
    ]
    for s in samples:
        run("""INSERT INTO listings (type,title,description,price,location,bedrooms,
            bathrooms,size,land_use,land_docs,status,featured)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", s)
        print(f"  ✅ {s[1]}")
else:
    print(f"\n🏠 Skipped listings — {listing_count} already exist")

# ── 5. Seed sample reviews (only if empty) ─────────
review_count = val("SELECT COUNT(*) FROM reviews")
if review_count == 0:
    print("\n⭐ Adding sample reviews...")
    for r in [
        ('Kwame Acheampong','Homebuyer, Accra',5,'Found my dream home in East Legon within 2 weeks. Professional, responsive, and genuinely helpful throughout the process.'),
        ('Abena Boateng','Business Owner, Kumasi',5,'Submitted a request and had 3 perfect options within days. Exceptional service and very trustworthy!'),
        ('Emmanuel Owusu','Investor, Tema',5,'Bought a plot in Kasoa with all documents intact. Fast, transparent, and completely stress-free.'),
    ]:
        run("INSERT INTO reviews (name,location,rating,body,approved) VALUES (%s,%s,%s,%s,1)", r)
        print(f"  ✅ Review from {r[0]}")
else:
    print(f"\n⭐ Skipped reviews — {review_count} already exist")

# ── Final summary ──────────────────────────────────
print("\n" + "="*50)
print("✅ DATABASE SETUP COMPLETE!")
print("="*50)
print(f"  Listings : {val('SELECT COUNT(*) FROM listings')}")
print(f"  Reviews  : {val('SELECT COUNT(*) FROM reviews')}")
print(f"  Admins   : {val('SELECT COUNT(*) FROM admin_users')}")
print(f"  Settings : {val('SELECT COUNT(*) FROM settings')}")
print()
print("🔐 Admin Login:")
print(f"   Email   : {ADMIN_EMAIL}")
print(f"   Password: {ADMIN_PASSWORD}")
print()
print("🌐 Your website is ready!")
