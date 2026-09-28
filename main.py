import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = Flask(__name__)

# ------------------ Gemini Client ------------------
# Automatically uses GEMINI_API_KEY from environment variables
client = genai.Client()

SYSTEM_INSTRUCTION = (
    "You are an empathetic, knowledgeable navigator for foster care and justice-involved youth in Rhode Island. "
    "Provide supportive, clear, and actionable steps. "
    "CRITICAL ACCURACY RULE: Only state verifiable public programs and official links. "
    "Key Rhode Island resources: "
    "- Postsecondary Tuition Grant: RI DCYF Higher Education Opportunity Grant (higheredgrant.dcyf.ri.gov). "
    "- Federal support: Chafee ETV and FAFSA independent student status for foster youth. "
    "- Local nonprofits: Foster Forward (ASPIRE program at fosterforward.net, 401-438-3900) and RI Legal Services (rils.org). "
    "Never fabricate URLs, phone numbers, or agency names. If you are unsure of an exact state-level program "
    "or link, advise the user to consult their caseworker, DCYF transition coordinator, or dial 211 (211ri.org)."
)

# ------------------ Tips Storage ------------------
anonymous_tips = []
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "supersecret")

# ------------------ Routes ------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form.get('question', '').strip()
    if not user_input:
        return jsonify({"response": "Please enter a question."}), 400

    try:
        # Generate response using Gemini 2.5 Flash
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2  # Lower temperature reduces creative hallucinations
            )
        )
        ai_text = response.text
        return jsonify({"response": ai_text})
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"response": "Sorry, I am having trouble connecting right now."}), 500

@app.route("/tip", methods=["POST"])
def receive_tip():
    tip = request.form.get("tip")
    if tip:
        anonymous_tips.append(tip)
    return redirect(url_for("index"))

@app.route("/tips", methods=["GET", "POST"])
def view_tips():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            return render_template("tips.html", tips=anonymous_tips)
        return render_template("login.html", error="Incorrect password")

    return render_template("login.html")

@app.route("/delete_tip", methods=["POST"])
def delete_tip():
    tip = request.form.get("tip")
    if tip in anonymous_tips:
        anonymous_tips.remove(tip)
    return redirect(url_for("view_tips"))

# ------------------ Server Boot ------------------
if __name__ == "__main__":
    # Binds dynamically to Render's required port and host
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
