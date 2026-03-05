"""
LandMark Realty — Flask + SQLite Backend
Run:  python app.py
Open: http://localhost:5000
Admin: http://localhost:5000/admin  (admin / agent2024)
"""

import os, sqlite3, base64, uuid, json
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, g, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ── App config ────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'landmark-secret-change-in-production')

DATABASE     = 'landmark.db'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXT  = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_IMG_SIZE = 8 * 1024 * 1024   # 8 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Database ──────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS listings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT    NOT NULL DEFAULT 'house',
            title       TEXT    NOT NULL,
            description TEXT,
            price       TEXT,
            location    TEXT,
            bedrooms    INTEGER,
            bathrooms   INTEGER,
            size        TEXT,
            status      TEXT    NOT NULL DEFAULT 'available',
            featured    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS listing_images (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
            filename   TEXT    NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS property_requests (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            phone      TEXT NOT NULL,
            email      TEXT,
            type       TEXT,
            location   TEXT,
            budget     TEXT,
            bedrooms   TEXT,
            purpose    TEXT,
            urgency    TEXT,
            details    TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            phone      TEXT,
            email      TEXT,
            subject    TEXT,
            body       TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # Default agent settings
    defaults = {
        'agent_name':  'Isaac Teye',
        'agent_phone': '+233 24 931 5662',
        'agent_email': 'Isaacteye@gmail.com',
        'agent_wa':    '233249315662',
        'agent_bio':   'With over 10 years of experience in Ghana\'s real estate market, I have helped hundreds of families, professionals, and investors find the right property at the right price.',
        'admin_user':  'admin',
        'admin_pass':  generate_password_hash('realisaac@@1234'),
        'admin_user': "Isaac",
        'admin_pass': generate_password_hash('efia@@1246'),
    }
    for k, v in defaults.items():
        db.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (k, v))

    # Seed sample listings if none exist
    count = db.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    if count == 0:
        samples = [
            ('house', 'Elegant 4-Bedroom Family Home',
             'Spacious modern home with open-plan living, fitted kitchen, master en-suite, and a large garden. 24/7 water and electricity with standby generator.',
             'GHS 850,000', 'East Legon, Accra', 4, 3, '320 sqm', 'available', 1),
            ('room', 'Self-Contained Studio Room',
             'Neat tiled self-contained room with private bath, kitchenette, and 24/7 water and electricity. Ideal for working professionals.',
             'GHS 1,200/mo', 'Tema, Community 25', 1, 1, '45 sqm', 'available', 0),
            ('land', 'Prime Residential Plot',
             'Fenced, gated 1-acre plot with Indenture, Site Plan, and Land Search Report. Perfect for development in a fast-growing area.',
             'GHS 400,000', 'Kasoa, Central Region', None, None, '1 acre', 'available', 1),
            ('house', 'Modern 3-Bedroom Townhouse',
             'Newly built townhouse with solar panels, CCTV security, covered parking, and beautiful garden. Estate living in Tema.',
             'GHS 620,000', 'Tema, Community 18', 3, 2, '220 sqm', 'available', 0),
            ('room', 'Furnished 2-Bedroom Apartment',
             'Fully furnished apartment with AC, washing machine, DSTV, and WiFi. Ideal for expats or corporate rental.',
             'GHS 4,500/mo', 'Airport Residential, Accra', 2, 2, '90 sqm', 'available', 1),
            ('land', 'Commercial Land — Main Road',
             'Half-acre commercial land on a busy road. Ideal for shops, offices, or mixed-use development. All documents available.',
             'GHS 750,000', 'Spintex Road, Accra', None, None, '0.5 acre', 'available', 0),
        ]
        for s in samples:
            db.execute("""INSERT INTO listings
                (type,title,description,price,location,bedrooms,bathrooms,size,status,featured)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", s)

    db.commit()
    db.close()
    print("✅ Database initialised:", DATABASE)

# ── Helpers ───────────────────────────────────────
def get_setting(key, default=''):
    row = get_db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row['value'] if row else default

def get_agent():
    return {
        'name':  get_setting('agent_name'),
        'phone': get_setting('agent_phone'),
        'email': get_setting('agent_email'),
        'wa':    get_setting('agent_wa'),
        'bio':   get_setting('agent_bio'),
    }

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def listing_to_dict(row):
    d = dict(row)
    db = get_db()
    imgs = db.execute(
        "SELECT filename FROM listing_images WHERE listing_id=? ORDER BY sort_order",
        (d['id'],)
    ).fetchall()
    d['images'] = [r['filename'] for r in imgs]
    return d

def fmt_dt(dt_str):
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y, %I:%M %p')
    except:
        return dt_str or ''

app.jinja_env.globals['fmt_dt'] = fmt_dt

# ── Auth decorator ────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ══════════════════════════════════════════════════
#  PUBLIC ROUTES
# ══════════════════════════════════════════════════

@app.route('/')
def index():
    db = get_db()
    featured = db.execute(
        "SELECT * FROM listings WHERE featured=1 AND status='available' ORDER BY created_at DESC LIMIT 6"
    ).fetchall()
    featured = [listing_to_dict(r) for r in featured]
    total_active = db.execute("SELECT COUNT(*) FROM listings WHERE status='available'").fetchone()[0]
    return render_template('index.html', featured=featured, total_active=total_active, agent=get_agent())

@app.route('/properties')
def properties():
    db = get_db()
    type_f   = request.args.get('type', '')
    budget_f = request.args.get('budget', '')
    loc_f    = request.args.get('loc', '').strip()
    sort_f   = request.args.get('sort', 'newest')

    query  = "SELECT * FROM listings WHERE status='available'"
    params = []
    if type_f:
        query += " AND type=?"; params.append(type_f)
    if loc_f:
        query += " AND (location LIKE ? OR title LIKE ?)"; params += [f'%{loc_f}%', f'%{loc_f}%']

    query += " ORDER BY " + ("featured DESC, created_at DESC" if sort_f == 'featured' else "created_at DESC")
    rows = db.execute(query, params).fetchall()
    listings = [listing_to_dict(r) for r in rows]

    # Budget filter in Python (price strings like "GHS 500,000")
    if budget_f:
        def price_num(p):
            import re
            m = re.search(r'[\d,]+', p.replace(',',''))
            return int(m.group().replace(',','')) if m else 0
        if budget_f == 'low':
            listings = [l for l in listings if price_num(l['price']) < 200000]
        elif budget_f == 'mid':
            listings = [l for l in listings if 200000 <= price_num(l['price']) <= 600000]
        elif budget_f == 'high':
            listings = [l for l in listings if price_num(l['price']) > 600000]

    return render_template('properties.html', listings=listings,
                           filters={'type':type_f,'budget':budget_f,'loc':loc_f,'sort':sort_f},
                           agent=get_agent())

@app.route('/property/<int:id>')
def property_detail(id):
    db = get_db()
    row = db.execute("SELECT * FROM listings WHERE id=?", (id,)).fetchone()
    if not row:
        return redirect(url_for('properties'))
    listing = listing_to_dict(row)
    return render_template('property_detail.html', listing=listing, agent=get_agent())

@app.route('/about')
def about():
    total = get_db().execute("SELECT COUNT(*) FROM listings WHERE status='available'").fetchone()[0]
    return render_template('about.html', agent=get_agent(), total_active=total)

@app.route('/services')
def services():
    return render_template('services.html', agent=get_agent())

@app.route('/contact')
def contact():
    return render_template('contact.html', agent=get_agent())

@app.route('/request', methods=['GET', 'POST'])
def property_request():
    if request.method == 'POST':
        get_db().execute("""
            INSERT INTO property_requests
            (name,phone,email,type,location,budget,bedrooms,purpose,urgency,details)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            request.form.get('name','').strip(),
            request.form.get('phone','').strip(),
            request.form.get('email',''),
            request.form.get('type',''),
            request.form.get('location',''),
            request.form.get('budget',''),
            request.form.get('bedrooms',''),
            request.form.get('purpose',''),
            request.form.get('urgency',''),
            request.form.get('details',''),
        ))
        get_db().commit()
        flash('success:Your request has been submitted! We will contact you within as soon as possible.')
        return redirect(url_for('property_request'))
    return render_template('request.html', agent=get_agent())

