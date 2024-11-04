import os
import PyPDF2
import ollama
from logger import setup_logger

class PDFModule:
    def __init__(self, assistant_query_llm):
        self.query_llm = assistant_query_llm  # Reference to AIAssistant's query method
        self.logger = setup_logger("PDFModuleLogger", "logs/pdf_module.log")
        self.file_embeddings = {}  # Dictionary to store embeddings by file

    def upload_directory(self, directory_path):
        """
        Processes each PDF file in the directory, extracting text and generating embeddings.
        """
        pdf_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.lower().endswith(".pdf")]
        if not pdf_files:
            self.logger.info("No PDF files found in the specified directory.")
            return False

        for pdf_file in pdf_files:
            file_text = self.extract_text_from_pdf(pdf_file)
            if file_text:
                self.file_embeddings[os.path.basename(pdf_file)] = self.generate_embeddings(file_text)

        if not self.file_embeddings:
            self.logger.info("No text extracted from PDFs.")
            return False

        return True

    def extract_text_from_pdf(self, pdf_file):
        """
        Extracts text from a PDF file.
        """
        text = ""
        try:
            with open(pdf_file, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            self.logger.info(f"Text extracted from {pdf_file}.")
        except Exception as e:
            self.logger.error(f"Failed to read {pdf_file}: {e}")
        return text

    def generate_embeddings(self, text):
        """
        Generates embeddings for the provided text using the local Ollama embed function.
        """
        self.logger.info(f"Generating embeddings for text: {text}")
        try:
            if isinstance(text, str):
                embeddings = ollama.embed(model="llama3.2", input=text)
            elif isinstance(text, list):
                embeddings = ollama.embed(model="llama3.2", input=text)
            else:
                raise ValueError("Text input must be a string or a list of strings.")
            
            self.logger.info("Embeddings generated successfully.")
            return embeddings
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            return []

    def query(self, question):
        """
        Answers a question based on the processed PDFs by querying embeddings.
        """
        if not self.file_embeddings:
            return "No documents have been processed. Please analyze a directory first."

        # Formulate prompt for querying based on each file's embeddings
        file_queries = []
        for file_name, embeddings in self.file_embeddings.items():
            file_queries.append(f"File: {file_name}, Embeddings: {embeddings}")

        prompt = f"The following files have been processed:\n" + "\n".join(file_queries)
        prompt += f"\n\nBased on these files, please answer the question:\n{question}"
        
        response = self.query_llm(prompt, is_private=False)
        return response
