# tests/test_ai_assistant.py
import unittest
from unittest.mock import patch, MagicMock
from ai_assistant import AIAssistant

class TestAIAssistant(unittest.TestCase):
    @patch("ai_assistant.openai.Client")
    def test_create_assistant_when_exists(self, MockClient):
        # Mock existing assistant list with one entry
        mock_client_instance = MockClient.return_value
        mock_client_instance.beta.assistants.list.return_value = [MagicMock(name="Personal AI Assistant")]

        # Initialize AIAssistant
        assistant = AIAssistant(name="Personal AI Assistant")

        # Assert that the assistant reused the existing instance
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
        # Mock existing vector store list with one entry
        mock_client_instance = MockClient.return_value
        mock_client_instance.beta.vector_stores.list.return_value = [MagicMock(name="Assistant Vector Store")]

        # Initialize AIAssistant
        assistant = AIAssistant()

        # Assert that the vector store reused the existing instance
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
        # Mock existing resources
        mock_client_instance = MockClient.return_value
        mock_client_instance.beta.assistants.list.return_value = [MagicMock(name="Personal AI Assistant")]
        mock_client_instance.beta.vector_stores.list.return_value = [MagicMock(name="Assistant Vector Store")]

        # Initialize AIAssistant
        assistant = AIAssistant(name="Personal AI Assistant")

        # Assert logging calls
        mock_logger_instance = MockLogger.return_value
        mock_logger_instance.warning.assert_any_call("Assistant 'Personal AI Assistant' already exists. Using the existing assistant.")
        mock_logger_instance.warning.assert_any_call("Vector store 'Assistant Vector Store' already exists. Using the existing vector store.")
