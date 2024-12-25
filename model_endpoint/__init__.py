from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:firas@localhost:5432/Reclam_Demo'
    
    # Configuration Flask-Mail
    app.config['MAIL_SERVER'] = 'imap.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'assistantstbbanque@gmail.com'
    app.config['MAIL_PASSWORD'] = 'izzm vhde kllh kvsc'
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    


    login_manager.login_view = 'main.login'

    from model_endpoint.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from model_endpoint.model import User
    from model_endpoint.model import Monetique

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    return app


