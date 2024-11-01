# central_agent.py
import json  # Added import for JSON parsing
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
        logger.info("CentralAgent initialized.")

    def handle_message(self, message):
        """
        Processes user messages and determines if further clarification or confirmation is needed.
        """
        if self.awaiting_confirmation:
            return "Please confirm the pending action to proceed.", True

        # If the assistant is awaiting the directory path
        if self.awaiting_directory:
            self.awaiting_directory = False
            directory_path = message.strip()
            self.pending_action_query = f"analyze_directory {directory_path}"
            self.awaiting_confirmation = True
            return f"I will analyze the files at '{directory_path}'. Please confirm to proceed.", True

        # Structured prompt to analyze intent
        prompt = intent_analysis_prompt(message)

        # Analyze the intent of the user's message
        intent_analysis = self.assistant.query_llm(prompt, is_private=True)
        logger.info(f"Intent analysis result: {intent_analysis}")

        # Parse the JSON response
        try:
            intent_data = json.loads(intent_analysis)
            intent = intent_data.get("intent", "").lower()
            privacy = intent_data.get("privacy", "").lower()
        except json.JSONDecodeError:
            logger.error("Failed to parse intent analysis response as JSON.")
            # Default to general inquiry if parsing fails
            intent = "general inquiry"
            privacy = "public data"

        # Check if the user wants to analyze a directory
        if "analyze directory" in message.lower():
            self.awaiting_directory = True
            return "What is the directory you would like me to analyze?", False

        # Determine action based on intent
        if intent == "clarification needed":
            clarification_question = "Can you provide more details on your request?"
            logger.info("Clarification requested.")
            return clarification_question, False
        elif intent == "action required":
            self.awaiting_confirmation = True
            self.pending_action_query = message
            return "I can proceed with this action. Please confirm to continue.", True
        else:
            # Process general inquiry
            is_private = privacy == "private data"
            response = self.assistant.query_llm(message, is_private=is_private)
            logger.info(f"Response to general inquiry: {response}")
            return response, False

    def confirm_action(self):
        """
        Executes the pending action and updates the session's task statistics.
        """
        if not self.pending_action_query:
            return "No action to confirm."

        if self.pending_action_query.startswith("analyze_directory"):
            directory_path = self.pending_action_query.split(" ", 1)[1]
            self.pdf_module = PDFModule(self.assistant)

            # Process the PDFs
            file_batch = self.pdf_module.upload_directory_to_vector_store(directory_path)
            if not file_batch:
                self.awaiting_confirmation = False
                self.pending_action_query = None
                return "No supported PDF files found in the specified directory."

            # Decide which model to use based on sensitive data
            total_pages = self.pdf_module.get_total_pages(directory_path)
            if total_pages < 100:
                model_info = "local model (documents are within size limits)"
            else:
                if self.pdf_module.contains_sensitive_data:
                    self.awaiting_privacy_confirmation = True
                    self.awaiting_confirmation = False
                    return "The documents are large and may contain sensitive data. Do you want to proceed using the local model with potential limitations?"
                else:
                    model_info = "local model (processing large documents)"
            
            # Store the directory path for future queries
            self.processed_directory = directory_path
            self.awaiting_confirmation = False
            self.pending_action_query = None

            return f"The files have been analyzed using the {model_info}. You can now ask questions about the documents."

        # Handle other actions
        response = self.assistant.query_llm(self.pending_action_query, is_private=True)

        # Update task statistics
        task_name = self.pending_action_query.split()[0]  # Simplistic task name extraction
        self.task_count[task_name] = self.task_count.get(task_name, 0) + 1
        logger.info(f"Task '{task_name}' executed. Total count: {self.task_count[task_name]}")

        # Reset pending action
        self.awaiting_confirmation = False
        self.pending_action_query = None

        return f"Action completed: {response}"

    def handle_pdf_query(self, message):
        """
        Handles user questions after the PDFs have been processed.
        """
        if self.pdf_module:
            response = self.pdf_module.query(message)
            return response
        else:
            return "Please analyze a directory first by typing 'analyze directory'."