@app.route('/send-message', methods=['POST'])
def send_message():
    name = request.form.get('name','').strip()
    body = request.form.get('body','').strip()
    if not name or not body:
        flash('error:Please fill in your name and message.')
        return redirect(url_for('contact'))
    get_db().execute("""
        INSERT INTO messages (name,phone,email,subject,body)
        VALUES (?,?,?,?,?)""", (
        name,
        request.form.get('phone',''),
        request.form.get('email',''),
        request.form.get('subject',''),
        body,
    ))
    get_db().commit()
    flash("success:Message sent! We'll get back to you soon.")
    return redirect(url_for('contact'))

# ══════════════════════════════════════════════════
#  ADMIN ROUTES
# ══════════════════════════════════════════════════

@app.route('/admin')
@app.route('/admin/')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_do_login():
    username = request.form.get('username','').strip()
    password = request.form.get('password','')
    stored_user = get_setting('admin_user')
    stored_hash = get_setting('admin_pass')
    if username == stored_user and check_password_hash(stored_hash, password):
        session['admin_logged_in'] = True
        session.permanent = True
        return redirect(url_for('admin_dashboard'))
    flash('error:Incorrect username or password.')
    return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        'total':    db.execute("SELECT COUNT(*) FROM listings").fetchone()[0],
        'active':   db.execute("SELECT COUNT(*) FROM listings WHERE status='available'").fetchone()[0],
        'requests': db.execute("SELECT COUNT(*) FROM property_requests").fetchone()[0],
        'messages': db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        'featured': db.execute("SELECT COUNT(*) FROM listings WHERE featured=1").fetchone()[0],
    }
    recent_requests = db.execute(
        "SELECT * FROM property_requests ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_requests=recent_requests, agent=get_agent())

# ── Listings CRUD ─────────────────────────────────

@app.route('/admin/listings')
@admin_required
def admin_listings():
    rows = get_db().execute("SELECT * FROM listings ORDER BY created_at DESC").fetchall()
    listings = [listing_to_dict(r) for r in rows]
    return render_template('admin/listings.html', listings=listings, agent=get_agent())

@app.route('/admin/listings/new', methods=['GET', 'POST'])
@admin_required
def admin_listing_new():
    if request.method == 'POST':
        return _save_listing(None)
    return render_template('admin/listing_form.html', listing=None, agent=get_agent())

@app.route('/admin/listings/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_listing_edit(id):
    row = get_db().execute("SELECT * FROM listings WHERE id=?", (id,)).fetchone()
    if not row:
        flash('error:Listing not found.')
        return redirect(url_for('admin_listings'))
    if request.method == 'POST':
        return _save_listing(id)
    listing = listing_to_dict(row)
    return render_template('admin/listing_form.html', listing=listing, agent=get_agent())

def _save_listing(listing_id):
    db   = get_db()
    data = {
        'type':        request.form.get('type', 'house'),
        'title':       request.form.get('title','').strip(),
        'description': request.form.get('description','').strip(),
        'price':       request.form.get('price','').strip(),
        'location':    request.form.get('location','').strip(),
        'bedrooms':    request.form.get('bedrooms') or None,
        'bathrooms':   request.form.get('bathrooms') or None,
        'size':        request.form.get('size','').strip(),
        'status':      request.form.get('status','available'),
        'featured':    1 if request.form.get('featured') else 0,
    }
    if not data['title'] or not data['price']:
        flash('error:Title and price are required.')
        return redirect(request.url)

    if listing_id:
        db.execute("""UPDATE listings SET type=:type,title=:title,description=:description,
            price=:price,location=:location,bedrooms=:bedrooms,bathrooms=:bathrooms,
            size=:size,status=:status,featured=:featured WHERE id=:id""",
            {**data, 'id': listing_id})
    else:
        cur = db.execute("""INSERT INTO listings
            (type,title,description,price,location,bedrooms,bathrooms,size,status,featured)
            VALUES (:type,:title,:description,:price,:location,:bedrooms,:bathrooms,:size,:status,:featured)""",
            data)
        listing_id = cur.lastrowid

    # Handle image uploads
    files = request.files.getlist('images')
    existing_count = db.execute(
        "SELECT COUNT(*) FROM listing_images WHERE listing_id=?", (listing_id,)
    ).fetchone()[0]
    order = existing_count
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            ext  = f.filename.rsplit('.', 1)[1].lower()
            fname = f"{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            db.execute("INSERT INTO listing_images (listing_id,filename,sort_order) VALUES (?,?,?)",
                       (listing_id, fname, order))
            order += 1

    # Delete removed images
    remove_ids = request.form.getlist('remove_image')
    for img_id in remove_ids:
        row = db.execute("SELECT filename FROM listing_images WHERE id=?", (img_id,)).fetchone()
        if row:
            try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], row['filename']))
            except: pass
            db.execute("DELETE FROM listing_images WHERE id=?", (img_id,))

    db.commit()
    flash('success:Listing saved successfully!')
    return redirect(url_for('admin_listings'))

