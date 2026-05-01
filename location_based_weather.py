import requests
from dotenv import load_dotenv
from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "").strip()
# 1. Configuration
OPENWEATHER_API_KEY = API_KEY
UNITS = "metric"  # Use 'imperial' for Fahrenheit

def get_weather_by_auto_location():
    try:
        # 2. Detect Location via IP
        print("Detecting your location...")
        # ip-api.com returns lat/lon based on your current internet connection
        geo_resp = requests.get("http://ip-api.com/json/")
        geo_data = geo_resp.json()
        
        if geo_data['status'] == 'fail':
            print("Could not detect location.")
            return

        lat = geo_data['lat']
        lon = geo_data['lon']
        city = geo_data['city']
        
        print(f"Location found: {city} ({lat}, {lon})")

        # 3. Get Weather for these coordinates
        weather_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHER_API_KEY,
            'units': UNITS
        }
        
        weather_resp = requests.get(weather_url, params=params)
        weather_data = weather_resp.json()

        if weather_resp.status_code == 200:
            temp = weather_data['main']['temp']
            desc = weather_data['weather'][0]['description']
            print(f"\n--- Weather in {city} ---")
            print(f"Temperature: {temp}°C")
            print(f"Condition: {desc.capitalize()}")
        else:
            print(f"Weather Error: {weather_data.get('message')}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    get_weather_by_auto_location()
