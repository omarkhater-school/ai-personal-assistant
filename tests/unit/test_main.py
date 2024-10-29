# tests/test_main.py
import unittest
from unittest.mock import patch, MagicMock
from main import run_pdf_feature

class TestMainPDFFeature(unittest.TestCase):
    @patch("main.PDFModule")
    @patch("main.AIAssistant")
    def test_pdf_feature_in_main(self, MockAIAssistant, MockPDFModule):
        # Create mock instances
        mock_assistant_instance = MockAIAssistant.return_value
        mock_assistant_instance.get_assistant_id.return_value = "mock_assistant_id"  # Return a mock assistant ID

        mock_pdf_module_instance = MockPDFModule.return_value

        # Mock the responses for upload and query functions
        mock_file_batch = MagicMock(status="completed")
        mock_pdf_module_instance.upload_directory_to_vector_store.return_value = mock_file_batch

        mock_query_run = MagicMock()
        mock_query_run.status = "success"
        mock_pdf_module_instance.query_pdf.return_value = mock_query_run

        # Run the function after setting up mocks
        run_pdf_feature()

        # Verify PDF upload was called
        mock_pdf_module_instance.upload_directory_to_vector_store.assert_called_once_with("path/to/your/pdf/directory")
        
        # Verify PDF query was called with the expected parameters
        mock_pdf_module_instance.query_pdf.assert_called_once_with(
            "What are the main findings in this report?", "path/to/your/pdf/question_file.pdf"
        )

        # Check output or status for verification
        self.assertEqual(mock_file_batch.status, "completed")
        self.assertEqual(mock_query_run.status, "success")
