# tests/test_ai_assistant.py
import unittest
from unittest.mock import patch, MagicMock
from ai_assistant import AIAssistant

class TestAIAssistant(unittest.TestCase):
    @patch("ai_assistant.openai.Client")
    def test_create_assistant_when_exists(self, MockClient):
        # Create a mock assistant object with the specified name
        mock_assistant = MagicMock()
        mock_assistant.name = "Personal AI Assistant"
        
        # Mock the client instance and assistant list to return the existing assistant
        mock_client_instance = MockClient.return_value
        mock_client_instance.beta.assistants.list.return_value = [mock_assistant]

        # Initialize AIAssistant
        assistant = AIAssistant(name="Personal AI Assistant")

        # Assert that create was not called because an assistant with the same name already exists
        mock_client_instance.beta.assistants.create.assert_not_called()

    @patch("ai_assistant.openai.Client")
    def test_create_assistant_when_not_exists(self, MockClient):
        # Mock no existing assistants
        mock_client_instance = MockClient.return_value
        mock_client_instance.beta.assistants.list.return_value = []

        # Initialize AIAssistant
        assistant = AIAssistant(name="New AI Assistant")

        # Assert that the assistant was created since none existed
        mock_client_instance.beta.assistants.create.assert_called_once()

    @patch("ai_assistant.openai.Client")
    def test_create_vector_store_when_exists(self, MockClient):
        # Create a mock vector store object with the specified name
        mock_vector_store = MagicMock()
        mock_vector_store.name = "Assistant Vector Store"
        
        # Mock the client instance and vector store list to return the existing vector store
        mock_client_instance = MockClient.return_value
        mock_client_instance.beta.vector_stores.list.return_value = [mock_vector_store]

        # Initialize AIAssistant
        assistant = AIAssistant()

        # Assert that create was not called because a vector store with the same name already exists
        mock_client_instance.beta.vector_stores.create.assert_not_called()

    @patch("ai_assistant.openai.Client")
    def test_create_vector_store_when_not_exists(self, MockClient):
        # Mock no existing vector stores
        mock_client_instance = MockClient.return_value
        mock_client_instance.beta.vector_stores.list.return_value = []

        # Initialize AIAssistant
        assistant = AIAssistant()

        # Assert that the vector store was created since none existed
        mock_client_instance.beta.vector_stores.create.assert_called_once()

    @patch("ai_assistant.setup_logger")
    @patch("ai_assistant.openai.Client")
    def test_logging_for_existing_resources(self, MockClient, MockLogger):
        # Create mock assistant and vector store objects with the specified names
        mock_assistant = MagicMock()
        mock_assistant.name = "Personal AI Assistant"
        mock_vector_store = MagicMock()
        mock_vector_store.name = "Assistant Vector Store"

        # Mock the client instance to return existing resources
        mock_client_instance = MockClient.return_value
        mock_client_instance.beta.assistants.list.return_value = [mock_assistant]
        mock_client_instance.beta.vector_stores.list.return_value = [mock_vector_store]

        # Initialize AIAssistant with name matching the existing assistant
        assistant = AIAssistant(name="Personal AI Assistant")

        # Assert that the logger outputs the correct warnings
        mock_logger_instance = MockLogger.return_value
        mock_logger_instance.warning.assert_any_call("Assistant 'Personal AI Assistant' already exists. Using the existing assistant.")
        mock_logger_instance.warning.assert_any_call("Vector store 'Assistant Vector Store' already exists. Using the existing vector store.")

    @patch("ai_assistant.openai.Client")
    def test_supported_model_gpt_4o_mini(self, MockClient):
        assistant = AIAssistant(name="Test Assistant", model="gpt-4o-mini")
        self.assertEqual(assistant.model, "gpt-4o-mini")

    @patch("ai_assistant.openai.Client")
    def test_supported_model_gpt_4_turbo(self, MockClient):
        assistant = AIAssistant(name="Test Assistant", model="gpt-4-turbo")
        self.assertEqual(assistant.model, "gpt-4-turbo")

    @patch("ai_assistant.openai.Client")
    def test_unsupported_model(self, MockClient):
        with self.assertRaises(ValueError) as context:
            AIAssistant(name="Test Assistant", model="unsupported-model")
        self.assertEqual(
            str(context.exception),
            "Unsupported model 'unsupported-model'. Choose either 'gpt-4o-mini' or 'gpt-4-turbo'."
        )