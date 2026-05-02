import smtplib
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from utils.export_commande import export_commande_excel

def envoyer_commande_email(df_commande, email_destinataire, nom_fournisseur="Fournisseur Portugal"):
    try:
        smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(st.secrets.get("SMTP_PORT", 587))
        email_expediteur = st.secrets.get("EMAIL_EXPEDITEUR", "")
        email_password = st.secrets.get("EMAIL_PASSWORD", "")

        if not email_expediteur or not email_password:
            return False, "❌ Configuration email manquante dans les Secrets."

        buffer = export_commande_excel(
            df_commande,
            nom_societe="Entrepôt Central — Guinée-Bissau",
            pays_fournisseur="Portugal"
        )

        msg = MIMEMultipart()
        msg["From"] = email_expediteur
        msg["To"] = email_destinataire
        msg["Subject"] = f"Bon de Commande — {datetime.now().strftime('%d/%m/%Y')} — Entrepôt Central Guinée-Bissau"

        corps = f"""
Bonjour,

Veuillez trouver ci-joint notre bon de commande du {datetime.now().strftime('%d/%m/%Y')}.

Résumé de la commande :
- Nombre de références : {len(df_commande)}
- Délai de livraison souhaité : 3 à 4 semaines

Merci de confirmer la réception de cette commande.

Cordialement,
Entrepôt Central — Guinée-Bissau
SMD Consulting
        """

        msg.attach(MIMEText(corps, "plain"))

        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f"attachment; filename=Commande_Portugal_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        msg.attach(attachment)

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_expediteur, email_password)
        server.sendmail(email_expediteur, email_destinataire, msg.as_string())
        server.quit()

        return True, f"✅ Email envoyé avec succès à {email_destinataire} !"

    except smtplib.SMTPAuthenticationError:
        return False, "❌ Erreur d'authentification email. Vérifiez vos identifiants."
    except smtplib.SMTPException as e:
        return False, f"❌ Erreur SMTP : {str(e)}"
    except Exception as e:
        return False, f"❌ Erreur : {str(e)}"