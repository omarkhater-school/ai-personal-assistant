# central_agent.py
from ai_assistant import AIAssistant
from logger import ai_assistant_logger as logger

class CentralAgent:
    def __init__(self, assistant_name="Personal AI Assistant"):
        self.assistant = AIAssistant(name=assistant_name, model="ollama")
        self.task_count = {}
        self.awaiting_confirmation = False
        self.pending_action_query = None
        logger.info("CentralAgent initialized.")

    def handle_message(self, message):
        """
        Processes user messages and determines if further clarification or confirmation is needed.
        """
        if self.awaiting_confirmation:
            return "Please confirm the pending action to proceed.", True

        # Analyze the intent of the user's message
        intent_analysis = self.assistant.query_llm(f"Analyze the task for this query: '{message}'", is_private=True)
        logger.info(f"Intent analysis result: {intent_analysis}")

        # Improved logic for determining if clarification or action is needed
        if "clarify" in intent_analysis.lower():
            clarification_question = "Can you provide more details on your request?"
            logger.info("Clarification requested.")
            return clarification_question, False
        elif "action" in intent_analysis.lower() and "no action" not in intent_analysis.lower():
            self.awaiting_confirmation = True
            self.pending_action_query = message
            return "I can proceed with this action. Please confirm to continue.", True
        else:
            # Process non-action or general informational queries
            response = self.assistant.query_llm(message, is_private="private" in intent_analysis.lower())
            logger.info(f"Response to non-action query: {response}")
            return response, False

    def confirm_action(self):
        """
        Executes the pending action and updates the session's task statistics.
        """
        if not self.pending_action_query:
            return "No action to confirm."

        # Execute the action
        response = self.assistant.query_llm(self.pending_action_query, is_private=True)
        
        # Update task statistics
        task_name = self.pending_action_query.split()[0]  # Simplistic task name extraction
        self.task_count[task_name] = self.task_count.get(task_name, 0) + 1
        logger.info(f"Task '{task_name}' executed. Total count: {self.task_count[task_name]}")

        # Reset pending action
        self.awaiting_confirmation = False
        self.pending_action_query = None

        return f"Action completed: {response}"
