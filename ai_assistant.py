# ai_assistant.py
import openai
from config import OPENAI_API_KEY
from logger import setup_logger


SUPPORTED_MODELS = {"gpt-4o-mini", "gpt-4-turbo"}

class AIAssistant:
    def __init__(self, name="Personal AI Assistant", instructions="Assist with tasks", model="gpt-4o-mini", tools=None):
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model '{model}'. Choose either 'gpt-4o-mini' or 'gpt-4-turbo'.")
        self.client = openai.Client(api_key=OPENAI_API_KEY)
        self.logger = setup_logger("AIAssistantLogger", "logs/ai_assistant.log")  # Corrected logger setup
        
        # Set default tools if none provided
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools or [{"type": "file_search"}]

        # Initialize assistant and vector store, checking if they already exist
        self.assistant = self._get_or_create_assistant()
        self.vector_store = self._get_or_create_vector_store()

    def _get_or_create_assistant(self):
        # Check if an assistant with the specified name already exists
        self.logger.info(f"Checking for existing assistant named '{self.name}'")
        existing_assistants = list(self.client.beta.assistants.list())
        
        for assistant in existing_assistants:
            if assistant.name == self.name:
                self.logger.warning(f"Assistant '{self.name}' already exists. Using the existing assistant.")
                return assistant

        # If no assistant found, create a new one
        self.logger.info(f"No existing assistant named '{self.name}' found. Creating a new assistant.")
        try:
            assistant = self.client.beta.assistants.create(
                name=self.name,
                instructions=self.instructions,
                model=self.model,
                tools=self.tools
            )
            self.logger.info("Assistant created successfully.")
            return assistant
        except Exception as e:
            self.logger.error(f"Failed to create assistant: {e}")
            return None

    def _get_or_create_vector_store(self):
        # Check if a vector store with the specified name already exists
        self.logger.info("Checking for existing vector store named 'Assistant Vector Store'")
        existing_vector_stores = list(self.client.beta.vector_stores.list())
        
        for vector_store in existing_vector_stores:
            if vector_store.name == "Assistant Vector Store":
                self.logger.warning("Vector store 'Assistant Vector Store' already exists. Using the existing vector store.")
                return vector_store

        # If no vector store found, create a new one
        self.logger.info("No existing vector store found. Creating a new vector store.")
        try:
            vector_store = self.client.beta.vector_stores.create(name="Assistant Vector Store")
            self.logger.info("Vector store created successfully.")
            return vector_store
        except Exception as e:
            self.logger.error(f"Failed to create vector store: {e}")
            return None

    def get_assistant_id(self):
        if self.assistant:
            return self.assistant.id
        else:
            self.logger.warning("Assistant is not initialized.")
            return None

    def get_vector_store_id(self):
        if self.vector_store:
            return self.vector_store.id
        else:
            self.logger.warning("Vector store is not initialized.")
            return None

    def query_llm(self, question, file_path=None):
        assistant_id = self.get_assistant_id()
        
        message = {
            "role": "user",
            "content": question,
            "attachments": []
        }

        if file_path:
            try:
                with open(file_path, "rb") as f:
                    message_file = self.client.files.create(file=f, purpose="assistants")
                file_id = message_file.id
                message["attachments"].append({"file_id": file_id, "tools": [{"type": "file_search"}]})
            except Exception as e:
                self.logger.error(f"Error opening file {file_path}: {e}")
                return None, "Error opening file."

        try:
            thread = self.client.beta.threads.create(messages=[message])
            run = self.client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=assistant_id)
            messages = list(self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
            
            if messages and messages[0].content:
                message_content = messages[0].content[0].text.value
                self.logger.info(f"Received message content: {message_content}")
                return run, message_content
            else:
                self.logger.warning("No content available in response.")
                return run, "No content available in response."
        except Exception as e:
            self.logger.error(f"Error during LLM query: {e}")
            return None, "Error during LLM query."
