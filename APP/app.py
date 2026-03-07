"""
LandMark Realty — Flask + SQLite Backend
Run:  python app.py
Open: http://localhost:5000
Admin: http://localhost:5000/admin  (iisaacteye@gmail.com / agent2024)
"""

import os, sqlite3, uuid, secrets
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, g, flash)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'landmark-secret-change-in-production')

DATABASE      = 'landmark.db'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXT   = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Database ──────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
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
        CREATE TABLE IF NOT EXISTS admin_users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            password    TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'admin',
            reset_token TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS listings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
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
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS listing_images (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
            filename   TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS property_requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
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
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            phone       TEXT,
            email       TEXT,
            subject     TEXT,
            body        TEXT NOT NULL,
            admin_reply TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            location   TEXT,
            rating     INTEGER NOT NULL DEFAULT 5,
            body       TEXT NOT NULL,
            approved   INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    defaults = {
        'agent_name':    'Isaac Teye',
        'agent_phone':   '0249315662',
        'agent_email':   'iisaacteye@gmail.com',
        'agent_wa':      '233249315662',
        'agent_bio':     'With years of experience in Ghana\'s real estate market, we help families, professionals, and investors find the right property at the right price.',
        'business_name': 'LandMark Realty',
    }
    for k, v in defaults.items():
        db.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (k, v))

    if db.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0] == 0:
        db.execute("INSERT INTO admin_users (full_name,email,password,role) VALUES (?,?,?,?)", (
            'Isaac Teye', 'iisaacteye@gmail.com',
            generate_password_hash('agent2024'), 'superadmin'))

    if db.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 0:
        for s in [
            ('house','Elegant 4-Bedroom Family Home','Spacious modern home with open-plan living, fitted kitchen, master en-suite, and a large garden.','GHS 850,000','East Legon, Accra',4,3,'320 sqm',None,None,'available',1),
            ('room','Self-Contained Studio Room','Neat tiled self-contained room with private bath, kitchenette, and 24/7 water and electricity.','GHS 1,200/mo','Tema, Community 25',1,1,'45 sqm',None,None,'available',0),
            ('land','Prime Residential Plot','Fenced, gated 1-acre plot with Indenture, Site Plan, and Land Search Report.','GHS 400,000','Kasoa, Central Region',None,None,'1 acre','Residential','Indenture, Site Plan','available',1),
            ('house','Modern 3-Bedroom Townhouse','Newly built townhouse with solar panels, CCTV security, covered parking.','GHS 620,000','Tema, Community 18',3,2,'220 sqm',None,None,'available',0),
            ('room','Furnished 2-Bedroom Apartment','Fully furnished apartment with AC, washing machine, DSTV, and WiFi.','GHS 4,500/mo','Airport Residential, Accra',2,2,'90 sqm',None,None,'available',1),
            ('land','Commercial Land — Main Road','Half-acre commercial land on a busy road. Ideal for shops, offices, or mixed-use development.','GHS 750,000','Spintex Road, Accra',None,None,'0.5 acre','Commercial','Indenture','available',0),
        ]:
            db.execute("INSERT INTO listings (type,title,description,price,location,bedrooms,bathrooms,size,land_use,land_docs,status,featured) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", s)

    if db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0:
        for r in [
            ('Kwame Acheampong','Homebuyer, Accra',5,'Found my dream home in East Legon within 2 weeks. Professional, responsive, and genuinely helpful.'),
            ('Abena Boateng','Business Owner, Kumasi',5,'Submitted a request and had 3 perfect options within days. Exceptional service!'),
            ('Emmanuel Owusu','Investor, Tema',5,'Bought a plot in Kasoa with all documents intact. Fast, transparent, and stress-free.'),
        ]:
            db.execute("INSERT INTO reviews (name,location,rating,body,approved) VALUES (?,?,?,?,1)", r)

    db.commit()
    db.close()
    print("✅ Database initialised:", DATABASE)

# ── Helpers ───────────────────────────────────────
def get_setting(key, default=''):
    row = get_db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
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
    imgs = get_db().execute(
        "SELECT filename FROM listing_images WHERE listing_id=? ORDER BY sort_order", (d['id'],)
    ).fetchall()
    d['images'] = [r['filename'] for r in imgs]
    return d

def fmt_dt(dt_str):
    try: return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y, %I:%M %p')
    except: return dt_str or ''

app.jinja_env.globals['fmt_dt'] = fmt_dt

