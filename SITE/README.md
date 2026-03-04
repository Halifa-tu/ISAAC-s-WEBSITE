# Hali-Tech Website

A full business website with admin portal built with Python (Flask) + Bootstrap.

## Setup

```bash
pip install flask
python app.py
```
## /c/Users/yakubuha/AppData/Roaming/uv/python/cpython-3.12-windows-x86_64-none/python.exe app.py
Then open: http://localhost:5000

## Admin Portal

URL: http://localhost:5000/admin/login
Username: admin
Password: Wiltord@@1234

⚠️ Change the password in app.py before going live!

## Admin Features
- Post blog posts, announcements, and service updates
- View all customer enquiries with urgency level
- Reply via WhatsApp or email directly from the dashboard
- Mark enquiries as read / delete them

## Contact Form
- Customer fills in name, email, phone, service, urgency, message
- Saved to SQLite database (halitech.db)
- A WhatsApp link auto-opens so you can reply instantly
- Enquiries appear in admin dashboard

## To go live
1. Change ADMIN_PASSWORD in app.py
2. Change app.secret_key to something random
3. Deploy on any Python host (PythonAnywhere, Railway, Render)
