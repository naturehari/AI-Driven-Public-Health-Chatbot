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
        model_name="gemini-1.5-flash",
        system_instruction=(
            "You are HealthBot AI."
        )
    )
    chat = model.start_chat()
    res = chat.send_message("I have a throat pain")
    print("SUCCESS 1.5-flash:", res.text)
except Exception as e:
    print("ERROR 1.5-flash:", e)
