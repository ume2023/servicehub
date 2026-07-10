import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'servicehub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
# CLI helper: seed some demo data
# ---------------------------------------------------------------------------

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
