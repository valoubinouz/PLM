import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime



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

# Charger les messages depuis le fichier JSON

def load_messages():
    with open('app/data/messages.json', "r") as f:
        content = f.read().strip()
        if not content:  # Vérifie si le fichier est vide
            return []  # Retourne une liste vide si le fichier est vide
        return json.loads(content)  # Charge et retourne les messages JSON

def save_messages(messages):
    with open('app/data/messages.json', 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=4)


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
            projects = load_project()
            user = {'username': session['username'], 'role': session['role']}
            
            validated = [p for p in projects if p['state'] == 'Validated']

            return render_template('admin_dashboard.html', projects=validated, user=user)
        return redirect(url_for('login'))
    
    @app.route('/admin/in_development')
    def in_development():
        if 'role' in session and session['role'] == 'admin':
            projects = load_project()
            user = {'username': session['username'], 'role': session['role']}
                
            in_development = [p for p in projects if p['state'] == 'In Development']

            return render_template('in_development.html', projects=in_development, user=user)
        return redirect(url_for('login'))
    
    @app.route('/admin/Rejected')
    def rejected():
        if 'role' in session and session['role'] == 'admin':
            projects = load_project()
            user = {'username': session['username'], 'role': session['role']}
                
            rejected = [p for p in projects if p['state'] == 'Rejected']

            return render_template('rejected.html', projects=rejected, user=user)
        return redirect(url_for('login'))
    
    @app.route('/admin/waiting', methods=['GET', 'POST'])
    def waiting_validation():
        if 'role' in session and session['role'] == 'admin':
            projects = load_project()

            # Handle Approve/Reject actions
            if request.method == 'POST':
                project_id = int(request.form['project_id'])
                action = request.form['action']

                for project in projects:
                    if project['id'] == project_id and project['state'] == 'Under Validation':
                        if action == 'approve':
                            project['state'] = 'Validated'
                            flash(f"Project '{project['name']}' has been approved!", "success")

                        elif action == 'reject':
                            project['state'] = 'Rejected'
                            flash(f"Project '{project['name']}' has been rejected.", "danger")

                        save_project(projects)
                        break

                return redirect(url_for('waiting_validation'))

        # Filter projects in "Under Validation" state
            pending_projects = [p for p in projects if p['state'] == 'Under Validation']
            return render_template('waiting_validation.html', projects=pending_projects)
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
                material_specifications = request.form.getlist('material_specification')
                material_quantities = request.form.getlist('material_quantity')
                material_units = request.form.getlist('material_unit')
                material_prices = request.form.getlist('material_unit_price')
 


                for i in range(len(material_names)):
                    if material_names[i].strip():
                        new_material = {
                            "id": i + 1,
                            "name": material_names[i],
                            "specification": material_specifications[i],
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
                        "specification": request.form['material_specification'],
                        "quantity": int(request.form['material_quantity']),
                        "unit": request.form['material_unit'],
                        "unit_price": float(request.form['material_unit_price'])
                    }
                    project['materials'].append(new_material)

                elif 'delete_material' in request.form:
                    # Supprimer une matière première
                    material_id = int(request.form['delete_material'])
                    project['materials'] = [m for m in project['materials'] if m['id'] != material_id]
                if 'update_project_info' in request.form:
                    # Mettre à jour les informations du projet
                    project['name'] = request.form['project_name']
                    project['description'] = request.form['project_description']
                    project['price'] = float(request.form['project_price'])

                    # Sauvegarder les modifications
                    save_project(projects)

                    # Rediriger pour refléter les changements
                    return redirect(url_for('project_details', username=username, project_id=project_id))


                elif 'create_new' in request.form:
                # Créer un nouveau projet basé sur l'actuel
                    new_project = {
                        "id": max((p["id"] for p in projects), default=0) + 1,
                        "name": f"{project['name']} (Copy)",
                        "price": sum(m["quantity"] * m["unit_price"] for m in project["materials"]),
                        "description": project['description'],
                        "owner": username,
                        "state": "In Development",
                        "materials": project['materials'][:],  # Copier les matériaux
                    }
                    projects.append(new_project)
                    save_project(projects)

                    # Rediriger vers la page des détails du nouveau projet
                    return redirect(url_for('project_details', username=username, project_id=new_project["id"]))
                
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

        return render_template('contact.html', user=user, messages=load_messages())

    @app.route('/submit_contact', methods=['POST'])
    def submit_contact():
        # Charger les messages existants
        messages = load_messages()
        username= session['username']

        # Ajouter le nouveau message
        new_message = {
            "id": len(messages) + 1,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Enregistrer la date actuelle
            "name": username,
            "project": request.form['project'],
            "message": request.form['message'],
            "response": None
        }
        messages.append(new_message)

        # Sauvegarder les messages mis à jour
        save_messages(messages)

        # Afficher un message de confirmation
        flash("Your message has been sent successfully!", "success")
        return redirect(url_for('contact'))

    @app.route('/admin/messages')
    def admin_contact():
        if 'role' in session and session['role'] == 'admin':
            messages = load_messages()
            return render_template('admin_contact.html', messages=messages)
        return redirect(url_for('login'))

    @app.route('/admin_contact/respond/<int:message_id>', methods=['POST'])
    def respond_to_message(message_id):
        try:
            messages = load_messages()
            response = request.form.get("response")
            if not response:
                flash("Response cannot be empty.", "warning")
                return redirect(url_for('admin_contact'))

            # Chercher le message correspondant
            for message in messages:
                if message["id"] == message_id:
                    message["response"] = response
                    break
            else:
                flash("Message not found.", "danger")
                return redirect(url_for('admin_contact'))

            # Sauvegarder les réponses dans le fichier JSON
            save_messages(messages)
            flash("Response sent successfully.", "success")
            return redirect(url_for('admin_contact'))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('admin_contact'))


    
