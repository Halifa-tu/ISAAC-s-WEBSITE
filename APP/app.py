"""
LandMark Realty — Flask + Neon (HTTP API, zero dependencies)
"""
import os, uuid, secrets, re, json, base64
from datetime import datetime
from functools import wraps
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from flask import (Flask, render_template, request, redirect,
                   url_for, session, g, flash)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'landmark-secret-2024')

DB_URL        = os.environ.get('DATABASE_URL', 'postgresql://neondb_owner:npg_D2Zuhakv8YNK@ep-damp-darkness-amse7s7j-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require')
# Vercel filesystem is read-only — only /tmp is writable
UPLOAD_FOLDER = "/tmp/uploads"
ALLOWED_EXT   = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError:
    UPLOAD_FOLDER = "/tmp"

# ── Neon HTTP SQL helper ───────────────────────────
def _sql(query, params=None):
    """Send SQL to Neon HTTP endpoint. Returns list of row dicts."""
    parsed   = urlparse(DB_URL)
    host     = parsed.hostname
    user     = parsed.username
    password = parsed.password
    database = parsed.path.lstrip('/')

    # Replace %s with $1, $2 ...
    if params:
        i = [0]
        def _r(_):
            i[0] += 1
            return f'${i[0]}'
        query = re.sub(r'%s', _r, query)

    body = json.dumps({
        "query":  query,
        "params": [None if p is None else str(p) for p in (params or [])]
    }).encode()

    cred = base64.b64encode(f"{user}:{password}".encode()).decode()
    req  = Request(
        f"https://{host}/sql",
        data    = body,
        headers = {
            "Content-Type":           "application/json",
            "Authorization":          f"Basic {cred}",
            "Neon-Connection-String": DB_URL,
        },
        method = "POST"
    )
    with urlopen(req, timeout=20) as r:
        data = json.loads(r.read())

    fields = [f['name'] for f in data.get('fields', [])]
    return [dict(zip(fields, row)) for row in data.get('rows', [])]

def db_all(sql, p=()):  return _sql(sql, p or None)
def db_one(sql, p=()):  rows = _sql(sql, p or None); return rows[0] if rows else None
def db_run(sql, p=()):  _sql(sql, p or None)
def db_val(sql, p=()):
    row = db_one(sql, p)
    return list(row.values())[0] if row else 0

