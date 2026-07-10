"""
Add or update a product, including a photo.

HOW TO USE:
1. Put your product photo inside the 'static/images/products' folder
   (e.g. static/images/products/charger.jpg)
2. Edit the values below (name, description, price, stock, image filename)
3. Run:  python add_product.py
"""

from app import app, db, Product

with app.app_context():
    product = Product(
        name="My Product Name",                 # <-- change this
        description="A short description.",      # <-- change this
        price=999,                                # <-- change this (in rupees)
        stock=20,                                 # <-- change this
        image_url="/static/images/products/YOUR_IMAGE_FILENAME.jpg",  # <-- change this
    )
    db.session.add(product)
    db.session.commit()
    print(f"Added product: {product.name} (id={product.id})")
