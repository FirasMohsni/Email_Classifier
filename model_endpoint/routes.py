from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from model_endpoint import db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from model_endpoint.model import User
from model_endpoint.automatisation import Automatisation
from model_endpoint.utils import preprocess_text
from model_endpoint.model import bilstm_model, label_encoder, label_encoder_type, naive_bayes_model, vectorizer, Statistics
import torch
from flask import session, redirect, url_for, flash
from flask_login import logout_user
from flask_mail import Message ,Mail
from flask_mail import Message
main = Blueprint('main', __name__)
from model_endpoint.model import *

mail = Mail()
# Mail server configuration
mail_server = 'imap.gmail.com'  
mail_username = 'assistantstbbanque@gmail.com'  
mail_password = 'izzm vhde kllh kvsc'  
smtp_server = 'smtp.gmail.com' 
smtp_port = 587  
imap_port = 993  
smtp_username = 'assistantstbbanque@gmail.com'  
smtp_password = 'izzm vhde kllh kvsc'  


# Initialize the Automatisation 
automatisation = Automatisation(mail_server, mail_username, mail_password, smtp_server, smtp_port,imap_port, smtp_username, smtp_password, vectorizer, bilstm_model, naive_bayes_model, label_encoder, label_encoder_type)

@main.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        print(f"Received text: {text}")

        # Preprocess the text
        preprocessed_text = preprocess_text(text)
        print(f"Preprocessed text: {preprocessed_text}")

        # Vectorize the text
        vectorized_text = vectorizer.transform([preprocessed_text]).toarray()
        input_tensor = torch.tensor(vectorized_text, dtype=torch.float32).unsqueeze(1)

        # Predict category with BiLSTM
        bilstm_model.eval()
        with torch.no_grad():
            output_category = bilstm_model(input_tensor)
            _, predicted_category = torch.max(output_category, 1)
            category = label_encoder.inverse_transform(predicted_category.numpy())[0]
            print(f"Predicted category: {category}")

        # Predict type with Naive Bayes
        type_prediction = naive_bayes_model.predict(vectorized_text)
        type_ = label_encoder_type.inverse_transform(type_prediction)[0]
        print(f"Predicted type: {type_}")

        return jsonify({'category': category, 'type': type_})

    return render_template('index.html')

@main.route('/automatisation', methods=['POST'])
def run_automatisation():
    try:
        # Appel à la méthode d'automatisation pour traiter les e-mails entrants
        automatisation.process_incoming_emails()
        return jsonify({'status': 'Automatisation terminée avec succès'})
    except Exception as e:
        return jsonify({'status': 'Erreur lors de l\'automatisation', 'error': str(e)})

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password, role=role, is_active=False)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! An administrator will activate it soon.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            if user.is_active:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.route_according_to_role'))
            else:
                flash('Account is not active. Please contact the administrator.', 'danger')
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')
@main.route('/route_according_to_role')
@login_required
def route_according_to_role():
    if current_user.role == 'admin':
        return redirect(url_for('main.reclamations_generales'))
    elif current_user.role == 'departement_monétique':
        return redirect(url_for('main.monetique'))
    elif current_user.role == 'département_fonctionnement_de_compte':
        return redirect(url_for('main.fonctionnement_de_comptes'))
    elif current_user.role == 'département_accueil_qualité_service':
        return redirect(url_for('main.accueil_qualite_service'))
    elif current_user.role == 'departement_crédit':
        return redirect(url_for('main.credit'))
    elif current_user.role == 'département_moyens_paiement_hors_monétique':
        return redirect(url_for('main.moyens_de_paiement_hors_monetique'))
    elif current_user.role == 'département_opération_internationales':
        return redirect(url_for('main.operations_internationales'))
    elif current_user.role == 'département_services_banquaires_distance':
        return redirect(url_for('main.services_bancaires_distance'))
    
    else:
        return redirect(url_for('main.dashboard'))
