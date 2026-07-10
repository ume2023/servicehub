"""
Delete one or more products by their ID number.

HOW TO USE:
1. Run list_products.py first to find the IDs of products you want to remove.
2. Put those ID numbers in the list below.
3. Run:  python remove_products.py
"""

from app import app, db, Product

ids_to_delete = [
    # Put the ID numbers you want to remove here, separated by commas.
    # Example: 1, 2, 3
]

with app.app_context():
    if not ids_to_delete:
        print("No IDs listed. Edit this file and add the product ID numbers to delete, then run again.")
    else:
        removed = 0
        for pid in ids_to_delete:
            product = Product.query.get(pid)
            if product:
                print(f"Deleting: ID {pid} - {product.name}")
                db.session.delete(product)
                removed += 1
            else:
                print(f"Skipped: no product found with ID {pid}")
        db.session.commit()
        print(f"Done. Removed {removed} product(s).")
