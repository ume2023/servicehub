import os
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'servicehub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Razorpay setup (for calibration payments). Set these as environment
# variables before running the app - see README for instructions.
# ---------------------------------------------------------------------------
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

razorpay_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    import razorpay
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

CALIBRATION_BASE_AMOUNT = 1800.00
CALIBRATION_GST_RATE = 0.18
CALIBRATION_GST_AMOUNT = round(CALIBRATION_BASE_AMOUNT * CALIBRATION_GST_RATE, 2)
CALIBRATION_TOTAL_AMOUNT = round(CALIBRATION_BASE_AMOUNT + CALIBRATION_GST_AMOUNT, 2)


def parse_unit_number(unit_number):
    """
    Parses unit numbers like 'D01260132':
      D       -> product/equipment code (any single letter)
      01      -> manufacturing month (2 digits)
      26      -> manufacturing year, 2-digit (2026)
      0132    -> serial number (remaining digits)
    Returns a dict, or None if the format isn't recognized.
    """
    s = (unit_number or '').strip().upper()
    if len(s) < 5 or not s[0].isalpha():
        return None
    digits = s[1:]
    if not digits.isdigit() or len(digits) < 4:
        return None

    month = int(digits[0:2])
    year_2digit = int(digits[2:4])
    serial = digits[4:] or '0000'

    if month < 1 or month > 12:
        return None

    year = 2000 + year_2digit
    try:
        manufacture_date = date(year, month, 1)
    except ValueError:
        return None

    return {
        'prefix': s[0],
        'month': month,
        'year': year,
        'serial': serial,
        'manufacture_date': manufacture_date,
    }


def check_unit_warranty(unit_number):
    parsed = parse_unit_number(unit_number)
    if not parsed:
        return {
            'valid': False,
            'error': "Unit number format not recognized. Expected a format like D01260132.",
        }

    manufacture_date = parsed['manufacture_date']
    warranty_end = date(manufacture_date.year + 1, manufacture_date.month, manufacture_date.day)
    today = date.today()

    return {
        'valid': True,
        'unit_number': unit_number.strip().upper(),
        'manufacture_date': manufacture_date,
        'warranty_end': warranty_end,
        'under_warranty': today <= warranty_end,
    }

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to continue.'


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(400))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(30), default='pending')  # pending, paid, shipped, completed, cancelled
    total = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')
    customer = db.relationship('User')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_at_purchase = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('User')
    replies = db.relationship('TicketReply', backref='ticket', cascade='all, delete-orphan')


class TicketReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
            return redirect(url_for('register'))

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Welcome! Your account has been created.', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

        flash('Invalid email or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Storefront routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    return render_template('index.html', products=products)


@app.route('/products')
def products():
    q = request.args.get('q', '').strip()
    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f'%{q}%'))
    products = query.order_by(Product.created_at.desc()).all()
    return render_template('products.html', products=products, q=q)


@app.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart = session.get('cart', {})
    qty = int(request.form.get('quantity', 1))
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session['cart'] = cart
    flash('Added to cart.', 'success')
    return redirect(request.referrer or url_for('products'))


@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            subtotal = product.price * qty
            total += subtotal
            items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return render_template('cart.html', items=items, total=total)


@app.route('/cart/remove/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('products'))

    order = Order(user_id=current_user.id, status='pending')
    total = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if product:
            item = OrderItem(product_id=product.id, quantity=qty, price_at_purchase=product.price)
            order.items.append(item)
            total += product.price * qty
    order.total = total
    db.session.add(order)
    db.session.commit()
    session['cart'] = {}
    flash('Order placed! We\u2019ll be in touch about payment and delivery.', 'success')
    return redirect(url_for('my_orders'))


@app.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)


# ---------------------------------------------------------------------------
# Staff: order management
# ---------------------------------------------------------------------------

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_staff:
        flash('Staff access only.', 'error')
        return redirect(url_for('index'))
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)


@app.route('/admin/orders/<int:order_id>', methods=['GET', 'POST'])
@login_required
def admin_order_detail(order_id):
    if not current_user.is_staff:
        flash('Staff access only.', 'error')
        return redirect(url_for('index'))
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        order.status = request.form['status']
        db.session.commit()
        flash('Order status updated.', 'success')
        return redirect(url_for('admin_order_detail', order_id=order.id))
    return render_template('admin_order_detail.html', order=order)


# ---------------------------------------------------------------------------
# Support ticket routes
# ---------------------------------------------------------------------------

@app.route('/tickets')
@login_required
def tickets():
    if current_user.is_staff:
        all_tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    else:
        all_tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('tickets.html', tickets=all_tickets)


