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

# ── Gemini AI Setup ────────────────────────────────────────────
GEMINI_AVAILABLE = False
genai = None
GEMINI_MODEL = "gemini-1.5-flash"

SYSTEM_INSTRUCTION = (
    "You are HealthBot AI, a friendly, empathetic, professional, and highly knowledgeable public health assistant. "
    "Your goal is to engage in a real, interactive, multi-turn conversation whenever a user mentions ANY disease, illness, health condition, or symptom.\n\n"

    "MANDATORY MULTI-TURN CONVERSATION FLOW (FOLLOW EVERY SINGLE TIME FOR ANY DISEASE OR HEALTH TOPIC):\n"
    "Whenever the user mentions ANY disease (e.g., Dengue, Malaria, Typhoid, COVID-19, Cholera, Tuberculosis, Asthma, Diabetes, Hypertension, Hepatitis, Jaundice, Chickenpox, Measles, Pneumonia, Migraine, Kidney Stones, Gastritis, Arthritis, Anemia, Eczema, Stroke, Appendicitis, or any other disease) OR any symptom/pain:\n\n"

    "STEP 1: Acknowledge the specific disease or symptom empathetically, and ask ONLY for the user's AGE.\n"
    "Example: 'I am sorry to hear that you are concerned about Dengue Fever. To provide personalized health advice, could you please tell me your age?'\n\n"

    "STEP 2: Once age is provided, ask ONLY for their current CITY or LOCATION.\n"
    "Example: 'Thank you. Which city or location are you currently in? (This helps check for local health context and hospital support if needed).'\n\n"

    "STEP 3: Once city is provided, ask ONLY for DURATION.\n"
    "Example: 'Got it. How long have you had symptoms or been experiencing this condition?'\n\n"

    "STEP 4: Once duration is provided, ask ONLY for SEVERITY (mild, moderate, or severe).\n"
    "Example: 'Would you describe the symptoms right now as mild, moderate, or severe?'\n\n"

    "STEP 5: Once severity is provided, ask ONLY if there are ANY OTHER ASSOCIATED SYMPTOMS.\n"
    "Example: 'Are there any other symptoms present (such as high fever, rash, nausea, body aches, or breathing difficulty)?'\n\n"

    "STEP 6: Once ALL 5 details (Age, City, Duration, Severity, Associated Symptoms) are collected, provide a COMPREHENSIVE PERSONALIZED ADVISORY REPORT including:\n"
    "  - Disease Explanation & Overview (tailored to their age group)\n"
    "  - Customized Risk Assessment based on their duration, severity, and city\n"
    "  - Practical Home Care & Rest Guidelines\n"
    "  - Food, Hydration & Dietary Recommendations\n"
    "  - Safe OTC Medication Guidance (general terms like Paracetamol; strict warnings against contraindicated drugs like Aspirin/Ibuprofen for Dengue)\n"
    "  - Prevention & Sanitation Measures\n"
    "  - Clear Red-Flag Warning Signs requiring immediate medical/hospital care\n"
    "  - End every report with: 'For a definitive diagnosis and prescription treatment, please consult a qualified medical professional.'\n\n"

    "CRITICAL RULES:\n"
    "- NEVER ask more than ONE question per turn during Steps 1-5.\n"
    "- NEVER jump straight to advice without gathering Age, City, Duration, Severity, and Symptoms.\n"
    "- IF THE USER REPORTS SEVERE SYMPTOMS or an emergency (difficulty breathing, chest pain, fainting, heavy bleeding):\n"
    "  Provide immediate First Aid instructions, urge them to visit an emergency room, and ask for their city if not already provided so nearby hospitals can be located.\n\n"

    "Be warm, empathetic, clear, and well-structured using markdown bolding and bullet points."
)

