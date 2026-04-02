import os
import resend

def send_analysis_email(analysis_text, activity_name):
    resend.api_key = os.getenv("RESEND_API_KEY")
    
    # Exclusief en direct naar het Gmail adres
    to_email = "jeffreyvdweerd@gmail.com"
    
    if not resend.api_key:
        print("WAARSCHUWING: Geen RESEND_API_KEY gevonden in Render. Kan niet mailen.")
        return
        
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [to_email],
            "subject": f"🟢 Jouw Hardloop Analyse: {activity_name}",
            "text": analysis_text
        }

        resend.Emails.send(params)
        print(f"Analyse-mail verzonden via Resend (onboarding@resend.dev) naar {to_email}!")
    except Exception as e:
        print(f"Fout bij het versturen via de Resend API: {e}")
