import os
import json
import uuid
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
    return render_template("AI.html")


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


if __name__ == "__main__":
    print("Starting Calorie Sense...")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True, port=5000)
