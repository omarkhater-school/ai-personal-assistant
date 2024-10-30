# app.py
import os
import re
import subprocess
import requests
from flask import Flask, render_template, request, jsonify
from ai_assistant import AIAssistant
from modules.pdf_module import PDFModule

app = Flask(__name__)

# Model info
MODEL_INFO = {
    "gpt-4o-mini": {
        "description": "GPT-4o-mini: Small and affordable for fast tasks. Points to gpt-4o-mini-2024-07-18.",
        "context_window": "128,000 tokens",
        "max_output_tokens": "16,384 tokens",
        "training_data": "Up to Oct 2023"
    },
    "gpt-4-turbo": {
        "description": "GPT-4 Turbo: Latest model with vision capabilities. Points to gpt-4-turbo-2024-04-09.",
        "context_window": "128,000 tokens",
        "max_output_tokens": "4,096 tokens",
        "training_data": "Up to Dec 2023"
    },
    "flan-t5": {
        "description": "Flan-T5: Open-source model suitable for fast local inference.",
        "context_window": "128,000 tokens",
        "max_output_tokens": "4,096 tokens",
        "training_data": "Up to Dec 2023"
    }
}

LOCAL_SERVER_URL = "http://127.0.0.1:8000/flan-t5"  # URL for the Flan-T5 local server

def start_local_server():
    """Starts the Flan-T5 local server if it's not already running."""
    try:
        # Check if the server is already running
        response = requests.get(LOCAL_SERVER_URL)
        if response.status_code == 200:
            print("Local LLM server is already running.")
            return
    except requests.ConnectionError:
        print("Starting the local LLM server for Flan-T5...")
        subprocess.Popen(["python", "local_llm_server/server.py"])

def format_response(response_text):
    response_text = re.sub(r'(\d\.\s)', r'</p><p>\1', response_text)
    response_text = re.sub(r'(\*\*.*?\*\*)', r'<strong>\1</strong>', response_text)
    response_text = re.sub(r'\*\*', '', response_text)
    return f"<p>{response_text}</p>"

@app.route("/")
def index():
    return render_template("index.html", models=MODEL_INFO)

@app.route("/run_query", methods=["POST"])
def run_query():
    model = request.form.get("model")
    directory_path = request.form.get("directory_path")
    question = request.form.get("question")

    if not model or not directory_path or not question:
        return jsonify({"error": "Please provide a model, directory path, and question."}), 400

    if model == "flan-t5":
        start_local_server()
        try:
            response = requests.post(LOCAL_SERVER_URL, json={"prompt": question})
            response_data = response.json()
            formatted_content = format_response(response_data["response"])
            return jsonify({"response": formatted_content})
        except requests.RequestException as e:
            return jsonify({"error": "Failed to connect to the local LLM server."}), 500
    else:
        ai_assistant = AIAssistant(name="My AI Assistant", instructions="Your helpful assistant", model=model)
        pdf_module = PDFModule(ai_assistant)
        file_batch = pdf_module.upload_directory_to_vector_store(directory_path)

        if file_batch:
            run, message_content = pdf_module.query_pdf(question)
            formatted_content = format_response(message_content.value)
            response = {
                "file_batch_status": file_batch.status,
                "query_result_status": run.status,
                "response": formatted_content
            }
            return jsonify(response)
        else:
            return jsonify({"error": "No PDF files found in the specified directory."}), 400

if __name__ == "__main__":
    app.run(debug=True)
