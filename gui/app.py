import os
import json
import uuid
import requests
import joblib
import numpy as np
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # Hide warning
import tensorflow as tf
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite-preview").strip()
client = genai.Client(api_key=API_KEY) if API_KEY else None

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "").strip()

try:
    scaler = joblib.load(BASE_DIR.parent / "out" / "models" / "scaler.pkl")
    ann_model = tf.keras.models.load_model(BASE_DIR.parent / "out" / "models" / "ann.keras")
    print("ANN Model and Scaler loaded successfully!")
except Exception as e:
    print(f"Warning: Could not load ANN model or scaler: {e}")
    scaler, ann_model = None, None

with open(BASE_DIR.parent / "data" / "JSON" / "gym_lookup.json", "r", encoding="utf-8") as f:
    GYM_LOOKUP: dict = json.load(f)

with open(BASE_DIR.parent / "data" / "JSON" / "exercises.json", "r", encoding="utf-8") as f:
    EXERCISES: list = json.load(f)

print(f"Loaded {len(GYM_LOOKUP)} recommendation profiles")
print(f"Loaded {len(EXERCISES)} exercises")
if not API_KEY:
    print("WARNING: GEMINI_API_KEY not found. Create a .env file before using the AI chat.")


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    return round(weight_kg / (height_m ** 2), 2)


def get_bmi_level(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25.0:
        return "Normal"
    if bmi < 30.0:
        return "Overweight"
    return "Obuse"  # kept to match the original dataset spelling


def lookup_recommendations(sex, age, height_m, weight_kg, hypertension, diabetes):
    bmi = calculate_bmi(weight_kg, height_m)
    level = get_bmi_level(bmi)
    matches = {}

    for key, val in GYM_LOOKUP.items():
        p = key.split("|")
        # key format: Sex|Age|Hypertension|Diabetes|Level|FitnessGoal|FitnessType
        if (
            p[0] == sex
            and int(p[1]) == age
            and p[2] == hypertension
            and p[3] == diabetes
            and p[4] == level
        ):
            matches[f"{p[5]} - {p[6]}"] = val

    return {"bmi": bmi, "level": level, "recommendations": matches}


def build_system_prompt(profile: dict, lookup: dict) -> str:
    exercises_text = "\n".join(
        [
            f"- {e['name']} | targets: {e['target_muscles']} | equipment: {e['equipment']}"
            for e in EXERCISES
        ]
    )

    recs_text = ""
    for label, rec in lookup["recommendations"].items():
        recs_text += (
            f"\n[{label}]\n"
            f"  Exercises: {rec['exercises']}\n"
            f"  Equipment: {rec['equipment']}\n"
            f"  Diet:      {rec['diet']}\n"
            f"  Advice:    {rec['recommendation']}\n"
        )

    if not recs_text:
        recs_text = "No exact match. Give general advice based on the user profile."

    return f"""You are an expert AI Fitness Coach for the Calorie Sense web app.
Give personalised, motivating, safe fitness advice.

USER PROFILE:
  Name: {profile.get('name', 'User')} | Sex: {profile['sex']} | Age: {profile['age']} yrs
  Height: {profile['height']} m | Weight: {profile['weight']} kg
  BMI: {lookup['bmi']} ({lookup['level']}) | Hypertension: {profile['hypertension']} | Diabetes: {profile['diabetes']}

PERSONALISED RECOMMENDATIONS FROM OUR DATABASE:
{recs_text}

AVAILABLE EXERCISES:
{exercises_text}

RULES:
1. Base advice on the profile, recommendations, and available exercise data when relevant.
2. Pick exercises from the Available Exercises list when relevant.
3. If Hypertension or Diabetes is Yes, always add a safety reminder.
4. Structure workout plans with clear days, sets, and reps.
5. For diet questions, use the diet guidance from the recommendations.
6. Never give unsafe medical advice. Refer to a doctor for medical issues.
7. Be friendly, clear, simple, and motivating.
"""


class CoachSession:
    def __init__(self, profile: dict):
        self.profile = profile
        self.lookup = lookup_recommendations(
            sex=profile["sex"],
            age=profile["age"],
            height_m=profile["height"],
            weight_kg=profile["weight"],
            hypertension=profile["hypertension"],
            diabetes=profile["diabetes"],
        )
        self.system_prompt = build_system_prompt(profile, self.lookup)
        self.history: list = []
        print(
            f"[Session] {profile.get('name')} | BMI={self.lookup['bmi']} "
            f"({self.lookup['level']}) | {len(self.lookup['recommendations'])} plans matched"
        )

    def chat(self, user_message: str) -> str:
        if client is None:
            return "Gemini API key is missing. Please create a .env file and add GEMINI_API_KEY."

        self.history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

        try:
            resp = client.models.generate_content(
                model=MODEL_NAME,
                contents=self.history,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    max_output_tokens=1024,
                    temperature=0.7,
                ),
            )
            reply = resp.text if resp.text is not None else "Sorry, I couldn't generate a response."
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "high demand" in error_str.lower():
                reply = "Currently experiencing high demand and having trouble connecting. Please wait a moment and try again!"
            else:
                reply = f"API error: {e}"

        self.history.append(types.Content(role="model", parts=[types.Part(text=reply)]))
        return reply


