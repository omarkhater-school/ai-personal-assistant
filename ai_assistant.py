# ai_assistant.py

import requests
from config_loader import get_endpoint
from logger import setup_logger
import json
from prompts import assistant_query_prompt, intent_analysis_prompt
import os
import re
from modules.pdf_module import PDFModule

class AIAssistant:
    def __init__(self, name="Personal AI Assistant"):
        self.logger = setup_logger("AIAssistantLogger", "logs/ai_assistant.log")
        self.name = name
        self.message_history = []  # Store all message history for /api/chat requests
        self.task_count = {}
        self.awaiting_confirmation = False
        self.pending_action_query = None
        self.awaiting_directory = False
        self.processed_directory = None
        self.pdf_module = None
        self.awaiting_privacy_confirmation = False
        self.directory_analyzed = False  # Track if a directory has been analyzed
        self.logger.info("AIAssistant initialized.")
        self.pdf_module = PDFModule(self.query_llm, logger=self.logger)

    def query_llm(self, question, is_private=False):
        """
        Query Ollama language model.
        """
        formatted_prompt = assistant_query_prompt(question)
        return self._query_ollama_chat(formatted_prompt)

    def _query_ollama_chat(self, question):
        try:
            self.message_history.append({"role": "user", "content": question})
            ollama_chat_url = get_endpoint("ollama_chat")
            payload = {
                "model": "llama3.2",
                "messages": self.message_history,
                "stream": False
            }
            response = requests.post(ollama_chat_url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "No response from Ollama.")
            self.message_history.append({"role": "assistant", "content": content})
            return content
        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            self.logger.error(f"Ollama request failed: {e}")
            return "Error processing request with the local model."

    def query_intent(self, prompt):
        """
        Perform intent analysis using Ollama.
        """
        try:
            ollama_chat_url = get_endpoint("ollama_chat")
            payload = {
                "model": "llama3.2",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
            response = requests.post(ollama_chat_url, json=payload, timeout=300)
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "{}")
            intent_data = json.loads(content)
            return intent_data
        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            self.logger.error(f"Intent analysis request failed: {e}")
            return {"intent": "general inquiry", "privacy": "public data"}

    def handle_message(self, message):
        """
        Processes user messages, handling queries about analyzed PDFs directly.
        """
        if self.awaiting_confirmation:
            return "Please confirm the pending action to proceed.", True

        if self.directory_analyzed:
            return self.handle_pdf_query(message)

        prompt = intent_analysis_prompt(message)
        intent_analysis = self.query_intent(prompt)
        intent = intent_analysis.get("intent", "").lower()
        privacy = intent_analysis.get("privacy", "").lower()

        if intent == "action required (proceed)" and "directory" in message.lower():
            directory_path = self.extract_directory_path(message)
            if directory_path:
                self.directory_analyzed = True
                return self.confirm_action_for_pdf(directory_path, privacy == "private data")
            else:
                return "The specified directory path is invalid or does not exist. Please check and try again.", False

        response = self.query_llm(message, is_private=privacy == "private data")
        return response, False

    def extract_directory_path(self, message):
        """
        Extracts a valid directory path from the message.
        """
        match = re.search(r"[A-Za-z]:\\(?:[^\s]+\\)*[^\s]+", message)
        if match:
            directory_path = match.group(0)
            if os.path.isdir(directory_path):
                return directory_path
            else:
                self.logger.error(f"The extracted path does not exist: {directory_path}")
        else:
            self.logger.error("No valid directory path found in the message.")
        return None

    def confirm_action_for_pdf(self, directory_path, is_private):
        """
        Executes the PDF analysis action.
        """
        self.pdf_module = PDFModule(self)
        file_batch = self.pdf_module.upload_directory_to_vector_store(directory_path)
        if not file_batch:
            self.clear_history()
            return "No supported PDF files found in the specified directory.", False

        total_pages = self.pdf_module.get_total_pages(directory_path)
        model_info = "local model"
        self.processed_directory = directory_path
        self.clear_history()

        return f"The files have been analyzed using the {model_info}. You can now ask questions about the documents.", False

    def handle_pdf_query(self, message):
        """
        Handles user questions after PDFs have been processed.
        """
        if "available papers" in message.lower():
            available_files = self.pdf_module.get_available_files()
            return f"The available papers are:\n" + "\n".join(available_files), False
        else:
            response = self.pdf_module.query(message)
            return response, False

    def confirm_action(self):
        """
        Executes the pending action.
        """
        if not self.pending_action_query:
            return "No action to confirm.", False

        response = self.query_llm(self.pending_action_query, is_private=True)
        task_name = self.pending_action_query.split()[0]
        self.task_count[task_name] = self.task_count.get(task_name, 0) + 1
        self.clear_history()
        return f"Action completed: {response}", False

    def clear_history(self):
        """ Clears the conversation history. """
        self.message_history = []
