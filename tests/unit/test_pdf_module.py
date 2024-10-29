# tests/test_pdf_module.py
import unittest
from unittest.mock import patch, MagicMock
from ai_assistant import AIAssistant
from modules.pdf_module import PDFModule

class TestPDFModule(unittest.TestCase):
    @patch("modules.pdf_module.open")
    @patch("modules.pdf_module.os")
    @patch("modules.pdf_module.openai.Client")
    def test_upload_directory_to_vector_store(self, MockClient, MockOS, MockOpen):
        # Mock directory listing to return a list of PDF files
        MockOS.listdir.return_value = ["file1.pdf", "file2.pdf"]
        MockOS.path.join.side_effect = lambda dir, f: f"{dir}/{f}"

        # Mock the open file streams
        mock_file_stream = MagicMock()
        MockOpen.return_value = mock_file_stream

        # Mock client instance and file upload method
        mock_client_instance = MockClient.return_value
        mock_client_instance.beta.vector_stores.file_batches.upload_and_poll.return_value = MagicMock(status="completed")

        # Initialize AIAssistant and PDFModule
        ai_assistant = AIAssistant()
        pdf_module = PDFModule(ai_assistant)

        # Run upload_directory_to_vector_store
        result = pdf_module.upload_directory_to_vector_store("test_dir")

        # Assertions
        MockOS.listdir.assert_called_once_with("test_dir")
        self.assertEqual(result.status, "completed")

    @patch("modules.pdf_module.open")
    @patch("modules.pdf_module.openai.Client")
    def test_query_pdf_with_file(self, MockClient, MockOpen):
        # Mock file open and client
        mock_client_instance = MockClient.return_value
        mock_file_stream = MagicMock()
        MockOpen.return_value = mock_file_stream

        # Initialize AIAssistant and PDFModule
        ai_assistant = AIAssistant()
        pdf_module = PDFModule(ai_assistant)

        # Mock thread and run creation
        mock_thread = MagicMock()
        mock_run = MagicMock()
        mock_client_instance.beta.threads.create.return_value = mock_thread
        mock_client_instance.beta.threads.runs.create_and_poll.return_value = mock_run

        # Run query_pdf with a file path
        result = pdf_module.query_pdf("What is the revenue?", "file_path.pdf")

        # Assertions
        mock_client_instance.beta.threads.create.assert_called_once()
        mock_client_instance.beta.threads.runs.create_and_poll.assert_called_once()
        self.assertEqual(result, mock_run)

    @patch("modules.pdf_module.openai.Client")
    def test_query_pdf_without_file(self, MockClient):
        # Mock client instance
        mock_client_instance = MockClient.return_value

        # Initialize AIAssistant and PDFModule
        ai_assistant = AIAssistant()
        pdf_module = PDFModule(ai_assistant)

        # Mock thread and run creation
        mock_thread = MagicMock()
        mock_run = MagicMock()
        mock_client_instance.beta.threads.create.return_value = mock_thread
        mock_client_instance.beta.threads.runs.create_and_poll.return_value = mock_run

        # Run query_pdf without a file path
        result = pdf_module.query_pdf("What is the revenue?")

        # Assertions
        mock_client_instance.beta.threads.create.assert_called_once()
        mock_client_instance.beta.threads.runs.create_and_poll.assert_called_once()
        self.assertEqual(result, mock_run)
