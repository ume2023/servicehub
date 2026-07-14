"""
Add MULTIPLE products at once, each with its own photo, description, and price.

HOW TO USE:
1. Put all your product photos inside: static/images/products/
   (e.g. static/images/products/limit-switch.jpg)
2. Edit the list below — add one block per product, separated by commas.
   Copy-paste a block to add more; delete blocks you don't need.
3. Run:  python add_product.py

Products with a name that already exists in the database will be SKIPPED
(so it's safe to re-run this file after adding more products later).
"""

from app import app, db, Product

products_to_add = [
    {
        "name": "Cable Drum",
        "description": "Controls boom length and angle.",
        "price": 25000,
        "stock": 100,
        "image_url": "/static/images/products/cable-drum.jpg",
    },
    {
        "name": "Counter Weight",
        "description": "Part of the limit switch, maintains switch position.",
        "price": 3500,
        "stock": 100,
        "image_url": "/static/images/products/counter-weight.jpg",
    },
    {
        "name": "Hydra Display",
        "description": "Main operator display unit.",
        "price": 25000,
        "stock": 100,
        "image_url": "/static/images/products/hydra-display.jpg",
    },
    {
        "name": "Limit Switch",
        "description": "Prevents over-travel of the boom mechanism.",
        "price": 5000,
        "stock": 100,
        "image_url": "/static/images/products/limit-switch.jpg",
    },
    {
        "name": "Pressure Sensor",
        "description": "Load sensor for accurate weight measurement.",
        "price": 10000,
        "stock": 100,
        "image_url": "/static/images/products/pressure-sensor.jpg",
    },
    {
        "name": "New Generation Display",
        "description": "Protects against vehicle tilt beyond safe limits.",
        "price": 35000,
        "stock": 100,
        "image_url": "/static/images/products/tilt-sensor.jpg",
    },

    # --- Add more products below by copy-pasting a block like this: ---
    # {
    #     "name": "Remote controller For Throttle",
    #     "description": "Remotly control the RPM.",
    #     "price": 80000,
    #     "stock": 100,
    #     "image_url": "/static/images/products/your-photo-name.jpg",
    # },
]

with app.app_context():
    added = 0
    skipped = 0
    for p in products_to_add:
        if Product.query.filter_by(name=p["name"]).first():
            print(f"Skipped '{p['name']}': a product with this name already exists.")
            skipped += 1
            continue
        product = Product(**p)
        db.session.add(product)
        added += 1
        print(f"Adding: {p['name']} — Rs.{p['price']}")

    db.session.commit()
    print(f"\nDone. Added {added} product(s), skipped {skipped} duplicate(s).")
