"""Fetch historical weather data from Open-Meteo Archive API for all F1 races.

Reads race dates and circuit locations from data/csv/races.csv, fetches weather
for each race day, and writes data/csv/weather.csv.

Open-Meteo is free, no API key required.

Usage:
    python -m scripts.fetch_weather
"""

import csv
import os
import sys
import time

import httpx

# Circuit name → (latitude, longitude)
CIRCUIT_COORDS = {
    "Albert Park Grand Prix Circuit": (-37.8497, 144.9680),
    "Autodromo Enzo e Dino Ferrari": (44.3439, 11.7167),
    "Autódromo Hermanos Rodríguez": (19.4042, -99.0907),
    "Autódromo Internacional do Algarve": (37.2319, -8.6267),
    "Autodromo Internazionale del Mugello": (43.9975, 11.3719),
    "Autódromo José Carlos Pace": (-23.7036, -46.6997),
    "Autodromo Nazionale di Monza": (45.6156, 9.2811),
    "Bahrain International Circuit": (26.0325, 50.5106),
    "Baku City Circuit": (40.3725, 49.8533),
    "Buddh International Circuit": (28.3487, 77.5331),
    "Circuit Gilles Villeneuve": (45.5000, -73.5228),
    "Circuit Park Zandvoort": (52.3888, 4.5409),
    "Circuit Paul Ricard": (43.2506, 5.7917),
    "Circuit de Barcelona-Catalunya": (41.5700, 2.2611),
    "Circuit de Monaco": (43.7347, 7.4206),
    "Circuit de Nevers Magny-Cours": (46.8642, 3.1636),
    "Circuit de Spa-Francorchamps": (50.4372, 5.9714),
    "Circuit of the Americas": (30.1328, -97.6411),
    "Fuji Speedway": (35.3717, 138.9278),
    "Hockenheimring": (49.3278, 8.5656),
    "Hungaroring": (47.5789, 19.2486),
    "Indianapolis Motor Speedway": (39.7950, -86.2347),
    "Istanbul Park": (40.9517, 29.4050),
    "Jeddah Corniche Circuit": (21.6319, 39.1044),
    "Korean International Circuit": (34.7333, 126.4170),
    "Las Vegas Strip Street Circuit": (36.1147, -115.1728),
    "Losail International Circuit": (25.4900, 51.4542),
    "Marina Bay Street Circuit": (1.2914, 103.8640),
    "Miami International Autodrome": (25.9581, -80.2389),
    "Nürburgring": (50.3356, 6.9475),
    "Red Bull Ring": (47.2197, 14.7647),
    "Sepang International Circuit": (2.7606, 101.7383),
    "Shanghai International Circuit": (31.3389, 121.2200),
    "Silverstone Circuit": (52.0786, -1.0169),
    "Sochi Autodrom": (43.4057, 39.9578),
    "Suzuka Circuit": (34.8431, 136.5406),
    "Valencia Street Circuit": (39.4589, -0.3317),
    "Yas Marina Circuit": (24.4672, 54.6031),
}

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

CSV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "csv")


def _fetch_weather(lat: float, lng: float, date: str) -> dict | None:
    """Fetch weather for a specific date and location from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lng,
        "start_date": date,
        "end_date": date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weather_code",
        "timezone": "auto",
    }
    try:
        resp = httpx.get(OPEN_METEO_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        return {
            "temperature_max": daily.get("temperature_2m_max", [None])[0],
            "temperature_min": daily.get("temperature_2m_min", [None])[0],
            "precipitation_mm": daily.get("precipitation_sum", [None])[0],
            "wind_speed_max": daily.get("wind_speed_10m_max", [None])[0],
            "weather_code": daily.get("weather_code", [None])[0],
        }
    except Exception as e:
        print(f"    WARNING: API error — {e}")
        return None


def run() -> None:
    races_path = os.path.join(CSV_DIR, "races.csv")
    output_path = os.path.join(CSV_DIR, "weather.csv")

    if not os.path.exists(races_path):
        print(f"ERROR: {races_path} not found. Run seed/export first.")
        sys.exit(1)

    with open(races_path, newline="", encoding="utf-8") as f:
        races = list(csv.DictReader(f))

    print(f"=== Fetching weather for {len(races)} races ===\n")

    results = []
    skipped = 0
    errors = 0

    for i, race in enumerate(races):
        race_id = race["id"]
        circuit = race["circuit_name"]
        date = race["date"]

        coords = CIRCUIT_COORDS.get(circuit)
        if not coords:
            print(f"  [{i+1}/{len(races)}] SKIP {circuit} — no coordinates mapped")
            skipped += 1
            continue

        if not date or date in ("", "None"):
            print(f"  [{i+1}/{len(races)}] SKIP race {race_id} — no date")
            skipped += 1
            continue

        lat, lng = coords
        weather = _fetch_weather(lat, lng, date)

        if weather:
            results.append({"race_id": race_id, **weather})
            print(f"  [{i+1}/{len(races)}] ✓ {race['name']} ({date}) — {weather['temperature_max']}°C, {weather['precipitation_mm']}mm rain")
        else:
            errors += 1
            print(f"  [{i+1}/{len(races)}] ✗ {race['name']} ({date}) — fetch failed")

        # Respect rate limits — Open-Meteo allows ~600 req/min
        if (i + 1) % 50 == 0:
            print(f"  ... pausing 2s (rate limit courtesy) ...")
            time.sleep(2)

    # Write CSV
    fieldnames = ["race_id", "temperature_max", "temperature_min", "precipitation_mm", "wind_speed_max", "weather_code"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n=== Done ===")
    print(f"  Written: {len(results)} rows to {output_path}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors:  {errors}")


if __name__ == "__main__":
    run()
