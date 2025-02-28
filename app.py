from flask import Flask, request, jsonify
import requests
from prognose import prognoseMonthlyData

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Willkommen bei der Heliodata API! Verwende POST /predict, um eine Prognose zu erstellen."})

@app.route('/predict', methods=['POST'])
def predict():
    print("POST-Anfrage empfangen")  
    
    try:
        # Die erforderlichen Parameter aus der POST-Anfrage extrahieren
        data_from_request = request.get_json()  # JSON-Daten aus der Anfrage
        print("Empfangene Daten:", data_from_request)  # Gib die empfangenen Daten aus
        
        # Umbenennen der Parameter, um sie an die ursprünglichen Variablen anzupassen
        latitude = data_from_request.get('lat')  # Umbenannt von 'latitude' zu 'lat'
        longitude = data_from_request.get('lon')  # Umbenannt von 'longitude' zu 'lon'
        peakpower = data_from_request.get('leistung')  # Umbenannt von 'peakpower' zu 'leistung'
        angle = data_from_request.get('neigung')  # Umbenannt von 'angle' zu 'neigung'
        aspect = data_from_request.get('himmelsrichtung')  # Umbenannt von 'aspect' zu 'himmelsrichtung'
        mountingplace = data_from_request.get('montageort')  # Umbenannt von 'montageort' zu 'montageort'
        userID = data_from_request.get('userID')

        # Ausgabe der Typen der empfangenen Werte (zur Fehlerdiagnose)
        print(f"Typen der empfangenen Werte: latitude={type(latitude)}, longitude={type(longitude)}, peakpower={type(peakpower)}, angle={type(angle)}, aspect={type(aspect)}, montageort={type(mountingplace)}")

        # Um sicherzustellen, dass alle Parameter den richtigen Typ haben, prüfen wir dies und konvertieren die Werte gegebenenfalls
        if not isinstance(latitude, (int, float)):
            raise ValueError("Der Wert für 'latitude' muss ein numerischer Wert sein.")
        if not isinstance(longitude, (int, float)):
            raise ValueError("Der Wert für 'longitude' muss ein numerischer Wert sein.")
        if not isinstance(peakpower, (int, float)):
            raise ValueError("Der Wert für 'peakpower' muss ein numerischer Wert sein.")
        if not isinstance(angle, (int, float)):
            raise ValueError("Der Wert für 'angle' muss ein numerischer Wert sein.")
        if not isinstance(aspect, str):
            raise ValueError("Der Wert für 'aspect' muss ein String sein.")
        if mountingplace not in ['building', 'free']:
            raise ValueError("Der Wert für 'montageort' muss entweder 'building' oder 'free' sein.")

        # Umrechnung des Aspekts (Himmelsrichtung) in einen Azimutwinkel
        aspect_dict = {
            'north': 180,    # Norden -> 0°
            'east': -90,   # Osten -> -90°
            'south': 0,  # Süden -> 180°
            'west': 90,     # Westen -> 90°
            'northeast': 45,  # Nordosten -> 45°
            'southeast': -45, # Südosten -> -45°
            'southwest': 135, # Südwesten -> 135°
            'northwest': -135 # Nordwesten -> -135°
        }
        
        if aspect.lower() not in aspect_dict:
            raise ValueError("Ungültiger Wert für 'aspect'. Erlaubte Werte sind 'north', 'east', 'south', 'west'.")
        
        aspect_numeric = aspect_dict[aspect.lower()]

        # Setze den Wert für "loss" fest auf 15
        loss = 10

        # Prognose mit den übergebenen Parametern und festem "loss"-Wert generieren
        prognoseResult, optimal_slope, optimal_azimuth = prognoseMonthlyData(latitude, longitude, peakpower, loss, angle, aspect_numeric, mountingplace)

        # Daten, die an PHP gesendet werden sollen (nur 'ds' und 'yhat')
        data = {
            "values": [
                {"ds": row['ds'].strftime('%Y-%m-%d'), "yhat": row['yhat']} 
                for row in prognoseResult
            ],
            "optimal_slope": optimal_slope,
            "optimal_azimuth": optimal_azimuth,
            "PHPSESSID": userID
        }

        url = "https://heliodata.digbizmistelbach.info/php/processData.php" 
        response = requests.post(url, json=data)

        # Antwort zurück an den Client (PHP)
        return jsonify({
            "message": "Daten erfolgreich verarbeitet",
            "data": data
        }), 200

    except ValueError as e:
        print(f"Fehler: {str(e)}")  # Fehlermeldung bei ungültigen Parametern
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Fehler: {str(e)}")  # Fehlermeldung ausgeben, falls etwas anderes schiefgeht
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
