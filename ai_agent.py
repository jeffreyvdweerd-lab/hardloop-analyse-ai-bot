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
Je bent een professionele hardloopcoach. Ik heb zojuist een hardloopactiviteit afgerond op Strava (vanuit mijn Garmin).
Analyseer mijn hardloopsessie en schrijf een motiverende e-mail in het Nederlands, met gebruik van Markdown-opmaak (gebruik headers, vetgedrukte tekst en lijstjes zodat dit makkelijk leesbaar is in een e-mail).
Begin je e-mail altijd exact met de aanhef: "Beste Jeffrey,\n\n".

Je MOET exact de volgende structuur en kopjes overnemen en invullen in je antwoord:
1. **Wat je hebt gedaan**: (Geef een opsomming van: Afstand, duur, gemiddelde hartslag, gemiddelde tempo).
2. **Analyse per blok/interval/ronde**: (Beoordeel de rondetijden, het tempo-verloop en de hartslag per blok). Gebruik deze specifieke data: {laps_info}
3. **Wat ging er echt goed**: (Waar mag ik trots op zijn gebaseerd op de data?).
4. **Wat zijn verbeterpunten**: (Kritische blik op bijvoorbeeld een te hoge hartslag, onregelmatig tempo, etc.).
5. **Belangrijkste conclusie**: (Korte samenvatting van de hele sessie).
6. **Eindoordeel**: (Geef een cijfer op een schaal van 1-10).
7. **Advies voor de volgende training**: (Wat kan ik de volgende keer het beste doen? Let op: we werken gericht toe naar een 10 kilometer in 55 minuten).

Hier zijn de algemene sessiegegevens:
- Titel: {activity_data.get('name', 'Onbekend')}
- Afstand: {afstand_km:.2f} km
- Tijd (bewegend): {tijd_minuten:.1f} minuten
- Gemiddeld tempo (pace): {tempo_weergave}
- Gemiddelde hartslag: {gem_hr} bpm
- Maximale hartslag: {activity_data.get('max_heartrate', 'Geen data')} bpm
- Hoogteverschillen: {activity_data.get('total_elevation_gain', 0)} meter
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Je bent een deskundige, behulpzame en motiverende Nederlandse hardloopcoach genaamd 'AI Coach'."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Fout tijdens de AI-analyse: {e}")
        return "De app liep tegen een fout aan bij het analyseren via ChatGPT. Controlleer de API API-instellingen."
