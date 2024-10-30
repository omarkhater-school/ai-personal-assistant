# tests/unit/test_pdf_module.py
import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules.pdf_module import PDFModule


class TestPDFModule(unittest.TestCase):
    def setUp(self):
        self.mock_ai_assistant = MagicMock()
        self.mock_ai_assistant.client = MagicMock()
        self.mock_ai_assistant.get_assistant_id.return_value = "assistant_id"
        self.pdf_module = PDFModule(self.mock_ai_assistant)
    
    @patch("modules.pdf_module.open", new_callable=mock_open)
    @patch("modules.pdf_module.os.listdir", return_value=["file1.pdf", "file2.pdf"])
    def test_upload_directory_to_vector_store(self, mock_listdir, mock_open):
        # Set up the mock file batch with a completed status
        mock_file_batch = MagicMock()
        mock_file_batch.status = "completed"

        # Set up the chain of mocks
        self.pdf_module.client.beta = MagicMock()
        self.pdf_module.client.beta.vector_stores = MagicMock()
        self.pdf_module.client.beta.vector_stores.file_batches = MagicMock()
        self.pdf_module.client.beta.vector_stores.file_batches.upload_and_poll.return_value = mock_file_batch

        # Run the function
        result = self.pdf_module.upload_directory_to_vector_store("dummy_directory")

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "completed")
        mock_listdir.assert_called_once_with("dummy_directory")
        mock_open.assert_any_call("dummy_directory\\file1.pdf", "rb")
        mock_open.assert_any_call("dummy_directory\\file2.pdf", "rb")
    
    @patch.object(PDFModule, 'query')
    def test_query_with_file(self, mock_query):
        # Configure mock to return simulated API response
        mock_run = MagicMock(status="completed")
        mock_message_content = MagicMock()
        mock_message_content.value = "This is the answer."
        mock_query.return_value = (mock_run, mock_message_content)
        
        # Run the query
        run, message_content = self.pdf_module.query("What is the revenue?", "file_path.pdf")

        # Assertions to verify the mock behavior
        self.assertEqual(run.status, "completed")
        self.assertEqual(message_content.value, "This is the answer.")

    @patch.object(PDFModule, 'query')
    def test_query_without_file(self, mock_query):
        # Configure mock to simulate a response with no content
        mock_run = MagicMock(status="completed")
        mock_message_content = MagicMock()
        mock_message_content.value = "No content available in response."
        mock_query.return_value = (mock_run, mock_message_content)

        # Run the query without a file
        run, message_content = self.pdf_module.query("What is the revenue?")

        # Assertions
        self.assertEqual(run.status, "completed")
        self.assertEqual(message_content.value, "No content available in response.")

    @patch("modules.pdf_module.os.listdir", return_value=[])
    def test_upload_directory_to_vector_store_no_files(self, mock_listdir):
        # Run the function with an empty directory
        result = self.pdf_module.upload_directory_to_vector_store("empty_directory")

        # Assertions
        self.assertIsNone(result, "Expected None when no files are found in the directory.")
        mock_listdir.assert_called_once_with("empty_directory")

if __name__ == "__main__":
    unittest.main()
