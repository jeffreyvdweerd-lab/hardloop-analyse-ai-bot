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
Nieuwe hardloopactiviteit binnengekomen!

Hier zijn de algemene sessiegegevens:
- Titel: {activity_data.get('name', 'Onbekend')}
- Afstand: {afstand_km:.2f} km
- Tijd (bewegend): {tijd_minuten:.1f} minuten
- Gemiddeld tempo (pace): {tempo_weergave}
- Gemiddelde hartslag: {gem_hr} bpm
- Maximale hartslag: {activity_data.get('max_heartrate', 'Geen data')} bpm
- Hoogteverschillen: {activity_data.get('total_elevation_gain', 0)} meter

Je MOET exact de volgende structuur en kopjes overnemen en invullen in je antwoord (gebruik Markdown):
1. **Wat je hebt gedaan**: (Geef een opsomming van: Afstand, duur, gemiddelde hartslag, gemiddelde tempo).
2. **Analyse per blok/interval/ronde**: {laps_info}
3. **Vergelijking met het verleden**: (Kijk naar voorgaande actviteiten in je logs en trek een vergelijkende conclusie).
4. **Wat ging er echt goed**: (Waar mag ik trots op zijn gebaseerd op de data?).
5. **Wat zijn verbeterpunten**: (Kritische blik op bijvoorbeeld een te hoge hartslag, onregelmatig tempo, etc.).
6. **Belangrijkste conclusie**: (Korte samenvatting van de hele sessie).
7. **Eindoordeel**: (Geef een cijfer op een schaal van 1-10).
8. **Advies voor de volgende training**: (Wat kan ik de volgende keer het beste doen?).
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
