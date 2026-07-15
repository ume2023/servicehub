"""
Fix product photos: updates each product's image_url to match the EXACT
filename (including spaces/capitals) sitting in static/images/products/.

Run:  python fix_product_images.py
"""

from app import app, db, Product

# name in database -> exact filename sitting in static/images/products/
fixes = {
    "Cable Drum": "cable drum.jpeg",
    "Counter Weight": "counter weight.jpeg",
    "Hydra Display": "Hydra display.jpeg",
    "Limit Switch": "limit swtich.jpeg",
    "Pressure Sensor": "pressure sensor.jpeg",
    "New Generation Display": "New Generation Display.jpeg",
}

with app.app_context():
    updated = 0
    for name, filename in fixes.items():
        product = Product.query.filter_by(name=name).first()
        if not product:
            print(f"Skipped '{name}': no product with this name found.")
            continue
        product.image_url = f"/static/images/products/{filename}"
        updated += 1
        print(f"Fixed: {name} -> {filename}")

    db.session.commit()
    print(f"\nDone. Updated {updated} product(s).")
