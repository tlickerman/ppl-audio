import os
import json
from flask import Flask, request, jsonify, render_template
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

TOPICS = {
    "all": "a mix of airspace, FAR regulations, weather theory, aerodynamics, aircraft systems, and emergency procedures",
    "airspace": "airspace classifications Class A through G, VFR weather minimums by class, and ATC communication requirements",
    "regulations": "FAR Part 61 pilot certification and FAR Part 91 operating rules for private pilots",
    "weather": "aviation weather including fronts, fog, thunderstorms, icing, wind shear, METARs, TAFs, and PIREPs",
    "aerodynamics": "aerodynamics including angle of attack, lift, drag, stalls, spins, stability, load factors, and Vx versus Vy",
    "systems": "aircraft systems including piston engines, magnetos, carburetor heat, fuel systems, pitot-static instruments, gyroscopic instruments, and electrical systems",
    "emergencies": "emergency procedures including engine failure, electrical failure, lost communications, fire in flight, and emergency descents"
}

SYSTEM_PROMPT = """You are a precise FAA private pilot knowledge test question generator with expert knowledge of FAR Parts 61 and 91, the Pilot's Handbook of Aeronautical Knowledge, and the Aeronautical Information Manual.

YOUR ENTIRE RESPONSE MUST BE A SINGLE VALID JSON OBJECT. No text before it, no text after it. No markdown. No code fences. Start with { and end with }.

Generate exactly 5 questions in this exact structure:
{"questions":[{"q":"question text","a":"A","options":{"A":"option text","B":"option text","C":"option text"},"explain":"one sentence explanation citing the FAR or principle"}]}

Rules:
- Exactly 3 options per question: A, B, C
- "a" field = correct answer letter
- NO math, calculations, weight and balance, or chart reading
- NO references to figures or diagrams
- Questions answerable by audio only
- Only include facts you are 100% certain about from official FAA publications
- Vary difficulty across easy, medium, and harder questions"""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/questions", methods=["POST"])
def get_questions():
    data = request.get_json()
    topic = data.get("topic", "all")
    desc = TOPICS.get(topic, TOPICS["all"])

    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Generate 5 private pilot knowledge test questions on: {desc}. Output only the JSON object."
            }]
        )

        raw = message.content[0].text
        start = raw.index("{")
        end = raw.rindex("}") + 1
        parsed = json.loads(raw[start:end])

        if not isinstance(parsed.get("questions"), list) or not parsed["questions"]:
            return jsonify({"error": "No questions in response"}), 500

        return jsonify(parsed)

    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON parse error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
