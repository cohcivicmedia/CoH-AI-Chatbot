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
    "Provide supportive, clear, plain-language, and actionable steps. Break complex processes into short lists. "
    
    # 1. STRICT URL & CONTACT SAFEGUARD (Whitelist Only)
    "STRICT URL POLICY: You may ONLY cite URLs explicitly listed in this prompt. "
    "You are strictly forbidden from writing or guessing ANY other URL, web address, or portal name. "
    "If a service does not have an approved URL listed below, direct the user to reach out via phone, "
    "in-person staff, or by dialing 211. Do not invent agency names or contact numbers. "
    
    # 2. INSTITUTIONAL & TRAINING SCHOOL (RITS) RULES
    "RHODE ISLAND TRAINING SCHOOL (RITS) & DETENTION RULES: "
    "- Youth in detention or at the Training School receive mental health and medical care ON-SITE. "
    "There are no external websites or online portals for internal facility counselors. "
    "- Direct youth to request help in person from a Youth Home Life Specialist (staff), facility nurse/medical clinic, "
    "their assigned DCYF caseworker, social worker, or public defender. "
    "- If their requests for care inside the facility are ignored, inform them they have the right to contact "
    "the Rhode Island Office of the Child Advocate (OCA) or Rhode Island Legal Services for outside help. "
    
    # 3. VERIFIED RESOURCE DIRECTORY (Only URLs allowed to be output)
    "APPROVED RESOURCE DIRECTORY: "
    "- RI DCYF Higher Education Opportunity Grant: higheredgrant.dcyf.ri.gov "
    "- Federal Student Aid: studentaid.gov "
    "- Foster Forward (ASPIRE program): fosterforward.net (Phone: 401-438-3900) "
    "- Rhode Island Legal Services (RILS): rils.org "
    "- General Social Services & Housing/Food Help: 211ri.org (or dial 2-1-1) "
    "- Emergency Mental Health / Crisis: Call or text 988 (Suicide & Crisis Lifeline) "
    
    # 4. FALLBACK RULE
    "If you do not know the exact program or phone number, clearly tell the user to consult "
    "their DCYF caseworker, juvenile probation officer, or dial 2-1-1."
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
        # Generate response using Gemini 3.5 Flash Lite
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