# ── DB init ───────────────────────────────────────
_ready = False
def init_db():
    global _ready
    if _ready: return
    for s in [
        "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)",
        """CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY, full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE, password TEXT NOT NULL,
            role TEXT DEFAULT 'admin', reset_token TEXT,
            created_at TIMESTAMP DEFAULT NOW())""",
        """CREATE TABLE IF NOT EXISTS listings (
            id SERIAL PRIMARY KEY, type TEXT DEFAULT 'house',
            title TEXT NOT NULL, description TEXT, price TEXT,
            location TEXT, bedrooms INTEGER, bathrooms INTEGER,
            size TEXT, land_use TEXT, land_docs TEXT,
            status TEXT DEFAULT 'available', featured INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW())""",
        """CREATE TABLE IF NOT EXISTS listing_images (
            id SERIAL PRIMARY KEY, listing_id INTEGER,
            filename TEXT, sort_order INTEGER DEFAULT 0)""",
        """CREATE TABLE IF NOT EXISTS property_requests (
            id SERIAL PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL,
            email TEXT, type TEXT, location TEXT, budget TEXT,
            bedrooms TEXT, purpose TEXT, urgency TEXT, land_size TEXT,
            land_use TEXT, land_docs TEXT, details TEXT, admin_reply TEXT,
            created_at TIMESTAMP DEFAULT NOW())""",
        """CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY, name TEXT NOT NULL, phone TEXT,
            email TEXT, subject TEXT, body TEXT NOT NULL,
            admin_reply TEXT, created_at TIMESTAMP DEFAULT NOW())""",
        """CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY, name TEXT NOT NULL, location TEXT,
            rating INTEGER DEFAULT 5, body TEXT NOT NULL,
            approved INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT NOW())""",
    ]:
        db_run(s)

    for k, v in {
        'agent_name':'Isaac Teye','agent_phone':'0249315662',
        'agent_email':'iisaacteye@gmail.com','agent_wa':'233249315662',
        'agent_bio':"With years of experience in Ghana's real estate market, I help families, professionals, and investors find the right property at the right price.",
        'business_name':'LandMark Realty',
    }.items():
        db_run("INSERT INTO settings(key,value) VALUES(%s,%s) ON CONFLICT(key) DO NOTHING", (k, v))

    if db_val("SELECT COUNT(*) FROM admin_users") == 0:
        db_run("INSERT INTO admin_users(full_name,email,password,role) VALUES(%s,%s,%s,%s)",
               ('Isaac Teye','iisaacteye@gmail.com',generate_password_hash('agent2024'),'superadmin'))

    if db_val("SELECT COUNT(*) FROM listings") == 0:
        for s in [
            ('house','Elegant 4-Bedroom Family Home','Spacious modern home with open-plan living, fitted kitchen, master en-suite, and a large garden.','GHS 850,000','East Legon, Accra','4','3','320 sqm',None,None,'available','1'),
            ('room','Self-Contained Studio Room','Neat tiled self-contained room with private bath, kitchenette, and 24/7 water and electricity.','GHS 1,200/mo','Tema, Community 25','1','1','45 sqm',None,None,'available','0'),
            ('land','Prime Residential Plot','Fenced, gated 1-acre plot with Indenture, Site Plan, and Land Search Report.','GHS 400,000','Kasoa, Central Region',None,None,'1 acre','Residential','Indenture, Site Plan','available','1'),
            ('house','Modern 3-Bedroom Townhouse','Newly built townhouse with solar panels, CCTV security, covered parking.','GHS 620,000','Tema, Community 18','3','2','220 sqm',None,None,'available','0'),
            ('room','Furnished 2-Bedroom Apartment','Fully furnished apartment with AC, washing machine, DSTV, and WiFi.','GHS 4,500/mo','Airport Residential, Accra','2','2','90 sqm',None,None,'available','1'),
            ('land','Commercial Land — Main Road','Half-acre commercial land on a busy road.','GHS 750,000','Spintex Road, Accra',None,None,'0.5 acre','Commercial','Indenture','available','0'),
        ]:
            db_run("""INSERT INTO listings(type,title,description,price,location,bedrooms,
                bathrooms,size,land_use,land_docs,status,featured)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", s)

    if db_val("SELECT COUNT(*) FROM reviews") == 0:
        for r in [
            ('Kwame Acheampong','Homebuyer, Accra','5','Found my dream home in East Legon within 2 weeks. Professional, responsive, and genuinely helpful.'),
            ('Abena Boateng','Business Owner, Kumasi','5','Submitted a request and had 3 perfect options within days. Exceptional service!'),
            ('Emmanuel Owusu','Investor, Tema','5','Bought a plot in Kasoa with all documents intact. Fast, transparent, and stress-free.'),
        ]:
            db_run("INSERT INTO reviews(name,location,rating,body,approved) VALUES(%s,%s,%s,%s,'1')", r)

    _ready = True

@app.before_request
def ensure_db():
    try: init_db()
    except Exception as e: app.logger.error(f"init_db: {e}")

# ── Helpers ───────────────────────────────────────
def get_setting(k, d=''):
    r = db_one("SELECT value FROM settings WHERE key=%s", (k,))
    return r['value'] if r else d

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
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_EXT

def listing_to_dict(row):
    d = dict(row)
    d['images'] = [{'id':r['id'],'filename':r['filename']}
                   for r in db_all("SELECT id,filename FROM listing_images WHERE listing_id=%s ORDER BY sort_order",(d['id'],))]
    return d

def fmt_dt(v):
    try:
        if isinstance(v, datetime): return v.strftime('%d %b %Y, %I:%M %p')
        return datetime.strptime(str(v)[:19],'%Y-%m-%d %H:%M:%S').strftime('%d %b %Y, %I:%M %p')
    except: return str(v) if v else ''

app.jinja_env.globals['fmt_dt'] = fmt_dt

def get_current_admin():
    if not session.get('admin_id'): return None
    return db_one("SELECT * FROM admin_users WHERE id=%s",(session['admin_id'],))

app.jinja_env.globals['get_current_admin'] = get_current_admin

def admin_required(f):
    @wraps(f)
    def dec(*a,**kw):
        if not session.get('admin_id'): return redirect(url_for('admin_login'))
        return f(*a,**kw)
    return dec

# ══════════════════════════════════════════════════
#  PUBLIC ROUTES
# ══════════════════════════════════════════════════
@app.route('/')
def index():
    featured     = [listing_to_dict(r) for r in db_all("SELECT * FROM listings WHERE featured=1 AND status='available' ORDER BY created_at DESC LIMIT 6")]
    total_active = db_val("SELECT COUNT(*) FROM listings WHERE status='available'")
    reviews      = db_all("SELECT * FROM reviews WHERE approved=1 ORDER BY created_at DESC LIMIT 6")
    return render_template('index.html', featured=featured, total_active=total_active, agent=get_agent(), reviews=reviews)

@app.route('/properties')
def properties():
    type_f=request.args.get('type',''); bdg_f=request.args.get('budget','')
    loc_f=request.args.get('loc','').strip(); sort_f=request.args.get('sort','newest')
    q="SELECT * FROM listings WHERE status='available'"; p=[]
    if type_f: q+=" AND type=%s"; p.append(type_f)
    if loc_f:  q+=" AND (location ILIKE %s OR title ILIKE %s)"; p+=[f'%{loc_f}%',f'%{loc_f}%']
    q+=" ORDER BY "+("featured DESC, created_at DESC" if sort_f=='featured' else "created_at DESC")
    listings=[listing_to_dict(r) for r in db_all(q,p)]
    if bdg_f:
        def pn(pr): m=re.search(r'\d+',pr.replace(',','')); return int(m.group()) if m else 0
        if bdg_f=='low':   listings=[l for l in listings if pn(l['price'])<200000]
        elif bdg_f=='mid': listings=[l for l in listings if 200000<=pn(l['price'])<=600000]
        elif bdg_f=='high':listings=[l for l in listings if pn(l['price'])>600000]
    return render_template('properties.html',listings=listings,
        filters={'type':type_f,'budget':bdg_f,'loc':loc_f,'sort':sort_f},agent=get_agent())

@app.route('/property/<int:id>')
def property_detail(id):
    row=db_one("SELECT * FROM listings WHERE id=%s",(id,))
    if not row: return redirect(url_for('properties'))
    return render_template('property_detail.html',listing=listing_to_dict(row),agent=get_agent())

@app.route('/about')
def about():
    return render_template('about.html',agent=get_agent(),
        total_active=db_val("SELECT COUNT(*) FROM listings WHERE status='available'"),
        reviews=db_all("SELECT * FROM reviews WHERE approved=1 ORDER BY created_at DESC"))

@app.route('/services')
def services(): return render_template('services.html',agent=get_agent())

@app.route('/contact')
def contact(): return render_template('contact.html',agent=get_agent())

@app.route('/request',methods=['GET','POST'])
def property_request():
    if request.method=='POST':
        db_run("""INSERT INTO property_requests(name,phone,email,type,location,budget,bedrooms,
            purpose,urgency,land_size,land_use,land_docs,details)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(
            request.form.get('name','').strip(),request.form.get('phone','').strip(),
            request.form.get('email',''),request.form.get('type',''),
            request.form.get('location',''),request.form.get('budget',''),
            request.form.get('bedrooms',''),request.form.get('purpose',''),
            request.form.get('urgency',''),request.form.get('land_size',''),
            request.form.get('land_use',''),request.form.get('land_docs',''),
            request.form.get('details',''),))
        flash('success:Your request has been submitted! We will contact you within 24 hours.')
        return redirect(url_for('property_request'))
    return render_template('request.html',agent=get_agent())

