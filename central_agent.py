# central_agent.py

import json
import os
import re
from ai_assistant import AIAssistant
from logger import ai_assistant_logger as logger
from modules.pdf_module import PDFModule
from prompts import intent_analysis_prompt

class CentralAgent:
    def __init__(self, assistant_name="Personal AI Assistant"):
        self.assistant = AIAssistant(name=assistant_name, model="ollama")
        self.task_count = {}
        self.awaiting_confirmation = False
        self.pending_action_query = None
        self.awaiting_directory = False
        self.processed_directory = None
        self.pdf_module = None
        self.awaiting_privacy_confirmation = False
        self.directory_analyzed = False  # Track if a directory has been analyzed
        logger.info("CentralAgent initialized.")

    def handle_message(self, message):
        """
        Processes user messages, handling queries about analyzed PDFs directly.
        """
        if self.awaiting_confirmation:
            return "Please confirm the pending action to proceed.", True

        # Check if a directory has been analyzed, and treat further messages as PDF queries
        if self.directory_analyzed:
            return self.handle_pdf_query(message)

        # Perform intent analysis without affecting the main message history
        prompt = intent_analysis_prompt(message)
        intent_analysis = self.assistant._query_ollama_intent_analysis(prompt)
        logger.info(f"Intent analysis result: {intent_analysis}")

        # Extract intent and privacy
        intent = intent_analysis.get("intent", "").lower()
        privacy = intent_analysis.get("privacy", "").lower()

        # Handle intent accordingly
        if intent == "action required (proceed)" and "directory" in message.lower():
            directory_path = self.extract_directory_path(message)
            if directory_path:
                self.directory_analyzed = True
                return self.confirm_action_for_pdf(directory_path, privacy == "private data")
            else:
                return "The specified directory path is invalid or does not exist. Please check and try again.", False

        # For other intents or general inquiries, pass the user's message to the LLM for a natural response
        response = self.assistant.query_llm(message, is_private=privacy == "private data")
        logger.info(f"Direct response from LLM: {response}")
        return response, False

    def extract_directory_path(self, message):
        """
        Extracts a valid directory path from the message using regular expressions.
        """
        match = re.search(r"[A-Za-z]:\\(?:[^\s]+\\)*[^\s]+", message)
        if match:
            directory_path = match.group(0)
            if os.path.isdir(directory_path):
                return directory_path
            else:
                logger.error(f"The extracted path does not exist: {directory_path}")
                return None
        else:
            logger.error("No valid directory path found in the message.")
            return None

    def confirm_action_for_pdf(self, directory_path, is_private):
        """
        Executes the PDF analysis action.
        """
        self.pdf_module = PDFModule(self.assistant)
        file_batch = self.pdf_module.upload_directory_to_vector_store(directory_path)
        if not file_batch:
            self.assistant.clear_history()
            return "No supported PDF files found in the specified directory.", False

        total_pages = self.pdf_module.get_total_pages(directory_path)
        model_info = "local model" if total_pages < 100 else "local model with extended limits"
        self.processed_directory = directory_path
        self.assistant.clear_history()

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
        Executes the pending action and updates the session's task statistics.
        """
        if not self.pending_action_query:
            return "No action to confirm.", False

        response = self.assistant.query_llm(self.pending_action_query, is_private=True)
        task_name = self.pending_action_query.split()[0]
        self.task_count[task_name] = self.task_count.get(task_name, 0) + 1
        self.assistant.clear_history()
        return f"Action completed: {response}", False
