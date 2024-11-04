# app.py

from flask import Flask, render_template, request, jsonify
from ai_assistant import AIAssistant
from logger import app_logger
import os
import time
import logging
import traceback
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_dev_secret")
ai_assistant = AIAssistant()

# Endpoint to get the status
status_message = ""

# Filter out status endpoint logs
class NoStatusEndpointFilter(logging.Filter):
    def filter(self, record):
        return "/status" not in record.getMessage()

# Apply the filter to the app logger
app_logger.addFilter(NoStatusEndpointFilter())
flask_logger = logging.getLogger("werkzeug")
flask_logger.addFilter(NoStatusEndpointFilter())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_status")
def status():
    return jsonify({"status": ai_assistant.get_status()})

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message")
    app_logger.info(f"User message received: {user_message}")

    try:
        # Update status for each step
        response, awaiting_confirmation = ai_assistant.handle_message(user_message)
    
        if awaiting_confirmation:
            ai_assistant.set_status("Waiting for the local model to respond")
        
        ai_assistant.set_status("Response received from the local model")
        ai_assistant.set_status("Ready to help you with your questions.")
        app_logger.info(f"Response: {response}")
        app_logger.info(f"Awaiting confirmation: {awaiting_confirmation}")
        
        return jsonify({
            "response": response,
            "awaiting_confirmation": awaiting_confirmation,
            "error": None
        })
    except Exception as e:
        app_logger.error(f"Error in chat processing: {e}")
        app_logger.error(traceback.format_exc())
        status_message = "Error processing the request."
        return jsonify({
            "error": "Error processing the request.",
            "response": None,
            "awaiting_confirmation": False
        }), 500  # Return HTTP 500 status for server errors

if __name__ == "__main__":
    app_logger.info("Starting the Flask app.")
    app.run(debug=True)