@app.route('/send-message',methods=['POST'])
def send_message():
    name=request.form.get('name','').strip(); body=request.form.get('body','').strip()
    if not name or not body: flash('error:Please fill in your name and message.'); return redirect(url_for('contact'))
    db_run("INSERT INTO messages(name,phone,email,subject,body) VALUES(%s,%s,%s,%s,%s)",
        (name,request.form.get('phone',''),request.form.get('email',''),request.form.get('subject',''),body))
    flash("success:Message sent! We'll get back to you soon.")
    return redirect(url_for('contact'))

@app.route('/submit-review',methods=['POST'])
def submit_review():
    name=request.form.get('name','').strip(); body=request.form.get('body','').strip()
    if not name or not body: flash('error:Please fill in your name and review.'); return redirect(request.referrer or url_for('index'))
    try: rating=max(1,min(5,int(request.form.get('rating','5'))))
    except: rating=5
    db_run("INSERT INTO reviews(name,location,rating,body,approved) VALUES(%s,%s,%s,%s,'0')",
        (name,request.form.get('location',''),str(rating),body))
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

@app.route('/admin/login',methods=['POST'])
def admin_do_login():
    email=request.form.get('email','').strip().lower(); pw=request.form.get('password','')
    user=db_one("SELECT * FROM admin_users WHERE email=%s",(email,))
    if user and check_password_hash(user['password'],pw):
        session['admin_id']=user['id']; session['admin_name']=user['full_name']
        session.permanent=True; return redirect(url_for('admin_dashboard'))
    flash('error:Incorrect email or password.'); return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout(): session.clear(); return redirect(url_for('admin_login'))