@app.route('/admin/listings/<int:id>/delete', methods=['POST'])
@admin_required
def admin_listing_delete(id):
    db = get_db()
    imgs = db.execute("SELECT filename FROM listing_images WHERE listing_id=?", (id,)).fetchall()
    for img in imgs:
        try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img['filename']))
        except: pass
    db.execute("DELETE FROM listings WHERE id=?", (id,))
    db.commit()
    flash('success:Listing deleted.')
    return redirect(url_for('admin_listings'))

# ── Requests & Messages ───────────────────────────

@app.route('/admin/requests')
@admin_required
def admin_requests():
    rows = get_db().execute("SELECT * FROM property_requests ORDER BY created_at DESC").fetchall()
    return render_template('admin/requests.html', requests=rows, agent=get_agent())

@app.route('/admin/requests/<int:id>/delete', methods=['POST'])
@admin_required
def admin_request_delete(id):
    get_db().execute("DELETE FROM property_requests WHERE id=?", (id,))
    get_db().commit()
    flash('success:Request deleted.')
    return redirect(url_for('admin_requests'))

@app.route('/admin/messages')
@admin_required
def admin_messages():
    rows = get_db().execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall()
    return render_template('admin/messages.html', messages=rows, agent=get_agent())

@app.route('/admin/messages/<int:id>/delete', methods=['POST'])
@admin_required
def admin_message_delete(id):
    get_db().execute("DELETE FROM messages WHERE id=?", (id,))
    get_db().commit()
    flash('success:Message deleted.')
    return redirect(url_for('admin_messages'))

# ── Settings ──────────────────────────────────────

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    db = get_db()
    if request.method == 'POST':
        fields = ['agent_name','agent_phone','agent_email','agent_wa','agent_bio']
        for f in fields:
            db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",
                       (f, request.form.get(f,'').strip()))
        # Password change
        new_pw = request.form.get('new_password','').strip()
        if new_pw:
            db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",
                       ('admin_pass', generate_password_hash(new_pw)))
        db.commit()
        flash('success:Settings saved!')
        return redirect(url_for('admin_settings'))

    return render_template('admin/settings.html',
        agent=get_agent(),
        admin_user=get_setting('admin_user')
    )

# ── Run ───────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print("🏠 LandMark Realty running at http://localhost:5000")
    print("🔐 Admin panel at http://localhost:5000/admin")
    app.run(debug=True, port=5000)
