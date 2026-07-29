# =============================================================
#  AI-Driven Public Health Chatbot — Flask Backend
#  app.py  (SQLite edition — zero setup required)
#
#  Run  : python app.py
#  Open : http://localhost:5000
# =============================================================

import os
import sqlite3
import re
import requests
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash

# ── Translation ────────────────────────────────────────────────
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

# ── Load .env automatically ────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Gemini AI ─────────────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)

        _gemini_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=(
                "You are HealthBot AI, a friendly, professional, and compassionate public health assistant. "
                "Your goal is to have a natural conversation with the user and provide safe, useful health information.\n\n"

                "IMPORTANT CONVERSATION RULE:\n"
                "When a user reports a symptom or health problem such as fever, cough, headache, stomach pain, vomiting, diarrhea, body pain, etc., "
                "do not immediately give a long medical answer. First, understand the user's situation through a natural conversation.\n\n"

                "For symptom-related conversations, ask relevant questions ONE AT A TIME. "
                "Do not ask all questions in a single message. "
                "Start by asking the user's age when appropriate. "
                "Then ask how long the symptom has been present. "
                "Next ask about severity and other important symptoms. "
                "Ask only the questions that are relevant to the user's situation.\n\n"

                "Example conversation:\n"
                "User: I have fever.\n"
                "Assistant: I'm sorry you're not feeling well. May I know your age?\n"
                "User: 21.\n"
                "Assistant: Thank you. How many days have you had the fever?\n"
                "User: 3 days.\n"
                "Assistant: I see. Would you describe the fever as mild, moderate, or severe? Do you know your temperature?\n"
                "User: Moderate, around 38.5°C.\n"
                "Assistant: Do you have any other symptoms, such as cough, headache, body pain, vomiting, rash, or breathing difficulty?\n\n"
                "SEVERE SYMPTOM AND HOSPITAL FLOW:\n"
                "After collecting age, duration, symptoms, and severity confirmation:\n"
                "If the user reports severe pain, difficulty breathing, fainting, heavy bleeding, unconsciousness, or any severity is confirmed as severe/emergency:\n"
                "First, immediately provide:\n"
                "- Immediate first aid steps\n"
                "- Safety precautions\n"
                "- A clear warning message\n\n"
                
                "Then, QUICKLY in the same message, ask the user which city they are currently in to enable hospital assistance.\n"
                "IMPORTANT: Do not skip first aid advice. Do not wait for a long conversation after severe confirmation. Ask for the location immediately after giving emergency guidance.\n\n"
                
                "Example format for severe cases:\n"
                "\'⚠️ This may require urgent medical attention.\n\n"
                "First aid:\n"
                "- Rest immediately\n"
                "- Stay calm\n"
                "- Follow basic safety steps\n\n"
                "If symptoms continue or worsen, seek medical help.\n\n"
                "Which city are you currently in?\'\n\n"
                
                "MILD OR NORMAL SYMPTOM FLOW:\n"
                "If the symptoms are mild or moderate, DO NOT ask for location.\n"
                "After collecting age, duration, symptoms, and severity:\n"
                "Provide:\n"
                "- Possible common causes (without diagnosing)\n"
                "- Home care tips\n"
                "- Food suggestions\n"
                "- OTC medicine guidance if suitable\n"
                "- Clear warning signs that indicate when to consult a doctor\n\n"

                "MEDICINE GUIDANCE:\n"
                "If appropriate, you may mention commonly available over-the-counter medicines in general terms, "
                "but do not prescribe prescription medicines or strong medicines. "
                "Always mention that the user should follow the medicine label or consult a healthcare professional, "
                "especially for children, pregnant users, elderly users, or people with existing medical conditions.\n\n"

                "THANK YOU FLOW:\n"
                "If the user says thank you, thanks, or expresses gratitude, respond warmly and briefly, "
                "for example: 'You're welcome! Take care and get well soon. 😊'\n\n"
                "After collecting enough relevant information, provide a concise personalized response containing:\n"
                "- A brief summary of what the symptoms could indicate, without giving a confirmed diagnosis.\n"
                "- Practical home-care and self-care tips.\n"
                "- Hydration, rest, diet, or other relevant supportive advice.\n"
                "- Prevention tips when relevant.\n"
                "- Clear warning signs that require urgent medical attention.\n"
                "- When the user should consult a doctor or healthcare professional.\n\n"

                "Always consider the user's age, symptom duration, severity, and other symptoms when giving guidance. "
                "Never claim certainty or diagnose a disease based only on chat information. "
                "If symptoms suggest a possible emergency, clearly advise the user to seek immediate medical care.\n\n"

                "Be warm, empathetic, conversational, and easy to understand. "
                "Avoid sounding like a search engine or a medical textbook. "
                "Use short paragraphs and bullet points when useful. "
                "Keep responses concise, generally under 250 words.\n\n"

                "For non-health-related questions, politely explain that you are designed to help with health and public health topics.\n\n"

                "End medical guidance with: "
                "'For a definitive diagnosis, please consult a qualified healthcare professional.'"
            )
        )

        GEMINI_AVAILABLE = True
        print("[AI] Gemini 1.5 Flash loaded successfully.")
    else:
        GEMINI_AVAILABLE = False
        print("[AI] No GEMINI_API_KEY found -- running keyword-fallback mode.")