try:
    import google.generativeai as genai
    _GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    if _GEMINI_API_KEY:
        genai.configure(api_key=_GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False


app = Flask(__name__)
def create_users_table():
    db = sqlite3.connect("database.db")
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        preferred_language TEXT
    )
    """)

    db.commit()
    db.close()

create_users_table()
app.secret_key = "healthbot-dev-secret-key-change-in-prod"

# ── CORS for React dev server ──────────────────────────────────
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.route("/api/<path:p>", methods=["OPTIONS"])
def api_options(p):
    """Handle CORS preflight for all /api/* routes."""
    resp = app.make_default_options_response()
    return resp

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
# Comprehensive Disease Knowledge Base (20+ Public Health Diseases)
HEALTH_KB = {
    # Greetings & Meta
    "hello": "Hello! I am HealthBot AI. Which disease or symptom are you dealing with or seeking information about?",
    "hi": "Hi there! What disease or symptom would you like to discuss today?",
    "who are you": "I am HealthBot AI, your public health assistant. I can guide you through symptom assessment, disease information, home care, and prevention.",
    "help": "I can help you with any disease (Dengue, Malaria, Typhoid, COVID-19, Tuberculosis, Diabetes, Asthma, Flu, etc.) or symptoms (fever, cough, pain). Just mention your condition!",

    # Common Symptoms
    "fever": "Fever is an elevation in body temperature commonly indicating infection or inflammation. It requires careful monitoring, adequate fluid intake, and resting.",
    "cough": "A cough is a reflex action to clear airways of mucus, irritants, or infection. It can be dry or productive and may stem from viral or bacterial causes.",
    "headache": "Headaches can stem from stress, dehydration, lack of sleep, eye strain, or underlying infections like dengue, flu, or sinusitis.",
    "diarrhea": "Diarrhea involves frequent loose or watery bowel movements. The main objective during diarrhea is preventing dehydration through oral rehydration.",
    "stomach": "Stomach discomfort or pain can be caused by gastritis, indigestion, food poisoning, or infection. Avoid spicy/fatty foods and drink clear fluids.",
    "vomiting": "Vomiting is the forceful expulsion of stomach contents. Sipping clear liquids or ORS slowly prevents dehydration while resting the stomach.",
    "rash": "Skin rashes can indicate viral fevers (like Dengue or Measles), allergies, or dermatological conditions. Keep the skin clean and cool.",
    "cold": "Common cold is a viral upper respiratory infection causing runny nose, sneezing, mild sore throat, and low fatigue.",
    "throat": "Sore throat is inflammation of the pharynx, often caused by viral colds, flu, or bacterial strep throat. Saltwater gargles provide relief.",
    "chest pain": "WARNING: Severe chest pain can be an emergency sign of heart or lung conditions. Immediate hospital assessment is crucial if accompanied by breathlessness.",
    "fatigue": "Extreme tiredness or fatigue can occur during fevers, viral infections, anemia, or metabolic imbalances like diabetes.",
    "dizzy": "Dizziness or lightheadedness may stem from dehydration, low blood pressure, low blood sugar, or inner ear issues.",

    # Extensive Disease Database (20+ Diseases)
    "dengue": "Dengue Fever is a mosquito-borne viral infection caused by the Aedes mosquito. Key symptoms include high sudden fever, severe headache, retro-orbital pain (behind eyes), muscle/joint pain ('breakbone fever'), and skin rash. Strict hydration and avoiding NSAIDs (like Ibuprofen/Aspirin) are mandatory to avoid bleeding risks.",
    "malaria": "Malaria is a mosquito-borne parasitic infection transmitted by female Anopheles mosquitoes. It manifests with cyclical high fever, severe chills, sweating, headache, and body aches. Requires medical diagnostic blood test (smear/rapid test) and specific prescription antimalarials.",
    "typhoid": "Typhoid Fever is a bacterial infection caused by Salmonella typhi, transmitted through contaminated food or water. Symptoms include prolonged high fever, abdominal pain, weakness, constipation or diarrhea, and rose spots. Antibiotic therapy prescribed by a doctor is required.",
    "covid": "COVID-19 is a respiratory illness caused by SARS-CoV-2. Common symptoms include fever, dry cough, fatigue, loss of taste or smell, sore throat, and muscle aches. Oxygen monitoring and isolation precautions are essential.",
    "flu": "Influenza (Flu) is a contagious viral respiratory infection. Symptoms start abruptly with high fever, body aches, dry cough, sore throat, and severe exhaustion. Annual vaccination helps prevent severe illness.",
    "cholera": "Cholera is an acute diarrheal infection caused by ingestion of food or water contaminated with Vibrio cholerae bacteria. It causes rapid, severe watery diarrhea ('rice-water stool') leading to extreme dehydration. Immediate ORS and IV fluid replacement is critical.",
    "tuberculosis": "Tuberculosis (TB) is a bacterial infection caused by Mycobacterium tuberculosis that primarily affects the lungs. Symptoms include persistent cough lasting >2 weeks, coughing up blood, night sweats, unexplained weight loss, and fever. Requires complete multi-month antibiotic regimen (DOTS).",
    "asthma": "Asthma is a chronic inflammatory disease of the airways causing wheezing, shortness of breath, chest tightness, and coughing. Avoid trigger allergens, stay warm, and keep prescribed rescue inhalers accessible.",
    "diabetes": "Diabetes Mellitus is a metabolic disorder characterized by elevated blood glucose levels. Symptoms include excessive thirst (polydipsia), frequent urination (polyuria), increased hunger, and fatigue. Requires dietary regulation, exercise, and medical management.",
    "hypertension": "Hypertension (High Blood Pressure) is a long-term condition where arterial blood pressure is persistently elevated. Often silent, but can cause headaches, dizziness, or chest discomfort. Requires sodium reduction, stress control, and daily medication adherence.",
    "jaundice": "Jaundice (Hepatitis) is yellowing of the skin and eyes caused by high bilirubin levels, often due to liver inflammation or viral hepatitis (A, B, C, E). Symptoms include dark urine, pale stools, fatigue, and abdominal pain. Requires strict bland diet and medical care.",
    "chickenpox": "Chickenpox (Varicella) is a highly contagious viral disease causing an itchy, blister-like skin rash, fever, and fatigue. Keep rash clean, apply calamine lotion, and avoid scratching to prevent secondary bacterial infection.",
    "measles": "Measles (Rubeola) is a viral infection marked by high fever, cough, runny nose, red watery eyes (conjunctivitis), and a characteristic widespread red skin rash. MMR vaccination is the primary prevention.",
    "pneumonia": "Pneumonia is an infection that inflames the air sacs in one or both lungs, filling them with fluid or pus. Symptoms include fever, chills, cough with phlegm, and sharp chest pain when breathing or coughing. Requires doctor evaluation.",
    "migraine": "Migraine is a neurological condition causing intense throbbing headache, usually on one side, accompanied by nausea, vomiting, and sensitivity to light and sound. Rest in a quiet, dark room.",
    "kidney stone": "Kidney stones (Nephrolithiasis) are hard mineral deposits that form in the kidneys. Cause severe sharp flank/back pain radiating to the lower abdomen, painful urination, and blood in urine. Drink 3+ Liters of water daily.",
    "gastritis": "Gastritis is inflammation of the stomach lining causing burning upper stomach pain, nausea, bloating, and indigestion. Avoid spicy, acidic, fried foods, and avoid taking painkillers on an empty stomach.",
    "arthritis": "Arthritis is inflammation of one or more joints causing pain, stiffness, swelling, and reduced range of motion. Warm compresses, gentle movement, and anti-inflammatory care help.",
    "anemia": "Anemia is a deficiency in red blood cells or hemoglobin, leading to reduced oxygen flow. Causes fatigue, pale skin, weakness, dizziness, and cold hands/feet. Iron-rich foods (spinach, jaggery, legumes) and supplements help.",
    "eczema": "Eczema (Atopic Dermatitis) causes dry, red, itchy, and inflamed skin patches. Keep skin moisturized with gentle emollients and avoid harsh soaps or synthetic fabrics.",
    "stroke": "Stroke occurs when blood supply to part of the brain is interrupted. Remember FAST: Face drooping, Arm weakness, Speech difficulty, Time to call emergency care immediately!",
    "appendicitis": "Appendicitis is acute inflammation of the appendix. Causes sudden severe pain starting around the navel and shifting to the lower right abdomen, with fever and vomiting. Requires urgent surgical evaluation."
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

def _interactive_fallback(message: str, sess: dict) -> str:
    """
    Multi-turn interactive state-machine fallback for ANY disease or symptom.
    Executes a 5-step conversation (Age -> City -> Duration -> Severity -> Symptoms -> Comprehensive Advisory Report)
    when offline or when Gemini API is unavailable.
    """
    msg_lower = message.lower().strip()

    # Reset command
    if msg_lower in ["reset", "clear", "start over", "new query", "hello", "hi"]:
        sess.pop("conv_step", None)
        sess.pop("conv_disease", None)
        sess.pop("conv_age", None)
        sess.pop("conv_city", None)
        sess.pop("conv_duration", None)
        sess.pop("conv_severity", None)
        sess.pop("conv_symptoms", None)
        if msg_lower in ["hello", "hi"]:
            return "Hello! I am HealthBot AI. Which disease or symptom are you dealing with or seeking advice on?"
        return "Conversation reset. Which disease or symptom would you like to discuss now?"

    # Current step
    step = sess.get("conv_step", 0)

    # Step 0: User mentions a disease or symptom
    if step == 0:
        detected_disease = None
        for key in sorted(HEALTH_KB.keys(), key=len, reverse=True):
            if re.search(rf'\b{re.escape(key)}\b', msg_lower):
                detected_disease = key.title()
                break
        
        if not detected_disease:
            cleaned = re.sub(r'^(i have|what is|tell me about|information on|treatment for|symptoms of|query for)\s+', '', msg_lower, flags=re.IGNORECASE).strip()
            detected_disease = cleaned.title() if cleaned else message.strip().title()

        sess["conv_disease"] = detected_disease
        sess["conv_step"] = 1
        return (f"I am here to guide you regarding **{detected_disease}**. "
                f"To provide you with safe, personalized health advice and guidance, "
                f"could you please tell me your **age**?")

    # Step 1: Age -> Ask City
    elif step == 1:
        sess["conv_age"] = message.strip()
        sess["conv_step"] = 2
        disease = sess.get("conv_disease", "your condition")
        return f"Thank you. Which **city or location** are you currently in? (This helps check for local health advisories and hospital options)."

    # Step 2: City -> Ask Duration
    elif step == 2:
        sess["conv_city"] = message.strip()
        sess["conv_step"] = 3
        disease = sess.get("conv_disease", "your condition")
        return f"Got it. How long have you had symptoms or been dealing with **{disease}**?"

    # Step 3: Duration -> Ask Severity
    elif step == 3:
        sess["conv_duration"] = message.strip()
        sess["conv_step"] = 4
        return f"Understood. Would you describe the current symptoms as **mild**, **moderate**, or **severe**?"

    # Step 4: Severity -> Ask Associated Symptoms
    elif step == 4:
        severity_val = message.strip()
        sess["conv_severity"] = severity_val
        
        # Check for severe emergency
        if "severe" in severity_val.lower() or "emergency" in severity_val.lower() or "critical" in severity_val.lower():
            city = sess.get("conv_city", "your area")
            disease = sess.get("conv_disease", "condition")
            sess["conv_step"] = 0
            return (
                f"🚨 **EMERGENCY WARNING — SEVERE CASE DETECTED**\n\n"
                f"Because you indicated severe symptoms for **{disease}**, please seek **IMMEDIATE EMERGENCY MEDICAL CARE**.\n\n"
                f"**Immediate Safety & First Aid Steps:**\n"
                f"- Stay calm, sit or lie down in a safe position.\n"
                f"- Do not perform heavy physical exertion.\n"
                f"- If breathing difficulty or chest pain occurs, loosen tight clothing.\n"
                f"- Have someone accompany you or call local emergency services immediately.\n\n"
                f"Searching for hospitals near **{city}**. Please use the hospital finder on your right or contact emergency services immediately."
            )

        sess["conv_step"] = 5
        return f"Are there any other associated symptoms present (such as fever, body pain, rash, nausea, cough, or weakness)?"

    # Step 5: Associated Symptoms -> Generate Comprehensive Advisory
    elif step == 5:
        sess["conv_symptoms"] = message.strip()
        disease   = sess.get("conv_disease", "Health Condition")
        age       = sess.get("conv_age", "N/A")
        city      = sess.get("conv_city", "N/A")
        duration  = sess.get("conv_duration", "N/A")
        severity  = sess.get("conv_severity", "N/A")
        symptoms  = sess.get("conv_symptoms", "N/A")

        # Reset state for next query
        sess["conv_step"] = 0

        # Retrieve specific disease kb info
        dis_key = disease.lower()
        kb_info = ""
        for k in HEALTH_KB:
            if k in dis_key:
                kb_info = HEALTH_KB[k]
                break

        if not kb_info:
            kb_info = f"{disease} requires careful symptom monitoring, fluid hydration, adequate rest, and professional medical evaluation."

        report = (
            f"📋 **Personalized Health Advisory Report for {disease}**\n\n"
            f"👤 **Patient Profile Summary:**\n"
            f"- **Condition/Disease:** {disease}\n"
            f"- **Age:** {age}\n"
            f"- **Location:** {city}\n"
            f"- **Duration:** {duration}\n"
            f"- **Severity Level:** {severity}\n"
            f"- **Associated Symptoms:** {symptoms}\n\n"

            f"🩺 **1. Medical Overview & Key Facts:**\n"
            f"{kb_info}\n\n"

            f"🏠 **2. Home Care & Rest Protocol:**\n"
            f"- Ensure complete bed rest to allow your immune system to recover.\n"
            f"- Monitor body temperature, pulse, and symptom changes every 4-6 hours.\n"
            f"- Keep the room well-ventilated, clean, and comfortable.\n\n"

            f"🥗 **3. Food, Hydration & Nutrition Advice:**\n"
            f"- Drink plenty of clean, boiled water, ORS (Oral Rehydration Solution), coconut water, or clear soups (2.5–3 Liters/day).\n"
            f"- Eat light, easily digestible meals (rice porridge, bananas, steamed vegetables, soups).\n"
            f"- Avoid greasy, spicy, processed foods, carbonated drinks, and alcohol.\n\n"

            f"💊 **4. Over-The-Counter (OTC) Guidance & Medication Safety:**\n"
            f"- For fever or mild body aches, **Paracetamol** (Acetaminophen) is generally recommended when used as per package directions.\n"
            f"- ⚠️ **CRITICAL WARNING:** Avoid NSAIDs like **Ibuprofen** or **Aspirin** if dengue or viral fevers are suspected, as they increase bleeding risks.\n"
            f"- Do NOT take antibiotics without a doctor's explicit prescription.\n\n"

            f"🛡️ **5. Prevention & Hygiene Measures:**\n"
            f"- Maintain hand hygiene by washing hands frequently with soap and water.\n"
            f"- If contagious, isolate in a well-ventilated room and wear a protective mask.\n"
            f"- Eliminate standing water around your living space to prevent vector breeding.\n\n"

            f"🚨 **6. Red-Flag Warning Signs (Seek Urgent Medical Care if present):**\n"
            f"- Persistent high fever (>39°C or >102°F) lasting over 3 days.\n"
            f"- Difficulty breathing, shortness of breath, or sharp chest pain.\n"
            f"- Persistent vomiting or severe diarrhea leading to dehydration.\n"
            f"- Unexplained bleeding (nose, gums, skin bruising, dark stools).\n"
            f"- Confusion, extreme lethargy, or fainting.\n\n"
            f"For a definitive diagnosis and prescription treatment, please consult a qualified medical professional in {city}."
        )
        return report

    sess["conv_step"] = 0
    return "Could you please rephrase your health question or mention the disease you would like help with?"


def gemini_respond(message: str, user_id: int, sess: dict = None) -> str:
    """
    Send message to Google Gemini with multi-turn conversation context.
    Falls back to interactive multi-turn state machine if Gemini is unavailable or quota exceeded.
    """
    if not GEMINI_AVAILABLE or genai is None:
        print("[Gemini] API not configured — using interactive state machine fallback.")
        return _interactive_fallback(message, sess or {})

    try:
        # Retrieve or create a Gemini chat session for this user
        if user_id not in _chat_sessions:
            gemini_model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=SYSTEM_INSTRUCTION
            )
            _chat_sessions[user_id] = gemini_model.start_chat(history=[])

        chat_session = _chat_sessions[user_id]
        response = chat_session.send_message(message)
        return response.text.strip()

    except Exception as e:
        err_str = str(e).lower()
        if "quota" in err_str or "resource_exhausted" in err_str or "429" in err_str:
            print(f"[Gemini] Quota exceeded: {e}")
        elif "api_key" in err_str or "invalid" in err_str:
            print(f"[Gemini] API key error: {e}")
        else:
            print(f"[Gemini Error] {e}")
        # Remove stale session so next call starts fresh
        _chat_sessions.pop(user_id, None)
        return _interactive_fallback(message, sess or {})


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

    # 2. Emergency detection
    emergency = detect_emergency(english_message)

    # Keep emergency flag if bot previously asked for city/location
    last_reply_lower = session.get("last_bot_reply", "").lower()
    if "city" in last_reply_lower or "location" in last_reply_lower or "hospital" in last_reply_lower:
        emergency = True

    # 3. Get AI response (Gemini or interactive multi-turn state machine fallback)
    english_reply = gemini_respond(english_message, session["user_id"], session)

    session["last_bot_reply"] = english_reply

    # 4. Translate reply back to user language
    try:
        if language != "en" and GoogleTranslator:
            reply = GoogleTranslator(source="en", target=language).translate(english_reply)
        else:
            reply = english_reply
    except Exception:
        reply = english_reply

    # 5. Persist chat history
    try:
        query_db(
            "INSERT INTO chat_history (user_id, message, response, language) VALUES (?,?,?,?)",
            (session["user_id"], message, reply, language),
            commit=True
        )
    except Exception as e:
        print(f"[Database Error] {e}")

    # 6. Return response
    return jsonify({
        "reply": reply,
        "emergency": emergency,
        "timestamp": datetime.now().strftime("%H:%M")
    })


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


@app.route("/api/diseases")
def api_diseases():
    disease_list = query_db("SELECT * FROM diseases ORDER BY name ASC")
    return jsonify({"diseases": [dict(d) for d in disease_list]})


@app.route("/api/vaccines")
def api_vaccines():
    vaccine_list = query_db(
        "SELECT v.*, d.name AS disease_name "
        "FROM vaccines v JOIN diseases d ON v.disease_id = d.id "
        "ORDER BY d.name, v.vaccine_name"
    )
    return jsonify({"vaccines": [dict(v) for v in vaccine_list]})


# =============================================================
#  JSON Auth API  (for React / SPA frontend)
# =============================================================
@app.route("/api/register", methods=["POST"])
def api_register():
    """Register a new user and return JSON."""
    data     = request.get_json(silent=True) or {}
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    lang     = data.get("preferred_language", "en")

    if not all([name, email, password]):
        return jsonify({"error": "All fields are required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    try:
        query_db(
            "INSERT INTO users (name, email, password_hash, preferred_language) VALUES (?,?,?,?)",
            (name, email, generate_password_hash(password), lang),
            commit=True
        )
        return jsonify({"ok": True, "message": "Account created! Please log in."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "An account with that email already exists."}), 409


@app.route("/api/login", methods=["POST"])
def api_login():
    """Authenticate user and set server-side session. Returns JSON."""
    data     = request.get_json(silent=True) or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"]  = user["id"]
        session["username"] = user["name"]
        session["lang"]     = user["preferred_language"]
        return jsonify({
            "ok":   True,
            "name": user["name"],
            "lang": user["preferred_language"]
        })
    else:
        return jsonify({"error": "Invalid email or password."}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    """Clear the server-side session. Returns JSON."""
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me")
def api_me():
    """Return the currently logged-in user's info, or 401 if not logged in."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated."}), 401
    return jsonify({
        "ok":      True,
        "name":    session.get("username"),
        "lang":    session.get("lang", "en"),
        "user_id": session.get("user_id")
    })


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
with app.app_context():
    init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
