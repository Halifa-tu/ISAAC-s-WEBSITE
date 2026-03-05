# LandMark Realty — Flask + SQLite

A full real estate website with a Python Flask backend and SQLite database.
All data (listings, photos, requests, messages) is stored permanently in `landmark.db`.

---

## ⚡ Quick Start (5 steps)

### 1. Install Python
Download from https://python.org — version 3.9 or newer.
During install on Windows, tick **"Add Python to PATH"**.

### 2. Open a terminal in this folder
- **Windows**: Right-click the folder → "Open in Terminal" (or open Command Prompt and `cd` to the folder)
- **Mac/Linux**: Open Terminal and `cd` to the folder

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Run the app
```
python app.py
```
## /c/Users/yakubuha/AppData/Roaming/uv/python/cpython-3.12-windows-x86_64-none/python.exe app.py
### 5. Open in browser
- **Website**: http://localhost:5000
- **Admin panel**: http://localhost:5000/admin

Default admin login: `admin` / `agent2024`
**Change this in Admin → Settings after your first login.**

---



## 🖥️ Hosting Options (to go live)

Since this is a Python app, you cannot host it on Vercel (Vercel is for Node.js/static sites).

### Option A — Render (Free tier, recommended)
1. Push this folder to a GitHub repository
2. Go to https://render.com and create a free account
3. Click "New Web Service" → connect your GitHub repo
4. Set:
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `gunicorn app:app`
5. Add to requirements.txt: `gunicorn>=21.0.0`

> ⚠️ Render's free tier resets the disk on each deploy. For permanent file storage on Render, use their "Disk" add-on ($1/month) or move images to Cloudinary (free).

### Option B — PythonAnywhere (Free tier, easiest)
1. Create free account at https://pythonanywhere.com
2. Go to "Files" and upload this entire folder
3. Go to "Web" → "Add a new web app" → Flask
4. Set the source code path to your folder
5. Your site will be live at `yourusername.pythonanywhere.com`
   PythonAnywhere persists the SQLite database and uploads permanently on their free tier.

### Option C — VPS (DigitalOcean, Hetzner, etc.)
Run on any Linux server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🔒 Security Notes for Production

1. **Change the secret key** in `app.py`:
   ```python
   app.secret_key = 'your-very-long-random-secret-key-here'
   ```
   Or set it as an environment variable: `SECRET_KEY=...`

2. **Change admin password** via Admin → Settings after first login.

3. **Back up your database** regularly — just copy `landmark.db`.

4. **Back up uploads** — copy the `static/uploads/` folder.

---

## 🗄️ Database

The database (`landmark.db`) is created automatically on first run.
It contains:
- `listings` — all property listings
- `listing_images` — photos linked to listings
- `property_requests` — requests submitted by visitors
- `messages` — contact form messages
- `settings` — agent info and admin credentials

To reset to factory defaults, delete `landmark.db` and restart the app.
