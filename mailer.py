import os
import resend

def send_analysis_email(analysis_text, activity_name):
    # Pak de API-sleutel (toegevoegd via Render Environment Variables)
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    # We sturen hem naar het adres waar het Resend account op geregistreerd is
    email_address = os.getenv("EMAIL_ADDRESS")
    
    if not resend.api_key:
        print("Geen RESEND_API_KEY gevonden in de configuratie. Kan niet mailen.")
        return
        
    try:
        # Dit is de razendsnelle HTTP API (vervangt het tragere SMTP)
        params = {
            "from": "onboarding@resend.dev",
            "to": [email_address],
            "subject": f"🟢 Jouw Hardloop Analyse: {activity_name}",
            "text": analysis_text
        }

        r = resend.Emails.send(params)
        print(f"Analyse-mail is via Resend afgeleverd in de inbox van {email_address}!")
    except Exception as e:
        print(f"Fout bij het versturen via de Resend API: {e}")
