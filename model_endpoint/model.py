import torch
import pickle
import os
import torch.nn as nn
from datetime import datetime
from model_endpoint import db
from . import db
from flask_login import UserMixin

# Define BiLSTMModel class
class BiLSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout_prob, num_layers):
        super(BiLSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=num_layers, batch_first=True, bidirectional=True)
        self.dropout = nn.Dropout(dropout_prob)
        self.layer_norm = nn.LayerNorm(hidden_dim * 2)
        self.fc = nn.Linear(hidden_dim * 2, output_dim)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        lstm_out = self.dropout(lstm_out)
        lstm_out = self.layer_norm(lstm_out[:, -1, :])
        out = self.fc(lstm_out)
        return out
    
input_dim = 1000  # Replace with your input dimension
hidden_dim = 256
output_dim = 7  # Replace with your number of classes
dropout_prob = 0.6940775997194615
num_layers = 1

MODEL_PATH = os.path.join(os.path.dirname(__file__), "C:\\Users\\MSI\\Documents\\PFE_firas\\models_savings")
VECTOR_PATH = os.path.join(os.path.dirname(__file__), "C:\\Users\\MSI\\Documents\\PFE_firas\\input_data\\vectorizer.pkl")
LABEL_ENCODER_PATH = os.path.join(os.path.dirname(__file__), "C:\\Users\\MSI\\Documents\\PFE_firas\\input_data\\label_encoder.pkl")
LABEL_ENCODER_TYPE_PATH = os.path.join(os.path.dirname(__file__), "C:\\Users\\MSI\\Documents\\PFE_firas\\input_data\\label_encoder_type.pkl")

NAIVE_BAYES_MODEL_PATH = os.path.join(os.path.dirname(__file__), "C:\\Users\\MSI\\Documents\\PFE_firas\\models_savings\\naive_bayes_model.pkl")


bilstm_model = BiLSTMModel(input_dim, hidden_dim, output_dim, dropout_prob, num_layers)
bilstm_model.load_state_dict(torch.load(os.path.join(MODEL_PATH, "C:\\Users\\MSI\\Documents\\PFE_firas\\models_savings\\bilstm_model.pth")))
bilstm_model.eval()

# Charger le vectorizer et le label encoder
with open(VECTOR_PATH, 'rb') as f:
    vectorizer = pickle.load(f)

with open(LABEL_ENCODER_PATH, 'rb') as f:
    label_encoder = pickle.load(f)

with open(LABEL_ENCODER_TYPE_PATH, 'rb') as f:
    label_encoder_type  = pickle.load(f)
# Load the Naive Bayes model
with open(NAIVE_BAYES_MODEL_PATH, 'rb') as model_file:
    naive_bayes_model = pickle.load(model_file)


class User(db.Model, UserMixin):
    __tablename__ = 'users'  
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    _is_active = db.Column(db.Boolean, default=False)
    messages_sent = db.relationship('Messages', backref='sender', lazy=True)
    

    def unread_messages_count(self):
        return Messages.query.filter(
            Messages.conversation_id.in_(
                db.session.query(conversation_participants.c.conversation_id).filter_by(user_id=self.id)
            ),
            Messages.is_read == False,
            Messages.sender_id != self.id
        ).count()


    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}', '{self.is_active}')"
    
class AccueilQualiteService(db.Model):
    __tablename__ = 'accueil_qualite_service'
    id = db.Column(db.Integer, primary_key=True)
    reclamation_id = db.Column(db.String(100), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    cin = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='non traité')
    date_received = db.Column(db.DateTime, nullable=False)
    agency_name = db.Column(db.String(100), nullable=False)
    agency_code = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<AccueilQualiteService {self.id}>'
    
