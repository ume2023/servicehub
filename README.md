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

## Adding your company logo

1. Save your logo as a **PNG file** (transparent background works best)
2. Name it exactly `logo.png`
3. Put it inside: `static/images/logo.png`
4. Refresh your site — it'll automatically replace the placeholder "ServiceHub" text in the top-left

## Adding real product photos

1. Save your product photo (JPG or PNG)
2. Put it inside: `static/images/products/` (e.g. `static/images/products/charger.jpg`)
3. Add the product using the helper script:
   ```
   python add_product.py
   ```
   Open `add_product.py` first and edit the name, description, price, stock, and image filename at the top, then run it. Repeat for each product.

   Alternatively, edit an *existing* product's image directly in a Python shell:
   ```python
   from app import app, db, Product
   with app.app_context():
       p = Product.query.filter_by(name="Wireless Charging Pad").first()
       p.image_url = "/static/images/products/charger.jpg"
       db.session.commit()
   ```

## Setting up payments (Call Support feature)

Your site now has a **paid call support** feature — customers pay, then get a phone number to call. This uses **Razorpay**, India's most common payment gateway (supports UPI, cards, netbanking, wallets — all through one integration).

### Before this works for real money, you need:

1. **A Razorpay account** — sign up free at **https://razorpay.com**
2. **Complete KYC verification** (business details, bank account) — required before you can accept *real* payments. Until then, you can only use **Test Mode** (fake payments, for practicing).
3. **Get your API keys**: Dashboard → Settings → API Keys → Generate Key. You'll get a **Key ID** and **Key Secret**.

### Connecting your keys to the app

Don't paste your keys directly into `app.py` (unsafe, especially once it's on GitHub, which is public). Instead, set them as **environment variables**:

**On your computer (for testing):**
```
$env:RAZORPAY_KEY_ID="your_key_id_here"
$env:RAZORPAY_KEY_SECRET="your_key_secret_here"
```
Run these before `python app.py` — you'll need to do this every time you open a new PowerShell window, or you can add them permanently via Windows System Environment Variables settings.

**On Render (for your live site):**
1. Go to your Web Service on Render → **"Environment"** tab
2. Add two entries: `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` with your real values
3. Save — Render will redeploy automatically

### Also update this line in `app.py`:
```python
SUPPORT_PHONE_NUMBER = "+91-XXXXXXXXXX"
```
Change it to your real support phone number.

### Test it safely first
Use Razorpay's test mode (test API keys, not live ones) and their test card numbers before switching to live keys — see https://razorpay.com/docs/payments/payments/test-card-upi-details/. **Only switch to live keys once you've completed KYC and tested the full flow.**

## Adding calibration videos

1. Upload your calibration video to **YouTube** (set it to "Unlisted" if you don't want it publicly searchable — it'll still work when embedded on your site)
2. On the YouTube video page: **Share → Embed → copy the URL inside `src="..."`** (looks like `https://www.youtube.com/embed/XXXXXXXXXXX`)
3. Open `add_calibration_video.py` in Notepad, fill in the title, description, and that embed URL
4. Run:
   ```
   python add_calibration_video.py
   ```
5. Repeat for each video

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
