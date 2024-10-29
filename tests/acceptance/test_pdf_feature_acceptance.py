# tests/acceptance/test_pdf_feature_acceptance.py
import unittest
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

    def test_pdf_upload_and_query(self):
        # Step 1: Upload all PDFs in the directory
        file_batch = self.pdf_module.upload_directory_to_vector_store(self.test_pdf_directory)
        self.assertIsNotNone(file_batch, "File batch upload failed.")
        self.assertEqual(file_batch.status, "completed", "File batch upload not completed.")

        # Step 2: Query the uploaded PDF with a question
        run_result = self.pdf_module.query_pdf(self.question, self.test_pdf_file)
        self.assertIsNotNone(run_result, "Query run failed.")
        
        # Accept either "completed" or "success" as a successful result
        self.assertIn(run_result.status, ["completed", "success"], "Query run did not complete successfully.")

if __name__ == "__main__":
    unittest.main()
