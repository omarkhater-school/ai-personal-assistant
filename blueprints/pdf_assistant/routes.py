# blueprints/pdf_assistant/routes.py
from flask import render_template, request, jsonify
from . import pdf_assistant_bp
from ai_assistant import AIAssistant
from modules.pdf_module import PDFModule
import requests

MODEL_INFO = {
    "gpt-4o-mini": {
        "description": "GPT-4o-mini: Small and affordable for fast tasks.",
        "context_window": "128,000 tokens",
        "max_output_tokens": "16,384 tokens",
        "training_data": "Up to Oct 2023",
        "parameters": "1.3 billion",
        "is_private_model": False
    },
    "gpt-4-turbo": {
        "description": "GPT-4 Turbo: Latest model with vision capabilities.",
        "context_window": "128,000 tokens",
        "max_output_tokens": "4,096 tokens",
        "training_data": "Up to Dec 2023",
        "parameters": "175 billion",
        "is_private_model": False
    },
    "flan-t5-large": {
        "description": "Flan-T5 Large: Local model deployed for private tasks.",
        "context_window": "512 tokens",
        "max_output_tokens": "512 tokens",
        "training_data": "Up to 2022",
        "parameters": "780 million",
        "is_private_model": True
    }
}

@pdf_assistant_bp.route("/", methods=["GET"])
def pdf_assistant_home():
    return render_template("pdf_assistant.html", models=MODEL_INFO)

@pdf_assistant_bp.route("/run_query", methods=["POST"])
def run_query():
    model = request.form.get("model")
    directory_path = request.form.get("directory_path")
    question = request.form.get("question")
    is_private = request.form.get("is_private") == 'true'

    # Check if model is public and request is private
    if is_private and not MODEL_INFO[model].get("is_private_model", False):
        return jsonify({
            "error": "Cannot use public API with private data. Please select the local model for private queries."
        }), 400

    if not model or not directory_path or not question:
        return jsonify({"error": "Please provide a model, directory path, and question."}), 400

    try:
        if MODEL_INFO[model]["is_private_model"]:
            # Use the local model for private tasks
            try:
                # Send request to local LLM server
                response = requests.post("http://127.0.0.1:8000/flan-t5-large/query_pdf", json={
                    "prompt": question
                })
                response_data = response.json()
                return jsonify(response_data), response.status_code
            except requests.ConnectionError:
                # If the local server is not reachable
                return jsonify({"error": "Local LLM server is not running. Please start the server and try again."}), 500
        else:
            # Use OpenAI API or other public API
            ai_assistant = AIAssistant(name="My AI Assistant", model=model)
            pdf_module = PDFModule(ai_assistant)

            file_batch = pdf_module.upload_directory_to_vector_store(directory_path)
            if file_batch:
                run, message_content = pdf_module.query(question)
                return jsonify({
                    "file_batch_status": file_batch.status,
                    "query_result_status": run.status,
                    "response": message_content
                })
            else:
                return jsonify({"error": "No PDF files found in the specified directory."}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to process query: {e}"}), 500

