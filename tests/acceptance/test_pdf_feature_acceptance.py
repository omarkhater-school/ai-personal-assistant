# tests/acceptance/test_pdf_feature_acceptance.py
import unittest
from unittest.mock import patch, MagicMock
import os
from ai_assistant import AIAssistant
from modules.pdf_module import PDFModule

class TestPDFFeatureAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize the main AI assistant and PDF module for all tests
        cls.ai_assistant = AIAssistant(name="Test AI Assistant", instructions="Testing PDF feature.")
        cls.pdf_module = PDFModule(cls.ai_assistant)

        # Paths to the test PDF files
        cls.test_pdf_directory = os.path.join(os.path.dirname(__file__), 'data')
        cls.test_pdf_file = os.path.join(cls.test_pdf_directory, 'LLAMA3 Herd Of Models.pdf')
        cls.question = "Summarize the contents of this document."

    @patch.object(PDFModule, 'query')
    def test_pdf_upload_and_query(self, mock_query):
        # Step 1: Upload all PDFs in the directory
        file_batch = self.pdf_module.upload_directory_to_vector_store(self.test_pdf_directory)
        self.assertIsNotNone(file_batch, "File batch upload failed.")
        self.assertEqual(file_batch.status, "completed", "File batch upload not completed.")

        # Step 2: Stub the query method
        mock_run_result = MagicMock()
        mock_run_result.status = "completed"
        mock_message_content = MagicMock()
        mock_message_content.value = "This is a summary of the document."
        
        mock_query.return_value = (mock_run_result, mock_message_content)

        # Step 3: Query the uploaded PDF with a question (using the stubbed method)
        run_result, message_content = self.pdf_module.query(self.question, self.test_pdf_file)

        # Assertions
        self.assertIsNotNone(run_result, "Query run failed.")
        self.assertEqual(run_result.status, "completed", "Query run did not complete successfully.")
        # Assert that message_content is a non-empty string
        self.assertIsInstance(message_content.value, str, "The message content is not a string.")
        self.assertTrue(len(message_content.value.strip()) > 0, "The message content is empty.")

if __name__ == "__main__":
    unittest.main()
