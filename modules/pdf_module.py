# modules/pdf_module.py
import os
from abc import ABC, abstractmethod

class BaseModule(ABC):
    def __init__(self, ai_assistant):
        self.ai_assistant = ai_assistant
        self.client = ai_assistant.client

    @abstractmethod
    def upload_directory_to_vector_store(self, directory_path):
        pass

    @abstractmethod
    def query(self, question, file_path=None):
        pass

class PDFModule(BaseModule):
    def upload_directory_to_vector_store(self, directory_path):
        vector_store_id = self.ai_assistant.get_vector_store_id()
        file_paths = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.endswith('.pdf')]
        
        if not file_paths:
            print("No PDF files found in the directory.")
            return None

        file_streams = [open(path, "rb") for path in file_paths]
        
        file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id, files=file_streams
        )

        for file in file_streams:
            file.close()

        return file_batch

    def query(self, question, file_path=None):
        return self.ai_assistant.query_llm(question, file_path)


