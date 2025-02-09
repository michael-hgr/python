import requests
import pandas as pd


def monthlyData(latitude, longitude, peakpower, loss, angle, aspect, mountingplace, startyear=2022, endyear=2023):
    url = "https://re.jrc.ec.europa.eu/api/seriescalc"

    params = {
        "lat": latitude,
        "lon": longitude,
        "usehorizon": 1,
        "pvcalculation": 1,
        "mountingplace": mountingplace,
        "peakpower": peakpower,
        "loss": loss,
        "angle": angle,
        "aspect": aspect,
        "outputformat": "json"
    }

    optimalParams = params.copy()
    optimalParams.update({
        "startyear": startyear,
        "endyear": endyear,
        "optimalangles": 1
    })

    response = requests.get(url, params=params)
    optimalResponse = requests.get(url, params=optimalParams)

    if response.status_code == 200:
        data = response.json()
        optimalData = optimalResponse.json()

        optimal_slope = optimalData["inputs"]["mounting_system"]["fixed"]["slope"]["value"]
        optimal_azimuth = optimalData["inputs"]["mounting_system"]["fixed"]["azimuth"]["value"]

        print(f"Optimaler Winkel: {optimal_slope}°")
        print(f"Optimaler Azimut: {optimal_azimuth}°")

        hourly_data = data.get("outputs", {}).get("hourly", [])
        if not hourly_data:
            print("Keine stündlichen Daten gefunden.")
        else:
            df = pd.DataFrame(hourly_data)
            df['time'] = pd.to_datetime(df['time'], format='%Y%m%d:%H%M')
            df['Energie_kWh'] = df['P'] / 1000
            df['Energie_kWh'] = df['Energie_kWh'].clip(lower=0)
            df['YearMonth'] = df['time'].dt.to_period('M')
            monthly_energy = df.groupby('YearMonth')['Energie_kWh'].sum().reset_index()
            monthly_energy.rename(columns={"YearMonth": "ds", "Energie_kWh": "y"}, inplace=True)
            monthly_energy['ds'] = pd.to_datetime(monthly_energy['ds'].astype(str))
            return monthly_energy, optimal_slope, optimal_azimuth
    else:
        raise ConnectionError(f"Fehler bei der Anfrage. Status Code: {response.status_code}")
