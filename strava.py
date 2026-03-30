import os
import requests

def get_fresh_access_token():
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
    
    if not refresh_token:
        print("Geen STRAVA_REFRESH_TOKEN gevonden in de configuratie!")
        return None
        
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get('access_token')
    else:
        print(f"Fout bij het vernieuwen van de Strava token: {response.text}")
        return None

def get_activity_details(activity_id):
    access_token = get_fresh_access_token()
    if not access_token:
        return None
        
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    # Via deze API halen we alle details van de run op
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Fout bij ophalen van activiteit {activity_id}: {response.text}")
        return None