except ImportError:
    GEMINI_AVAILABLE = False
    print("[AI] google.generativeai not installed -- running keyword-fallback mode.")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "healthbot-dev-secret-key-change-in-prod")

# ─── Database path (created automatically on first run) ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE  = os.path.join(BASE_DIR, "healthbot.db")


# =============================================================
#  SQLite helpers
# =============================================================
def get_db():
    """Return a per-request SQLite connection."""
    if "db" not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False, commit=False):
    """Helper: run a query and return results."""
    db  = get_db()
    cur = db.execute(sql, args)
    if commit:
        db.commit()
        return cur.lastrowid
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


# =============================================================
#  Database initialisation & seed data
# =============================================================
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT    NOT NULL,
    email              TEXT    NOT NULL UNIQUE,
    password_hash      TEXT    NOT NULL,
    preferred_language TEXT    NOT NULL DEFAULT 'en',
    created_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message   TEXT    NOT NULL,
    response  TEXT    NOT NULL,
    language  TEXT    NOT NULL DEFAULT 'en',
    timestamp TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS diseases (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    symptoms   TEXT NOT NULL,
    prevention TEXT NOT NULL,
    info_link  TEXT
);

CREATE TABLE IF NOT EXISTS vaccines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_id      INTEGER NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
    vaccine_name    TEXT NOT NULL,
    recommended_age TEXT NOT NULL,
    description     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS health_alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    date_issued TEXT NOT NULL,
    severity    TEXT NOT NULL DEFAULT 'medium'
);
"""

SEED_DISEASES = [
    ("Dengue Fever",
     "High fever (40°C), severe headache, pain behind the eyes, muscle and joint pain, nausea, vomiting, skin rash",
     "Eliminate standing water. Use mosquito repellent and long-sleeved clothing. Install window screens. Use bed nets.",
     "https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue"),
    ("Malaria",
     "Fever and chills, headache, nausea, muscle pain, fatigue, sweating, chest or abdominal pain",
     "Sleep under insecticide-treated bed nets. Use indoor residual spraying. Take prophylaxis when travelling.",
     "https://www.who.int/news-room/fact-sheets/detail/malaria"),
    ("COVID-19",
     "Fever, dry cough, fatigue, loss of taste or smell, sore throat, headache, shortness of breath",
     "Get vaccinated and boostered. Wear a well-fitted mask in crowds. Wash hands frequently.",
     "https://www.who.int/health-topics/coronavirus"),
    ("Typhoid",
     "Prolonged high fever, weakness, stomach pain, headache, constipation or diarrhea, loss of appetite",
     "Drink only boiled or treated water. Eat cooked food. Practice hand hygiene. Get vaccinated.",
     "https://www.who.int/news-room/fact-sheets/detail/typhoid"),
    ("Influenza (Flu)",
     "Sudden high fever, dry cough, headache, muscle pain, malaise, sore throat, runny nose",
     "Annual flu vaccination. Wash hands regularly. Avoid contact with sick persons. Cover coughs.",
     "https://www.who.int/news-room/fact-sheets/detail/influenza-(seasonal)"),
    ("Cholera",
     "Profuse watery diarrhea (rice-water stool), vomiting, rapid dehydration, muscle cramps",
     "Drink safe water (boiled or treated). Practice proper sanitation and hygiene. Wash hands with soap.",
     "https://www.who.int/news-room/fact-sheets/detail/cholera"),
]

SEED_VACCINES = [
    (1, "Dengvaxia (CYD-TDV)", "9–45 years (seropositive only)",
     "A live recombinant tetravalent dengue vaccine. Recommended only for individuals with prior dengue infection."),
    (2, "RTS,S/AS01 (Mosquirix)", "Infants 5–17 months",
     "First WHO-approved malaria vaccine. Provides partial protection against P. falciparum. 4-dose schedule."),
    (3, "Covishield / AstraZeneca", "18+ years",
     "Viral vector vaccine. Two doses 4–12 weeks apart. Highly effective against severe COVID-19 disease."),
    (3, "Covaxin (BBV152)", "18+ years",
     "Whole-virion inactivated SARS-CoV-2 vaccine developed in India. Two doses 28 days apart."),
    (4, "Typhoid Conjugate Vaccine (TCV)", "6 months and above",
     "Single-dose injectable conjugate vaccine for longer-lasting immunity. WHO-recommended for endemic areas."),
    (5, "Seasonal Influenza Vaccine", "6 months and above (annually)",
     "Annual vaccination required as strains change. Available as injection or nasal spray."),
    (6, "Shanchol / Dukoral", "1 year and above",
     "Oral cholera vaccines providing 65–85% protection. Two doses 14 days apart."),
]

SEED_ALERTS = [
    ("Dengue Outbreak Warning — Tamil Nadu",
     "A significant rise in dengue cases reported across Chennai. Residents advised to eliminate stagnant water and use repellents.",
     datetime.now().strftime("%Y-%m-%d"), "high"),
    ("Monsoon Fever Advisory",
     "Risk of waterborne diseases (typhoid, cholera) rises during monsoon. Ensure drinking water is boiled or treated.",
     datetime.now().strftime("%Y-%m-%d"), "medium"),
    ("COVID-19 Booster Reminder",
     "Health authorities recommend eligible adults receive COVID-19 booster. Free camps at government hospitals.",
     datetime.now().strftime("%Y-%m-%d"), "low"),
    ("Cholera Alert — Coastal Regions",
     "Cholera cases identified in coastal fishing communities. WHO deploying oral vaccines and water purification tablets.",
     datetime.now().strftime("%Y-%m-%d"), "critical"),
]


def init_db():
    """Create tables and seed if empty."""
    db = sqlite3.connect(DATABASE)
    db.executescript(SCHEMA)
    # Seed diseases
    if db.execute("SELECT COUNT(*) FROM diseases").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO diseases (name, symptoms, prevention, info_link) VALUES (?,?,?,?)",
            SEED_DISEASES
        )
    # Seed vaccines
    if db.execute("SELECT COUNT(*) FROM vaccines").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO vaccines (disease_id, vaccine_name, recommended_age, description) VALUES (?,?,?,?)",
            SEED_VACCINES
        )
    # Seed alerts
    if db.execute("SELECT COUNT(*) FROM health_alerts").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO health_alerts (title, description, date_issued, severity) VALUES (?,?,?,?)",
            SEED_ALERTS
        )
    db.commit()
    db.close()


# =============================================================
#  Auth guard
# =============================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# =============================================================
#  AI Engine — Gemini 1.5 Flash (primary) + keyword fallback
# =============================================================

# Per-session conversation history store  { user_id: [{'role':..,'parts':..}] }
_chat_sessions = {}

# Keyword fallback (used when API key is absent or quota exceeded)
HEALTH_KB = {
    # Greetings & Chatbot Meta
    "hello": "Hello! I am HealthBot. Please tell me your symptoms or ask a health-related question.",
    "hi": "Hi there! How can I assist you with your health today?",
    "who are you": "I am HealthBot, your local public health assistant. I can provide guidance on common diseases, symptoms, and prevention.",
    "help": "I'm here to help! Describe your symptoms (e.g., 'I have a fever and cough') or ask about a disease (e.g., 'What is dengue?').",

    # Common Symptoms
    "fever": "Fever is often a sign of infection. Rest well, stay hydrated, and take paracetamol if your temperature exceeds 38.5°C. Consult a doctor if the fever persists beyond 3 days or exceeds 40°C.",
    "cough": "A cough can be viral (cold, flu) or bacterial. Stay hydrated, inhale steam, and rest. If the cough produces blood, causes severe chest pain, or lasts more than 2 weeks, see a doctor.",
    "headache": "Headaches are commonly caused by dehydration, stress, lack of sleep, or minor infections. Drink water and rest in a quiet room. If the headache is sudden and incredibly severe, seek emergency care.",
    "diarrhea": "For diarrhea, your priority is rehydration. Drink ORS (Oral Rehydration Solution) or water with a pinch of salt and sugar. Avoid dairy and greasy foods. Seek help if it lasts over 48 hours or if you see blood.",
    "stomach": "For an upset stomach, stick to a bland diet (bananas, rice, applesauce, toast - the BRAT diet) and sip water slowly. Avoid spicy, fatty, or highly acidic foods.",
    "vomiting": "If you are vomiting, do not eat solid food. Sip clear liquids or ORS slowly. Once vomiting stops for a few hours, try plain crackers or toast. Seek urgent care if you cannot keep liquids down for 24 hours.",
    "rash": "Skin rashes can stem from allergies, heat, or viral infections. Keep the area clean and avoid scratching. If the rash spreads rapidly, blisters, or is accompanied by a high fever, consult a doctor promptly.",
    "cold": "Common cold symptoms include a runny nose, sneezing, and a mild sore throat. Rest, drink plenty of warm fluids, and take over-the-counter decongestants if necessary. It usually resolves in 7-10 days.",
    "throat": "For a sore throat, gargle with warm salt water, drink warm tea with honey, and rest your voice. If you have a high fever or difficulty swallowing, consult a healthcare provider for a possible strep test.",
    "chest pain": "WARNING: Chest pain can indicate a serious heart or lung condition. If the pain is severe, crushing, radiates to your arm or jaw, or is accompanied by shortness of breath, call emergency services immediately.",
    "fatigue": "Persistent fatigue can be caused by anemia, poor sleep, stress, or a viral infection. Ensure you are getting 8 hours of sleep, eating a balanced diet, and staying hydrated. If it persists for weeks, see a doctor.",
    "dizzy": "Dizziness can result from dehydration, low blood pressure, or inner ear issues. Sit or lie down immediately to avoid falling. Drink water. If you also experience blurry vision or speech difficulty, seek emergency care.",
    "muscle pain": "Muscle aches are common with viral fevers like the flu or dengue. Rest and gentle stretching can help. If the pain is localized and severe after an injury, apply ice and elevate the area.",
    
    # Specific Diseases
    "dengue": "Dengue is a mosquito-borne viral infection. Symptoms include high fever, severe headache, and joint pain. Stay strictly hydrated and avoid ibuprofen/aspirin (use paracetamol instead). Seek immediate care if you experience bleeding or severe abdominal pain.",
    "malaria": "Malaria causes recurring chills, high fever, and sweating. It requires a specific blood test and prescription anti-malarial medication. Consult a doctor immediately if you suspect malaria.",
    "typhoid": "Typhoid is a bacterial infection from contaminated food/water causing prolonged fever and stomach pain. It requires antibiotics prescribed by a doctor. Prevent it by drinking only boiled or bottled water.",
    "covid": "COVID-19 symptoms include fever, cough, loss of taste/smell, and fatigue. Isolate yourself, rest, and monitor your oxygen levels. Seek emergency care if you have difficulty breathing.",
    "diabetes": "Diabetes is a chronic condition affecting blood sugar. Management requires a balanced diet low in refined sugars, regular exercise, and medication as prescribed by an endocrinologist.",
    "asthma": "Asthma is a lung condition causing breathing difficulty and wheezing. Always keep your prescribed inhaler nearby. If an attack doesn't improve with your inhaler, seek emergency care.",
    "hypertension": "High blood pressure often has no symptoms but increases heart disease risk. Reduce salt intake, exercise regularly, and take your prescribed medication. If you experience severe headache or chest pain, seek immediate help.",
    "flu": "Influenza causes sudden fever, body aches, chills, and fatigue. Rest, hydrate, and take antiviral medication if prescribed by a doctor early on. Get an annual flu vaccine to prevent it.",

    # General Advice & First Aid
    "vaccine": "Vaccinations are the most effective public health tool. Common adult vaccines include the annual flu shot, COVID-19 boosters, and Tdap. Check the 'Vaccines' page on your dashboard for more details.",
    "prevention": "To prevent common diseases: wash your hands frequently with soap, drink clean/boiled water, ensure your food is thoroughly cooked, use mosquito repellents, and maintain a clean environment.",
    "burn": "For minor burns, immediately run cool (not ice cold) water over the area for 10-15 minutes. Do not pop blisters or apply butter. Cover with a clean, non-stick bandage. For severe or large burns, go to the hospital.",
    "cut": "For minor cuts or bleeding, apply direct pressure with a clean cloth until it stops. Wash the wound gently with soap and water, apply an antiseptic, and bandage it. If the cut is deep or won't stop bleeding, seek medical help.",
    "choking": "If someone is choking and cannot cough or breathe, perform the Heimlich maneuver immediately (abdominal thrusts) and call emergency services.",
    "bleeding": "For heavy bleeding, apply firm direct pressure with a clean cloth, elevate the injured area above the heart if possible, and seek emergency medical assistance immediately.",
    "fracture": "If you suspect a broken bone (fracture), immobilize the area, apply a cold pack to reduce swelling, and go to the nearest emergency room.",
    "sprain": "For a sprain, remember RICE: Rest, Ice, Compression, and Elevation. If the pain is severe or you cannot put weight on it, see a doctor for an X-ray.",

    # Mental Health
    "stress": "Stress can affect both mind and body. Try deep breathing exercises, physical activity, and adequate sleep. If stress feels overwhelming, consider talking to a therapist or counselor.",
    "anxiety": "Anxiety can cause a racing heart, sweating, and feelings of panic. Focus on slow, deep breaths. If anxiety disrupts your daily life, professional psychological support is highly recommended.",
    "depression": "Depression causes persistent sadness or loss of interest. It is a medical condition, not a weakness. Please reach out to a mental health professional, a doctor, or a local crisis helpline.",
    
    # Diet & Lifestyle
    "diet": "A healthy diet includes plenty of fruits, vegetables, lean proteins, and whole grains. Limit processed foods, sugar, and excess salt. Stay hydrated by drinking plenty of water.",
    "weight loss": "Healthy weight loss requires a balance of burning more calories than you consume, regular exercise, and eating nutrient-dense foods. Avoid extreme crash diets.",
    "sleep": "Good sleep hygiene involves 7-9 hours of sleep, avoiding screens an hour before bed, and maintaining a consistent sleep schedule. Poor sleep can weaken your immune system."
}
# =============================================================
# Emergency / Severe Symptom Detection
# =============================================================
# =============================================================
# Best Hospitals by City
# =============================================================

BEST_HOSPITALS = {

    "karur": [
        "Velan Hospital",
        "Apollo Reach Hospital",
        "Amaravathi Hospital",
        "Government Medical College Hospital"
    ],

    "chennai": [
        "Apollo Hospital",
        "MIOT Hospital",
        "Fortis Malar Hospital",
        "SIMS Hospital"
    ],

    "coimbatore": [
        "KMCH",
        "Ganga Hospital",
        "PSG Hospital",
        "Royal Care Hospital"
    ],

    "madurai": [
        "Meenakshi Mission Hospital",
        "Apollo Speciality Hospital",
        "Velammal Hospital"
    ]
}

EMERGENCY_KEYWORDS = [
    # Severe pain
    "severe pain",
    "very severe pain",
    "extreme pain",
    "unbearable pain",
    "worst pain",
    "excruciating pain",

    # Breathing emergency
    "difficulty breathing",
    "breathing difficulty",
    "shortness of breath",
    "cannot breathe",
    "can't breathe",

    # Severe chest pain
    "severe chest pain",
    "crushing chest pain",
    "chest pain and difficulty breathing",
    "chest pain is severe",
    "chest pain very bad",
    "chest pain",

    # Bleeding
    "heavy bleeding",
    "severe bleeding",
    "vomiting blood",
    "coughing blood",

    # Fever and Abdominal
    "high fever",
    "severe abdominal pain",
    "severe stomach pain",

    # Other emergencies
    "unconscious",
    "not responding",
    "fainting",
    "fainted",
    "seizure",
    "stroke",
    "face drooping",
    "slurred speech",
    "severe allergic reaction",
    "anaphylaxis",
    "choking"
]


def detect_emergency(message):
    """
    Detect potentially serious emergency symptoms.
    Hospital assistance will be enabled only when
    severe or emergency symptoms are detected.
    """

    message = message.lower().strip()

    for keyword in EMERGENCY_KEYWORDS:
        if keyword in message:
            return True

    return False
# =============================================================
# Nearby Hospital Search using OpenStreetMap
# =============================================================

@app.route("/api/nearby-hospitals", methods=["POST"])
@login_required
def nearby_hospitals():

    data = request.get_json(silent=True) or {}

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        return jsonify({
            "error": "Location is required."
        }), 400

    try:

        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="hospital"](around:20000,{latitude},{longitude});
          way["amenity"="hospital"](around:20000,{latitude},{longitude});
          relation["amenity"="hospital"](around:20000,{latitude},{longitude});
        );
        out center;
        """

        overpass_servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter"
        ]

        response = None

        for server in overpass_servers:

            try:

                print(
                    f"[Hospital Search] Trying server: {server}"
                )

                temp_response = requests.post(
                    server,
                    data=query,
                    headers={
                        "User-Agent": "HealthBot-AI/1.0"
                    },
                    timeout=30
                )

                if temp_response.status_code == 200:

                    response = temp_response

                    print(
                        f"[Hospital Search] Success: {server}"
                    )

                    break

                else:

                    print(
                        f"[Hospital Search] Failed: "
                        f"{server} - Status {temp_response.status_code}"
                    )

            except requests.exceptions.RequestException as e:

                print(
                    f"[Hospital Search] Server failed: "
                    f"{server} - {e}"
                )

        if response is None:

            return jsonify({
                "error": "All hospital search services are currently unavailable."
            }), 503

        
        response.raise_for_status()

        result = response.json()
        print("OVERPASS STATUS:", response.status_code)
        print("OVERPASS RESPONSE:", result)

        hospitals = []

        for item in result.get("elements", []):

            tags = item.get("tags", {})

            name = tags.get(
                "name",
                "Unnamed Hospital"
            )

            # Node hospital
            if "lat" in item and "lon" in item:

                hospital_lat = item["lat"]
                hospital_lon = item["lon"]

            # Way / Relation hospital
            else:

                center = item.get("center", {})

                hospital_lat = center.get("lat")
                hospital_lon = center.get("lon")

            if hospital_lat is None or hospital_lon is None:
                continue

            # Address
            address_parts = []

            for key in [
                "addr:housenumber",
                "addr:street",
                "addr:city",
                "addr:postcode"
            ]:
                if tags.get(key):
                    address_parts.append(tags[key])

            address = ", ".join(address_parts)

            if not address:
                address = "Address not available"

            hospitals.append({
                "name": name,
                "latitude": hospital_lat,
                "longitude": hospital_lon,
                "address": address,
                "maps_url":
                    f"https://www.google.com/maps/dir/?api=1"
                    f"&destination={hospital_lat},{hospital_lon}"
            })

        # Remove duplicate hospitals
        unique_hospitals = []
        seen = set()

        for hospital in hospitals:

            key = (
                hospital["name"],
                hospital["latitude"],
                hospital["longitude"]
            )

            if key not in seen:
                seen.add(key)
                unique_hospitals.append(hospital)

        # Limit to 10 hospitals
        unique_hospitals = unique_hospitals[:10]

        print(
            f"[Hospital Search] Found {len(unique_hospitals)} hospitals"
        )

        return jsonify({
            "hospitals": unique_hospitals
        })

    except requests.exceptions.RequestException as e:

        print(
            "[Hospital Search Network Error]",
            e
        )

        return jsonify({
            "error": "Hospital search service is temporarily unavailable."
        }), 500

    except Exception as e:

        print(
            "[Hospital Search Error]",
            e
        )

        return jsonify({
            "error": "Unable to find nearby hospitals."
        }), 500