@app.route('/admin/signup',methods=['GET','POST'])
def admin_signup():
    if not session.get('admin_id'): flash('error:Login required.'); return redirect(url_for('admin_login'))
    if request.method=='POST':
        fn=request.form.get('full_name','').strip(); em=request.form.get('email','').strip().lower()
        pw=request.form.get('password',''); cf=request.form.get('confirm_password','')
        if not fn or not em or not pw: flash('error:All fields are required.'); return redirect(url_for('admin_signup'))
        if pw!=cf: flash('error:Passwords do not match.'); return redirect(url_for('admin_signup'))
        if len(pw)<6: flash('error:Password must be at least 6 characters.'); return redirect(url_for('admin_signup'))
        if db_one("SELECT id FROM admin_users WHERE email=%s",(em,)): flash('error:Email already exists.'); return redirect(url_for('admin_signup'))
        db_run("INSERT INTO admin_users(full_name,email,password,role) VALUES(%s,%s,%s,'admin')",(fn,em,generate_password_hash(pw)))
        flash('success:Admin account created!'); return redirect(url_for('admin_users'))
    return render_template('admin/signup.html')

@app.route('/admin/forgot-password',methods=['GET','POST'])
def admin_forgot_password():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower()
        user=db_one("SELECT * FROM admin_users WHERE email=%s",(email,))
        if user:
            token=secrets.token_urlsafe(32)
            db_run("UPDATE admin_users SET reset_token=%s WHERE email=%s",(token,email))
            flash(f"success:Reset link: {url_for('admin_reset_password',token=token,_external=True)}")
        else: flash('error:No account found with that email.')
        return redirect(url_for('admin_forgot_password'))
    return render_template('admin/forgot_password.html')

@app.route('/admin/reset-password/<token>',methods=['GET','POST'])
def admin_reset_password(token):
    user=db_one("SELECT * FROM admin_users WHERE reset_token=%s",(token,))
    if not user: flash('error:Invalid or expired link.'); return redirect(url_for('admin_login'))
    if request.method=='POST':
        pw=request.form.get('password','')
        if pw!=request.form.get('confirm_password',''): flash('error:Passwords do not match.'); return redirect(request.url)
        if len(pw)<6: flash('error:Password must be at least 6 characters.'); return redirect(request.url)
        db_run("UPDATE admin_users SET password=%s, reset_token=NULL WHERE id=%s",(generate_password_hash(pw),user['id']))
        flash('success:Password reset! Please log in.'); return redirect(url_for('admin_login'))
    return render_template('admin/reset_password.html',token=token)

