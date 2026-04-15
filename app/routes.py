from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Product, Order

# Blueprint groups all routes together under one name 'main'
# This is registered in __init__.py
main = Blueprint('main', __name__)

# ================================================================
# AUTH ROUTES — login, register, logout
# ================================================================

# Login page — GET shows the form, POST handles form submission
@main.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # find user by username in database
        user = User.query.filter_by(username=username).first()
        # check_password_hash compares plain password with stored hash
        if user and check_password_hash(user.password, password):
            login_user(user)  # Flask-Login handles the session
            return redirect(url_for('main.dashboard'))
        flash('Wrong username or password')
    return render_template('login.html')

# Register page — creates a new shop owner account
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        shop_name = request.form['shop_name']
        # never store plain password — always hash it
        password = generate_password_hash(request.form['password'])
        # check if username already taken
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('main.register'))
        user = User(username=username, shop_name=shop_name, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please login.')
        return redirect(url_for('main.login'))
    return render_template('register.html')

# Logout — clears the session and sends user back to login
@main.route('/logout')
@login_required  # only logged in users can logout
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# ================================================================
# DASHBOARD — summary stats for the shop owner
# ================================================================

@main.route('/dashboard')
@login_required
def dashboard():
    # only fetch orders and products belonging to current logged in user
    orders = Order.query.filter_by(user_id=current_user.id).all()
    products = Product.query.filter_by(user_id=current_user.id).all()

    # calculate total revenue from delivered orders only
    total_revenue = sum(o.total + o.delivery_charge for o in orders if o.status == 'Delivered')

    # count how many orders are still pending
    pending = len([o for o in orders if o.status == 'Pending'])

    # find products with 3 or fewer pairs left — show alert
    low_stock = [p for p in products if p.stock <= 3]

    return render_template('dashboard.html',
        orders=orders, products=products,
        total_revenue=total_revenue,
        pending=pending, low_stock=low_stock)

# ================================================================
# ORDER ROUTES — view, add, update orders
# ================================================================

# Orders page — shows all orders + add order form
@main.route('/orders')
@login_required
def orders():
    # order by newest first
    all_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('orders.html', orders=all_orders, products=products)

# Add new order — called when shop owner submits the order form
@main.route('/orders/add', methods=['POST'])
@login_required
def add_order():
    product = Product.query.get(request.form['product_id'])
    quantity = int(request.form['quantity'])
    delivery_charge = float(request.form.get('delivery_charge', 0))

    # total = (price x quantity) + delivery charge
    total = (product.price * quantity) + delivery_charge

    order = Order(
        customer_name=request.form['customer_name'],
        customer_phone=request.form['customer_phone'],
        customer_address=request.form.get('customer_address', ''),
        product_id=product.id,
        quantity=quantity,
        size=request.form.get('size', ''),      # shoe size selected
        color=request.form.get('color', ''),    # color selected
        total=total,
        delivery_charge=delivery_charge,
        notes=request.form.get('notes', ''),
        platform=request.form['platform'],
        user_id=current_user.id
    )

    # reduce stock by ordered quantity
    product.stock -= quantity
    db.session.add(order)
    db.session.commit()
    return redirect(url_for('main.orders'))

# Update order status — triggered when shop owner changes dropdown
@main.route('/orders/update/<int:order_id>', methods=['POST'])
@login_required
def update_order(order_id):
    order = Order.query.get(order_id)
    order.status = request.form['status']
    db.session.commit()
    return redirect(url_for('main.orders'))

# ================================================================
# API — used by JavaScript on orders page
# when shop owner selects a product, JS fetches its sizes & colors
# ================================================================

@main.route('/api/product/<int:product_id>')
@login_required
def get_product(product_id):
    product = Product.query.get(product_id)
    # returns JSON so JavaScript can dynamically fill size/color dropdowns
    return jsonify({
        'sizes': product.get_sizes(),
        'colors': product.get_colors(),
        'price': product.price
    })

# ================================================================
# INVENTORY ROUTES — view, add, update, delete products
# ================================================================

# Inventory page — shows all products
@main.route('/inventory')
@login_required
def inventory():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('inventory.html', products=products)

# Add new shoe product
@main.route('/inventory/add', methods=['POST'])
@login_required
def add_product():
    product = Product(
        name=request.form['name'],
        brand=request.form.get('brand', ''),
        category=request.form.get('category', ''),
        price=float(request.form['price']),
        stock=int(request.form['stock']),
        # colors and sizes come as comma separated strings e.g. "Black,White"
        colors=request.form.get('colors', ''),
        sizes=request.form.get('sizes', ''),
        description=request.form.get('description', ''),
        user_id=current_user.id
    )
    db.session.add(product)
    db.session.commit()
    return redirect(url_for('main.inventory'))

# Update stock count for a product
@main.route('/inventory/update/<int:product_id>', methods=['POST'])
@login_required
def update_stock(product_id):
    product = Product.query.get(product_id)
    product.stock = int(request.form['stock'])
    db.session.commit()
    return redirect(url_for('main.inventory'))

# Delete a product permanently
@main.route('/inventory/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('main.inventory'))