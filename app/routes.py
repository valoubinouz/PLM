import json
from flask import Flask, render_template, request, redirect, url_for

# Charger les données depuis le fichier JSON
def load_data():
    with open('app/data.json', 'r') as f:
        return json.load(f)

def save_data(data):
    with open('app/data.json', 'w') as f:
        json.dump(data, f, indent=4)

def init_routes(app):
    @app.route('/')
    def home():
        data = load_data()
        products = data.get('products', [])
        return render_template('home.html', products=products)

    @app.route('/product/<int:product_id>')
    def product(product_id):
        data = load_data()
        product = next((p for p in data.get('products', []) if p['id'] == product_id), None)
        if not product:
            return "Product not found", 404
        return render_template('product.html', product=product)

    @app.route('/cart')
    def cart():
        data = load_data()
        cart = data.get('cart', [])
        return render_template('cart.html', cart=cart)

    @app.route('/add_to_cart/<int:product_id>')
    def add_to_cart(product_id):
        data = load_data()
        product = next((p for p in data.get('products', []) if p['id'] == product_id), None)
        if not product:
            return "Product not found", 404

        # Ajouter au panier
        cart = data.get('cart', [])
        cart_item = next((item for item in cart if item['id'] == product_id), None)
        if cart_item:
            cart_item['quantity'] += 1
        else:
            cart.append({'id': product_id, 'name': product['name'], 'price': product['price'], 'quantity': 1})

        data['cart'] = cart
        save_data(data)
        return redirect(url_for('cart'))
