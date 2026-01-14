from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

from fall_detection import fall_detection_bp
from guardian_auth import guardian_auth_bp
from elderly_management import elderly_management_bp
from medicine_management import medicine_bp
from suggestions_management import suggestions_bp

main_app = Flask(__name__)
CORS(main_app)

main_app.register_blueprint(fall_detection_bp)
main_app.register_blueprint(guardian_auth_bp)
main_app.register_blueprint(elderly_management_bp)
main_app.register_blueprint(medicine_bp)
main_app.register_blueprint(suggestions_bp)

API_KEY = "YOUR API KEY HERE"
client = genai.Client(api_key=API_KEY)


@main_app.route("/chat", methods=["POST"])
def chat():
    print("--- MESSAGE RECEIVED ---")
    data = request.get_json()
    user_message = data.get("message", "")
    print(f"User said: {user_message}")

    model_options = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-8b"]
    for model_name in model_options:
        try:
            print(f"Trying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name, 
                contents=user_message
            )
            print(f"Success with {model_name}!")
            return jsonify({"reply": response.text})
        except Exception as e:
            print(f"Failed {model_name}: {e}")
            continue 

    return jsonify({"reply": "I'm right here. I'm just organizing my thoughts. How can I help you feel better?"})


@main_app.route("/", methods=["GET"])
def home():
    print("🚀 Starting SilverCare Backend")
    return {
        "status": "success",
        "message": "SilverCare Main Backend",
        "endpoints": {
            "guardian": {
                "register": "POST /guardian-register",
                "login": "POST /guardian-login",
                "info": "GET /guardian-info/<username>",
                "update": "POST /guardian-update",
                "elderly": "GET /guardian-elderly/<username>"
            },
            "elderly": {
                "register": "POST /elderly-register",
                "info": "GET /elderly-info/<elderly_id>",
                "update": "POST /elderly-update",
                "by_guardian": "GET /guardian-elderly/<username>"
            },
            "fall_detection": {
                "detect": "POST /detect-fall",
                "status": "GET /fall-status",
                "clear": "POST /clear-fall",
                "notify_fall": "POST /notify-guardian-fall",
                "notify_no_response": "POST /notify-guardian-no-response",
                "notify_safe": "POST /notify-guardian-safe"
            },
            "chatbot": {
                "chat": "POST /chat"
            },
            "medicine_management": {
                "add_medicine": "POST /medicine/add",
                "get_medicines": "GET /medicines/<elderly_id>",
                "confirm_medicine": "POST /medicine/confirm",
                "manage_suggestions": "GET/POST /medicine/suggestions/<elderly_id>"
            }
        }
    }, 200


if __name__ == "__main__":
    main_app.run(port=5001, debug=True)