app = Flask(__name__)
sessions = {}


@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")


@app.route("/AI.html")
def ai_page():
    return render_template("ai.html")


@app.route("/calorie.html")
def calorie_page():
    return render_template("calorie.html")


@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.get_json(force=True)

    try:
        profile = {
            "name": data.get("name", "User"),
            "sex": str(data["sex"]),
            "age": max(18, min(63, int(data["age"]))),
            "height": float(data["height"]),
            "weight": float(data["weight"]),
            "hypertension": str(data["hypertension"]),
            "diabetes": str(data["diabetes"]),
        }
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"Bad input: {e}"}), 400

    session = CoachSession(profile)
    session_id = str(uuid.uuid4())[:10]
    sessions[session_id] = session

    return jsonify(
        {
            "session_id": session_id,
            "bmi": session.lookup["bmi"],
            "level": session.lookup["level"],
            "plans_found": len(session.lookup["recommendations"]),
        }
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    session_id = data.get("session_id", "")
    message = data.get("message", "").strip()

    if session_id not in sessions:
        return jsonify({"error": "Session not found. Please refresh and start again."}), 404
    if not message:
        return jsonify({"error": "Empty message."}), 400

    reply = sessions[session_id].chat(message)
    return jsonify({"reply": reply})


@app.route("/api/weather", methods=["GET", "POST"])
def api_weather():
    if not OPENWEATHER_API_KEY:
        return jsonify({"error": "OpenWeather API key missing."}), 500
    try:
        lat, lon, city = None, None, "Unknown"

        # Check if coordinates were sent in POST body
        if request.method == "POST":
            data = request.get_json(silent=True)
            if data:
                lat = data.get("lat")
                lon = data.get("lon")
                city = "Your Location"

        # If no coordinates from client, fall back to IP-based detection
        if lat is None or lon is None:
            geo_resp = requests.get("http://ip-api.com/json/")
            geo_data = geo_resp.json()
            if geo_data.get("status") == "fail":
                return jsonify({"error": "Could not detect location."}), 400
            lat, lon = geo_data["lat"], geo_data["lon"]
            city = geo_data.get("city", "Unknown")
        
        weather_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": "metric"}
        weather_resp = requests.get(weather_url, params=params)
        weather_data = weather_resp.json()
        
        if weather_resp.status_code == 200:
            temp = weather_data["main"]["temp"]
            desc = weather_data["weather"][0]["description"].lower()
            
            # Categorize
            if "rain" in desc or "drizzle" in desc or "thunder" in desc:
                condition = "Rainy"
            elif "clear" in desc or "sun" in desc:
                condition = "Sunny"
            else:
                condition = "Cloudy"
                
            return jsonify({
                "city": city,
                "temp": temp,
                "description": desc.capitalize(),
                "condition": condition
            })
        else:
            return jsonify({"error": weather_data.get("message")}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict_calorie", methods=["POST"])
def api_predict_calorie():
    if not ann_model or not scaler:
        return jsonify({"error": "Model not loaded on server."}), 500
        
    data = request.get_json(force=True)
    try:
        gender_str = data.get("gender", "Male")
        gender_val = 1.0 if gender_str.lower() == "male" else 0.0
        
        age = float(data.get("age", 25))
        hr = float(data.get("hr", 120))
        duration = float(data.get("duration", 1.0))
        intensity = float(data.get("intensity", 5.0))
        condition = data.get("condition", "Cloudy")
        
        max_hr_perc = hr / (220.0 - age) if age < 220 else 0.5
        workload = intensity * duration
        
        rainy_val = 1.0 if condition == "Rainy" else 0.0
        sunny_val = 1.0 if condition == "Sunny" else 0.0
        
        # Order: Gender, Max_HR_Percentage, Weather_Rainy, HR, Workload, Weather_Sunny, Exercise_Duration
        features = np.array([[
            gender_val,
            max_hr_perc,
            rainy_val,
            hr,
            workload,
            sunny_val,
            duration
        ]])
        
        scaled_features = scaler.transform(features)
        pred = ann_model.predict(scaled_features)
        calories = float(pred[0][0])
        
        return jsonify({"calories_burned": round(calories, 2)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Starting Calorie Sense...")
    print(f"Open http://127.0.0.1:{port} in your browser")
    app.run(host="0.0.0.0", port=port, debug=True)
