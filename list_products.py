"""
List every product currently in the store, with its ID number.

Run this first to see the ID of any product you want to delete, then use
that ID in remove_products.py.

HOW TO USE:
   python list_products.py
"""

from app import app, Product

with app.app_context():
    products = Product.query.order_by(Product.id).all()
    if not products:
        print("No products found.")
    for p in products:
        print(f"ID {p.id}: {p.name}  (₹{p.price})")
