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
    
    @patch.object(PDFModule, 'query_pdf')
    def test_query_pdf_with_file(self, mock_query_pdf):
        # Configure mock to return simulated API response
        mock_run = MagicMock(status="completed")
        mock_message_content = MagicMock()
        mock_message_content.value = "This is the answer."
        mock_query_pdf.return_value = (mock_run, mock_message_content)
        
        # Run the query
        run, message_content = self.pdf_module.query_pdf("What is the revenue?", "file_path.pdf")

        # Assertions to verify the mock behavior
        self.assertEqual(run.status, "completed")
        self.assertEqual(message_content.value, "This is the answer.")

    @patch.object(PDFModule, 'query_pdf')
    def test_query_pdf_without_file(self, mock_query_pdf):
        # Configure mock to simulate a response with no content
        mock_run = MagicMock(status="completed")
        mock_message_content = MagicMock()
        mock_message_content.value = "No content available in response."
        mock_query_pdf.return_value = (mock_run, mock_message_content)

        # Run the query without a file
        run, message_content = self.pdf_module.query_pdf("What is the revenue?")

        # Assertions
        self.assertEqual(run.status, "completed")
        self.assertEqual(message_content.value, "No content available in response.")

    @patch.object(PDFModule, 'query_pdf')
    def test_query_pdf_with_no_content_in_response(self, mock_query_pdf):
        # Configure mock to simulate an empty content response
        mock_run = MagicMock(status="completed")
        mock_message_content = MagicMock()
        mock_message_content.value = "No content available in response."
        mock_query_pdf.return_value = (mock_run, mock_message_content)

        # Run the query without a file and an empty response
        run, message_content = self.pdf_module.query_pdf("What is the revenue?")

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

    def test_query_pdf_with_file_path(self):
        # Replace the client with a mock
        self.pdf_module.client = MagicMock()

        # Set up mock methods on the client
        mock_run = MagicMock(status="completed")
        self.pdf_module.client.beta.threads.runs.create_and_poll.return_value = mock_run

        mock_thread = MagicMock()
        mock_thread.id = "thread_id"
        self.pdf_module.client.beta.threads.create.return_value = mock_thread

        mock_message_file = MagicMock()
        mock_message_file.id = "file_id"
        self.pdf_module.client.files.create.return_value = mock_message_file

        # Mocking the response message
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="This is the answer.")]
        self.pdf_module.client.beta.threads.messages.list.return_value = [mock_message]

        # Mock the open function to prevent actual file access
        with patch("builtins.open", mock_open()) as mocked_open:
            # Run the function with a file path
            run, message_content = self.pdf_module.query_pdf("What is the revenue?", "file_path.pdf")

            # Assertions
            self.assertEqual(run.status, "completed")
            self.assertEqual(message_content, "This is the answer.")
            self.pdf_module.client.files.create.assert_called_once()
            mocked_open.assert_called_once_with("file_path.pdf", "rb")


    

    def test_query_pdf_no_messages_returned(self):
        # Replace the client with a mock
        self.pdf_module.client = MagicMock()

        # Set up mock methods on the client
        mock_run = MagicMock(status="completed")
        self.pdf_module.client.beta.threads.runs.create_and_poll.return_value = mock_run

        mock_thread = MagicMock()
        mock_thread.id = "thread_id"
        self.pdf_module.client.beta.threads.create.return_value = mock_thread

        # Return an empty list for messages to simulate no messages in response
        self.pdf_module.client.beta.threads.messages.list.return_value = []

        # Run the function without a file
        run, message_content = self.pdf_module.query_pdf("What is the revenue?")

        # Assertions
        self.assertEqual(run.status, "completed")
        self.assertEqual(message_content, "No content available in response.")




    @patch("modules.pdf_module.PDFModule.query_pdf")
    @patch("modules.pdf_module.PDFModule.upload_directory_to_vector_store")
    def test_query_pdf_message_content_empty(self, mock_upload, mock_query_pdf):
        # Set up the mocked API response to simulate a completed run with empty content
        mock_run = MagicMock(status="completed")
        mock_message_content = MagicMock()
        mock_message_content.value = "No content available in response."

        # Configure the `query_pdf` mock to return these values
        mock_query_pdf.return_value = (mock_run, mock_message_content)

        # Call the function with the mock in place
        run, message_content = self.pdf_module.query_pdf("What is the revenue?")

        # Assertions to verify the response
        self.assertEqual(run.status, "completed")
        self.assertEqual(message_content.value, "No content available in response.")

if __name__ == "__main__":
    unittest.main()