@app.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    if request.method == 'POST':
        ticket = Ticket(
            user_id=current_user.id,
            subject=request.form['subject'].strip(),
            description=request.form['description'].strip(),
            priority=request.form.get('priority', 'normal'),
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Your ticket has been submitted.', 'success')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))
    return render_template('new_ticket.html')


@app.route('/tickets/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not current_user.is_staff and ticket.user_id != current_user.id:
        flash('You do not have access to that ticket.', 'error')
        return redirect(url_for('tickets'))

    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            reply = TicketReply(ticket_id=ticket.id, user_id=current_user.id, message=message)
            db.session.add(reply)
        if current_user.is_staff and request.form.get('status'):
            ticket.status = request.form['status']
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))

    return render_template('ticket_detail.html', ticket=ticket)


# ---------------------------------------------------------------------------
# Chatbot: auto-reply widget
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Chatbot: auto-reply widget
# ---------------------------------------------------------------------------

CALIBRATION_INFO = [
    # (keywords, title, reply)
    (["length calibration", "length"],
     "Length Calibration",
     "Length calibration checks and adjusts boom length measurement accuracy "
     "on your equipment. Ask us to schedule a technician, or raise a support "
     "ticket with your equipment details and we'll get back to you with pricing."),

    (["angle calibration", "angle"],
     "Angle Calibration",
     "Angle calibration checks and adjusts boom angle sensor accuracy. "
     "Raise a support ticket with your equipment model and location, and "
     "our team will schedule a visit and confirm pricing."),

    (["load calibration", "load"],
     "Load Calibration",
     "Load calibration checks and adjusts the load/pressure sensor readings "
     "for accurate weight measurement. Raise a support ticket with your "
     "equipment details and we'll schedule this for you."),

    (["duty calibration", "duty"],
     "Duty Calibration",
     "Duty calibration checks and adjusts the duty cycle / operating limits "
     "on your equipment. Raise a support ticket with your equipment details "
     "and our team will confirm scheduling and pricing."),

    (["no. of falls calibration", "number of falls", "no of falls", "falls calibration", "falls"],
     "No. of Falls Calibration",
     "No. of falls calibration checks and sets the rope/cable fall count "
     "configuration for accurate load rating. Raise a support ticket with "
     "your equipment details and we'll schedule this for you."),
]

CHATBOT_RULES = [
    # (keywords to look for, reply)
    (["hi", "hello", "hey"],
     "Hi there! \U0001F44B I'm the ServiceHub assistant. I can help with products, "
     "prices, calibration services, orders, tickets, and shipping. What do you need?"),

    (["calibration"],
     "We offer 5 types of calibration: Length, Angle, Load, Duty, and "
     "No. of Falls calibration. Which one do you need? You can also just "
     "type the type directly, e.g. 'load calibration'."),

    (["price", "cost", "how much"],
     "Tell me a product name and I'll look up the price for you, or ask "
     "for 'products list' to see everything we sell with prices."),

    (["order", "my order", "track"],
     "You can check the status of your orders anytime on the "
     "'My Orders' page (you'll need to be logged in)."),

    (["ticket", "support", "problem", "issue", "complaint"],
     "Sorry to hear you're having trouble! You can raise a support ticket "
     "from the 'Tickets' page and our team will get back to you."),

    (["shipping", "delivery", "deliver"],
     "We currently confirm delivery details after you place an order — "
     "our team will reach out with shipping info once your order is placed."),

    (["payment", "pay", "razorpay", "stripe", "upi"],
     "Orders are placed as 'pending' and our team will contact you to "
     "confirm payment details."),

    (["contact", "phone", "email", "reach"],
     "You can reach us by raising a support ticket, and our staff will "
     "respond as soon as possible."),

    (["thanks", "thank you"],
     "You're welcome! Let me know if there's anything else I can help with."),

    (["bye", "goodbye"],
     "Take care! Feel free to chat again anytime."),
]

DEFAULT_REPLY = (
    "I'm not totally sure about that one. You can browse our products page, "
    "ask for a 'products list', ask about calibration services, or raise a "
    "support ticket and our team will help you directly."
)


def products_list_reply() -> str:
    products = Product.query.order_by(Product.name).all()
    if not products:
        return "We don't have any products listed yet — check back soon!"
    lines = [f"{p.name} — \u20b9{p.price:g}" for p in products]
    return "Here's what we have available:\n" + "\n".join(lines)


