from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3, os, json
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'halitech-secret-2025-change-in-production'

DB = 'halitech.db'

# ── Config (edit these) ──────────────────────────────────────────────
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'Wiltord@@1234'   # Change this!
WHATSAPP_NUMBER = '233507094316'  # Your WhatsApp number
CONTACT_EMAIL   = 'halitechfix@gmail.com'
# ─────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,         -- 'blog', 'service_update', 'announcement'
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT,
            published INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, email TEXT,
            service TEXT, urgency TEXT, message TEXT,
            read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    ''')
    # Seed sample data if empty
    count = db.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    if count == 0:
        db.executemany('INSERT INTO posts (type,title,content,summary) VALUES (?,?,?,?)', [
            ('announcement', 'Welcome to the New Hali-Tech Website!',
             'We have launched our brand-new website. You can now browse all our services, check pricing, and contact us directly online. We are excited to serve you better!',
             'Our new website is live — browse services and get in touch easily.'),
            ('blog', 'Why Regular PC Maintenance Matters',
             'Most people only think about their computer when something goes wrong. But regular maintenance — clearing junk files, updating drivers, scanning for viruses — keeps your PC running fast and prevents bigger problems down the line. Aim for a checkup every 3–6 months.',
             'Keep your PC healthy with regular maintenance. Here\'s why it matters.'),
            ('service_update', 'Remote Support Now Available 24/7',
             'We have expanded our remote support hours. You can now reach us any time of day for urgent software issues, virus removal, and troubleshooting — no need to leave your home.',
             'Remote support is now available around the clock for urgent issues.'),
        ])
        db.commit()
    db.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated

# ── Public API ────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/posts')
def api_posts():
    ptype = request.args.get('type')
    db = get_db()
    if ptype:
        rows = db.execute('SELECT * FROM posts WHERE published=1 AND type=? ORDER BY created_at DESC LIMIT 10', (ptype,)).fetchall()
    else:
        rows = db.execute('SELECT * FROM posts WHERE published=1 ORDER BY created_at DESC LIMIT 20').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/contact', methods=['POST'])
def api_contact():
    d = request.get_json()
    name    = d.get('name','').strip()
    phone   = d.get('phone','').strip()
    email   = d.get('email','').strip()
    service = d.get('service','').strip()
    urgency = d.get('urgency','').strip()
    message = d.get('message','').strip()

    if not all([name, email, service, urgency, message]):
        return jsonify({'success': False, 'error': 'Please fill in all required fields.'})

    # Save to DB
    db = get_db()
    db.execute('INSERT INTO enquiries (name,phone,email,service,urgency,message) VALUES (?,?,?,?,?,?)',
               (name, phone, email, service, urgency, message))
    db.commit()
    db.close()

    # Build WhatsApp message link (opens wa.me with pre-filled text)
    wa_text = f"New Hali-Tech Enquiry!\nName: {name}\nPhone: {phone}\nEmail: {email}\nService: {service}\nUrgency: {urgency}\nMessage: {message}"
    wa_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={wa_text.replace(' ','%20').replace('\n','%0A')}"

    print(f"\n📩 New Enquiry — {name} | {service} | {urgency}")
    print(f"   Email: {email} | Phone: {phone}")
    print(f"   Message: {message}")
    print(f"   WhatsApp: {wa_link}\n")

    return jsonify({'success': True, 'message': f"Thanks {name}! We'll be in touch very soon.", 'wa_link': wa_link})

# ── Admin ─────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        u = request.form.get('username','')
        p = request.form.get('password','')
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        error = 'Incorrect username or password.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin/login')

@app.route('/admin')
@login_required
def admin_dashboard():
    db = get_db()
    posts      = db.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    enquiries  = db.execute('SELECT * FROM enquiries ORDER BY created_at DESC').fetchall()
    unread     = db.execute('SELECT COUNT(*) FROM enquiries WHERE read=0').fetchone()[0]
    db.close()
    return render_template('admin.html', posts=posts, enquiries=enquiries, unread=unread)

@app.route('/admin/post/new', methods=['GET','POST'])
@login_required
def admin_new_post():
    if request.method == 'POST':
        db = get_db()
        db.execute('INSERT INTO posts (type,title,content,summary,published) VALUES (?,?,?,?,?)',
                   (request.form['type'], request.form['title'],
                    request.form['content'], request.form.get('summary',''),
                    1 if request.form.get('published') else 0))
        db.commit()
        db.close()
        return redirect('/admin')
    return render_template('admin_post_form.html', post=None, action='New')

@app.route('/admin/post/edit/<int:pid>', methods=['GET','POST'])
@login_required
def admin_edit_post(pid):
    db = get_db()
    if request.method == 'POST':
        db.execute('UPDATE posts SET type=?,title=?,content=?,summary=?,published=?,updated_at=datetime("now") WHERE id=?',
                   (request.form['type'], request.form['title'],
                    request.form['content'], request.form.get('summary',''),
                    1 if request.form.get('published') else 0, pid))
        db.commit()
        db.close()
        return redirect('/admin')
    post = db.execute('SELECT * FROM posts WHERE id=?', (pid,)).fetchone()
    db.close()
    return render_template('admin_post_form.html', post=post, action='Edit')

@app.route('/admin/post/delete/<int:pid>', methods=['POST'])
@login_required
def admin_delete_post(pid):
    db = get_db()
    db.execute('DELETE FROM posts WHERE id=?', (pid,))
    db.commit()
    db.close()
    return redirect('/admin')

@app.route('/admin/enquiry/read/<int:eid>', methods=['POST'])
@login_required
def admin_mark_read(eid):
    db = get_db()
    db.execute('UPDATE enquiries SET read=1 WHERE id=?', (eid,))
    db.commit()
    db.close()
    return redirect('/admin#enquiries')

@app.route('/admin/enquiry/delete/<int:eid>', methods=['POST'])
@login_required
def admin_delete_enquiry(eid):
    db = get_db()
    db.execute('DELETE FROM enquiries WHERE id=?', (eid,))
    db.commit()
    db.close()
    return redirect('/admin#enquiries')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
