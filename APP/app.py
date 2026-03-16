"""
LandMark Realty — Flask + PostgreSQL (Neon) Backend
Deploy: Vercel  |  DB: Neon PostgreSQL
Admin: /admin   |  Login: iisaacteye@gmail.com / agent2024
"""

import os, uuid, secrets
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, g, flash)
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'landmark-secret-change-in-production')

DATABASE_URL  = os.environ.get('DATABASE_URL', '')
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXT   = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Database ──────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        g.db.autocommit = False
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        try: db.close()
        except: pass

def db_execute(sql, params=(), fetchone=False, fetchall=False, commit=False):
    """Helper: converts ? placeholders to %s for psycopg2, executes, returns result."""
    sql = sql.replace('?', '%s')
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(sql, params)
    result = None
    if fetchone:  result = cur.fetchone()
    if fetchall:  result = cur.fetchall()
    if commit:    conn.commit()
    return result, cur

def db_commit():
    get_db().commit()

def init_db():
    """Create tables and seed default data. Safe to run multiple times."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS admin_users (
            id          SERIAL PRIMARY KEY,
            full_name   TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            password    TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'admin',
            reset_token TEXT,
            created_at  TIMESTAMP NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS listings (
            id          SERIAL PRIMARY KEY,
            type        TEXT NOT NULL DEFAULT 'house',
            title       TEXT NOT NULL,
            description TEXT,
            price       TEXT,
            location    TEXT,
            bedrooms    INTEGER,
            bathrooms   INTEGER,
            size        TEXT,
            land_use    TEXT,
            land_docs   TEXT,
            status      TEXT NOT NULL DEFAULT 'available',
            featured    INTEGER NOT NULL DEFAULT 0,
            created_at  TIMESTAMP NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS listing_images (
            id         SERIAL PRIMARY KEY,
            listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
            filename   TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS property_requests (
            id          SERIAL PRIMARY KEY,
            name        TEXT NOT NULL,
            phone       TEXT NOT NULL,
            email       TEXT,
            type        TEXT,
            location    TEXT,
            budget      TEXT,
            bedrooms    TEXT,
            purpose     TEXT,
            urgency     TEXT,
            land_size   TEXT,
            land_use    TEXT,
            land_docs   TEXT,
            details     TEXT,
            admin_reply TEXT,
            created_at  TIMESTAMP NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS messages (
            id          SERIAL PRIMARY KEY,
            name        TEXT NOT NULL,
            phone       TEXT,
            email       TEXT,
            subject     TEXT,
            body        TEXT NOT NULL,
            admin_reply TEXT,
            created_at  TIMESTAMP NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id         SERIAL PRIMARY KEY,
            name       TEXT NOT NULL,
            location   TEXT,
            rating     INTEGER NOT NULL DEFAULT 5,
            body       TEXT NOT NULL,
            approved   INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)

    # Seed settings
    defaults = {
        'agent_name':    'Isaac Teye',
        'agent_phone':   '0249315662',
        'agent_email':   'iisaacteye@gmail.com',
        'agent_wa':      '233249315662',
        'agent_bio':     "With years of experience in Ghana's real estate market, we help families, professionals, and investors find the right property at the right price.",
        'business_name': 'LandMark Realty',
    }
    for k, v in defaults.items():
        cur.execute("INSERT INTO settings (key,value) VALUES (%s,%s) ON CONFLICT (key) DO NOTHING", (k, v))

    # Seed admin
    cur.execute("SELECT COUNT(*) FROM admin_users")
    if cur.fetchone()['count'] == 0:
        cur.execute("INSERT INTO admin_users (full_name,email,password,role) VALUES (%s,%s,%s,%s)", (
            'Isaac Teye', 'iisaacteye@gmail.com',
            generate_password_hash('agent2024'), 'superadmin'))

    # Seed listings
    cur.execute("SELECT COUNT(*) FROM listings")
    if cur.fetchone()['count'] == 0:
        sample = [
            ('house','Elegant 4-Bedroom Family Home','Spacious modern home with open-plan living, fitted kitchen, master en-suite, and a large garden.','GHS 850,000','East Legon, Accra',4,3,'320 sqm',None,None,'available',1),
            ('room','Self-Contained Studio Room','Neat tiled self-contained room with private bath, kitchenette, and 24/7 water and electricity.','GHS 1,200/mo','Tema, Community 25',1,1,'45 sqm',None,None,'available',0),
            ('land','Prime Residential Plot','Fenced, gated 1-acre plot with Indenture, Site Plan, and Land Search Report.','GHS 400,000','Kasoa, Central Region',None,None,'1 acre','Residential','Indenture, Site Plan','available',1),
            ('house','Modern 3-Bedroom Townhouse','Newly built townhouse with solar panels, CCTV security, covered parking.','GHS 620,000','Tema, Community 18',3,2,'220 sqm',None,None,'available',0),
            ('room','Furnished 2-Bedroom Apartment','Fully furnished apartment with AC, washing machine, DSTV, and WiFi.','GHS 4,500/mo','Airport Residential, Accra',2,2,'90 sqm',None,None,'available',1),
            ('land','Commercial Land — Main Road','Half-acre commercial land on a busy road. Ideal for shops, offices, or mixed-use development.','GHS 750,000','Spintex Road, Accra',None,None,'0.5 acre','Commercial','Indenture','available',0),
        ]
        for s in sample:
            cur.execute("""INSERT INTO listings (type,title,description,price,location,bedrooms,bathrooms,
                size,land_use,land_docs,status,featured) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", s)

    # Seed reviews
    cur.execute("SELECT COUNT(*) FROM reviews")
    if cur.fetchone()['count'] == 0:
        for r in [
            ('Kwame Acheampong','Homebuyer, Accra',5,'Found my dream home in East Legon within 2 weeks. Professional, responsive, and genuinely helpful.'),
            ('Abena Boateng','Business Owner, Kumasi',5,'Submitted a request and had 3 perfect options within days. Exceptional service!'),
            ('Emmanuel Owusu','Investor, Tema',5,'Bought a plot in Kasoa with all documents intact. Fast, transparent, and stress-free.'),
        ]:
            cur.execute("INSERT INTO reviews (name,location,rating,body,approved) VALUES (%s,%s,%s,%s,1)", r)

    conn.commit()
    conn.close()
    print("✅ PostgreSQL database initialised (Neon)")

