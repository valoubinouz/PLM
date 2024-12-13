import json
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Charger les données depuis le fichier JSON
def load_product():
    with open('app/data/product.json', 'r') as f:
        return json.load(f)

def save_product(data):
    with open('app/data/product.json', 'w') as f:
        json.dump(data, f, indent=4)

def init_routes(app):
    @app.route('/')
    def home():
        data = load_product()
        products = data.get('products', [])
        return render_template('home.html', products=products)

    
    @app.route('/login')
    def login():
        return render_template('login.html')

# Charger les utilisateurs depuis le fichier JSON
def load_users():
    with open('app/data.json', 'r') as f:
        data = json.load(f)
    return data.get('users', [])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

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

        # En cas d'échec
        return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    return redirect(url_for('login'))

@app.route('/client')
def client_dashboard():
    if 'role' in session and session['role'] == 'client':
        return render_template('client_dashboard.html')
    return redirect(url_for('login'))