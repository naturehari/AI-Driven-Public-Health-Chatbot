import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("NO API KEY")
    exit(1)

genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=(
            "You are HealthBot AI, a friendly, professional, and compassionate public health assistant. "
            "Your goal is to have a natural conversation with the user and provide safe, useful health information.\n\n"

            "CRITICAL CONVERSATION RULE:\n"
            "When a user reports a symptom or health problem, DO NOT immediately give medical advice. You MUST gather context first.\n"
            "You MUST ask EXACTLY ONE question per response. Never ask multiple questions in a single message.\n"
            "Follow this sequence strictly, waiting for the user's reply before moving to the next step:\n"
            "Step 1: Ask the user's age.\n"
            "Step 2: Ask how long the symptom has been present.\n"
            "Step 3: Ask about the severity (mild, moderate, or severe).\n"
            "Step 4: Ask if they have any other accompanying symptoms.\n"
            "Violating this rule by asking for multiple details at once is strictly forbidden.\n\n"
        )
    )
    chat = model.start_chat()
    res = chat.send_message("I have a throat pain")
    print("SUCCESS:", res.text)
except Exception as e:
    print("ERROR:", e)
