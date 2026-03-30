import os
from openai import OpenAI

def format_tempo(snelheid_ms):
    if snelheid_ms > 0:
        tempo_min_per_km = 16.666666666667 / snelheid_ms
        minuten = int(tempo_min_per_km)
        seconden = int((tempo_min_per_km - minuten) * 60)
        return f"{minuten}:{seconden:02d} min/km"
    return "Onbekend"

def analyze_run(activity_data):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    thread_id = os.getenv("OPENAI_THREAD_ID")
    
    if not assistant_id or not thread_id:
        print("Geen OPENAI_ASSISTANT_ID of OPENAI_THREAD_ID gevonden!")
        return "Configuratiefout: OPENAI_ASSISTANT_ID of OPENAI_THREAD_ID is niet ingesteld in Render."

    afstand_km = activity_data.get('distance', 0) / 1000
    tijd_minuten = activity_data.get('moving_time', 0) / 60
    tempo_weergave = format_tempo(activity_data.get('average_speed', 0))
    gem_hr = activity_data.get('average_heartrate', 'Onbekend')
    cadans = activity_data.get('average_cadence', 'Onbekend')
    if cadans != 'Onbekend':
        cadans = cadans * 2 # Strava geeft vaak cadans per been
    notities = activity_data.get('description', 'Geen notities ingevuld in Strava.')

    # Analyse per blok/interval/ronde opbouwen
    laps_info = ""
    laps = activity_data.get('laps', [])
    if laps:
        laps_info += "Hier zijn de gegevens per ronde/lap:\n"
        for lap in laps:
            lap_idx = lap.get('lap_index', 0)
            lap_dist = lap.get('distance', 0) / 1000
            lap_time = lap.get('moving_time', 0) / 60
            lap_tempo = format_tempo(lap.get('average_speed', 0))
            lap_hr = lap.get('average_heartrate', 'Geen data')
            laps_info += f"- Ronde {lap_idx}: {lap_dist:.2f} km in {lap_time:.1f} min (Tempo: {lap_tempo}, Hartslag: {lap_hr} bpm)\n"
    else:
        laps_info = "Er zijn geen gedetailleerde rondes/laps geregistreerd in Garmin/Strava voor deze activiteit."

    prompt = f"""
Nieuwe hardloopactiviteit binnengekomen! Dit is DE IDEALE ANALYSE.

Hier zijn de harde sessiegegevens uit Strava:
- Titel: {activity_data.get('name', 'Onbekend')}
- Afstand: {afstand_km:.2f} km
- Tijd (bewegend): {tijd_minuten:.1f} minuten
- Gemiddeld tempo (pace): {tempo_weergave}
- Gemiddelde hartslag: {gem_hr} bpm
- Maximale hartslag: {activity_data.get('max_heartrate', 'Geen data')} bpm
- Cadans (spm): {cadans}
- Hoogteverschillen: {activity_data.get('total_elevation_gain', 0)} meter
- Notities/Gevoel (uit Strava beschrijving): {notities}

Je MOET exact de volgende structuur en kopjes (inclusief emoticons) overnemen en invullen in je antwoord (gebruik Markdown):

1️⃣ 📊 **Samenvatting (Kort en krachtig dashboard)**: Afstand, Tijd, Gemiddeld tempo, Gemiddelde HR, Max HR.
2️⃣ ❤️ **Hartslag analyse**: Tijd in zones, verloop, opbouw en stabiliteit. Interpretatie: zat ik in de juiste zone? Was er cardiac drift?
3️⃣ 🏃 **Tempo & pacing**: {laps_info}. Interpretatie: te snel gestart? Stabiel? Negatieve split?
4️⃣ ⚙️ **Efficiëntie**: Tempo vs hartslag en Cadans integreren. Interpretatie: zelfde HR met sneller tempo = progressie?
5️⃣ 🔥 **Trainingsbelasting**: Type training (herstel, duur, tempo, interval). Was dit de juiste prikkel? Te zwaar of licht?
6️⃣ 🧠 **Gevoel vs data**: Baseer dit op de Notities: "{notities}". Als er geen notities zijn, geef dan aan waarom het noteren van het gevoel belangrijk is om context te snappen (vermoeidheid vs data).
7️⃣ ⚠️ **Afwijkingen / bijzonderheden**: Hartslag meetfout, stoppen of verkeersmomenten?
8️⃣ 📈 **Progressie check**: Vergelijk ALTIJD met de logboek geschiedenis in deze Thread (tempo vs HR, gevoel vs prestatie t.o.v. vorige runs).
9️⃣ 🎯 **Advies volgende training (concreet uitvoerbaar)**: Duur (bijv 45 min), tempo range, hartslag range, focus (rustig/tempo/techniek).

🔥 **BONUS**:
📌 **1 Belangrijkste leerpunt** (Bijv: "Start rustiger om HR stabiel te houden")
📌 **1 Focuspunt volgende run** (Bijv: "Blok 1 onder 145 bpm houden")
    """
    
    try:
        # 1. Stuur het nieuwe bericht de vaste Thread (het Logboek) in
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt
        )

        # 2. Geef de Assistent de opdracht om te lezen en te antwoorden
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
            max_prompt_tokens=15000
        )

        # 3. Haal het antwoord op als hij klaar is
        if run.status == 'completed': 
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            # Fetch het meest recente antwoord van de assistent (de eerste is altijd het nieuwste)
            return messages.data[0].content[0].text.value
        else:
            return f"De AI analyse liep vast. Status: {run.status}"
            
    except Exception as e:
        print(f"Fout tijdens de AI-analyse met de Assistants API: {e}")
        return "De app liep tegen een fout aan bij het analyseren met de ChatGPT Assistants API. Controleer de logs."
