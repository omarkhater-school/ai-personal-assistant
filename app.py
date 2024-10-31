# app.py
import re
from flask import Flask, render_template, request, jsonify
from ai_assistant import AIAssistant
from modules.pdf_module import PDFModule
import requests
from logger import app_logger, local_server_logger, openai_logger  # Import loggers

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # If you need CORS

app = Flask(__name__)
CORS(app)  # Enable CORS if needed

MODEL_INFO = {
    "gpt-4o-mini": {
        "description": "GPT-4o-mini: Small and affordable for fast tasks.",
        "context_window": "128,000 tokens",
        "max_output_tokens": "16,384 tokens",
        "training_data": "Up to Oct 2023",
        "parameters": "1.3 billion"  # This is a placeholder; adjust based on actual info if available
    },
    "gpt-4-turbo": {
        "description": "GPT-4 Turbo: Latest model with vision capabilities.",
        "context_window": "128,000 tokens",
        "max_output_tokens": "4,096 tokens",
        "training_data": "Up to Dec 2023",
        "parameters": "175 billion"  # This aligns with GPT-4 architecture scale
    },
    "flan-t5-large": {
        "description": "Flan-T5 Large: Local model deployed for private tasks.",
        "context_window": "512 tokens",
        "max_output_tokens": "512 tokens",
        "training_data": "Up to 2022",
        "parameters": "780 million"
    }
}

@app.route("/")
def index():
    app_logger.info("Rendering index page with model information.")
    return render_template("index.html", models=MODEL_INFO)

def format_response(response_text):
    if not isinstance(response_text, str):
        app_logger.error("Invalid response text type. Expected a string.")
        return "Invalid response format."

    # Use regex to identify and replace numbered points with HTML list formatting
    response_text = re.sub(r'(\d\.\s)', r'</p><p>\1', response_text)  # Close and open paragraphs around numbered points
    response_text = re.sub(r'(\*\*.*?\*\*)', r'<strong>\1</strong>', response_text)  # Bold text between asterisks
    response_text = re.sub(r'\*\*', '', response_text)  # Remove extra asterisks after adding HTML <strong>

    # Wrap response in paragraphs for a clean HTML format
    return f"<p>{response_text}</p>"

@app.route("/run_query", methods=["POST"])
def run_query():
    model = request.form.get("model")
    directory_path = request.form.get("directory_path")
    question = request.form.get("question")
    is_private = request.form.get("is_private") == 'true'  # Convert to boolean

    app_logger.info(f"Received query with model: {model}, directory: {directory_path}, private: {is_private}")

    if not model or not directory_path or not question:
        app_logger.warning("Missing model, directory path, or question in the request.")
        response = jsonify({"error": "Please provide a model, directory path, and question."})
        response.headers['Content-Type'] = 'application/json'
        return response, 400

    if is_private:
        if model == "flan-t5-large":
            # Route to local LLM
            try:
                local_server_logger.info("Routing query to local LLM.")
                response = requests.post("http://127.0.0.1:8000/flan-t5-large/query_pdf", json={
                    "prompt": question
                })
                response_data = response.json()  # Extract the JSON data from the response
                local_server_logger.info(f"Received response from local LLM: {response_data}")
                return jsonify(response_data), response.status_code
            except requests.RequestException as e:
                local_server_logger.error(f"Error communicating with local LLM: {e}")
                return jsonify({"error": "Failed to communicate with local LLM. Please check the server and try again."}), 500
        else:
            app_logger.warning("Attempt to use public API with private data.")
            response = jsonify({
                "error": "Cannot use public API with private data. Please select the local model for private queries."
            })
            response.headers['Content-Type'] = 'application/json'
            return response, 400
    else:
        # Use OpenAI API
        try:
            openai_logger.info("Using OpenAI API for query.")
            ai_assistant = AIAssistant(name="My AI Assistant", model=model)
            pdf_module = PDFModule(ai_assistant)

            file_batch = pdf_module.upload_directory_to_vector_store(directory_path)
            if file_batch:
                run, message_content = pdf_module.query(question)
                formatted_content = format_response(message_content)
                response = {
                    "file_batch_status": file_batch.status,
                    "query_result_status": run.status,
                    "response": formatted_content
                }
                openai_logger.info("Query processed successfully with OpenAI API.")
                return jsonify(response)
            else:
                openai_logger.warning("No PDF files found in the specified directory.")
                return jsonify({"error": "No PDF files found in the specified directory."}), 400
        except Exception as e:
            openai_logger.error(f"Error using OpenAI API: {e}")
            return jsonify({"error": "Failed to process query with OpenAI API. Please try again later."}), 500

if __name__ == "__main__":
    app_logger.info("Starting Flask application.")
    app.run(debug=True)