def get_current_admin():
    if not session.get('admin_id'): return None
    return get_db().execute("SELECT * FROM admin_users WHERE id=?", (session['admin_id'],)).fetchone()

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
    db = get_db()
    featured     = [listing_to_dict(r) for r in db.execute("SELECT * FROM listings WHERE featured=1 AND status='available' ORDER BY created_at DESC LIMIT 6").fetchall()]
    total_active = db.execute("SELECT COUNT(*) FROM listings WHERE status='available'").fetchone()[0]
    reviews      = db.execute("SELECT * FROM reviews WHERE approved=1 ORDER BY created_at DESC LIMIT 6").fetchall()
    return render_template('index.html', featured=featured, total_active=total_active,
                           agent=get_agent(), reviews=reviews)

@app.route('/properties')
def properties():
    db     = get_db()
    type_f = request.args.get('type','')
    bdg_f  = request.args.get('budget','')
    loc_f  = request.args.get('loc','').strip()
    sort_f = request.args.get('sort','newest')
    q      = "SELECT * FROM listings WHERE status='available'"
    p      = []
    if type_f: q += " AND type=?"; p.append(type_f)
    if loc_f:  q += " AND (location LIKE ? OR title LIKE ?)"; p += [f'%{loc_f}%', f'%{loc_f}%']
    q += " ORDER BY " + ("featured DESC, created_at DESC" if sort_f == 'featured' else "created_at DESC")
    listings = [listing_to_dict(r) for r in db.execute(q, p).fetchall()]
    if bdg_f:
        import re
        def pn(p): m = re.search(r'\d+', p.replace(',','')); return int(m.group()) if m else 0
        if bdg_f == 'low':  listings = [l for l in listings if pn(l['price']) < 200000]
        elif bdg_f == 'mid': listings = [l for l in listings if 200000 <= pn(l['price']) <= 600000]
        elif bdg_f == 'high': listings = [l for l in listings if pn(l['price']) > 600000]
    return render_template('properties.html', listings=listings,
                           filters={'type':type_f,'budget':bdg_f,'loc':loc_f,'sort':sort_f},
                           agent=get_agent())

@app.route('/property/<int:id>')
def property_detail(id):
    row = get_db().execute("SELECT * FROM listings WHERE id=?", (id,)).fetchone()
    if not row: return redirect(url_for('properties'))
    return render_template('property_detail.html', listing=listing_to_dict(row), agent=get_agent())

@app.route('/about')
def about():
    total   = get_db().execute("SELECT COUNT(*) FROM listings WHERE status='available'").fetchone()[0]
    reviews = get_db().execute("SELECT * FROM reviews WHERE approved=1 ORDER BY created_at DESC").fetchall()
    return render_template('about.html', agent=get_agent(), total_active=total, reviews=reviews)

@app.route('/services')
def services():
    return render_template('services.html', agent=get_agent())

@app.route('/contact')
def contact():
    return render_template('contact.html', agent=get_agent())

