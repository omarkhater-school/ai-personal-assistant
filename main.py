# main.py
from ai_assistant import AIAssistant
from modules.pdf_module import PDFModule

def run_pdf_feature():
    # Initialize the main AI assistant
    ai_assistant = AIAssistant(name="My AI Assistant", instructions="Your helpful assistant")
    
    # Ensure assistant initialization was successful
    assistant_id = ai_assistant.get_assistant_id()
    if not assistant_id:
        print("Error: Unable to initialize the AI assistant.")
        return
    
    # Initialize the PDF module using the assistant
    pdf_module = PDFModule(ai_assistant)

    # Step 1: Upload all PDFs in a directory to vector store
    directory_path = "path/to/your/pdf/directory"
    file_batch = pdf_module.upload_directory_to_vector_store(directory_path)
    if file_batch:
        print("File Batch Status:", file_batch.status)

    # Step 2: Query a specific PDF with a question
    question = "What are the main findings in this report?"
    file_path = "path/to/your/pdf/question_file.pdf"
    run = pdf_module.query_pdf(question, file_path)
    print("Query Result Status:", run.status)

if __name__ == "__main__":
    run_pdf_feature()