def chatbot_reply(message: str) -> str:
    text = message.lower()

    # 1. Products list request
    if any(kw in text for kw in ["products list", "all products", "price list", "parts available", "what do you sell"]):
        return products_list_reply()

    # 2. Specific calibration subsection (checked before generic product/keyword match)
    for keywords, title, reply in CALIBRATION_INFO:
        if any(kw in text for kw in keywords):
            return f"{title}: {reply}"

    # 3. Try to match a product name from the database
    products = Product.query.all()
    for product in products:
        if product.name.lower() in text:
            return (
                f"{product.name} — \u20b9{product.price:g}. "
                f"{product.description or ''} "
                f"{'In stock.' if product.stock and product.stock > 0 else 'Currently out of stock.'}"
            ).strip()

    # 4. Try general keyword rules
    for keywords, reply in CHATBOT_RULES:
        if any(kw in text for kw in keywords):
            return reply

    # 5. Fallback
    return DEFAULT_REPLY


@app.route('/api/chatbot', methods=['POST'])
def api_chatbot():
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({"reply": "Say something and I'll try to help!"})
    return jsonify({"reply": chatbot_reply(message)})



# ---------------------------------------------------------------------------
# CLI helper: seed some demo data
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Placeholder routes (temporary — replace with real features one at a time)
# ---------------------------------------------------------------------------

PLACEHOLDER_PAGE = """
<!doctype html>
<html>
<head><title>{title}</title></head>
<body style="font-family: system-ui; text-align: center; padding: 60px;">
  <h1>{title}</h1>
  <p>This page is coming soon.</p>
  <a href="/">← Back to home</a>
</body>
</html>
"""

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_staff:
        flash('Staff access only.', 'error')
        return redirect(url_for('index'))
    return PLACEHOLDER_PAGE.format(title="Manage Products")

@app.route('/calibration')
def calibration():
    return render_template('calibration.html')


@app.route('/calibration/check-warranty', methods=['POST'])
def calibration_check_warranty():
    unit_number = request.form.get('unit_number', '')
    warranty_result = check_unit_warranty(unit_number)
    return render_template('calibration.html', warranty_result=warranty_result, active_tab='under')


@app.route('/calibration/create-order', methods=['POST'])
def calibration_create_order():
    if not razorpay_client:
        return jsonify({"error": "Online payment isn't set up yet. Please raise a support ticket instead."}), 503

    amount_paise = int(CALIBRATION_TOTAL_AMOUNT * 100)
    order = razorpay_client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1,
    })
    return jsonify({
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID,
    })


@app.route('/calibration/verify-payment', methods=['POST'])
def calibration_verify_payment():
    if not razorpay_client:
        return jsonify({"status": "failed", "message": "Online payment isn't set up yet."}), 503

    data = request.get_json(silent=True) or {}
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature'),
        })
        return jsonify({
            "status": "success",
            "message": "Payment received! Our team will contact you to schedule your calibration.",
        })
    except Exception:
        return jsonify({"status": "failed", "message": "Payment verification failed. Please contact support."}), 400

@app.route('/call-support')
def call_support():
    return PLACEHOLDER_PAGE.format(title="Call Support")

@app.route('/check-warranty')
def check_warranty():
    return PLACEHOLDER_PAGE.format(title="Check Warranty")

@app.route('/call-support/create-order', methods=['POST'])
def create_call_support_order():
    return PLACEHOLDER_PAGE.format(title="Call Support Order")

@app.route('/call-support/verify-payment', methods=['POST'])
def verify_call_support_payment():
    return PLACEHOLDER_PAGE.format(title="Payment Verification")


@app.cli.command('seed')
def seed():
    """Populate the database with demo products and a staff account."""
    db.create_all()
    if not User.query.filter_by(email='staff@servicehub.test').first():
        staff = User(name='Support Staff', email='staff@servicehub.test', is_staff=True)
        staff.set_password('staffpass123')
        db.session.add(staff)

    if Product.query.count() == 0:
        demo_products = [
            Product(name='Wireless Charging Pad', description='Fast 15W wireless charger.', price=1499, stock=40),
            Product(name='USB-C Hub (7-in-1)', description='HDMI, USB 3.0, SD card and more.', price=2299, stock=25),
            Product(name='Noise Cancelling Earbuds', description='20-hour battery, ANC.', price=3999, stock=15),
            Product(name='Laptop Stand (Aluminium)', description='Adjustable, foldable stand.', price=1899, stock=30),
        ]
        db.session.add_all(demo_products)

    db.session.commit()
    print('Seed complete. Staff login: staff@servicehub.test / staffpass123')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
