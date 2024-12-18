import json
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Charger les données depuis le fichier JSON
def load_product():
    with open('app/data/product.json', 'r') as f:
        return json.load(f)

def save_product(products):
    with open('app/data/product.json', 'w') as f:
        json.dump(products, f, indent=4)

def load_user():
    with open('app/data/user.json', 'r') as f:
        users = json.load(f)
        print("Loaded users:", users)  # Ajoutez cette ligne pour déboguer
        return users

def save_user(users):
    with open('app/data/user.json', 'w') as f:
        json.dump(users, f, indent=4)

def init_routes(app):
    @app.route('/')
    def home():
        products = load_product()
        return render_template('home.html', products=products)

    @app.route('/product/<int:product_id>')
    def product(product_id):
        products = load_product()
        product = next((p for p in products if p['id'] == product_id), None)
        if not product:
            return "Product not found", 404
        return render_template('product.html', product=product)

    # Route pour la page de login avec méthode GET et POST combinées
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            users = load_user()

            # Vérifier si l'utilisateur existe
            user = next((u for u in users if u['username'] == username and u['password'] == password), None)
            if user:
                session['username'] = user['username']
                session['role'] = user['role']

                # Rediriger selon le rôle
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'client':
                    return redirect(url_for('client_dashboard'))
                
                # Si le rôle n'est ni admin ni client, rediriger vers une erreur
                return redirect(url_for('login'))

            return render_template('login.html', error="Invalid credentials")

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # Dashboard admin
    @app.route('/admin')
    def admin_dashboard():
        if 'role' in session and session['role'] == 'admin':
            return render_template('admin_dashboard.html')
        return redirect(url_for('login'))

    # Dashboard client
    @app.route('/client')
    def client_dashboard():
        if 'role' in session and session['role'] == 'client':
            user = {'username': session['username'], 'role': session['role']}  # Créer un dictionnaire user
            products = load_product()
            # Filtrer uniquement les produits appartenant à l'utilisateur connecté
            user_products = [p for p in products if p['owner'] == user['username']]
            return render_template('client_products.html', user=session, products=user_products)
        return redirect(url_for('login'))
   

    @app.route('/client/<username>/add_product', methods=['GET', 'POST'])
    def add_product(username):
        if 'username' in session and session['username'] == username:
            if request.method == 'POST':
                products = load_product()
                # Récupérer les données du formulaire
                new_product = {
                    "id": len(products) + 1,
                    "name": request.form['name'],
                    "price": float(request.form['price']),
                    "description": request.form['description'],
                    "owner": username
                }
                products.append(new_product)
                save_product(products)
                return redirect(url_for('client_dashboard', username=username))
            return render_template('client_add_product.html', user=session)
        return redirect(url_for('login'))
    
    @app.route('/client/<username>/delete_product/<int:product_id>', methods=['POST'])
    def delete_product(username, product_id):
        if 'username' in session and session['username'] == username:
            products = load_product()
            # Filtrer les produits pour exclure celui à supprimer
            updated_products = [p for p in products if not (p['id'] == product_id and p['owner'] == username)]

            # Si aucun produit n'a été supprimé, renvoyer une erreur (au cas où un utilisateur tente de supprimer un produit qui ne lui appartient pas)
            if len(products) == len(updated_products):
                return "Product not found or you are not authorized to delete it.", 403

            # Sauvegarder la liste mise à jour
            save_product(updated_products)
            return redirect(url_for('client_dashboard'))
        return redirect(url_for('login'))


  