# ══════════════════════════════════════════════════
#  ADMIN PAGES
# ══════════════════════════════════════════════════
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats={
        'total':   db_val("SELECT COUNT(*) FROM listings"),
        'active':  db_val("SELECT COUNT(*) FROM listings WHERE status='available'"),
        'requests':db_val("SELECT COUNT(*) FROM property_requests"),
        'messages':db_val("SELECT COUNT(*) FROM messages"),
        'reviews': db_val("SELECT COUNT(*) FROM reviews WHERE approved=0"),
        'admins':  db_val("SELECT COUNT(*) FROM admin_users"),
    }
    return render_template('admin/dashboard.html',stats=stats,
        recent_requests=db_all("SELECT * FROM property_requests ORDER BY created_at DESC LIMIT 5"),agent=get_agent())

@app.route('/admin/listings')
@admin_required
def admin_listings():
    return render_template('admin/listings.html',
        listings=[listing_to_dict(r) for r in db_all("SELECT * FROM listings ORDER BY created_at DESC")],agent=get_agent())

@app.route('/admin/listings/new',methods=['GET','POST'])
@admin_required
def admin_listing_new():
    if request.method=='POST': return _save_listing(None)
    return render_template('admin/listing_form.html',listing=None,agent=get_agent())

@app.route('/admin/listings/<int:id>/edit',methods=['GET','POST'])
@admin_required
def admin_listing_edit(id):
    row=db_one("SELECT * FROM listings WHERE id=%s",(id,))
    if not row: flash('error:Listing not found.'); return redirect(url_for('admin_listings'))
    if request.method=='POST': return _save_listing(id)
    return render_template('admin/listing_form.html',listing=listing_to_dict(row),agent=get_agent())