# ── Helpers ───────────────────────────────────────
def get_setting(key, default=''):
    row, _ = db_execute("SELECT value FROM settings WHERE key=%s", (key,), fetchone=True)
    return row['value'] if row else default

def get_agent():
    return {
        'name':     get_setting('agent_name',    'Isaac Teye'),
        'phone':    get_setting('agent_phone',   '0249315662'),
        'email':    get_setting('agent_email',   'iisaacteye@gmail.com'),
        'wa':       get_setting('agent_wa',      '233249315662'),
        'bio':      get_setting('agent_bio',     ''),
        'business': get_setting('business_name', 'LandMark Realty'),
    }

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def listing_to_dict(row):
    d = dict(row)
    imgs, _ = db_execute(
        "SELECT id, filename FROM listing_images WHERE listing_id=%s ORDER BY sort_order",
        (d['id'],), fetchall=True)
    d['images'] = [{'id': r['id'], 'filename': r['filename']} for r in (imgs or [])]
    return d

def fmt_dt(dt_val):
    try:
        if isinstance(dt_val, datetime): return dt_val.strftime('%d %b %Y, %I:%M %p')
        return datetime.strptime(str(dt_val), '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y, %I:%M %p')
    except: return str(dt_val) if dt_val else ''

app.jinja_env.globals['fmt_dt'] = fmt_dt

def get_current_admin():
    if not session.get('admin_id'): return None
    row, _ = db_execute("SELECT * FROM admin_users WHERE id=%s", (session['admin_id'],), fetchone=True)
    return row

app.jinja_env.globals['get_current_admin'] = get_current_admin

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ══════════════════════════════════════════════════
#  PUBLIC ROUTES
# ══════════════════════════════════════════════════

@app.route('/')
def index():
    featured, _ = db_execute(
        "SELECT * FROM listings WHERE featured=1 AND status='available' ORDER BY created_at DESC LIMIT 6",
        fetchall=True)
    total_row, _ = db_execute(
        "SELECT COUNT(*) FROM listings WHERE status='available'", fetchone=True)
    total_active = total_row['count'] if total_row else 0
    reviews, _   = db_execute(
        "SELECT * FROM reviews WHERE approved=1 ORDER BY created_at DESC LIMIT 6", fetchall=True)
    return render_template('index.html',
        featured=[listing_to_dict(r) for r in (featured or [])],
        total_active=total_active, agent=get_agent(), reviews=reviews or [])

