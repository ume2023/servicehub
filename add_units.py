"""
Register product units (serial numbers) for warranty tracking.

Every physical unit you sell should get a unique serial number and its
manufacturing date recorded here. Customers use this serial number on the
Support page to check if they're covered by free warranty support.

HOW TO USE:
1. Edit the list below — one entry per physical unit.
2. manufacturing_date format: "YYYY-MM-DD" (e.g. "2025-07-15" for 15 July 2025)
3. Run:  python add_units.py
"""

from datetime import date
from app import app, db, Product, ProductUnit

units_to_add = [
    {
        "product_name": "Limit Switch",          # must match an existing product's name exactly
        "serial_number": "SN-2025-00123",         # must be unique, write it on the physical unit too
        "manufacturing_date": "2025-07-15",       # YYYY-MM-DD
        "warranty_days": 365,                     # 365 = 1 year (change if different)
    },
    # Add more units below, separated by commas:
    # {
    #     "product_name": "Pressure Sensor",
    #     "serial_number": "SN-2025-00124",
    #     "manufacturing_date": "2025-03-01",
    #     "warranty_days": 365,
    # },
]

with app.app_context():
    added = 0
    for u in units_to_add:
        product = Product.query.filter_by(name=u["product_name"]).first()
        if not product:
            print(f"Skipped '{u['serial_number']}': no product named '{u['product_name']}' found.")
            continue

        if ProductUnit.query.filter_by(serial_number=u["serial_number"]).first():
            print(f"Skipped '{u['serial_number']}': already exists.")
            continue

        year, month, day = map(int, u["manufacturing_date"].split("-"))
        unit = ProductUnit(
            product_id=product.id,
            serial_number=u["serial_number"],
            manufacturing_date=date(year, month, day),
            warranty_days=u.get("warranty_days", 365),
        )
        db.session.add(unit)
        added += 1

    db.session.commit()
    print(f"Added {added} unit(s).")
