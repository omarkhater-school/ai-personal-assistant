# ai_assistant.py

import requests
import re
import os
import json
from config_loader import get_endpoint
from logger import setup_logger
from prompts import assistant_query_prompt, intent_analysis_prompt, email_drafting_prompt, clarification_prompt
from modules.pdf_module import PDFModule
from modules.email_module import EmailModule

class AIAssistant:
    def __init__(self, name="Personal AI Assistant"):
        self.logger = setup_logger("AIAssistantLogger", "logs/ai_assistant.log")
        self.name = name
        self.message_history = []  # Store all message history for /api/chat requests
        self.awaiting_confirmation = False
        self.pending_action = None
        self.pdf_module = PDFModule(self.query_llm)
        self.email_module = EmailModule(self.query_llm)

        # Define handlers for different actions
        self.action_handlers = {
            "send_email": self.handle_email_intent,
            "read_pdfs": self.handle_read_pdfs_intent,
        }
        self.logger.info("AIAssistant initialized.")

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
        Processes user messages and handles different intents.
        """
        if self.awaiting_confirmation:
            return self.handle_confirmation(message)

        # Perform intent analysis
        intent_data = self.query_intent(intent_analysis_prompt(message, self.message_history))
        self.logger.info(f"Intent analysis result: {intent_data}")

        intent = intent_data.get("intent", "").lower() if intent_data.get("intent") else None
        action = intent_data.get("action", "").lower() if intent_data.get("action") else None

        if intent == "clarification needed":
            return self.handle_clarification_needed(intent_data), False

        elif intent in ["action required (confirm)", "action required (proceed)"]:
            if action in self.action_handlers:
                return self.action_handlers[action](message, intent_data)
            else:
                self.logger.error(f"Unknown action: {action}. Supported actions are: {self.action_handlers.keys()}")
                return "I'm sorry, I didn't understand the action you want me to perform.", False

        elif intent == "general inquiry":
            response = self.query_llm(message, is_private=(intent_data.get("privacy") == "private data"))
            return response, False

        else:
            response = self.query_llm(message, is_private=(intent_data.get("privacy") == "private data"))
            return response, False

    def handle_clarification_needed(self, intent_data):
        """
        Handles cases where clarification is needed.
        Constructs a request for missing information based on the chat history.
        """
        missing_info = []
        action = intent_data.get("action", "").lower() if intent_data.get("action") else None

        # Check required fields based on action type
        if action == "send_email":
            if not intent_data.get("recipient_name"):
                missing_info.append("recipient name")
            if not intent_data.get("subject"):
                missing_info.append("subject")

        elif action == "read_pdfs":
            if not intent_data.get("directory_path"):
                missing_info.append("directory path")

        elif action == "schedule_meeting":
            if not intent_data.get("participants"):
                missing_info.append("participants")
            if not intent_data.get("time"):
                missing_info.append("time")

        elif action == "internet_search":
            if not intent_data.get("query"):
                missing_info.append("query")

        # Create a clarification prompt based on the missing information and chat history
        response = self.query_llm(clarification_prompt(action, missing_info), is_private=True)
        
        self.logger.info(f"Clarification response from LLM: {response}")
        return response

    def handle_email_intent(self, user_message, intent_data):
        """
        Handles the email drafting and confirmation process.
        """
        recipient_name = intent_data.get("recipient_name")
        subject = intent_data.get("subject", "Welcome")

        if not recipient_name:
            return "Could you please specify the recipient of the email?", False

        to_addr = self.email_module.find_email(recipient_name)
        if not to_addr:
            return f"Email address for {recipient_name} not found in contacts.", False

        prompt = email_drafting_prompt(recipient_name, subject, user_message)
        email_body = self.query_llm(prompt, is_private=True)

        draft_message = f"""
Here is the drafted email:

To: {to_addr}
Subject: {subject}
Body:
{email_body}

Please confirm if you want to send this email.
"""
        self.pending_action = {
            "action": "send_email",
            "to_addr": to_addr,
            "subject": subject,
            "body": email_body
        }
        self.awaiting_confirmation = True
        return draft_message, True

    def handle_read_pdfs_intent(self, user_message, intent_data):
        """
        Handles PDF reading and analysis process.
        """
        directory_path = intent_data.get("directory_path")
        query = intent_data.get("query", "What did you find in the directory?")
        if not directory_path:
            return "Could you please specify the directory path for the PDF files?", False

        if self.pdf_module.upload_directory(directory_path):
                response = self.pdf_module.query(query)
                return response, False
        else:
            return "Failed to process PDF files. Please check the directory path or contents.", False

    def handle_confirmation(self, message):
        """
        Handles the user's confirmation for pending actions.
        """
        if message.strip().lower() in ['yes', 'y']:
            if self.pending_action and self.pending_action['action'] == 'send_email':
                result = self.email_module.send_email(
                    self.pending_action['to_addr'],
                    self.pending_action['subject'],
                    self.pending_action['body']
                )
                self.awaiting_confirmation = False
                self.pending_action = None
                return result, False
            else:
                self.awaiting_confirmation = False
                self.pending_action = None
                return "No pending action to confirm.", False
        else:
            self.awaiting_confirmation = False
            self.pending_action = None
            return "Email sending was canceled.", False

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
        self.pdf_module = PDFModule(self.query_llm, logger=self.logger)
        file_batch = self.pdf_module.upload_directory(directory_path)
        if not file_batch:
            self.clear_history()
            return "No supported PDF files found in the specified directory.", False

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
