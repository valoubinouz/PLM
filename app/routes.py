import json
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Charger les données depuis le fichier JSON
def load_project():
    with open('app/data/project.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_project(projects):
    with open('app/data/project.json', 'w', encoding='utf-8') as f:
        json.dump(projects, f, indent=4)

def load_user():
    with open('app/data/user.json', 'r', encoding='utf-8') as f:
        users = json.load(f)
        print("Loaded users:", users)  # Ajoutez cette ligne pour déboguer
        return users

def save_user(users):
    with open('app/data/user.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def init_routes(app):
    @app.route('/')
    def home():
        projects = load_project()
        return render_template('home.html', projects=projects)

    @app.route('/project/<int:project_id>')
    def project(project_id):
        projects = load_project()
        project = next((p for p in projects if p['id'] == project_id), None)
        if not project:
            return "project not found", 404
        return render_template('project.html', project=project)

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
                    return redirect(url_for('client_dashboard', username=user['username']))
                
                # Si le rôle n'est ni admin ni client, rediriger vers une erreur
                return redirect(url_for('login'))

            return render_template('login.html', error="Invalid credentials")

        return render_template('login.html')
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            # Charger les utilisateurs existants
            users = load_user()

            # Vérifier si le nom d'utilisateur existe déjà
            if any(u['username'] == username for u in users):
                return render_template('login.html', signup_error="Username already exists")

            # Ajouter le nouvel utilisateur avec un rôle par défaut (par exemple : client)
            new_user = {
                "username": username,
                "password": password,
                "role": "client"  # Vous pouvez changer le rôle par défaut si nécessaire
            }
            users.append(new_user)
            save_user(users)

            # Rediriger vers la page de login avec un message de succès
            return render_template('login.html', signup_success="Account created successfully! Please log in.")

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
    @app.route('/client/<username>', methods=['GET'])
    def client_dashboard(username):
        if 'username' in session and session['username'] == username:
            projects = load_project()
            user_projects = [p for p in projects if p['owner'] == username]
            for project in user_projects:
                total_material_price = 0
                for material in project['materials']:
                    total_material_price += material['quantity'] * material['unit_price']
                project['total_material_price'] = total_material_price
            return render_template('client_projects.html', user=session, projects=user_projects)
        return redirect(url_for('login'))

    @app.route('/client/<username>/add_project', methods=['GET', 'POST'])
    def add_project(username):
        if 'username' in session and session['username'] == username:
            if request.method == 'POST':
                projects = load_project()
                # Récupérer les données du formulaire

                new_project = {
                    "id": len(projects) + 1,
                    "name": request.form['name'],
                    "price": float(request.form['price']),
                    "description": request.form['description'],
                    "owner": username,
                    "state": "In Development",
                    "materials": []
                }
                # Ajouter des matériaux s'ils sont renseignés
               
                material_names = request.form.getlist('material_name')
                material_quantities = request.form.getlist('material_quantity')
                material_units = request.form.getlist('material_unit')
                material_prices = request.form.getlist('material_unit_price')
 


                for i in range(len(material_names)):
                    if material_names[i].strip():
                        new_material = {
                            "id": i + 1,
                            "name": material_names[i],
                            "quantity": int(material_quantities[i]),
                            "unit": material_units[i],
                            "unit_price": float(material_prices[i])
                        }
                    new_project['materials'].append(new_material)
                    
            

                # Ajouter le nouveau projet à la liste
                projects.append(new_project)
                save_project(projects)
                return redirect(url_for('client_dashboard', username=username))
            return render_template('client_add_project.html', user=session)
        return redirect(url_for('login'))
    
    @app.route('/client/<username>/delete_project/<int:project_id>', methods=['POST'])
    def delete_project(username, project_id):
        if 'username' in session and session['username'] == username:
            projects = load_project()
            # Filtrer les produits pour exclure celui à supprimer
            updated_projects = [p for p in projects if not (p['id'] == project_id and p['owner'] == username)]

            # Si aucun produit n'a été supprimé, renvoyer une erreur (au cas où un utilisateur tente de supprimer un produit qui ne lui appartient pas)
            if len(projects) == len(updated_projects):
                return "project not found or you are not authorized to delete it.", 403

            # Sauvegarder la liste mise à jour
            save_project(updated_projects)
            return redirect(url_for('client_dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/client/<username>/project/<int:project_id>/details', methods=['GET', 'POST'])
    def project_details(username, project_id):
        if 'username' in session and session['username'] == username:
            projects = load_project()
            project = next((p for p in projects if p['id'] == project_id and p['owner'] == username), None)

            if not project:
                return "Project not found or you are not authorized to view it.", 403

            if request.method == 'POST':
                if 'add_material' in request.form:
                    # Ajouter une nouvelle matière première
                    new_material = {
                        "id": max((m["id"] for m in project["materials"]), default=0) + 1,
                        "name": request.form['material_name'],
                        "quantity": int(request.form['material_quantity']),
                        "unit": request.form['material_unit'],
                        "unit_price": float(request.form['material_unit_price'])
                    }
                    project['materials'].append(new_material)

                elif 'delete_material' in request.form:
                    # Supprimer une matière première
                    material_id = int(request.form['delete_material'])
                    project['materials'] = [m for m in project['materials'] if m['id'] != material_id]

                # Sauvegarder les modifications
                save_project(projects)

            return render_template('project_details.html', user=session, project=project)
        return redirect(url_for('login'))
    
    @app.route('/client/<username>/project/<int:project_id>/request_validation', methods=['POST'])
    def request_validation(username, project_id):
        if 'username' in session and session['username'] == username:
            projects = load_project()
            
            # Trouver le projet en fonction de l'ID et de l'utilisateur
            project = next((p for p in projects if p['id'] == project_id and p['owner'] == username), None)

            if not project:
                return "Project not found or you are not authorized to modify it.", 403
            
            # Vérifier si l'état actuel est 'In Development'
            if project['state'] == 'In Development':
                project['state'] = 'Under Validation'  # Changer l'état du projet
            
            # Sauvegarder les modifications
            save_project(projects)
            return redirect(url_for('client_dashboard', username=username))

        return redirect(url_for('login'))

    @app.route('/contact', methods=['GET'])
    def contact():
        if 'username' in session:
            user = {
                'username': session['username'],
                'role': session['role']
            }
        else:
            user = None  # Si l'utilisateur n'est pas connecté

        return render_template('contact.html', user=user)




  
