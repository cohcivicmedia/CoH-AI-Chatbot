import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

app = Flask(__name__)

# ------------------ Mistral ------------------
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

# ------------------ Tips Storage ------------------
anonymous_tips = []
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "supersecret")

# ------------------ Routes ------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form.get('question', '')
    if not user_input:
        return jsonify({"response": "Please enter a question."}), 400

    # Put the system prompt and user input here:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an empathetic, knowledgeable navigator for foster care and justice-involved youth. "
                "Provide supportive, clear, actionable steps. "
                "CRITICAL ACCURACY RULE: Only state verifiable public programs. "
                "Never fabricate URL links or organization names. If you are unsure of an exact state-level program "
                "or contact link, advise the user to consult their caseworker, DCYF transition coordinator, "
                "or 211 (211.org) directly."
            )
        },
        {"role": "user", "content": user_input}
    ]

    try:
        response = client.chat.complete(
            model="ministral-8b-latest",
            messages=messages
        )
        ai_text = response.choices[0].message.content
        return jsonify({"response": ai_text})
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
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


if __name__ == "__main__":
    app.run(debug=True)