@app.route('/properties')
def properties():
    type_f = request.args.get('type', '')
    bdg_f  = request.args.get('budget', '')
    loc_f  = request.args.get('loc', '').strip()
    sort_f = request.args.get('sort', 'newest')

    q = "SELECT * FROM listings WHERE status='available'"
    p = []
    if type_f: q += " AND type=%s"; p.append(type_f)
    if loc_f:  q += " AND (location ILIKE %s OR title ILIKE %s)"; p += [f'%{loc_f}%', f'%{loc_f}%']
    q += " ORDER BY " + ("featured DESC, created_at DESC" if sort_f == 'featured' else "created_at DESC")

    rows, _ = db_execute(q, p, fetchall=True)
    listings = [listing_to_dict(r) for r in (rows or [])]

    if bdg_f:
        import re
        def pn(p): m = re.search(r'\d+', p.replace(',','')); return int(m.group()) if m else 0
        if bdg_f == 'low':   listings = [l for l in listings if pn(l['price']) < 200000]
        elif bdg_f == 'mid': listings = [l for l in listings if 200000 <= pn(l['price']) <= 600000]
        elif bdg_f == 'high':listings = [l for l in listings if pn(l['price']) > 600000]

    return render_template('properties.html', listings=listings,
        filters={'type':type_f,'budget':bdg_f,'loc':loc_f,'sort':sort_f}, agent=get_agent())

@app.route('/property/<int:id>')
def property_detail(id):
    row, _ = db_execute("SELECT * FROM listings WHERE id=%s", (id,), fetchone=True)
    if not row: return redirect(url_for('properties'))
    return render_template('property_detail.html', listing=listing_to_dict(row), agent=get_agent())

@app.route('/about')
def about():
    total_row, _ = db_execute("SELECT COUNT(*) FROM listings WHERE status='available'", fetchone=True)
    reviews, _   = db_execute("SELECT * FROM reviews WHERE approved=1 ORDER BY created_at DESC", fetchall=True)
    return render_template('about.html', agent=get_agent(),
        total_active=total_row['count'] if total_row else 0, reviews=reviews or [])

@app.route('/services')
def services():
    return render_template('services.html', agent=get_agent())

@app.route('/contact')
def contact():
    return render_template('contact.html', agent=get_agent())