@app.route('/request', methods=['GET','POST'])
def property_request():
    if request.method == 'POST':
        get_db().execute("""INSERT INTO property_requests
            (name,phone,email,type,location,budget,bedrooms,purpose,urgency,land_size,land_use,land_docs,details)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            request.form.get('name','').strip(), request.form.get('phone','').strip(),
            request.form.get('email',''),        request.form.get('type',''),
            request.form.get('location',''),     request.form.get('budget',''),
            request.form.get('bedrooms',''),     request.form.get('purpose',''),
            request.form.get('urgency',''),      request.form.get('land_size',''),
            request.form.get('land_use',''),     request.form.get('land_docs',''),
            request.form.get('details',''),
        ))
        get_db().commit()
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
    get_db().execute("INSERT INTO messages (name,phone,email,subject,body) VALUES (?,?,?,?,?)", (
        name, request.form.get('phone',''), request.form.get('email',''),
        request.form.get('subject',''), body))
    get_db().commit()
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
    get_db().execute("INSERT INTO reviews (name,location,rating,body,approved) VALUES (?,?,?,?,0)", (
        name, request.form.get('location',''), rating, body))
    get_db().commit()
    flash('success:Thank you for your review!')
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
    user = get_db().execute("SELECT * FROM admin_users WHERE email=?", (email,)).fetchone()
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
        if get_db().execute("SELECT id FROM admin_users WHERE email=?", (email,)).fetchone():
            flash('error:An account with that email already exists.'); return redirect(url_for('admin_signup'))
        get_db().execute("INSERT INTO admin_users (full_name,email,password,role) VALUES (?,?,?,?)",
                         (full_name, email, generate_password_hash(password), 'admin'))
        get_db().commit()
        flash('success:Admin account created successfully!')
        return redirect(url_for('admin_users'))
    return render_template('admin/signup.html')

@app.route('/admin/forgot-password', methods=['GET','POST'])
def admin_forgot_password():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        user  = get_db().execute("SELECT * FROM admin_users WHERE email=?", (email,)).fetchone()
        if user:
            token = secrets.token_urlsafe(32)
            get_db().execute("UPDATE admin_users SET reset_token=? WHERE email=?", (token, email))
            get_db().commit()
            reset_url = url_for('admin_reset_password', token=token, _external=True)
            flash(f'success:Password reset link: {reset_url}')
        else:
            flash('error:No account found with that email address.')
        return redirect(url_for('admin_forgot_password'))
    return render_template('admin/forgot_password.html')

@app.route('/admin/reset-password/<token>', methods=['GET','POST'])
def admin_reset_password(token):
    user = get_db().execute("SELECT * FROM admin_users WHERE reset_token=?", (token,)).fetchone()
    if not user:
        flash('error:Invalid or expired reset link.')
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        pw = request.form.get('password','')
        if pw != request.form.get('confirm_password',''):
            flash('error:Passwords do not match.'); return redirect(request.url)
        if len(pw) < 6:
            flash('error:Password must be at least 6 characters.'); return redirect(request.url)
        get_db().execute("UPDATE admin_users SET password=?, reset_token=NULL WHERE id=?",
                         (generate_password_hash(pw), user['id']))
        get_db().commit()
        flash('success:Password reset successfully! Please log in.')
        return redirect(url_for('admin_login'))
    return render_template('admin/reset_password.html', token=token)

# ══════════════════════════════════════════════════
#  ADMIN PAGES
# ══════════════════════════════════════════════════

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        'total':    db.execute("SELECT COUNT(*) FROM listings").fetchone()[0],
        'active':   db.execute("SELECT COUNT(*) FROM listings WHERE status='available'").fetchone()[0],
        'requests': db.execute("SELECT COUNT(*) FROM property_requests").fetchone()[0],
        'messages': db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        'reviews':  db.execute("SELECT COUNT(*) FROM reviews WHERE approved=0").fetchone()[0],
        'admins':   db.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0],
    }
    recent = db.execute("SELECT * FROM property_requests ORDER BY created_at DESC LIMIT 5").fetchall()
    return render_template('admin/dashboard.html', stats=stats, recent_requests=recent, agent=get_agent())

@app.route('/admin/listings')
@admin_required
def admin_listings():
    rows = get_db().execute("SELECT * FROM listings ORDER BY created_at DESC").fetchall()
    return render_template('admin/listings.html', listings=[listing_to_dict(r) for r in rows], agent=get_agent())

@app.route('/admin/listings/new', methods=['GET','POST'])
@admin_required
def admin_listing_new():
    if request.method == 'POST': return _save_listing(None)
    return render_template('admin/listing_form.html', listing=None, agent=get_agent())

@app.route('/admin/listings/<int:id>/edit', methods=['GET','POST'])
@admin_required
def admin_listing_edit(id):
    row = get_db().execute("SELECT * FROM listings WHERE id=?", (id,)).fetchone()
    if not row: flash('error:Listing not found.'); return redirect(url_for('admin_listings'))
    if request.method == 'POST': return _save_listing(id)
    return render_template('admin/listing_form.html', listing=listing_to_dict(row), agent=get_agent())

def _save_listing(listing_id):
    db   = get_db()
    data = {
        'type': request.form.get('type','house'), 'title': request.form.get('title','').strip(),
        'description': request.form.get('description','').strip(), 'price': request.form.get('price','').strip(),
        'location': request.form.get('location','').strip(), 'bedrooms': request.form.get('bedrooms') or None,
        'bathrooms': request.form.get('bathrooms') or None, 'size': request.form.get('size','').strip(),
        'land_use': request.form.get('land_use','').strip(), 'land_docs': request.form.get('land_docs','').strip(),
        'status': request.form.get('status','available'), 'featured': 1 if request.form.get('featured') else 0,
    }
    if not data['title'] or not data['price']:
        flash('error:Title and price are required.'); return redirect(request.url)
    if listing_id:
        db.execute("""UPDATE listings SET type=:type,title=:title,description=:description,price=:price,
            location=:location,bedrooms=:bedrooms,bathrooms=:bathrooms,size=:size,land_use=:land_use,
            land_docs=:land_docs,status=:status,featured=:featured WHERE id=:id""", {**data,'id':listing_id})
    else:
        cur = db.execute("""INSERT INTO listings (type,title,description,price,location,bedrooms,bathrooms,
            size,land_use,land_docs,status,featured) VALUES (:type,:title,:description,:price,:location,
            :bedrooms,:bathrooms,:size,:land_use,:land_docs,:status,:featured)""", data)
        listing_id = cur.lastrowid
    order = db.execute("SELECT COUNT(*) FROM listing_images WHERE listing_id=?", (listing_id,)).fetchone()[0]
    for f in request.files.getlist('images'):
        if f and f.filename and allowed_file(f.filename):
            ext = f.filename.rsplit('.', 1)[1].lower()
            fname = f"{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            db.execute("INSERT INTO listing_images (listing_id,filename,sort_order) VALUES (?,?,?)", (listing_id,fname,order))
            order += 1
    for img_id in request.form.getlist('remove_image'):
        row = db.execute("SELECT filename FROM listing_images WHERE id=?", (img_id,)).fetchone()
        if row:
            try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], row['filename']))
            except: pass
            db.execute("DELETE FROM listing_images WHERE id=?", (img_id,))
    db.commit()
    flash('success:Listing saved!')
    return redirect(url_for('admin_listings'))

@app.route('/admin/listings/<int:id>/delete', methods=['POST'])
@admin_required
def admin_listing_delete(id):
    db = get_db()
    for img in db.execute("SELECT filename FROM listing_images WHERE listing_id=?", (id,)).fetchall():
        try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img['filename']))
        except: pass
    db.execute("DELETE FROM listings WHERE id=?", (id,))
    db.commit(); flash('success:Listing deleted.')
    return redirect(url_for('admin_listings'))

@app.route('/admin/requests')
@admin_required
def admin_requests():
    rows = get_db().execute("SELECT * FROM property_requests ORDER BY created_at DESC").fetchall()
    return render_template('admin/requests.html', requests=rows, agent=get_agent())

@app.route('/admin/requests/<int:id>/reply', methods=['POST'])
@admin_required
def admin_request_reply(id):
    get_db().execute("UPDATE property_requests SET admin_reply=? WHERE id=?", (request.form.get('reply',''), id))
    get_db().commit(); flash('success:Reply saved.')
    return redirect(url_for('admin_requests'))

@app.route('/admin/requests/<int:id>/delete', methods=['POST'])
@admin_required
def admin_request_delete(id):
    get_db().execute("DELETE FROM property_requests WHERE id=?", (id,))
    get_db().commit(); flash('success:Request deleted.')
    return redirect(url_for('admin_requests'))

@app.route('/admin/messages')
@admin_required
def admin_messages():
    rows = get_db().execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall()
    return render_template('admin/messages.html', messages=rows, agent=get_agent())

@app.route('/admin/messages/<int:id>/reply', methods=['POST'])
@admin_required
def admin_message_reply(id):
    get_db().execute("UPDATE messages SET admin_reply=? WHERE id=?", (request.form.get('reply',''), id))
    get_db().commit(); flash('success:Reply saved.')
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/<int:id>/delete', methods=['POST'])
@admin_required
def admin_message_delete(id):
    get_db().execute("DELETE FROM messages WHERE id=?", (id,))
    get_db().commit(); flash('success:Message deleted.')
    return redirect(url_for('admin_messages'))

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    rows = get_db().execute("SELECT * FROM reviews ORDER BY approved ASC, created_at DESC").fetchall()
    return render_template('admin/reviews.html', reviews=rows, agent=get_agent())

@app.route('/admin/reviews/<int:id>/approve', methods=['POST'])
@admin_required
def admin_review_approve(id):
    get_db().execute("UPDATE reviews SET approved=1 WHERE id=?", (id,))
    get_db().commit(); flash('success:Review approved and is now live.')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:id>/delete', methods=['POST'])
@admin_required
def admin_review_delete(id):
    get_db().execute("DELETE FROM reviews WHERE id=?", (id,))
    get_db().commit(); flash('success:Review deleted.')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = get_db().execute("SELECT * FROM admin_users ORDER BY created_at DESC").fetchall()
    return render_template('admin/users.html', users=users, agent=get_agent())

@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@admin_required
def admin_user_delete(id):
    if id == session.get('admin_id'):
        flash('error:You cannot delete your own account.')
    else:
        get_db().execute("DELETE FROM admin_users WHERE id=?", (id,))
        get_db().commit(); flash('success:Admin user deleted.')
    return redirect(url_for('admin_users'))

@app.route('/admin/settings', methods=['GET','POST'])
@admin_required
def admin_settings():
    db = get_db()
    if request.method == 'POST':
        for f in ['agent_name','agent_phone','agent_email','agent_wa','agent_bio','business_name']:
            db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (f, request.form.get(f,'').strip()))
        new_pw = request.form.get('new_password','').strip()
        if new_pw:
            if len(new_pw) < 6:
                flash('error:Password must be at least 6 characters.'); return redirect(url_for('admin_settings'))
            db.execute("UPDATE admin_users SET password=? WHERE id=?",
                       (generate_password_hash(new_pw), session['admin_id']))
        db.commit(); flash('success:Settings saved!')
        return redirect(url_for('admin_settings'))
    return render_template('admin/settings.html', agent=get_agent(), current_admin=get_current_admin())

if __name__ == '__main__':
    init_db()
    print("🏠 LandMark Realty — http://localhost:5000")
    print("🔐 Admin — http://localhost:5000/admin")
    print("📧 Login: iisaacteye@gmail.com / agent2024")
    app.run(debug=True, port=5000)