def _save_listing(lid):
    t=request.form.get('type','house'); titl=request.form.get('title','').strip()
    desc=request.form.get('description','').strip(); pr=request.form.get('price','').strip()
    loc=request.form.get('location','').strip(); bed=request.form.get('bedrooms') or None
    bath=request.form.get('bathrooms') or None; sz=request.form.get('size','').strip()
    lu=request.form.get('land_use','').strip(); ld=request.form.get('land_docs','').strip()
    st=request.form.get('status','available'); feat='1' if request.form.get('featured') else '0'
    if not titl or not pr: flash('error:Title and price are required.'); return redirect(request.url)
    if lid:
        db_run("""UPDATE listings SET type=%s,title=%s,description=%s,price=%s,location=%s,
            bedrooms=%s,bathrooms=%s,size=%s,land_use=%s,land_docs=%s,status=%s,featured=%s
            WHERE id=%s""",(t,titl,desc,pr,loc,bed,bath,sz,lu,ld,st,feat,str(lid)))
    else:
        row=db_one("""INSERT INTO listings(type,title,description,price,location,bedrooms,
            bathrooms,size,land_use,land_docs,status,featured)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",(t,titl,desc,pr,loc,bed,bath,sz,lu,ld,st,feat))
        lid=row['id']
    order=db_val("SELECT COUNT(*) FROM listing_images WHERE listing_id=%s",(str(lid),))
    for f in request.files.getlist('images'):
        if f and f.filename and allowed_file(f.filename):
            ext=f.filename.rsplit('.',1)[1].lower(); fname=f"{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],fname))
            db_run("INSERT INTO listing_images(listing_id,filename,sort_order) VALUES(%s,%s,%s)",(str(lid),fname,str(order)))
            order+=1
    for img_id in request.form.getlist('remove_image'):
        img=db_one("SELECT filename FROM listing_images WHERE id=%s",(img_id,))
        if img:
            try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'],img['filename']))
            except: pass
            db_run("DELETE FROM listing_images WHERE id=%s",(img_id,))
    flash('success:Listing saved!'); return redirect(url_for('admin_listings'))

@app.route('/admin/listings/<int:id>/delete',methods=['POST'])
@admin_required
def admin_listing_delete(id):
    for img in db_all("SELECT filename FROM listing_images WHERE listing_id=%s",(str(id),)):
        try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'],img['filename']))
        except: pass
    db_run("DELETE FROM listings WHERE id=%s",(str(id),))
    flash('success:Listing deleted.'); return redirect(url_for('admin_listings'))

@app.route('/admin/requests')
@admin_required
def admin_requests():
    return render_template('admin/requests.html',
        requests=db_all("SELECT * FROM property_requests ORDER BY created_at DESC"),agent=get_agent())

@app.route('/admin/requests/<int:id>/reply',methods=['POST'])
@admin_required
def admin_request_reply(id):
    db_run("UPDATE property_requests SET admin_reply=%s WHERE id=%s",(request.form.get('reply',''),str(id)))
    flash('success:Reply saved.'); return redirect(url_for('admin_requests'))

@app.route('/admin/requests/<int:id>/delete',methods=['POST'])
@admin_required
def admin_request_delete(id):
    db_run("DELETE FROM property_requests WHERE id=%s",(str(id),))
    flash('success:Request deleted.'); return redirect(url_for('admin_requests'))

@app.route('/admin/messages')
@admin_required
def admin_messages():
    return render_template('admin/messages.html',
        messages=db_all("SELECT * FROM messages ORDER BY created_at DESC"),agent=get_agent())

@app.route('/admin/messages/<int:id>/reply',methods=['POST'])
@admin_required
def admin_message_reply(id):
    db_run("UPDATE messages SET admin_reply=%s WHERE id=%s",(request.form.get('reply',''),str(id)))
    flash('success:Reply saved.'); return redirect(url_for('admin_messages'))

@app.route('/admin/messages/<int:id>/delete',methods=['POST'])
@admin_required
def admin_message_delete(id):
    db_run("DELETE FROM messages WHERE id=%s",(str(id),))
    flash('success:Message deleted.'); return redirect(url_for('admin_messages'))

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    return render_template('admin/reviews.html',
        reviews=db_all("SELECT * FROM reviews ORDER BY approved ASC, created_at DESC"),agent=get_agent())

@app.route('/admin/reviews/<int:id>/approve',methods=['POST'])
@admin_required
def admin_review_approve(id):
    db_run("UPDATE reviews SET approved=1 WHERE id=%s",(str(id),))
    flash('success:Review approved.'); return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:id>/delete',methods=['POST'])
@admin_required
def admin_review_delete(id):
    db_run("DELETE FROM reviews WHERE id=%s",(str(id),))
    flash('success:Review deleted.'); return redirect(url_for('admin_reviews'))

@app.route('/admin/users')
@admin_required
def admin_users():
    return render_template('admin/users.html',
        users=db_all("SELECT * FROM admin_users ORDER BY created_at DESC"),agent=get_agent())

@app.route('/admin/users/<int:id>/delete',methods=['POST'])
@admin_required
def admin_user_delete(id):
    if id==session.get('admin_id'): flash('error:Cannot delete your own account.')
    else:
        db_run("DELETE FROM admin_users WHERE id=%s",(str(id),))
        flash('success:Admin deleted.')
    return redirect(url_for('admin_users'))

@app.route('/admin/settings',methods=['GET','POST'])
@admin_required
def admin_settings():
    if request.method=='POST':
        for f in ['agent_name','agent_phone','agent_email','agent_wa','agent_bio','business_name']:
            db_run("INSERT INTO settings(key,value) VALUES(%s,%s) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value",
                (f,request.form.get(f,'').strip()))
        pw=request.form.get('new_password','').strip()
        if pw:
            if len(pw)<6: flash('error:Password must be at least 6 characters.'); return redirect(url_for('admin_settings'))
            db_run("UPDATE admin_users SET password=%s WHERE id=%s",(generate_password_hash(pw),str(session['admin_id'])))
        flash('success:Settings saved!'); return redirect(url_for('admin_settings'))
    return render_template('admin/settings.html',agent=get_agent(),current_admin=get_current_admin())

if __name__=='__main__':
    init_db()
    print("🏠 http://localhost:5000  |  Admin: /admin")
    app.run(debug=True,port=5000)
