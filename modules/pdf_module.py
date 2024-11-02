# pdf_module.py

import os
import requests
import PyPDF2
import re
from config_loader import get_endpoint
from logger import setup_logger
from prompts import pdf_query_prompt

class PDFModule:
    def __init__(self, assistant_query_llm):
        self.query_llm = assistant_query_llm  # Reference to AIAssistant's query method
        self.contains_sensitive_data = False
        self.logger = setup_logger("PDFModuleLogger", "logs/pdf_module.log")
        self.processed_text = ""
        self.embeddings = []  
        self.file_paths = [] 

    def upload_directory(self, directory_path):
        """
        Processes PDF files in the given directory and stores text and embeddings locally.
        """
        pdf_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.lower().endswith(".pdf")]
        if not pdf_files:
            self.logger.info("No PDF files found in the specified directory.")
            return False

        self.processed_text = ""
        for pdf_file in pdf_files:
            try:
                with open(pdf_file, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            self.processed_text += text + "\n"
                self.file_paths.append(os.path.basename(pdf_file))  # Track available files
            except Exception as e:
                self.logger.error(f"Failed to read {pdf_file}: {e}")

        if not self.processed_text:
            self.logger.info("No text extracted from PDFs.")
            return False

        self.contains_sensitive_data = self.scan_for_sensitive_data(self.processed_text)
        self.embeddings = self.generate_embeddings(self.processed_text)  # Store embeddings in memory
        return True

    def generate_embeddings(self, text):
        """
        Generates embeddings for the provided text using the Ollama embedding API.
        """
        embed_endpoint = get_endpoint("ollama_embed")
        if not embed_endpoint:
            self.logger.error("Embedding endpoint not found.")
            return None

        try:
            response = requests.post(embed_endpoint, json={"model": "all-minilm", "input": [text]}, timeout=30)
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
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z|A-Z]{2,}\b'

        patterns = {"SSN": ssn_pattern, "Credit Card Number": cc_pattern, "Email": email_pattern}
        for name, pattern in patterns.items():
            if re.search(pattern, text):
                self.logger.info(f"Sensitive data detected: {name}")
                return True
        return False

    def get_available_files(self):
        """
        Returns a list of available PDF files.
        """
        return self.file_paths if self.file_paths else ["No PDF files available."]

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
                        total_pages += len(reader.pages)
                except Exception as e:
                    self.logger.error(f"Failed to read {file_path}: {e}")
        return total_pages

    def query(self, question):
        """
        Answers a question based on the processed PDFs using embeddings.
        """
        if not self.embeddings:
            return "No documents have been processed. Please analyze a directory first."

        # Retrieve file names for context
        file_names = self.get_available_files()
        
        # Use the updated prompt from prompts.py, including file names
        prompt = pdf_query_prompt(question, file_names)
        
        # Send the prompt to the assistant directly for response
        response = self.query_llm(prompt, is_private=self.contains_sensitive_data)
        return response
