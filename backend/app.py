# =============================================================
#  AI-Driven Public Health Chatbot — Flask Backend
#  app.py  (SQLite edition — zero setup required)
#
#  Run  : python app.py
#  Open : http://localhost:5000
# =============================================================

import os
import sqlite3
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
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(dotenv_path=os.path.join(_base_dir, ".env"))
except ImportError:
    pass

# ── Gemini AI ─────────────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=(
                "You are HealthBot AI, a professional public health assistant. "
                "Provide clear, accurate, and compassionate health information. Always:\n"
                "- Give practical, actionable health guidance based on described symptoms.\n"
                "- Use brief bullet points when listing symptoms or steps.\n"
                "- Mention red flag symptoms that require urgent doctor visits.\n"
                "- Cover: disease info, symptom guidance, prevention, vaccination, first aid.\n"
                "- Be warm, professional, and reassuring -- never alarmist.\n"
                "- End every response with: 'For a definitive diagnosis, please consult a qualified healthcare professional.'\n"
                "- Keep responses concise (under 200 words) and easy to read.\n"
                "- If asked about non-health topics, politely redirect to health questions."
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
app.secret_key = "healthbot-dev-secret-key-change-in-prod"

# ─── Database path (created automatically on first run) ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE  = os.path.join(BASE_DIR, "healthbot.db")


# =============================================================
#  SQLite helpers
# =============================================================
def get_db():
    """Return a per-request SQLite connection."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row   # rows behave like dicts
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
        print(f"[Gemini Error] {e}")
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
            english_message = GoogleTranslator(source=language, target='en').translate(message)
        else:
            english_message = message
    except Exception:
        english_message = message

    # 2. Get AI / Fallback reply in English
    english_reply = gemini_respond(english_message, session["user_id"])

    # 3. Translate reply back to user's language
    try:
        if language != "en" and GoogleTranslator:
            reply = GoogleTranslator(source='en', target=language).translate(english_reply)
        else:
            reply = english_reply
    except Exception:
        reply = english_reply

    # Persist chat history
    try:
        query_db(
            "INSERT INTO chat_history (user_id, message, response, language) VALUES (?,?,?,?)",
            (session["user_id"], message, reply, language),
            commit=True
        )
    except Exception:
        pass

    return jsonify({"reply": reply, "timestamp": datetime.now().strftime("%H:%M")})


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