@app.route('/request', methods=['GET','POST'])
def property_request():
    if request.method == 'POST':
        db_execute("""INSERT INTO property_requests
            (name,phone,email,type,location,budget,bedrooms,purpose,urgency,land_size,land_use,land_docs,details)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (
            request.form.get('name','').strip(), request.form.get('phone','').strip(),
            request.form.get('email',''),        request.form.get('type',''),
            request.form.get('location',''),     request.form.get('budget',''),
            request.form.get('bedrooms',''),     request.form.get('purpose',''),
            request.form.get('urgency',''),      request.form.get('land_size',''),
            request.form.get('land_use',''),     request.form.get('land_docs',''),
            request.form.get('details',''),
        ), commit=True)
        flash('success:Your request has been submitted! We will contact you within 24 hours.')
        return redirect(url_for('property_request'))
    return render_template('request.html', agent=get_agent())

@app.route('/send-message', methods=['POST'])
def send_message():
    name = request.form.get('name','').strip()
    body = request.form.get('body','').strip()
    if not name or not body:
        flash('error:Please fill in your name and message.')
        return redirect(url_for('contact'))
    db_execute("INSERT INTO messages (name,phone,email,subject,body) VALUES (%s,%s,%s,%s,%s)", (
        name, request.form.get('phone',''), request.form.get('email',''),
        request.form.get('subject',''), body), commit=True)
    flash("success:Message sent! We'll get back to you soon.")
    return redirect(url_for('contact'))

@app.route('/submit-review', methods=['POST'])
def submit_review():
    name = request.form.get('name','').strip()
    body = request.form.get('body','').strip()
    if not name or not body:
        flash('error:Please fill in your name and review.')
        return redirect(request.referrer or url_for('index'))
    try: rating = max(1, min(5, int(request.form.get('rating','5'))))
    except: rating = 5
    db_execute("INSERT INTO reviews (name,location,rating,body,approved) VALUES (%s,%s,%s,%s,0)", (
        name, request.form.get('location',''), rating, body), commit=True)
    flash('success:Thank you for your review! It will appear after approval.')
    return redirect(request.referrer or url_for('index'))

# ══════════════════════════════════════════════════
#  ADMIN AUTH
# ══════════════════════════════════════════════════

@app.route('/admin')
@app.route('/admin/')
def admin_login():
    if session.get('admin_id'): return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_do_login():
    email    = request.form.get('email','').strip().lower()
    password = request.form.get('password','')
    user, _  = db_execute("SELECT * FROM admin_users WHERE email=%s", (email,), fetchone=True)
    if user and check_password_hash(user['password'], password):
        session['admin_id']   = user['id']
        session['admin_name'] = user['full_name']
        session.permanent     = True
        return redirect(url_for('admin_dashboard'))
    flash('error:Incorrect email or password.')
    return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/signup', methods=['GET','POST'])
def admin_signup():
    if not session.get('admin_id'):
        flash('error:You must be logged in to create an admin account.')
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        email     = request.form.get('email','').strip().lower()
        password  = request.form.get('password','')
        confirm   = request.form.get('confirm_password','')
        if not full_name or not email or not password:
            flash('error:All fields are required.'); return redirect(url_for('admin_signup'))
        if password != confirm:
            flash('error:Passwords do not match.'); return redirect(url_for('admin_signup'))
        if len(password) < 6:
            flash('error:Password must be at least 6 characters.'); return redirect(url_for('admin_signup'))
        existing, _ = db_execute("SELECT id FROM admin_users WHERE email=%s", (email,), fetchone=True)
        if existing:
            flash('error:An account with that email already exists.'); return redirect(url_for('admin_signup'))
        db_execute("INSERT INTO admin_users (full_name,email,password,role) VALUES (%s,%s,%s,%s)",
                   (full_name, email, generate_password_hash(password), 'admin'), commit=True)
        flash('success:Admin account created successfully!')
        return redirect(url_for('admin_users'))
    return render_template('admin/signup.html')

@app.route('/admin/forgot-password', methods=['GET','POST'])
def admin_forgot_password():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        user, _ = db_execute("SELECT * FROM admin_users WHERE email=%s", (email,), fetchone=True)
        if user:
            token = secrets.token_urlsafe(32)
            db_execute("UPDATE admin_users SET reset_token=%s WHERE email=%s", (token, email), commit=True)
            reset_url = url_for('admin_reset_password', token=token, _external=True)
            flash(f'success:Password reset link: {reset_url}')
        else:
            flash('error:No account found with that email address.')
        return redirect(url_for('admin_forgot_password'))
    return render_template('admin/forgot_password.html')

@app.route('/admin/reset-password/<token>', methods=['GET','POST'])
def admin_reset_password(token):
    user, _ = db_execute("SELECT * FROM admin_users WHERE reset_token=%s", (token,), fetchone=True)
    if not user:
        flash('error:Invalid or expired reset link.')
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        pw = request.form.get('password','')
        if pw != request.form.get('confirm_password',''):
            flash('error:Passwords do not match.'); return redirect(request.url)
        if len(pw) < 6:
            flash('error:Password must be at least 6 characters.'); return redirect(request.url)
        db_execute("UPDATE admin_users SET password=%s, reset_token=NULL WHERE id=%s",
                   (generate_password_hash(pw), user['id']), commit=True)
        flash('success:Password reset successfully! Please log in.')
        return redirect(url_for('admin_login'))
    return render_template('admin/reset_password.html', token=token)

# ══════════════════════════════════════════════════
#  ADMIN PAGES
# ══════════════════════════════════════════════════

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    def count(sql): r, _ = db_execute(sql, fetchone=True); return r['count'] if r else 0
    stats = {
        'total':    count("SELECT COUNT(*) FROM listings"),
        'active':   count("SELECT COUNT(*) FROM listings WHERE status='available'"),
        'requests': count("SELECT COUNT(*) FROM property_requests"),
        'messages': count("SELECT COUNT(*) FROM messages"),
        'reviews':  count("SELECT COUNT(*) FROM reviews WHERE approved=0"),
        'admins':   count("SELECT COUNT(*) FROM admin_users"),
    }
    recent, _ = db_execute("SELECT * FROM property_requests ORDER BY created_at DESC LIMIT 5", fetchall=True)
    return render_template('admin/dashboard.html', stats=stats, recent_requests=recent or [], agent=get_agent())

@app.route('/admin/listings')
@admin_required
def admin_listings():
    rows, _ = db_execute("SELECT * FROM listings ORDER BY created_at DESC", fetchall=True)
    return render_template('admin/listings.html',
        listings=[listing_to_dict(r) for r in (rows or [])], agent=get_agent())

@app.route('/admin/listings/new', methods=['GET','POST'])
@admin_required
def admin_listing_new():
    if request.method == 'POST': return _save_listing(None)
    return render_template('admin/listing_form.html', listing=None, agent=get_agent())

@app.route('/admin/listings/<int:id>/edit', methods=['GET','POST'])
@admin_required
def admin_listing_edit(id):
    row, _ = db_execute("SELECT * FROM listings WHERE id=%s", (id,), fetchone=True)
    if not row: flash('error:Listing not found.'); return redirect(url_for('admin_listings'))
    if request.method == 'POST': return _save_listing(id)
    return render_template('admin/listing_form.html', listing=listing_to_dict(row), agent=get_agent())

def _save_listing(listing_id):
    data = {
        'type':        request.form.get('type','house'),
        'title':       request.form.get('title','').strip(),
        'description': request.form.get('description','').strip(),
        'price':       request.form.get('price','').strip(),
        'location':    request.form.get('location','').strip(),
        'bedrooms':    request.form.get('bedrooms') or None,
        'bathrooms':   request.form.get('bathrooms') or None,
        'size':        request.form.get('size','').strip(),
        'land_use':    request.form.get('land_use','').strip(),
        'land_docs':   request.form.get('land_docs','').strip(),
        'status':      request.form.get('status','available'),
        'featured':    1 if request.form.get('featured') else 0,
    }
    if not data['title'] or not data['price']:
        flash('error:Title and price are required.'); return redirect(request.url)

    if listing_id:
        db_execute("""UPDATE listings SET type=%(type)s,title=%(title)s,description=%(description)s,
            price=%(price)s,location=%(location)s,bedrooms=%(bedrooms)s,bathrooms=%(bathrooms)s,
            size=%(size)s,land_use=%(land_use)s,land_docs=%(land_docs)s,status=%(status)s,
            featured=%(featured)s WHERE id=%(id)s""",
            {**data, 'id': listing_id})
    else:
        row, cur = db_execute("""INSERT INTO listings (type,title,description,price,location,
            bedrooms,bathrooms,size,land_use,land_docs,status,featured)
            VALUES (%(type)s,%(title)s,%(description)s,%(price)s,%(location)s,
            %(bedrooms)s,%(bathrooms)s,%(size)s,%(land_use)s,%(land_docs)s,%(status)s,%(featured)s)
            RETURNING id""", data, fetchone=True)
        listing_id = row['id']

    order_row, _ = db_execute("SELECT COUNT(*) FROM listing_images WHERE listing_id=%s", (listing_id,), fetchone=True)
    order = order_row['count'] if order_row else 0

    for f in request.files.getlist('images'):
        if f and f.filename and allowed_file(f.filename):
            ext   = f.filename.rsplit('.', 1)[1].lower()
            fname = f"{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            db_execute("INSERT INTO listing_images (listing_id,filename,sort_order) VALUES (%s,%s,%s)",
                       (listing_id, fname, order))
            order += 1

    for img_id in request.form.getlist('remove_image'):
        img_row, _ = db_execute("SELECT filename FROM listing_images WHERE id=%s", (img_id,), fetchone=True)
        if img_row:
            try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img_row['filename']))
            except: pass
            db_execute("DELETE FROM listing_images WHERE id=%s", (img_id,))

    db_commit()
    flash('success:Listing saved!')
    return redirect(url_for('admin_listings'))

@app.route('/admin/listings/<int:id>/delete', methods=['POST'])
@admin_required
def admin_listing_delete(id):
    imgs, _ = db_execute("SELECT filename FROM listing_images WHERE listing_id=%s", (id,), fetchall=True)
    for img in (imgs or []):
        try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img['filename']))
        except: pass
    db_execute("DELETE FROM listings WHERE id=%s", (id,), commit=True)
    flash('success:Listing deleted.')
    return redirect(url_for('admin_listings'))

@app.route('/admin/requests')
@admin_required
def admin_requests():
    rows, _ = db_execute("SELECT * FROM property_requests ORDER BY created_at DESC", fetchall=True)
    return render_template('admin/requests.html', requests=rows or [], agent=get_agent())

@app.route('/admin/requests/<int:id>/reply', methods=['POST'])
@admin_required
def admin_request_reply(id):
    db_execute("UPDATE property_requests SET admin_reply=%s WHERE id=%s",
               (request.form.get('reply',''), id), commit=True)
    flash('success:Reply saved.')
    return redirect(url_for('admin_requests'))

@app.route('/admin/requests/<int:id>/delete', methods=['POST'])
@admin_required
def admin_request_delete(id):
    db_execute("DELETE FROM property_requests WHERE id=%s", (id,), commit=True)
    flash('success:Request deleted.')
    return redirect(url_for('admin_requests'))

@app.route('/admin/messages')
@admin_required
def admin_messages():
    rows, _ = db_execute("SELECT * FROM messages ORDER BY created_at DESC", fetchall=True)
    return render_template('admin/messages.html', messages=rows or [], agent=get_agent())

@app.route('/admin/messages/<int:id>/reply', methods=['POST'])
@admin_required
def admin_message_reply(id):
    db_execute("UPDATE messages SET admin_reply=%s WHERE id=%s",
               (request.form.get('reply',''), id), commit=True)
    flash('success:Reply saved.')
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/<int:id>/delete', methods=['POST'])
@admin_required
def admin_message_delete(id):
    db_execute("DELETE FROM messages WHERE id=%s", (id,), commit=True)
    flash('success:Message deleted.')
    return redirect(url_for('admin_messages'))

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    rows, _ = db_execute("SELECT * FROM reviews ORDER BY approved ASC, created_at DESC", fetchall=True)
    return render_template('admin/reviews.html', reviews=rows or [], agent=get_agent())

@app.route('/admin/reviews/<int:id>/approve', methods=['POST'])
@admin_required
def admin_review_approve(id):
    db_execute("UPDATE reviews SET approved=1 WHERE id=%s", (id,), commit=True)
    flash('success:Review approved and is now live.')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:id>/delete', methods=['POST'])
@admin_required
def admin_review_delete(id):
    db_execute("DELETE FROM reviews WHERE id=%s", (id,), commit=True)
    flash('success:Review deleted.')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/users')
@admin_required
def admin_users():
    users, _ = db_execute("SELECT * FROM admin_users ORDER BY created_at DESC", fetchall=True)
    return render_template('admin/users.html', users=users or [], agent=get_agent())

@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@admin_required
def admin_user_delete(id):
    if id == session.get('admin_id'):
        flash('error:You cannot delete your own account.')
    else:
        db_execute("DELETE FROM admin_users WHERE id=%s", (id,), commit=True)
        flash('success:Admin user deleted.')
    return redirect(url_for('admin_users'))

@app.route('/admin/settings', methods=['GET','POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        for f in ['agent_name','agent_phone','agent_email','agent_wa','agent_bio','business_name']:
            db_execute("INSERT INTO settings (key,value) VALUES (%s,%s) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
                       (f, request.form.get(f,'').strip()))
        new_pw = request.form.get('new_password','').strip()
        if new_pw:
            if len(new_pw) < 6:
                flash('error:Password must be at least 6 characters.')
                return redirect(url_for('admin_settings'))
            db_execute("UPDATE admin_users SET password=%s WHERE id=%s",
                       (generate_password_hash(new_pw), session['admin_id']))
        db_commit()
        flash('success:Settings saved!')
        return redirect(url_for('admin_settings'))
    return render_template('admin/settings.html', agent=get_agent(), current_admin=get_current_admin())

if __name__ == '__main__':
    init_db()
    print("🏠 LandMark Realty — http://localhost:5000")
    print("🔐 Admin — http://localhost:5000/admin")
    print("📧 Login: iisaacteye@gmail.com / agent2024")
    app.run(debug=True, port=5000)
