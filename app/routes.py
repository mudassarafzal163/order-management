from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Product, Order

main = Blueprint('main', __name__)

# ---------- AUTH ----------

@main.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Wrong username or password')
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        shop_name = request.form['shop_name']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('main.register'))
        user = User(username=username, shop_name=shop_name, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please login.')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# ---------- DASHBOARD ----------

@main.route('/dashboard')
@login_required
def dashboard():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    products = Product.query.filter_by(user_id=current_user.id).all()
    total_revenue = sum(o.total for o in orders if o.status == 'Delivered')
    pending = len([o for o in orders if o.status == 'Pending'])
    low_stock = [p for p in products if p.stock <= 3]
    return render_template('dashboard.html',
        orders=orders, products=products,
        total_revenue=total_revenue,
        pending=pending, low_stock=low_stock)

# ---------- ORDERS ----------

@main.route('/orders')
@login_required
def orders():
    all_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('orders.html', orders=all_orders, products=products)

@main.route('/orders/add', methods=['POST'])
@login_required
def add_order():
    product = Product.query.get(request.form['product_id'])
    quantity = int(request.form['quantity'])
    total = product.price * quantity
    order = Order(
        customer_name=request.form['customer_name'],
        customer_phone=request.form['customer_phone'],
        product_id=product.id,
        quantity=quantity,
        total=total,
        platform=request.form['platform'],
        user_id=current_user.id
    )
    product.stock -= quantity
    db.session.add(order)
    db.session.commit()
    return redirect(url_for('main.orders'))

@main.route('/orders/update/<int:order_id>', methods=['POST'])
@login_required
def update_order(order_id):
    order = Order.query.get(order_id)
    order.status = request.form['status']
    db.session.commit()
    return redirect(url_for('main.orders'))

# ---------- INVENTORY ----------

@main.route('/inventory')
@login_required
def inventory():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('inventory.html', products=products)

@main.route('/inventory/add', methods=['POST'])
@login_required
def add_product():
    product = Product(
        name=request.form['name'],
        price=float(request.form['price']),
        stock=int(request.form['stock']),
        user_id=current_user.id
    )
    db.session.add(product)
    db.session.commit()
    return redirect(url_for('main.inventory'))

@main.route('/inventory/update/<int:product_id>', methods=['POST'])
@login_required
def update_stock(product_id):
    product = Product.query.get(product_id)
    product.stock = int(request.form['stock'])
    db.session.commit()
    return redirect(url_for('main.inventory'))