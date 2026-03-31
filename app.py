import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import threading

# Load env before importing other modules
load_dotenv()

from strava import get_activity_details
from ai_agent import analyze_run
from mailer import send_analysis_email

app = Flask(__name__)

# Dit is het verificatie-token dat we zelf verzinnen en eenmalig aan Strava moeten doorgeven
VERIFY_TOKEN = "STRAVA_WEBHOOK_VERIFY_TOKEN_KSC"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("Strava Webhook Geverifieerd!")
            return jsonify({"hub.challenge": challenge}), 200
        return 'Forbidden', 403
    return 'Invalid request', 400

processed_activities = set()

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    print("Nieuw bericht van Strava binnen:", data)
    
    # We luisteren bewust naar 'update' ipv 'create', 
    # omdat de gebruiker eerst een doeltitel in Strava moet kunnen uittypen.
    if data.get('object_type') == 'activity' and data.get('aspect_type') == 'update':
        updates = data.get('updates', {})
        
        # We controleren of specifiek de titel óf de beschrijving/notities zojuist is bewerkt.
        if 'title' in updates or 'description' in updates:
            activity_id = data.get('object_id')
            
            # Voorkom dat Render dubbele e-mails stuurt als je snel achter elkaar de titel en daarna de notities aanpast.
            if activity_id not in processed_activities:
                processed_activities.add(activity_id)
                # Leeg het geheugen af en toe veiligheidshalve
                if len(processed_activities) > 100:
                    processed_activities.clear()
                    processed_activities.add(activity_id)
                
                print(f"Trigger! Titel of beschrijving geüpdatet. Start met analasyeren van activiteit {activity_id}...")
                threading.Thread(target=process_activity, args=(activity_id,)).start()
            else:
                print(f"Activiteit {activity_id} was zojuist al verwerkt. Ik voorkom dubbele emails.")
        else:
            print("Update negeren: het was geen wijziging in titel of notities.")
            
    elif data.get('aspect_type') == 'create':
        print("Create event genegeerd: We wachten tot de gebruiker een titel/doel invoert.")
        
    return 'EVENT_RECEIVED', 200

def process_activity(activity_id):
    print(f"Activiteit {activity_id} verwerken...")
    activity_data = get_activity_details(activity_id)
    
    if not activity_data:
        print("Kon activiteit niet ophalen of er trad een fout op.")
        return
        
    # Checken of het überhaupt een hardloopactiviteit is (en geen fietstocht o.i.d.)
    if activity_data.get('type') not in ['Run', 'TrailRun']:
        print("Geen hardloopactiviteit, we slaan deze over.")
        return
        
    activity_name = activity_data.get('name', 'Hardloopsessie')
    
    # 1. AI Analyse uitvoeren
    print("Start AI Analyse...")
    analysis = analyze_run(activity_data)
    
    # 2. E-mail naar onszelf versturen
    print("E-mail wordt verstuurd...")
    send_analysis_email(analysis, activity_name)

if __name__ == '__main__':
    # Luister op alle interfaces voor lokaal of cloud gebruik
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
