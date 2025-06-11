from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import traceback
import json

#  Load .env file
from dotenv import load_dotenv
import os

# Load environment variables (works locally with .env, safely skips on Render)
load_dotenv()

# Securely fetch the API key
api_key = os.getenv("OPENAI_API_KEY")
print("🔐 Loaded API Key:", api_key[:4] + "..." if api_key else "Not Found")

# Print current working directory for debug purposes
print("📂 Current working directory:", os.getcwd())

# Print API key to confirm it's loaded (masking for safety in production)
api_key = os.getenv("OPENAI_API_KEY")
print("🔐 Loaded API Key:", api_key[:8] + "..." if api_key else "None")

# testing



#  Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")

# Enable CORS for all frontend environments
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    "https://tenagrc.com",
    "https://www.tenagrc.com"
])


#  Initialize OpenAI client with required project ID
client = OpenAI(
    api_key=api_key,
    project="proj_SRtvvFfZT2vFJu3em1U1NAOv"
)

# Frontend route
@app.route("/")
def home():
    return "✅ EasyGRC backend is live and accepting JSON"


# ✅ Prompt generator for dashboard
def generate_prompt(data):
    lines = [f"{key.replace('-', ' ').capitalize()}: {value}" for key, value in data.items()]
    survey_summary = "\n".join(lines)

    return f"""Based on the following cybersecurity risk survey, provide:
1. A brief risk posture assessment (e.g., Low/Moderate/High Risk),
2. Also include 3 bullet points of what the organization is doing well,
3. The top 3 most concerning issues, 
4. Three practical mitigation recommendations, utilizing NIST, ISACA & ISO for controls,
5. A short summary.

Return your response strictly as a JSON object with keys:
'posture', 'strengths', 'top_risks', 'mitigations', and 'summary'.

Survey:
{survey_summary}
"""

# ✅ Risk survey analysis endpoint
@app.route("/analyze-json", methods=["POST"])
def analyze_json():
    try:
        data = request.get_json()
        print("📥 Received data:", data)

        # 🧠 Prompt for scoring and visual analysis
        scoring_prompt = f"""
        You are an experienced cybersecurity GRC consultant with over 45 years in describing complex technological risks to non-technical stakeholders. 
        You are known for your amazing communication skills  taking complex terms and making them feel extremely simple. 
        Given the following organization's answers to a security risk survey:
        {data}

        Score their cybersecurity posture on a scale from 1 to 10 (with 10 being excellent and 1 being critical risk).
        Then, based on that score, recommend a short 1-paragraph analysis of their risk level and suggest next steps.
        Make the explanation simple and readable, but insightful — be honest and realistic in your assessment, but if there is consistent monitoring (monthly or quarterly) for risks, give it a higher score. I want people to feel better about their risk posture IF it shows that they are continually dedciated to it. let the best of the best get 10/10 but be generous in handing out 8-9.5 if it seems they are consistently monitoring risks and providing trainings to staff.

        
        Format your response exactly like this:
        {{
            "score": float (1 to 10),
            "analysis": "string summary with recommendations"
        }}
        Only return valid JSON.
        """

        scoring_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": scoring_prompt}],
            temperature=0.7
        )

        scoring_content = scoring_response.choices[0].message.content.strip()
        print("🧠 GPT Scoring Response:", scoring_content)

        scoring_data = json.loads(scoring_content)
        score = float(scoring_data["score"])
        analysis = scoring_data["analysis"]

        # 🎨 Determine color based on score
        if score <= 3.0:
            color = "red"
        elif score <= 5.9:
            color = "orange"
        elif score <= 8.4:
            color = "lightgreen"
        else:
            color = "green"

        # 🧠 Prompt for dashboard insights
        dashboard_prompt = generate_prompt(data)
        dashboard_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": dashboard_prompt}],
            temperature=0.7
        )

        dashboard_content = dashboard_response.choices[0].message.content.strip()
        print("📊 GPT Dashboard Response:", dashboard_content)

        # Check if dashboard_content is JSON, or fallback to string
        try:
            json.loads(dashboard_content)
            insights = dashboard_content
        except:
            insights = json.dumps({
                "posture": "Unknown",
                "strengths": [],
                "top_risks": [],
                "mitigations": [],
                "summary": dashboard_content
            })

            

        # ✅ Final combined response
        return jsonify({
            "score": score,
            "color": color,
            "analysis": analysis,
            "insights": insights
        })

    except Exception as e:
        print("❌ Error:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# ✅ Run app
if __name__ == '__main__':
    print("🚀 Starting EasyGRC backend...")
    app.run(host='0.0.0.0', port=5000, debug=True)
