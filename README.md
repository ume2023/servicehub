# ServiceHub — Support Tickets + Product Store

A starter web app (also installable on phones as a PWA) with two modules:

- **Support tickets** — customers report problems, your team resolves them
- **Product store** — browse products, add to cart, place orders

Built with Python (Flask) so you can run and extend it with the skills you already have.

## 1. Setup

```bash
cd servicehub
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Create the database and demo data

```bash
export FLASK_APP=app.py         # Windows: set FLASK_APP=app.py
flask seed
```

This creates `servicehub.db` (SQLite) with 4 demo products and a staff login:
- **Staff email:** staff@servicehub.test
- **Staff password:** staffpass123

Staff accounts can see and update every ticket. Regular accounts only see their own.

## 3. Run it

```bash
python3 app.py
```

Visit **http://localhost:5000** in your browser. To test on your phone, make sure your phone is on the same WiFi as your computer, find your computer's local IP (e.g. `192.168.1.x`), and visit `http://192.168.1.x:5000` from your phone's browser.

## 4. Install it as a "mobile app"

On your phone, open the site in Chrome (Android) or Safari (iOS) and choose **"Add to Home Screen"**. It'll behave like an installed app — its own icon, full-screen, no browser bar. This is powered by the `manifest.json` and `sw.js` files in `static/`.

## What's included

```
servicehub/
├── app.py                 # All routes + database models
├── requirements.txt
├── static/
│   ├── css/style.css      # All styling
│   ├── manifest.json      # PWA config (name, icons, colors)
│   ├── sw.js               # Service worker (enables "installability")
│   └── icons/              # App icons
└── templates/              # All pages (Jinja2/HTML)
```

## How to extend it

- **Add products**: easiest via a Python shell:
  ```python
  from app import app, db, Product
  with app.app_context():
      db.session.add(Product(name="New Item", description="...", price=999, stock=10))
      db.session.commit()
  ```
- **Payments**: this starter creates orders as "pending" — plug in Razorpay/Stripe in the `checkout()` route in `app.py` before marking an order "paid".
- **Email notifications**: use `Flask-Mail` to notify customers when a ticket status changes, or notify staff when a new ticket comes in.
- **Deploy it**: for a company-facing app, deploy to a host like Render, Railway, or PythonAnywhere, and switch `SQLALCHEMY_DATABASE_URI` from SQLite to Postgres for production use.
- **True native mobile app later**: if you eventually want an app in the App Store/Play Store (not just "Add to Home Screen"), this same Flask app can serve as the backend API for a React Native or Flutter app — you wouldn't need to rewrite the logic, just add API endpoints that return JSON instead of HTML.

## Notes

- `app.config['SECRET_KEY']` — change this before putting the app anywhere public.
- Passwords are hashed with Werkzeug's `generate_password_hash` — never stored in plain text.
- This is a starting point, not a production-hardened app: add input validation, rate limiting, and HTTPS before going live with real customers.
