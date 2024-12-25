import re
import pandas as pd
import imaplib
import email
import smtplib
import torch
from langdetect import detect
from .utils import preprocess_text
from .model import bilstm_model, label_encoder, label_encoder_type, naive_bayes_model, vectorizer
import nltk
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
import psycopg2
from datetime import datetime
nltk.download('words')
from email.utils import formataddr
from email.message import EmailMessage


french_words = set(nltk.corpus.words.words())

class Automatisation:
    def __init__(self, mail_server, mail_username, mail_password, smtp_server, smtp_port,imap_port, smtp_username, smtp_password, vectorizer, bilstm_model, naive_bayes_model, label_encoder, label_encoder_type):
        self.mail_server = mail_server
        self.mail_username = mail_username
        self.mail_password = mail_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_port= imap_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.vectorizer = vectorizer
        self.bilstm_model = bilstm_model
        self.naive_bayes_model = naive_bayes_model
        self.label_encoder = label_encoder
        self.label_encoder_type = label_encoder_type
        self.df = pd.read_excel("C:\\Users\\MSI\\Documents\\PFE_firas\\input_data\\Book1.xlsx")
        self.knowledge_base = {
            "Quel est votre numéro de téléphone ?": "Notre numéro de téléphone est +1234567890.",
            "Bonjour,quels sont vos heures d'ouverture ?": "Nous sommes ouverts de 9h à 17h du lundi au vendredi."
        }
        self.categories_emails = {
            "crédit": "firasmohsni5@gmail.com",
            "monétique": "benromdhanea35@gmail.com",
            "fonctionnement de comptes": "achoury637@gmail.com",
            "paiement hors monétique": "paiement@example.com",
            "accueil et qualité de service": "achoury637@gmail.com",
            "services bancaires à distance": "mohamedfiras.mohsni@esprit.tn",
            "opérations bancaires internationales": "firasmohsni13@gmail.com"
        }
        self.conn = psycopg2.connect(database="Reclam_Demo",user="postgres",password="firas",host="localhost",client_encoding='utf-8')

    def predict_category(self, email_body):
        preprocessed_text = preprocess_text(email_body)
        vectorized_text = self.vectorizer.transform([preprocessed_text]).toarray()
        input_tensor = torch.tensor(vectorized_text, dtype=torch.float32).unsqueeze(1)
        self.bilstm_model.eval()
        with torch.no_grad():
            output_category = self.bilstm_model(input_tensor)
            _, predicted_category = torch.max(output_category, 1)
            category = self.label_encoder.inverse_transform(predicted_category.numpy())[0]
        return category

    def predict_type(self, email_body):
        vectorized_text = self.vectorizer.transform([email_body]).toarray()
        type_prediction = self.naive_bayes_model.predict(vectorized_text)
        type_ = self.label_encoder_type.inverse_transform(type_prediction)[0]
        return type_
    

    def search_for_agence(self, text):
            patterns = [
                r"l'agence\s+([a-zA-Z\s]+)",
                r"de l'agence\s+([a-zA-Z\s]+)",
                r"l'agence de\s+([a-zA-Z\s]+)",
                r"de\s+([a-zA-Z\s]+)\s+l'agence\s*de\s*([a-zA-Z\s]+)",
                r"l'agence\s*de\s*([a-zA-Z\s]+)",
                r"de\s+([a-zA-Z\s]+)\s+l'agence",
                r"del'agence\s*de\s*([a-zA-Z\s]+)",
                r"agence\s+([a-zA-Z\s]+)"
                
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    detected_text = match.group(1).strip().upper()
                    print("Nom d'agence détecté avant nettoyage :", detected_text)
                    
                    # Comparer chaque mot avec les noms des agences
                    for agency in self.df["AGENCES"].str.upper().values:
                        if agency in detected_text:
                            print("Nom d'agence détecté après nettoyage :", agency)
                            agency_row = self.df[self.df["AGENCES"].str.upper() == agency]
                            agency_code = str(int(agency_row["INDICE AG"].iloc[0])).zfill(3)
                            return agency.title(), agency_code  # Retourne le nom en format titre
            return None, None
    def detect_account_number(self,text):
        # Rechercher une série de 10 chiffres dans le texte
        match = re.search(r'\b\d{10}\b', text)
        if match:
            return match.group(0)  # Retourner le numéro de compte trouvé
        else:
            return None  # Retourner None si aucun numéro de compte n'est trouvé

    def extract_agency_code(self,account_number):
        if account_number:
            agency_code = account_number[:3]
            return agency_code  
        else:
            return None

    def extract_question(self, body):
        body = body.strip()
        sentences = nltk.sent_tokenize(body)
        for sentence in sentences:
            if re.search(r'\?$', sentence):
                return sentence
        print(sentence)
        return None

    def send_response(self, receiver_email, subject, response):
        if response.strip():
            try:
                # Création du message avec EmailMessage qui gère bien l'encodage
                msg = EmailMessage()
                msg.set_content(response, subtype='plain', charset='utf-8')
                msg['Subject'] = subject
                msg['From'] = self.smtp_username
                msg['To'] = receiver_email

                # Envoi du message
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                print("Réponse à l'e-mail envoyée avec succès.")
                server.quit()
            except Exception as e:
                print(f"Erreur lors de l'envoi de la réponse par e-mail: {e}")
        else:
            print("La réponse est vide. Aucun e-mail ne sera envoyé.")
            
    def process_incoming_emails(self):
        try:
            mail = imaplib.IMAP4_SSL(self.mail_server)
            mail.login(self.mail_username, self.mail_password)
            mail.select('inbox')

            result, data = mail.search(None, 'UNSEEN')
            if result == 'OK':
                email_ids = data[0].split()
                for num in email_ids:
                    typ, data = mail.fetch(num, '(RFC822)')
                    raw_email = data[0][1]
                    email_message = email.message_from_bytes(raw_email)

                    email_processed = False

                    if email_processed:
                        print("Cet e-mail a déjà été traité. Passez à l'e-mail suivant.")
                        continue

                    self.process_email(email_message)
                    email_processed = True
        except imaplib.IMAP4.error as e:
            print(f"Erreur IMAP: {e}")
        finally:
            try:
                mail.close()
            except Exception as e:
                print(f"Erreur lors de la fermeture de la boîte aux lettres: {e}")
            try:
                mail.logout()
            except Exception as e:
                print(f"Erreur lors de la déconnexion: {e}")    

    def send_confirmation_to_sender(self, sender_email):
        confirmation_subject = "Confirmation de réception de votre email"
        confirmation_message = "Bonjour,\n\nNous avons bien reçu votre email et il est actuellement en cours de traitement. Nous vous répondrons dans les plus brefs délais.\n\nCordialement,\nL'équipe de support"
        msg = MIMEText(confirmation_message)
        msg['From'] = self.smtp_username
        msg['To'] = sender_email
        msg['Subject'] = confirmation_subject
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.smtp_username, sender_email, msg.as_string())
            print("Confirmation email sent successfully.")
            server.quit()
        except Exception as e:
            print(f"Error sending confirmation email: {e}")
    
    def get_agency_name_from_code(self, agency_code):
        # Assurez-vous que le code est bien formaté
        agency_code = str(agency_code).strip().zfill(3)
        
        # Supprimez les espaces avant la comparaison
        self.df["INDICE AG"] = self.df["INDICE AG"].astype(str).str.strip().str.zfill(3)
        
        agency_row = self.df[self.df["INDICE AG"] == agency_code]
        
        print("Recherche du nom de l'agence pour le code :", agency_code)
        print(agency_row)
        
        if not agency_row.empty:
            return agency_row["AGENCES"].values[0]
        else:
            print(f"Aucun nom d'agence trouvé pour le code : {agency_code}")
            return None

            
    def process_email(self, msg):
        sender = msg['From']
        subject = msg['Subject']
        body = ""
        response_subject = ""
        response_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', 'ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', 'ignore')
           

        print("Subject:", repr(subject))
        print("Body Preview:", repr(body[:500]))

        try:
            language = detect(body)
        except:
            language = 'fr'

        if language != 'fr':
            response_subject = "Reformulation de la demande nécessaire"
            response_body = "Cher client,\n\nNous avons remarqué que votre demande est dans une langue autre que le français. Veuillez reformuler votre demande de manière claire et précise.\n\nMerci.\nVotre Banque STB"
            self.send_response(sender, response_subject, response_body)
        else:
            if not body.strip() or len(body.split()) < 5 or not any(word.lower() in french_words for word in body.split()):
                response_subject = "Reformulation de la demande nécessaire"
                response_body = "Cher client,\n\nNous avons remarqué que votre e-mail est mal formulé ou vide. Veuillez reformuler votre demande de manière claire et précise.\n\nMerci.\nVotre Banque STB"
                self.send_response(sender, response_subject, response_body)
            else:
                cleaned_body = preprocess_text(body)
                predicted_category = self.predict_category(cleaned_body)
                predicted_type = self.predict_type(cleaned_body)

                print(f"E-mail reçu de {sender} avec le sujet : {subject}")
                print(f"Corps de l'e-mail : {body}")
                print(f"Type prédit de la réclamation ou de la requête : il s'agit de {predicted_type}")
                print(f"Catégorie prédite : {predicted_category}")

                if predicted_type == "Réclamation":
                    card_code_found = re.search(r'\b\d{16}\b', body)
                    card_code=card_code_found.group(0) if card_code_found else None
                    cin_found = re.search(r'\b\d{8}\b', body)
                    cin=cin_found.group(0) if cin_found else None
                    
                    acc_num = self.detect_account_number(body)
                    agency_code_from_acc_num = self.extract_agency_code(acc_num)
                    agency_name, agency_code = self.search_for_agence(body)

                    if agency_name:
                        agency_row = self.df[self.df["AGENCES"].str.upper() == agency_name.upper()]
                        if not agency_row.empty:
                            agency_code = str(int(agency_row["INDICE AG"].iloc[0])).zfill(3)
                        else:
                            agency_name = None

                    if agency_code_from_acc_num and not agency_name:
                        agency_name = self.get_agency_name_from_code(agency_code_from_acc_num)
                        agency_code = agency_code_from_acc_num if agency_name else None

                    print(f"Nom agence trouvé : {agency_name}")
                    print(f"Code agence trouvé : {agency_code}")

                    missing_details = []
                    if predicted_category in ["fonctionnement de comptes", "opérations bancaires internationales",
                                              "moyens de paiement hors monétique", "services bancaires à distance",
                                              "crédit"]:
                        if not cin_found:
                           missing_details.append("CIN")
                        if not acc_num:
                            missing_details.append("numéro de compte")
                        if not agency_code and not agency_code_from_acc_num:
                           missing_details.append("code d'agence")
                        elif not agency_name:
                           missing_details.append("nom agence")
                    elif predicted_category == "monétique":
                        if not cin_found:
                             missing_details.append("CIN")
                        if not card_code_found:
                             missing_details.append("code de la carte")
                        if not agency_name:
                            missing_details.append("nom agence")
                    elif predicted_category == "accueil et qualité de service":
                        if not (cin_found and (agency_code or agency_code_from_acc_num)):
                            missing_details.extend(["CIN", "code/nom d'agence"])
                    email_data = {
                        'sender': sender,
                        'subject': subject,
                        'body': body,
                        'predicted_category': predicted_category,
                        'predicted_type': predicted_type,
                        'date_received': datetime.now(),
                        'cin': cin if cin else False,
                        'account_number': acc_num if acc_num else False,
                        'card_number': card_code if card_code else False,
                        'agency_name': agency_name if agency_name else False,
                        'agency_code': agency_code if agency_code else (agency_code_from_acc_num if agency_code_from_acc_num else False)
                    }
                    # Sauvegarde des données générales avant vérification des détails manquants
                    general_email_id = self.store_email_general(email_data)

                    if missing_details:
                        response_subject = "Informations manquantes"
                        response_body = f"Il manque certaines informations essentielles pour traiter votre demande ({', '.join(missing_details)}). Veuillez fournir ces détails pour continuer.\n\nCordialement,\nL'équipe de support"
                   
                    else:
                        response_subject = "Demande en cours de traitement"
                        response_body = "Bonjour,\n\nNous avons bien reçu votre email et il est actuellement en cours de traitement.Nous vous répondrons dans les plus brefs délais.\n\nCordialement,\nL'équipe de support"
                        specific_data = {
                            'reclamation_id': general_email_id,
                            'cin': email_data['cin'],
                            'account_number': email_data['account_number'],
                            'sender': sender,
                            'subject': subject,
                            'body': body,
                            'agency_name': email_data['agency_name'],
                            'agency_code': email_data['agency_code']
                        }

                        specific_data_monétique = {
                            'reclamation_id': general_email_id,
                            'cin': email_data['cin'],
                            'sender': sender,
                            'subject': subject,
                            'body': body,
                            'card_number': email_data['card_number'],
                            'agency_name': email_data['agency_name'],
                            'agency_code': email_data['agency_code']
                        }
                        specific_data_accueil = {
                            'reclamation_id': general_email_id,
                            'cin': email_data['cin'],
                            'sender': sender,
                            'subject': subject,
                            'body': body,
                            'agency_name': email_data['agency_name'],
                            'agency_code': email_data['agency_code']    
                            }

                        if predicted_category == "monétique":
                            self.store_specific_email("monétique", specific_data_monétique)
                        elif predicted_category in ["fonctionnement de comptes", "opérations bancaires internationales",
                                                    "moyens de paiement hors monétique", "services bancaires à distance",
                                                    "crédit"]:
                            self.store_specific_email(predicted_category.replace(" ", "_"), specific_data)
                        elif predicted_category == "accueil et qualité de service":
                            
                            self.store_specific_email("accueil_qualite_service", specific_data_accueil)
                        
                    self.send_response(sender, response_subject, response_body)

                elif predicted_type == "Requête":
                        question = self.extract_question(body)
                        print(f"Question extraite : {question}")

                        email_data = {
                            'sender': sender,
                            'subject': subject,
                            'body': body,
                            'predicted_category': predicted_category,
                            'predicted_type': predicted_type,
                            'date_received': datetime.now(),
                            'question': question
                        }

                        # Sauvegarde des données générales
                        general_email_id = self.store_email_general(email_data)
                        print(f"Email ID généré après le stockage général : {general_email_id}")

                        # Si une question est détectée
                        if question:
                            if question in ["Comment créer un livret d'épargne à distance?", "Comment créer un compte bancaire à distance?"]:
                                response_subject = "Création d'un compte à distance"
                                response_body = "Pour créer un compte à distance avec la Banque STB, veuillez suivre ces étapes :\n\n"
                                response_body += "1. Visitez notre site web officiel : [Banque STB](https://stbdigital.stb.com.tn/stbeverywhere)\n"
                                response_body += "2. Cliquez sur 'Menu'\n"
                                response_body += "3. Sélectionnez 'Devenir client'\n"
                                response_body += "4. Suivez les instructions pour compléter le processus d'inscription en ligne.\n"
                                response_body += "\nSi vous avez besoin d'assistance supplémentaire, n'hésitez pas à nous contacter."
                                self.send_response(sender, response_subject, response_body)
                            elif question in self.knowledge_base:
                                answer = self.knowledge_base[question]
                                self.send_response(sender, subject, answer)
                                print("Réponse à la question envoyée avec succès.")
                            else:
                                # Si la question n'est pas dans la base de connaissances
                                print("Question non trouvée dans la base de connaissances. L'e-mail sera routé normalement.")
                                category_email = self.categories_emails.get(predicted_category, "botmail766@gmail.com")
                                self.send_confirmation_to_sender(sender)
                        else:
                            # Si aucune question n'est détectée, traiter comme une requête normale
                            specific_data = {
                                'reclamation_id': general_email_id,
                                'sender': sender,
                                'subject': subject,
                                'body': body,
                                'question': question,
                                'predicted_category': predicted_category,
                            }

                            if predicted_category in ["fonctionnement de comptes", "opérations bancaires internationales",
                                                    "moyens de paiement hors monétique", "services bancaires à distance",
                                                    "crédit"]:
                                self.store_specific_email(predicted_category.replace(" ", "_"), specific_data)
                            elif predicted_category == "monétique":
                                self.store_specific_email("monétique", specific_data)
                            elif predicted_category == "accueil et qualité de service":
                                self.store_specific_email("accueil_qualite_service", specific_data)

                        # Vérification et réponse aux questions spécifiques sur les prêts
                        if question in ["Comment avoir un prêt auto?", "Comment avoir un prêt épargne logement?",
                                        "Comment avoir un prêt computer?", "Comment avoir un prêt épargne confort?",
                                        "Comment avoir un prêt épargne étude?", "Comment avoir un crédit direct?",
                                        "Comment avoir un crédit Eslah Masken?", "Comment avoir un crédit habitat?"]:
                            response_subject = "Informations sur les prêts et crédits"
                            response_body = "Pour obtenir plus d'informations sur les différents types de prêts et crédits que nous proposons, veuillez consulter le lien suivant :\n\n"
                            response_body += "[Informations sur les prêts et crédits](https://bit.ly/3cEUP7H)"
                            self.send_response(sender, response_subject, response_body)
                        else:
                            print("Aucune question trouvée ou traitée spécifiquement.")

                        
    def store_email_general(self, email_data):
        query = """
        INSERT INTO reclamations_generales (sender, subject, body, predicted_category, predicted_type, date_received, agency_name, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (
                    email_data['sender'], 
                    email_data['subject'], 
                    email_data['body'], 
                    email_data['predicted_category'], 
                    email_data['predicted_type'], 
                    email_data['date_received'],
                    email_data.get('agency_name', 'False'),  # Ajoute agency_name ou None si non défini
                    email_data.get('status', 'non traitée')  # Ajoute status ou 'pending' par défaut
                ))
                reclamation_id = cursor.fetchone()[0]
            self.conn.commit()
            return reclamation_id
        except Exception as e:
            print(f"Error storing general email: {e}")
            self.conn.rollback()
            return None
        
        
    def store_specific_email(self, table_name, data):
        placeholders = ", ".join(["%s"] * len(data))
        columns = ", ".join(data.keys())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, list(data.values()))
            self.conn.commit()
        except Exception as e:
            print(f"Error storing specific email in {table_name}: {e}")
            self.conn.rollback()

