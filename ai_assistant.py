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
        self.logger = setup_logger()
        
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
