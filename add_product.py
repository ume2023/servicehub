from app import app, db, Product

products_to_add = [
    {
        "name": "Cable Drum",
        "description": "boom length and angle",
        "price": 25000,
        "stock": 100,
        "image_url": "/static/images/products/cable-drum.jpeg",
    },
    {
        "name": "Counter Weight",
        "description": "part of the limit swtich maintain the swtich position",
        "price": 3500,
        "stock": 100,
        "image_url": "/static/images/products/counter-weight.jpeg",
    },
    {
        "name": "Hydra Display",
        "description": "Display",
        "price": 25000,
        "stock": 100,
        "image_url": "/static/images/products/Hydra-display.jpeg",
    },
    {
        "name": "Limit Switch",
        "description": "Anti to block",
        "price": 5000,
        "stock": 100,
        "image_url": "/static/images/products/limitswtich.jpeg",
    },
    {
        "name": "Pressure Sensor",
        "description": "load sensor",
        "price": 10000,
        "stock": 100,
        "image_url": "/static/images/products/pressure-sensor.jpeg",
    },
    {
        "name": "Tilt Sensor",
        "description": "protect from tilt of vehicle",
        "price": 10,000,
        "stock": 1000,
        "image_url": "/static/images/products/tilt-image.jpeg",
    },
]

with app.app_context():
    for p in products_to_add:
        product = Product(**p)
        db.session.add(product)
    db.session.commit()
    print(f"Added {len(products_to_add)} products.")