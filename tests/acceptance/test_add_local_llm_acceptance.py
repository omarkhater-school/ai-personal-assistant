# tests/acceptance/test_add_local_llm_acceptance.py
import unittest
from unittest.mock import patch, MagicMock
import os
import requests
from ai_assistant import AIAssistant

class TestAddLocalLLMAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_pdf_directory = os.path.join(os.path.dirname(__file__), 'data')
        cls.test_pdf_file_1 = os.path.join(cls.test_pdf_directory, 'File1.pdf')
        cls.test_pdf_file_2 = os.path.join(cls.test_pdf_directory, 'File2.pdf')
        cls.question = "What are the main topics covered in these documents?"

    @patch("requests.post")
    def test_private_pdf_query_uses_local_llm(self, mock_post):
        """
        GIVEN a user selects 'Private PDF' and adds a directory with PDFs
        WHEN the user submits a query
        THEN the system should use the local LLM (Flan-T5) and not OpenAI API
        """

        # Mock response from the local LLM server
        mock_local_response = MagicMock()
        mock_local_response.json.return_value = {
            "response": "This is a locally generated response."
        }
        mock_post.return_value = mock_local_response

        # Run the query as private
        is_private = True
        response = requests.post("http://127.0.0.1:8000/flan-t5/query_pdf", json={
            "directory_path": self.test_pdf_directory,
            "question": self.question,
            "is_private": is_private
        })

        # Assert that the local LLM endpoint was called
        mock_post.assert_called_once_with("http://127.0.0.1:8000/flan-t5/query_pdf", json={
            "directory_path": self.test_pdf_directory,
            "question": self.question,
            "is_private": is_private
        })

        # Verify the response content
        response_data = response.json()
        self.assertIn("response", response_data)
        self.assertEqual(response_data["response"], "This is a locally generated response.")

    @patch("requests.post")
    def test_model_selection_for_local_vs_openai(self, mock_post):
        """
        GIVEN a list of models including a local and an OpenAI option
        WHEN the user selects a model and submits a query
        THEN the system should use the appropriate model's endpoint
        """

        # Scenario: User selects 'flan-t5' (local model)
        is_private = True
        mock_local_response = MagicMock()
        mock_local_response.json.return_value = {
            "response": "This is a locally generated response."
        }
        mock_post.return_value = mock_local_response

        local_response = requests.post("http://127.0.0.1:8000/flan-t5/query_pdf", json={
            "directory_path": self.test_pdf_directory,
            "question": self.question,
            "is_private": is_private
        })
        
        # Verify local model was used for private query
        mock_post.assert_called_once_with("http://127.0.0.1:8000/flan-t5/query_pdf", json={
            "directory_path": self.test_pdf_directory,
            "question": self.question,
            "is_private": is_private
        })
        
        # Scenario: User selects 'gpt-4-turbo' (OpenAI model)
        with patch.object(AIAssistant, 'query_llm', return_value=("completed", "This is an OpenAI response")) as mock_openai_query:
            ai_assistant = AIAssistant(name="My AI Assistant", model="gpt-4-turbo")
            run, openai_response = ai_assistant.query_llm(question=self.question)
            
            # Assert the OpenAI API was used
            mock_openai_query.assert_called_once_with(question=self.question)
            self.assertEqual(openai_response, "This is an OpenAI response")

    @patch("requests.post")
    def test_display_query_results_with_file_info(self, mock_post):
        """
        GIVEN a directory of PDF files
        WHEN the user submits a query
        THEN the system should return the names of the PDF files and response content
        """

        # Mock the local server response to include PDF names
        mock_local_response = MagicMock()
        mock_local_response.json.return_value = {
            "response": "This is a summary of File1.pdf and File2.pdf",
            "files": ["File1.pdf", "File2.pdf"]
        }
        mock_post.return_value = mock_local_response

        response = requests.post("http://127.0.0.1:8000/flan-t5/query_pdf", json={
            "directory_path": self.test_pdf_directory,
            "question": self.question,
            "is_private": True,
        })

        # Assert the response includes file names and content
        response_data = response.json()
        self.assertIn("response", response_data)
        self.assertIn("files", response_data)
        self.assertEqual(response_data["files"], ["File1.pdf", "File2.pdf"])
        self.assertEqual(response_data["response"], "This is a summary of File1.pdf and File2.pdf")

if __name__ == "__main__":
    unittest.main()
