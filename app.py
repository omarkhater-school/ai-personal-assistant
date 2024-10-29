# app.py
import re
from flask import Flask, render_template, request, jsonify
from ai_assistant import AIAssistant
from modules.pdf_module import PDFModule

app = Flask(__name__)

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
    }
}

@app.route("/")
def index():
    return render_template("index.html", models=MODEL_INFO)

def format_response(response_text):
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

    if not model or not directory_path or not question:
        return jsonify({"error": "Please provide a model, directory path, and question."}), 400

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