class Credit(db.Model):
    __tablename__ = 'crédit'
    id = db.Column(db.Integer, primary_key=True)
    reclamation_id = db.Column(db.String(100), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    cin = db.Column(db.String(50), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    agency_name = db.Column(db.String(100), nullable=False)
    agency_code = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='non traité')
    date_received = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Crédit {self.id}>'    
    
class FonctionnementDeComptes(db.Model):
    __tablename__ = 'fonctionnement_de_comptes'
    id = db.Column(db.Integer, primary_key=True)
    reclamation_id = db.Column(db.String(100), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    cin = db.Column(db.String(50), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    agency_name = db.Column(db.String(100), nullable=True)
    agency_code = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='non traité')
    date_received = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<FonctionnementDeComptes {self.id}>'
    
class Monetique(db.Model):
    __tablename__ = 'monétique'
    id = db.Column(db.Integer, primary_key=True)
    reclamation_id = db.Column(db.String(100), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    cin = db.Column(db.String(50), nullable=True)
    card_number = db.Column(db.String(50), nullable=True)
    agency_name = db.Column(db.String(100), nullable=True)
    agency_code = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='non traité')
    date_received = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Monetique {self.id}>'

class MoyensPaiementHorsMonetique(db.Model):
    __tablename__ = 'moyens_de_paiement_hors_monétique'
    id = db.Column(db.Integer, primary_key=True)
    reclamation_id = db.Column(db.String(100), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    cin = db.Column(db.String(50), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    agency_name = db.Column(db.String(100), nullable=True)
    agency_code = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='non traité')
    date_received = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<MoyensPaiementHorsMonetique {self.id}>'

class OperationsInternationales(db.Model):
    __tablename__ = 'operations_internationales'
    id = db.Column(db.Integer, primary_key=True)
    reclamation_id = db.Column(db.String(100), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    cin = db.Column(db.String(50), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    agency_name = db.Column(db.String(100), nullable=True)
    agency_code = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='non traité')
    date_received = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<OperationsInternationales {self.id}>'

class ServicesBancairesDistance(db.Model):
    __tablename__ = 'services_bancaires_distance'
    id = db.Column(db.Integer, primary_key=True)
    reclamation_id = db.Column(db.String(100), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    cin = db.Column(db.String(50), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    agency_name = db.Column(db.String(100), nullable=True)
    agency_code = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='non traité')
    date_received = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<ServicesBancairesDistance {self.id}>'


class ReclamationsGenerales(db.Model):
    __tablename__ = 'reclamations_generales'
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    predicted_category = db.Column(db.String(100), nullable=False)
    predicted_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='non traité')
    date_received = db.Column(db.DateTime, nullable=False)
    agency_name = db.Column(db.String(100), nullable=True)
    

    def __repr__(self):
        return f'<ReclamationsGenerales {self.id}>'
    
conversation_participants = db.Table('conversation_participants',
    db.Column('conversation_id', db.Integer, db.ForeignKey('conversation.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)    
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    admin = db.relationship('User', backref='started_conversations', foreign_keys=[admin_id])
    participants = db.relationship('User', secondary=conversation_participants, backref=db.backref('conversations', lazy='dynamic'))
    messages = db.relationship('Messages', backref='conversation', lazy=True)  # Ajouter cette ligne pour la relation
    
    def has_unread_messages(self, user_id):
        return any(not message.is_read and message.sender_id != user_id for message in self.messages)

class Messages(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)

from sqlalchemy.sql import func


class Statistics:
    @staticmethod
    def get_reclamations_by_department():
        return db.session.query(
            ReclamationsGenerales.predicted_category, func.count(ReclamationsGenerales.id)
        ).group_by(ReclamationsGenerales.predicted_category).all()
    
    @staticmethod
    def get_reclamations_by_status():
        return db.session.query(
            ReclamationsGenerales.status, func.count(ReclamationsGenerales.id)
        ).group_by(ReclamationsGenerales.status).all()

    @staticmethod
    def get_reclamations_by_month():
        return db.session.query(
            func.date_trunc('month', ReclamationsGenerales.date_received), func.count(ReclamationsGenerales.id)
        ).group_by(func.date_trunc('month', ReclamationsGenerales.date_received)).all()

    @staticmethod
    def get_average_processing_time():
        return db.session.query(
            func.avg(func.julianday(ReclamationsGenerales.date_resolved) - func.julianday(ReclamationsGenerales.date_received))
        ).filter(ReclamationsGenerales.date_resolved != None).scalar()

    @staticmethod
    def get_user_activity():
        return db.session.query(
            User.username, func.count(Messages.id)
        ).join(Messages).group_by(User.username).all()
    
class Rapport(db.Model):
    __tablename__ = 'rapport'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reclamation_id = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    rapport_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Rapport {self.id}>'