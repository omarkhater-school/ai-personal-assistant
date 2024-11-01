# modules/pdf_module.py
import os
import requests
import PyPDF2
import re
from config_loader import get_endpoint
from logger import setup_logger
from ai_assistant import AIAssistant

class PDFModule:
    def __init__(self, assistant: AIAssistant):
        self.assistant = assistant
        self.contains_sensitive_data = False
        self.logger = setup_logger("PDFModuleLogger", "logs/pdf_module.log")
        self.processed_text = ""
        self.embeddings = []
        self.vector_store = None  # Placeholder for a real vector store implementation

    def upload_directory_to_vector_store(self, directory_path):
        """
        Processes PDF files in the given directory, generates embeddings for their content, 
        and builds a vector store for question-answering.
        """
        pdf_files = []
        for filename in os.listdir(directory_path):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(directory_path, filename)
                pdf_files.append(file_path)

        if not pdf_files:
            self.logger.info("No PDF files found in the specified directory.")
            return False  # No PDF files found

        # Extract text from PDFs
        self.processed_text = ""
        total_pages = 0
        for pdf_file in pdf_files:
            try:
                with open(pdf_file, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    num_pages = len(reader.pages)
                    total_pages += num_pages
                    for page_num in range(num_pages):
                        page = reader.pages[page_num]
                        text = page.extract_text()
                        if text:
                            self.processed_text += text + "\n"
            except Exception as e:
                self.logger.error(f"Failed to read {pdf_file}: {e}")
                continue

        if not self.processed_text:
            self.logger.info("No text extracted from PDFs.")
            return False

        # Scan for sensitive data
        self.contains_sensitive_data = self.scan_for_sensitive_data(self.processed_text)
        self.logger.info(f"Sensitive data detected: {self.contains_sensitive_data}")

        # Generate embeddings for the extracted text
        self.embeddings = self.generate_embeddings(self.processed_text)
        if not self.embeddings:
            self.logger.error("Failed to generate embeddings.")
            return False

        # For now, assume vector_store is built
        self.vector_store = True  # Placeholder
        self.logger.info("PDF files have been processed and embeddings have been generated.")
        return True

    def generate_embeddings(self, text):
        """
        Generates embeddings for the provided text using Ollama's embedding API.
        """
        embed_endpoint = get_endpoint("ollama_embed")
        if not embed_endpoint:
            self.logger.error("Embedding endpoint not found in configuration.")
            return None

        try:
            response = requests.post(
                embed_endpoint,
                json={"model": "all-minilm", "input": [text]},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings", [])
            self.logger.info("Embeddings generated successfully.")
            return embeddings
        except requests.RequestException as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            return None

    def scan_for_sensitive_data(self, text):
        """
        Scans the text for patterns that might indicate sensitive data.
        """
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'  # Social Security Number pattern
        cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'  # Credit Card Number pattern
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z|A-Z]{2,}\b'  # Email pattern

        sensitive_patterns = {
            "SSN": ssn_pattern,
            "Credit Card Number": cc_pattern,
            "Email Address": email_pattern
        }

        for data_type, pattern in sensitive_patterns.items():
            if re.search(pattern, text):
                self.logger.info(f"Sensitive data detected: {data_type}")
                return True

        return False

    def get_total_pages(self, directory_path):
        """
        Returns the total number of pages in all PDF files in the directory.
        """
        total_pages = 0
        for filename in os.listdir(directory_path):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(directory_path, filename)
                try:
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        num_pages = len(reader.pages)
                        total_pages += num_pages
                except Exception as e:
                    self.logger.error(f"Failed to read {file_path}: {e}")
                    continue
        return total_pages

    def query(self, question):
        """
        Answers a question based on the processed PDFs using embeddings.
        """
        if not self.vector_store or not self.embeddings:
            return "No documents have been processed. Please analyze a directory first."

        # Placeholder for querying a vector store. In practice, this would involve a similarity search.
        prompt = f"Based on the following embeddings, answer the question:\n\nQuestion: {question}"
        response = self.assistant.query_llm(prompt, is_private=self.contains_sensitive_data)
        return response
