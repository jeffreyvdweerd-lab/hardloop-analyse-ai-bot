import os
import smtplib
from email.message import EmailMessage

def send_analysis_email(analysis_text, activity_name):
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp-mail.outlook.com")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 587))
    
    if not email_address or not email_password:
        print("Geen e-mailgegevens gevonden in de configuratie (.env). Kan niet mailen.")
        return
    
    msg = EmailMessage()
    msg['Subject'] = f"🟢 Jouw Hardloop Analyse: {activity_name}"
    msg['From'] = email_address
    msg['To'] = email_address
    
    # We zetten de content voor een fallback
    msg.set_content(analysis_text)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(msg)
        print(f"Analyse-mail is verstuurd naar {email_address}!")
    except Exception as e:
        print(f"Fout bij het versturen van SMTP e-mail: {e}")