@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    session.pop('_flashes', None)  # Clear flash messages
    return redirect(url_for('main.login'))

@main.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('main.dashboard'))
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@main.route('/activate_user/<int:user_id>')
@login_required
def activate_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.dashboard'))
    user = User.query.get(user_id)
    if user:
        user.is_active = True
        db.session.commit()
    return redirect(url_for('main.manage_users'))
@main.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)

@main.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form['role']
        user.is_active = 'is_active' in request.form
        db.session.commit()
        flash('User has been updated!', 'success')
        return redirect(url_for('main.manage_users'))
    return render_template('edit_user.html', user=user)

@main.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted!', 'success')
    return redirect(url_for('main.manage_users'))

@main.before_request
def restrict_to_admin():
    if request.endpoint in ['main.manage_users', 'main.edit_user', 'main.delete_user']:
        if current_user.is_authenticated and current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))

@main.route('/monetique')
@login_required
def monetique():
    if current_user.role != 'departement_monétique':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))

    # Récupérer les paramètres de filtre
    status_filter = request.args.get('status', '')
    agency_name_filter = request.args.get('agency_name', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Construire la requête de base
    query = Monetique.query

    # Appliquer le filtre de statut si présent
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Appliquer le filtre de nom d'agence si présent
    if agency_name_filter:
        query = query.filter_by(agency_name=agency_name_filter)

    # Appliquer le filtre de date si les dates sont présentes
    if start_date:
        query = query.filter(Monetique.date_received >= start_date)
    if end_date:
        query = query.filter(Monetique.date_received <= end_date)

    # Récupérer les données filtrées
    données = query.order_by(Monetique.date_received.desc()).all()

    # Récupérer tous les noms d'agences disponibles pour le filtre
    agency_names = Monetique.query.with_entities(Monetique.agency_name).distinct().all()
    agency_names = [agency[0] for agency in agency_names if agency[0]]  # Extraire uniquement les noms non vides

    return render_template('monetique.html', données=données, agency_names=agency_names)



@main.route('/update_monetique/<int:id>', methods=['POST'])
@login_required
def update_monetique(id):
    if current_user.role != 'departement_monétique':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.index'))
    
    # Mise à jour dans la table Monetique
    data = Monetique.query.get_or_404(id)
    new_status = request.form['status']
    data.status = new_status
    db.session.commit()

    # Mise à jour dans la table reclamations_generales
    general_data = ReclamationsGenerales.query.filter_by(id=data.reclamation_id).first()
    if general_data:
        general_data.status = new_status
        db.session.commit()
        flash('État mis à jour avec succès dans les deux tables', 'success')
    else:
        flash('Impossible de mettre à jour le statut dans reclamations_generales', 'danger')
    
    return redirect(url_for('main.monetique'))

@main.route('/fonctionnement_de_comptes')
@login_required
def fonctionnement_de_comptes():
    if current_user.role != 'département_fonctionnement_de_compte':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Récupérer les paramètres de filtre
    status_filter = request.args.get('status', '')
    agency_name_filter = request.args.get('agency_name', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Construire la requête de base
    query = FonctionnementDeComptes.query

    # Appliquer le filtre de statut si présent
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Appliquer le filtre de nom d'agence si présent
    if agency_name_filter:
        query = query.filter_by(agency_name=agency_name_filter)

    # Appliquer le filtre de date si les dates sont présentes
    if start_date:
        query = query.filter(FonctionnementDeComptes.date_received >= start_date)
    if end_date:
        query = query.filter(FonctionnementDeComptes.date_received <= end_date)

    # Récupérer les données filtrées
    données = query.order_by(FonctionnementDeComptes.date_received.desc()).all()

    # Récupérer tous les noms d'agences disponibles pour le filtre
    agency_names = FonctionnementDeComptes.query.with_entities(FonctionnementDeComptes.agency_name).distinct().all()
    agency_names = [agency[0] for agency in agency_names if agency[0]]  # Extraire uniquement les noms non vides

    return render_template('fonctionnement_de_comptes.html', données=données, agency_names=agency_names)


@main.route('/update_fonctionnement_de_comptes/<int:id>', methods=['POST'])
@login_required
def update_fonctionnement_de_comptes(id):
    if current_user.role != 'département_fonctionnement_de_compte':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Mise à jour dans la table FonctionnementDeComptes
    data = FonctionnementDeComptes.query.get_or_404(id)
    new_status = request.form['status']
    data.status = new_status
    db.session.commit()

    # Mise à jour dans la table reclamations_generales
    general_data = ReclamationsGenerales.query.filter_by(id=data.reclamation_id).first()
    if general_data:
        general_data.status = new_status
        db.session.commit()
        flash('État mis à jour avec succès dans les deux tables', 'success')
    else:
        flash('Impossible de mettre à jour le statut dans reclamations_generales', 'danger')
    
    return redirect(url_for('main.fonctionnement_de_comptes'))

@main.route('/accueil_qualite_service')
@login_required
def accueil_qualite_service():
    if current_user.role != 'département_accueil_qualité_service':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Récupérer les paramètres de filtre
    status_filter = request.args.get('status', '')
    agency_name_filter = request.args.get('agency_name', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Construire la requête de base
    query = AccueilQualiteService.query

    # Appliquer le filtre de statut si présent
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Appliquer le filtre de nom d'agence si présent
    if agency_name_filter:
        query = query.filter_by(agency_name=agency_name_filter)

    # Appliquer le filtre de date si les dates sont présentes
    if start_date:
        query = query.filter(AccueilQualiteService.date_received >= start_date)
    if end_date:
        query = query.filter(AccueilQualiteService.date_received <= end_date)

    # Récupérer les données filtrées
    données = query.order_by(AccueilQualiteService.date_received.desc()).all()

    # Récupérer tous les noms d'agences disponibles pour le filtre
    agency_names = AccueilQualiteService.query.with_entities(AccueilQualiteService.agency_name).distinct().all()
    agency_names = [agency[0] for agency in agency_names if agency[0]]  # Extraire uniquement les noms non vides

    return render_template('accueil_qualite_service.html', données=données, agency_names=agency_names)


@main.route('/update_accueil_qualite_service/<int:id>', methods=['POST'])
@login_required
def update_accueil_qualite_service(id):
    if current_user.role != 'département_accueil_qualité_service':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Mise à jour dans la table AccueilQualiteService
    data = AccueilQualiteService.query.get_or_404(id)
    new_status = request.form['status']
    data.status = new_status
    db.session.commit()

    # Mise à jour dans la table reclamations_generales
    general_data = ReclamationsGenerales.query.filter_by(id=data.reclamation_id).first()
    if general_data:
        general_data.status = new_status
        db.session.commit()
        flash('État mis à jour avec succès dans les deux tables', 'success')
    else:
        flash('Impossible de mettre à jour le statut dans reclamations_generales', 'danger')

    return redirect(url_for('main.accueil_qualite_service'))


@main.route('/credit')
@login_required
def credit():
    if current_user.role != 'departement_crédit':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Récupérer les paramètres de filtre
    status_filter = request.args.get('status', '')
    agency_name_filter = request.args.get('agency_name', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Construire la requête de base
    query = Credit.query

    # Appliquer le filtre de statut si présent
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Appliquer le filtre de nom d'agence si présent
    if agency_name_filter:
        query = query.filter_by(agency_name=agency_name_filter)

    # Appliquer le filtre de date si les dates sont présentes
    if start_date:
        query = query.filter(Credit.date_received >= start_date)
    if end_date:
        query = query.filter(Credit.date_received <= end_date)

    # Récupérer les données filtrées
    données = query.order_by(Credit.date_received.desc()).all()

    # Récupérer tous les noms d'agences disponibles pour le filtre
    agency_names = Credit.query.with_entities(Credit.agency_name).distinct().all()
    agency_names = [agency[0] for agency in agency_names if agency[0]]  # Extraire uniquement les noms non vides

    return render_template('credit.html', données=données, agency_names=agency_names)


@main.route('/update_credit/<int:id>', methods=['POST'])
@login_required
def update_credit(id):
    if current_user.role != 'departement_crédit':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Mise à jour dans la table Credit
    data = Credit.query.get_or_404(id)
    new_status = request.form['status']
    data.status = new_status
    db.session.commit()

    # Mise à jour dans la table reclamations_generales
    general_data = ReclamationsGenerales.query.filter_by(id=data.reclamation_id).first()
    if general_data:
        general_data.status = new_status
        db.session.commit()
        flash('État mis à jour avec succès dans les deux tables', 'success')
    else:
        flash('Impossible de mettre à jour le statut dans reclamations_generales', 'danger')

    return redirect(url_for('main.credit'))

@main.route('/moyens_de_paiement_hors_monetique')
@login_required
def moyens_de_paiement_hors_monetique():
    if current_user.role != 'département_moyens_paiement_hors_monétique':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Récupérer les paramètres de filtre
    status_filter = request.args.get('status', '')
    agency_name_filter = request.args.get('agency_name', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Construire la requête de base
    query = MoyensPaiementHorsMonetique.query

    # Appliquer le filtre de statut si présent
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Appliquer le filtre de nom d'agence si présent
    if agency_name_filter:
        query = query.filter_by(agency_name=agency_name_filter)

    # Appliquer le filtre de date si les dates sont présentes
    if start_date:
        query = query.filter(MoyensPaiementHorsMonetique.date_received >= start_date)
    if end_date:
        query = query.filter(MoyensPaiementHorsMonetique.date_received <= end_date)

    # Récupérer les données filtrées
    données = query.order_by(MoyensPaiementHorsMonetique.date_received.desc()).all()

    # Récupérer tous les noms d'agences disponibles pour le filtre
    agency_names = MoyensPaiementHorsMonetique.query.with_entities(MoyensPaiementHorsMonetique.agency_name).distinct().all()
    agency_names = [agency[0] for agency in agency_names if agency[0]]  # Extraire uniquement les noms non vides

    return render_template('moyens_de_paiement_hors_monetique.html', données=données, agency_names=agency_names)

@main.route('/update_moyens_de_paiement_hors_monetique/<int:id>', methods=['POST'])
@login_required
def update_moyens_de_paiement_hors_monetique(id):
    if current_user.role != 'département_moyens_paiement_hors_monétique':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Mise à jour dans la table MoyensPaiementHorsMonetique
    data = MoyensPaiementHorsMonetique.query.get_or_404(id)
    new_status = request.form['status']
    data.status = new_status
    db.session.commit()

    # Mise à jour dans la table reclamations_generales
    general_data = ReclamationsGenerales.query.filter_by(id=data.reclamation_id).first()
    if general_data:
        general_data.status = new_status
        db.session.commit()
        flash('État mis à jour avec succès dans les deux tables', 'success')
    else:
        flash('Impossible de mettre à jour le statut dans reclamations_generales', 'danger')

    return redirect(url_for('main.moyens_de_paiement_hors_monetique'))

@main.route('/operations_internationales')
@login_required
def operations_internationales():
    if current_user.role != 'département_opération_internationales':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Récupérer les paramètres de filtre
    status_filter = request.args.get('status', '')
    agency_name_filter = request.args.get('agency_name', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Construire la requête de base
    query = OperationsInternationales.query

    # Appliquer le filtre de statut si présent
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Appliquer le filtre de nom d'agence si présent
    if agency_name_filter:
        query = query.filter_by(agency_name=agency_name_filter)

    # Appliquer le filtre de date si les dates sont présentes
    if start_date:
        query = query.filter(OperationsInternationales.date_received >= start_date)
    if end_date:
        query = query.filter(OperationsInternationales.date_received <= end_date)

    # Récupérer les données filtrées
    données = query.order_by(OperationsInternationales.date_received.desc()).all()

    # Récupérer tous les noms d'agences disponibles pour le filtre
    agency_names = OperationsInternationales.query.with_entities(OperationsInternationales.agency_name).distinct().all()
    agency_names = [agency[0] for agency in agency_names if agency[0]]  # Extraire uniquement les noms non vides

    return render_template('operations_internationales.html', données=données, agency_names=agency_names)


@main.route('/update_operations_internationales/<int:id>', methods=['POST'])
@login_required
def update_operations_internationales(id):
    if current_user.role != 'département_opération_internationales':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Mise à jour dans la table OperationsInternationales
    data = OperationsInternationales.query.get_or_404(id)
    new_status = request.form['status']
    data.status = new_status
    db.session.commit()

    # Mise à jour dans la table reclamations_generales
    general_data = ReclamationsGenerales.query.filter_by(id=data.reclamation_id).first()
    if general_data:
        general_data.status = new_status
        db.session.commit()
        flash('État mis à jour avec succès dans les deux tables', 'success')
    else:
        flash('Impossible de mettre à jour le statut dans reclamations_generales', 'danger')

    return redirect(url_for('main.operations_internationales'))



@main.route('/services_bancaires_distance')
@login_required
def services_bancaires_distance():
    if current_user.role != 'département_services_banquaires_distance':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Récupérer les paramètres de filtre
    status_filter = request.args.get('status', '')
    agency_name_filter = request.args.get('agency_name', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Construire la requête de base
    query = ServicesBancairesDistance.query

    # Appliquer le filtre de statut si présent
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Appliquer le filtre de nom d'agence si présent
    if agency_name_filter:
        query = query.filter_by(agency_name=agency_name_filter)

    # Appliquer le filtre de date si les dates sont présentes
    if start_date:
        query = query.filter(ServicesBancairesDistance.date_received >= start_date)
    if end_date:
        query = query.filter(ServicesBancairesDistance.date_received <= end_date)

    # Récupérer les données filtrées
    données = query.order_by(ServicesBancairesDistance.date_received.desc()).all()

    # Récupérer tous les noms d'agences disponibles pour le filtre
    agency_names = ServicesBancairesDistance.query.with_entities(ServicesBancairesDistance.agency_name).distinct().all()
    agency_names = [agency[0] for agency in agency_names if agency[0]]  # Extraire uniquement les noms non vides

    return render_template('services_bancaires_distance.html', données=données, agency_names=agency_names)


@main.route('/update_services_bancaires_distance/<int:id>', methods=['POST'])
@login_required
def update_services_bancaires_distance(id):
    if current_user.role != 'département_services_banquaires_distance':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Mise à jour dans la table ServicesBancairesDistance
    data = ServicesBancairesDistance.query.get_or_404(id)
    new_status = request.form['status']
    data.status = new_status
    db.session.commit()

    # Mise à jour dans la table reclamations_generales
    general_data = ReclamationsGenerales.query.filter_by(id=data.reclamation_id).first()
    if general_data:
        general_data.status = new_status
        db.session.commit()
        flash('État mis à jour avec succès dans les deux tables', 'success')
    else:
        flash('Impossible de mettre à jour le statut dans reclamations_generales', 'danger')

    return redirect(url_for('main.services_bancaires_distance'))



# Dictionnaire pour mapper les départements à leurs modèles
DEPARTMENT_MODELS = {
    'accueil_qualite_service': AccueilQualiteService,
    'monetique': Monetique,
    'fonctionnement_de_comptes': FonctionnementDeComptes,
    'credit': Credit,
    'moyens_de_paiement_hors_monetique': MoyensPaiementHorsMonetique,
    'operations_internationales': OperationsInternationales,
    'services_bancaires_distance': ServicesBancairesDistance,
    'reclamations_generales' : ReclamationsGenerales,
}


@main.route('/reply/<string:department>/<int:id>', methods=['POST'])
@login_required
def reply(department, id):
    model = DEPARTMENT_MODELS.get(department)
    if not model:
        flash('Invalid department', 'danger')
        return redirect(url_for('main.dashboard'))
    
    data = model.query.get_or_404(id)
    subject = request.form['subject']
    body = request.form['body']
    
    msg = Message(subject, sender='assitantstb@outlook.com', recipients=[data.sender])
    msg.body = body
    mail.send(msg)
    
    flash('Email sent successfully!', 'success')
    return redirect(url_for(f'main.{department}'))


@main.route('/reclamations_generales')
@login_required
def reclamations_generales():
    if current_user.role != 'admin':  # Vérifiez que seul l'administrateur a accès à cette route
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))

    # Récupérer les paramètres de filtre
    status_filter = request.args.get('status', '')
    agency_name_filter = request.args.get('agency_name', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    category_filter = request.args.get('predicted_category', '')
    type_filter = request.args.get('predicted_type', '')

    # Construire la requête de base
    query = ReclamationsGenerales.query

    # Appliquer le filtre de statut si présent
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Appliquer le filtre de nom d'agence si présent
    if agency_name_filter:
        query = query.filter_by(agency_name=agency_name_filter)

    # Appliquer le filtre de date si les dates sont présentes
    if start_date:
        query = query.filter(ReclamationsGenerales.date_received >= start_date)
    if end_date:
        query = query.filter(ReclamationsGenerales.date_received <= end_date)

    # Appliquer le filtre de catégorie prédite si présent
    if category_filter:
        query = query.filter_by(predicted_category=category_filter)

    # Appliquer le filtre de type prédit si présent
    if type_filter:
        query = query.filter_by(predicted_type=type_filter)

    # Récupérer les données filtrées
    données = query.order_by(ReclamationsGenerales.date_received.desc()).all()

    # Récupérer tous les noms d'agences disponibles pour le filtre
    agency_names = ReclamationsGenerales.query.with_entities(ReclamationsGenerales.agency_name).distinct().all()
    agency_names = [agency[0] for agency in agency_names if agency[0]]  # Extraire uniquement les noms non vides

    # Récupérer toutes les catégories prédites disponibles pour le filtre
    predicted_categories = ReclamationsGenerales.query.with_entities(ReclamationsGenerales.predicted_category).distinct().all()
    predicted_categories = [category[0] for category in predicted_categories if category[0]]  # Extraire uniquement les catégories non vides

    # Récupérer tous les types prédits disponibles pour le filtre
    predicted_types = ReclamationsGenerales.query.with_entities(ReclamationsGenerales.predicted_type).distinct().all()
    predicted_types = [type_[0] for type_ in predicted_types if type_[0]]  # Extraire uniquement les types non vides

    return render_template('reclamations_generales.html', données=données, agency_names=agency_names, predicted_categories=predicted_categories, predicted_types=predicted_types)


@main.route('/conversations')
@login_required
def conversations():
    departments = [
        'departement_monétique', 
        'département_fonctionnement_de_compte', 
        'département_accueil_qualité_service', 
        'departement_crédit', 
        'département_services_banquaires_distance', 
        'département_opération_internationales', 
        'département_moyens_paiement_hors_monétique'
    ]
    
    unread_messages_count = current_user.unread_messages_count()

    if current_user.role == 'admin':
        conversations = Conversation.query.all()
    else:
        conversations = Conversation.query.filter(
            Conversation.participants.any(User.id == current_user.id)
        ).all()
    
    return render_template('conversations.html', 
                           conversations=conversations, 
                           departments=departments, 
                           unread_messages_count=unread_messages_count)




@main.route('/start_conversation', methods=['POST'])
@login_required
def start_conversation():
    subject = request.form.get('subject')
    department = request.form.get('department')
    start_date = request.form.get('start_date')
    
    if not subject or not department or not start_date:
        flash('Tous les champs sont obligatoires', 'danger')
        return redirect(url_for('main.conversations'))
    
    start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
    
    department_users = User.query.filter_by(role=department).all()
    
    conversation = Conversation(subject=subject, start_date=start_date, admin_id=current_user.id, department=department)
    
    # Ajouter l'utilisateur actuel s'il n'est pas déjà dans les participants
    if current_user not in conversation.participants:
        conversation.participants.append(current_user)
    
    # Ajouter les utilisateurs du département s'ils ne sont pas déjà dans les participants
    for user in department_users:
        if user not in conversation.participants:
            conversation.participants.append(user)
    
    db.session.add(conversation)
    db.session.commit()
    
    flash('Conversation démarrée avec succès', 'success')
    return redirect(url_for('main.conversations'))




@main.route('/conversation/<int:conversation_id>', methods=['GET', 'POST'])
@login_required
def view_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    messages = Messages.query.filter_by(conversation_id=conversation_id).order_by(Messages.timestamp).all()
    
    # Mark messages as read for the current user if they are not the sender
    for message in messages:
        if message.sender_id != current_user.id and not message.is_read:
            message.is_read = True
    db.session.commit()
    
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            new_message = Messages(content=content, sender_id=current_user.id, conversation_id=conversation_id)
            db.session.add(new_message)
            db.session.commit()
            return redirect(url_for('main.view_conversation', conversation_id=conversation_id))
    
    return render_template('conversation.html', conversation=conversation, messages=messages)




@main.route('/send_message/<int:conversation_id>', methods=['POST'])
@login_required
def send_message(conversation_id):
    content = request.form.get('content')
    if not content:
        flash('Le message ne peut pas être vide', 'danger')
        return redirect(url_for('main.view_conversation', conversation_id=conversation_id))
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    message = Messages(content=content, sender_id=current_user.id, conversation_id=conversation_id)
    db.session.add(message)
    db.session.commit()
    
    flash('Message envoyé avec succès', 'success')
    return redirect(url_for('main.view_conversation', conversation_id=conversation_id))


from flask import render_template, jsonify



@main.route('/statistics')
def statistics():
    reclamations_by_department = Statistics.get_reclamations_by_department()
    reclamations_by_status = Statistics.get_reclamations_by_status()
    reclamations_by_month = Statistics.get_reclamations_by_month()
    user_activity = Statistics.get_user_activity()

    # Convertir les résultats en listes de dictionnaires
    reclamations_by_department = [{"department": row[0], "count": row[1]} for row in reclamations_by_department]
    reclamations_by_status = [{"status": row[0], "count": row[1]} for row in reclamations_by_status]
    reclamations_by_month = [{"month": row[0].strftime('%Y-%m'), "count": row[1]} for row in reclamations_by_month]
    user_activity = [{"username": row[0], "count": row[1]} for row in user_activity]

    return render_template('statistics.html', 
                           reclamations_by_department=reclamations_by_department, 
                           reclamations_by_status=reclamations_by_status, 
                           reclamations_by_month=reclamations_by_month,
                           user_activity=user_activity)


def filter_reclamations(model, search='', status_filter=''):
    query = model.query

    # Appliquer la recherche si présente
    if search:
        query = query.filter(model.subject.ilike(f'%{search}%') | model.body.ilike(f'%{search}%'))

    # Appliquer le filtre de statut si présent
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Retourner les réclamations filtrées
    return query.order_by(model.date_received.desc()).all()

@main.context_processor
def inject_unread_messages_count():
    unread_messages_count = current_user.unread_messages_count() if current_user.is_authenticated else 0
    return dict(unread_messages_count=unread_messages_count)
