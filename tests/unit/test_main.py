# tests/unit/test_main.py
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
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

        # Mock a Text-like object with a `value` attribute to simulate the real API
        mock_query_run = MagicMock(status="success")
        mock_message_content = MagicMock()
        mock_message_content.value = "This is the answer."

        # Ensure `query_pdf` returns both the mock run and the mock message_content
        mock_pdf_module_instance.query_pdf.return_value = (mock_query_run, mock_message_content)

        # Run the function after setting up mocks
        run_pdf_feature()

        # Verify PDF upload was called with the expected directory path
        mock_pdf_module_instance.upload_directory_to_vector_store.assert_called_once_with("D:\\projects\\papers")
        
        # Verify PDF query was called with the expected question
        mock_pdf_module_instance.query_pdf.assert_called_once_with("What are the tree of thoughts")

        # Check output or status for verification
        self.assertEqual(mock_file_batch.status, "completed")
        self.assertEqual(mock_query_run.status, "success")
        self.assertEqual(mock_message_content.value, "This is the answer.")


if __name__ == "__main__":
    unittest.main()
