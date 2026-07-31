import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    chat = model.start_chat()
    res = chat.send_message("hi")
    print("SUCCESS lite:", res.text)
except Exception as e:
    print("ERROR lite:", e)