import re

def _keyword_fallback(message: str) -> str:
    msg_lower = message.lower()
    
    # Sort keys by length descending to match longer multi-word phrases first (e.g. 'chest pain')
    sorted_keys = sorted(HEALTH_KB.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        # Use regex to match whole words only, avoiding substring matches like 'hi' in 'while'
        if re.search(rf'\b{re.escape(key)}\b', msg_lower):
            return HEALTH_KB[key]
            
    return ("I'm currently running in offline mode. I can answer questions about common symptoms "
            "(e.g., fever, cough, pain location). Always consult a qualified healthcare professional for diagnosis.")


def gemini_respond(message: str, user_id: int) -> str:
    """
    Send message to Gemini 1.5 Flash with multi-turn conversation context.
    Falls back to keyword matching if Gemini is not configured.
    """
    if not GEMINI_AVAILABLE:
        return _keyword_fallback(message)

    try:
        # Retrieve or create chat session for this user
        if user_id not in _chat_sessions:
            _chat_sessions[user_id] = _gemini_model.start_chat(history=[])

        chat = _chat_sessions[user_id]
        response = chat.send_message(message)
        return response.text.strip()

    except Exception as e:
        error_msg = str(e)
        print(f"[Gemini Error] {error_msg}")
        # Silently fall back — never show raw error to user
        return _keyword_fallback(message)


# =============================================================
#  Routes — Pages
# =============================================================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        lang     = request.form.get("preferred_language", "en")

        if not all([name, email, password]):
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("register"))

        try:
            query_db(
                "INSERT INTO users (name, email, password_hash, preferred_language) VALUES (?,?,?,?)",
                (name, email, generate_password_hash(password), lang),
                commit=True
            )
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.", "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"]  = user["id"]
            session["username"] = user["name"]
            session["lang"]     = user["preferred_language"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    alerts = query_db("SELECT * FROM health_alerts ORDER BY date_issued DESC LIMIT 4")
    return render_template("dashboard.html", alerts=alerts, now_hour=datetime.now().hour)


@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html")


@app.route("/diseases")
@login_required
def diseases():
    disease_list = query_db("SELECT * FROM diseases ORDER BY name ASC")
    return render_template("diseases.html", diseases=disease_list)


@app.route("/vaccines")
@login_required
def vaccines():
    vaccine_list = query_db(
        "SELECT v.*, d.name AS disease_name "
        "FROM vaccines v JOIN diseases d ON v.disease_id = d.id "
        "ORDER BY d.name, v.vaccine_name"
    )
    return render_template("vaccines.html", vaccines=vaccine_list)


# =============================================================
#  API Endpoints
# =============================================================
@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data     = request.get_json(silent=True) or {}
    message  = data.get("message", "").strip()
    language = data.get("language", session.get("lang", "en"))

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    # 1. Translate incoming message to English
    try:
        if language != "en" and GoogleTranslator:
            english_message = GoogleTranslator(
                source=language,
                target="en"
            ).translate(message)
        else:
            english_message = message

    except Exception:
        english_message = message


    # =========================================================
    # 2. Conversation State Management
    # =========================================================
    msg_lower = english_message.lower()
    emergency = False
    
    symptoms_list = ["fever", "cough", "headache", "chest pain", "stomach pain", "vomiting", "diarrhea", "body pain", "cold"]
    chat_state = session.get("chat_state", "")

    # Thank you handler — always respond warmly regardless of state
    thankyou_words = ["thank you", "thanks", "thank u", "thankyou", "thx", "ty", "நன்றி", "ధన్యవాదాలు", "धन्यवाद"]
    if any(t in msg_lower for t in thankyou_words):
        session["chat_state"] = ""  # Reset any ongoing state
        english_reply = (
            "You're welcome! 😊\n\n"
            "Get well soon and take care of yourself! 🌿\n\n"
            "If you ever need health guidance again, feel free to chat with me anytime. I'm always here to help! 💙"
        )
    
    # Step 1: Detect symptoms and start flow
    elif any(s in msg_lower for s in symptoms_list) and chat_state == "":
        session["chat_state"] = "waiting_for_age"
        english_reply = "I'm sorry you're not feeling well.\nMay I know your age?"
        
    # Step 2: Waiting for age
    elif chat_state == "waiting_for_age":
        session["user_age"] = english_message
        session["chat_state"] = "waiting_for_duration"
        english_reply = "How long have you had this problem?"
        
    # Step 3: Waiting for duration
    elif chat_state == "waiting_for_duration":
        session["symptom_days"] = english_message
        session["chat_state"] = "waiting_for_symptoms"
        english_reply = "Can you describe your symptoms in more detail?"
        
    # Step 4: Waiting for symptoms details
    elif chat_state == "waiting_for_symptoms":
        session["symptoms"] = english_message
        session["chat_state"] = "waiting_for_severity"
        english_reply = "Is it mild, moderate, or severe?"
        
    # Step 5: Waiting for severity
    elif chat_state == "waiting_for_severity":
        session["severity"] = english_message
        session["chat_state"] = "" # Reset state
        
        is_severe = "severe" in msg_lower or detect_emergency(session.get("symptoms", "")) or detect_emergency(english_message)
        
        if is_severe:
            emergency = True
            prompt = f"""
User Age: {session.get('user_age')}
Duration: {session.get('symptom_days')}
Symptoms: {session.get('symptoms')}
Severity: {english_message}

This is a severe case.
Respond exactly in this structure:

⚠️ Your symptoms may require urgent medical attention.

Possible reasons:
- [Reason 1]
- [Reason 2]

Immediate First Aid & Tips:
✅ [Safety step 1]
✅ [Safety step 2]
✅ [Helpful tip]

Please share your city/location so I can find nearby hospitals.
"""
        else:
            prompt = f"""
User Age: {session.get('user_age')}
Duration: {session.get('symptom_days')}
Symptoms: {session.get('symptoms')}
Severity: {english_message}

This is a mild/moderate case. Do NOT ask for location.
Respond exactly in this structure:

Based on your symptoms:

Possible reasons:
- [Reason 1]
- [Reason 2]

Home care:
✅ [Tip 1]
✅ [Tip 2]

Food suggestions:
✅ [Food 1]

Consult a doctor if:
⚠️ [Warning sign]
"""
        english_reply = gemini_respond(prompt, session["user_id"])
        
        # If Gemini is unavailable (quota/offline), use built-in structured response
        if "offline mode" in english_reply.lower() or "quota" in english_reply.lower() or "api" in english_reply[:10].lower():
            symptoms_text = session.get('symptoms', 'your symptoms')
            age = session.get('user_age', 'you')
            days = session.get('symptom_days', 'a few days')
            
            if is_severe:
                english_reply = f"""⚠️ Your symptoms may require urgent medical attention.

Based on what you've shared (Age: {age}, Duration: {days}, Symptoms: {symptoms_text}):

Possible reasons:
- Infection or inflammation
- Dehydration or electrolyte imbalance
- Underlying medical condition that needs attention

Immediate First Aid & Tips:
✅ Lie down and rest immediately — avoid any physical exertion
✅ Stay calm and breathe slowly and deeply
✅ Drink small sips of water if you are conscious and able to swallow
✅ Do NOT take any medicine without medical advice in this condition
✅ Ask someone to stay with you — do not be alone

Please share your city/location so I can find nearby hospitals for you."""
            else:
                english_reply = f"""Based on your symptoms (Age: {age}, Duration: {days}, Symptoms: {symptoms_text}):

Possible reasons:
- Common viral or bacterial infection
- Fatigue, stress, or dietary imbalance
- Seasonal changes affecting your health

Home care:
✅ Rest as much as possible — avoid strenuous activity
✅ Drink plenty of fluids (water, coconut water, ORS if needed)
✅ Monitor your temperature/symptoms every few hours
✅ Take paracetamol for fever or pain if needed (follow label instructions)

Food suggestions:
✅ Light foods: rice porridge (kanji), idli, soups, bananas
✅ Avoid oily, spicy, or heavy food
✅ Warm liquids like ginger tea or turmeric milk can help

Consult a doctor if:
⚠️ Symptoms worsen or do not improve within 2-3 days
⚠️ High fever (above 39°C / 102°F) that doesn't reduce
⚠️ Difficulty breathing, chest pain, or severe vomiting

For a definitive diagnosis, please consult a qualified healthcare professional."""

    else:
        # General chat or follow-up
        if detect_emergency(english_message):
            emergency = True
        
        # Keep emergency flag true if we are in the middle of a severe follow-up (like asking for city)
        last_reply = session.get("last_bot_reply", "").lower()
        if "which city are you currently in" in last_reply:
            emergency = True
            
        english_reply = gemini_respond(english_message, session["user_id"])
    
    session["last_bot_reply"] = english_reply

    # =========================================================
    # 4. Translate reply back to user's language
    # =========================================================
    try:
        if language != "en" and GoogleTranslator:
            reply = GoogleTranslator(source="en", target=language).translate(english_reply)
        else:
            reply = english_reply
    except Exception:
        reply = english_reply

    # =========================================================
    # 5. Persist chat history
    # =========================================================
    try:
        query_db(
            "INSERT INTO chat_history (user_id, message, response, language) VALUES (?,?,?,?)",
            (session["user_id"], message, reply, language),
            commit=True
        )
    except Exception as e:
        print(f"[Database Error] {e}")

    # =========================================================
    # 6. Return response to chat.html
    # =========================================================
    return jsonify({
        "reply": reply,
        "emergency": emergency,
        "timestamp": datetime.now().strftime("%H:%M")
    })
    # =============================================================
# Nearby Hospital Search
# =============================================================


# =============================================================
# Search Hospitals by City / Area using OpenStreetMap
# =============================================================

@app.route("/api/search-hospitals", methods=["POST"])
@login_required
def search_hospitals():

    data = request.get_json(silent=True) or {}

    location = data.get("location", "").strip()

    if not location:
        return jsonify({
            "error": "Please enter a city or area name."
        }), 400

    try:

        # Step 1: Convert city/area name into latitude & longitude
        geocode_url = "https://nominatim.openstreetmap.org/search"

        geocode_response = requests.get(
            geocode_url,
            params={
                "q": location,
                "format": "json",
                "limit": 1
            },
            headers={
                "User-Agent": "HealthBot-AI/1.0"
            },
            timeout=15
        )

        geocode_response.raise_for_status()

        locations = geocode_response.json()

        if not locations:
            return jsonify({
                "error": "Location not found."
            }), 404

        latitude = float(
            locations[0]["lat"]
        )

        longitude = float(
            locations[0]["lon"]
        )

        # Step 2: Search hospitals around that location
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="hospital"](around:20000,{latitude},{longitude});
          way["amenity"="hospital"](around:20000,{latitude},{longitude});
          relation["amenity"="hospital"](around:20000,{latitude},{longitude});
        );
        out center;
        """

        overpass_servers = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.private.coffee/api/interpreter"
        ]

        response = None

        for server in overpass_servers:

            try:

                print(
                    f"[Hospital Search] Trying server: {server}"
                )

                temp_response = requests.post(
                    server,
                    data=query,
                    headers={
                        "User-Agent": "HealthBot-AI/1.0"
                    },
                    timeout=30
                )

                if temp_response.status_code == 200:

                    response = temp_response

                    print(
                        f"[Hospital Search] Success: {server}"
                    )

                    break

            except requests.exceptions.RequestException as e:

                print(
                    f"[Hospital Search] Server failed: {server} - {e}"
                )

        if response is None:

            return jsonify({
                "error": "Hospital search services are currently unavailable."
            }), 503

        response.raise_for_status()

        result = response.json()

        hospitals = []

        for item in result.get("elements", []):

            tags = item.get("tags", {})

            name = tags.get(
                "name",
                "Unnamed Hospital"
            )

            # Node
            if "lat" in item and "lon" in item:

                hospital_lat = item["lat"]
                hospital_lon = item["lon"]

            # Way / Relation
            else:

                center = item.get("center", {})

                hospital_lat = center.get("lat")
                hospital_lon = center.get("lon")

            if hospital_lat is None or hospital_lon is None:
                continue

            # Address
            address_parts = []

            for key in [
                "addr:housenumber",
                "addr:street",
                "addr:city",
                "addr:postcode"
            ]:

                if tags.get(key):
                    address_parts.append(
                        tags[key]
                    )

            address = ", ".join(
                address_parts
            )

            if not address:
                address = location

            hospitals.append({
                "name": name,
                "latitude": hospital_lat,
                "longitude": hospital_lon,
                "address": address,
                "maps_url":
                    f"https://www.google.com/maps/dir/?api=1"
                    f"&destination={hospital_lat},{hospital_lon}"
            })

        # Remove duplicates
        unique_hospitals = []
        seen = set()

        for hospital in hospitals:

            key = (
                hospital["name"],
                hospital["latitude"],
                hospital["longitude"]
            )

            if key not in seen:

                seen.add(key)

                unique_hospitals.append(
                    hospital
                )

        # Limit results
        unique_hospitals = unique_hospitals[:10]

        print(
            f"[Hospital Search] {location} - "
            f"Found {len(unique_hospitals)} hospitals"
        )

        return jsonify({
            "hospitals": unique_hospitals
        })

    except requests.exceptions.RequestException as e:

        print(
            "[Hospital Search Network Error]",
            e
        )

        return jsonify({
            "error": "Hospital search service is temporarily unavailable."
        }), 500

    except Exception as e:

        print(
            "[Hospital Search Error]",
            e
        )

        return jsonify({
            "error": "Unable to search hospitals."
        }), 500
@app.route("/api/alerts")
def api_alerts():
    alerts = query_db("SELECT * FROM health_alerts ORDER BY date_issued DESC")
    return jsonify({"alerts": [dict(a) for a in alerts]})


@app.route("/api/history")
@login_required
def api_history():
    history = query_db(
        "SELECT message, response, language, timestamp FROM chat_history "
        "WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20",
        (session["user_id"],)
    )
    return jsonify({"history": [dict(h) for h in history]})


# =============================================================
#  Bootstrap & Run
# =============================================================
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)