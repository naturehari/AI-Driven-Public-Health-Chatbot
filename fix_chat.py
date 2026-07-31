import os

app_path = os.path.join('AI_mini_proj', 'backend', 'app.py')
content = open(app_path, 'r', encoding='utf-8').read()

start_marker = '@app.route("/api/chat", methods=["POST"])'
end_marker = '@app.route("/api/search-hospitals", methods=["POST"])'

start_idx = content.index(start_marker)
end_idx = content.index(end_marker)

new_func = '''\
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

    # 3. Get AI response
    # Gemini handles ALL messages: any disease, typos, unknown terms.
    # The system prompt already instructs Gemini to ask age, duration,
    # severity step-by-step, so no rigid state machine is needed.
    english_reply = gemini_respond(english_message, session["user_id"])

    # Keyword fallback if Gemini is completely unavailable
    if "offline mode" in english_reply.lower():
        english_reply = _keyword_fallback(english_message)

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

'''

new_content = content[:start_idx] + new_func + content[end_idx:]
open(app_path, 'w', encoding='utf-8').write(new_content)
print(f"Done! Total lines: {len(new_content.splitlines())}")
