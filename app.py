# app.py
from flask import Flask, render_template, request, jsonify, session
from central_agent import CentralAgent
from logger import app_logger
import os
# Initialize Flask app and session
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_dev_secret")  # Use a default for development
central_agent = CentralAgent()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    # Get the user's message from the request
    user_message = request.form.get("message")
    app_logger.info(f"User message received: {user_message}")

    try:
        # Handle the message through CentralAgent
        response, awaiting_confirmation = central_agent.handle_message(user_message)
        return jsonify({"response": response, "awaiting_confirmation": awaiting_confirmation})
    except Exception as e:
        app_logger.error(f"Error in chat processing: {e}")
        return jsonify({"error": "Error processing the request."})

@app.route("/confirm_action", methods=["POST"])
def confirm_action():
    try:
        # Confirm the pending action through CentralAgent
        response = central_agent.confirm_action()
        return jsonify({"response": response})
    except Exception as e:
        app_logger.error(f"Error in action confirmation: {e}")
        return jsonify({"error": "Error confirming the action."})

if __name__ == "__main__":
    app_logger.info("Starting the Flask app.")
    app.run(debug=True)
