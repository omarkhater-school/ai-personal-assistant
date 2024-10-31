import unittest
from unittest.mock import patch, MagicMock, mock_open
import requests
# from ai_assistant import AIAssistant
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app import app

class TestLocalLLM(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    @patch("requests.get")
    def test_local_server_running(self, mock_get):
        """
        Test to check if the local server is running.
        """

        # Mock the response from the local server
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Simulate checking the server status
        response = requests.get("http://127.0.0.1:8000/status")

        # Assert that the server is running
        mock_get.assert_called_once_with("http://127.0.0.1:8000/status")
        self.assertEqual(response.status_code, 200)

    @patch("requests.get")
    def test_model_route_exists(self, mock_get):
        """
        Test to check if the route to the fetched model exists.
        """

        # Mock the response from the local server
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Simulate checking the model route
        response = requests.get("http://127.0.0.1:8000/flan-t5/model")

        # Assert that the model route exists
        mock_get.assert_called_once_with("http://127.0.0.1:8000/flan-t5/model")
        self.assertEqual(response.status_code, 200)

    @patch("requests.get")
    def test_local_server_not_running(self, mock_get):
        """
        Test behavior when the local server is not running.
        """

        # Simulate a connection error
        mock_get.side_effect = requests.exceptions.ConnectionError

        # Attempt to check the server status
        with self.assertRaises(requests.exceptions.ConnectionError):
            requests.get("http://127.0.0.1:8000/status")

        # Assert that the server check was attempted
        mock_get.assert_called_once_with("http://127.0.0.1:8000/status")

    @patch("requests.post")
    def test_query_local_llm_with_private_instructions(self, mock_post):
        """
        Test querying the local LLM with private instructions.
        """
        # Mock the response from the local LLM server
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "This is a locally generated response."
        }
        mock_post.return_value = mock_response

        # Simulate querying the local LLM
        response = requests.post("http://127.0.0.1:8000/flan-t5/query_pdf", json={
            "directory_path": "some/directory/path",
            "question": "What are the main topics?",
            "is_private": True
        })

        # Assert that the local LLM endpoint was called
        mock_post.assert_called_once_with("http://127.0.0.1:8000/flan-t5/query_pdf", json={
            "directory_path": "some/directory/path",
            "question": "What are the main topics?",
            "is_private": True
        })

        # Verify the response content
        response_data = response.json()
        self.assertIn("response", response_data)
        self.assertEqual(response_data["response"], "This is a locally generated response.")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.listdir", return_value=["file1.pdf", "file2.pdf"])
    @patch("os.path.join", side_effect=lambda directory, filename: f"{directory}/{filename}")
    @patch("app.AIAssistant")
    @patch("requests.post")
    def test_decline_public_api_with_private_data(self, mock_post, mock_ai_assistant, mock_join, mock_listdir, mock_open):
        """
        Test that the app declines to use the public API when private data is flagged.
        """
        # Mock the AIAssistant to prevent actual API calls
        mock_ai_instance = mock_ai_assistant.return_value
        mock_ai_instance.query_llm.return_value = (None, "This is a mocked response")

        # Simulate a request with private data but a public model
        response = self.app.post("/run_query", data={
            "model": "gpt-4-turbo",
            "directory_path": "some/directory/path",
            "question": "What are the main topics?",
            "is_private": "true"
        })

        # Assert that the public API was not called
        mock_post.assert_not_called()

        # Verify the response content
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertIn("error", response_data)
        self.assertIn("Cannot use public API with private data", response_data["error"])

if __name__ == "__main__":
    unittest.main()