# app.py

from flask import Flask, render_template, request, jsonify
from ai_assistant import AIAssistant
from logger import app_logger
import os
import time
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_dev_secret")
ai_assistant = AIAssistant()  # Using AIAssistant instead of CentralAgent

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

@app.route("/status")
def status():
    global status_message
    return jsonify({"status": status_message})

@app.route("/chat", methods=["POST"])
def chat():
    global status_message
    user_message = request.form.get("message")
    app_logger.info(f"User message received: {user_message}")

    try:
        # Update status for each step
        status_message = "Sending to the local model"
        response, awaiting_confirmation = ai_assistant.handle_message(user_message)
        
        # Simulate a delay to show progressive updates (can remove this in production)
        time.sleep(1)
        
        if awaiting_confirmation:
            status_message = "Waiting for the local model to respond"
        
        status_message = "Response received from the local model"
        return jsonify({
            "response": response,
            "awaiting_confirmation": awaiting_confirmation,
            "error": None  # Indicate no error
        })
    except Exception as e:
        app_logger.error(f"Error in chat processing: {e}")
        status_message = "Error processing the request."
        return jsonify({
            "error": "Error processing the request.",
            "response": None,
            "awaiting_confirmation": False
        }), 500  # Return HTTP 500 status for server errors

if __name__ == "__main__":
    app_logger.info("Starting the Flask app.")
    app.run(debug=True)
