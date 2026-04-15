from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

# This tells Flask-Login how to load a user from the database
# It runs every time a logged-in user makes a request
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User table — each shop owner has one account
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)   # must be unique
    password = db.Column(db.String(200), nullable=False)               # stored as hash, never plain text
    shop_name = db.Column(db.String(100), nullable=False)              # shown on dashboard

    # relationships — one user has many orders and products
    orders = db.relationship('Order', backref='owner', lazy=True)
    products = db.relationship('Product', backref='owner', lazy=True)

# Product table — each shoe product belongs to one shop owner
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)        # e.g. "Nike Air Max"
    brand = db.Column(db.String(50), default='')            # e.g. "Nike", "Adidas", "Local"
    category = db.Column(db.String(50), default='')         # e.g. "Sneakers", "Formal", "Sandals"
    price = db.Column(db.Float, nullable=False)             # price in PKR
    colors = db.Column(db.String(200), default='')          # stored as comma separated e.g. "Black,White,Red"
    sizes = db.Column(db.String(200), default='')           # stored as comma separated e.g. "40,41,42,43"
    stock = db.Column(db.Integer, default=0)                # total pairs available
    description = db.Column(db.String(300), default='')     # optional extra notes
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # which shop owns this

    # helper method — converts "Black,White,Red" string into ['Black', 'White', 'Red'] list
    def get_colors(self):
        return [c.strip() for c in self.colors.split(',') if c.strip()]

    # helper method — converts "40,41,42" string into ['40', '41', '42'] list
    def get_sizes(self):
        return [s.strip() for s in self.sizes.split(',') if s.strip()]

# Order table — each order belongs to one shop owner and one product
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.String(200), default='')    # delivery address
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(10), default='')                 # selected shoe size e.g. "42"
    color = db.Column(db.String(30), default='')                # selected color e.g. "Black"
    total = db.Column(db.Float, nullable=False)                 # product price x quantity + delivery
    delivery_charge = db.Column(db.Float, default=0)            # extra delivery fee in PKR
    notes = db.Column(db.String(300), default='')               # e.g. "gift wrap this"
    status = db.Column(db.String(20), default='Pending')        # Pending → Confirmed → Packed → Delivered
    platform = db.Column(db.String(20), default='WhatsApp')     # where order came from
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # auto timestamp
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # relationship — lets us do order.product.name directly in templates
    product = db.relationship('Product', backref='orders')