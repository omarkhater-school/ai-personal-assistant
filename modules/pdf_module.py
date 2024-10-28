# modules/pdf_module.py
import os

class PDFModule:
    def __init__(self, ai_assistant):
        self.ai_assistant = ai_assistant
        self.client = ai_assistant.client

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

    def query_pdf(self, question, file_path=None):
        assistant_id = self.ai_assistant.get_assistant_id()
        
        # Prepare the message
        message = {
            "role": "user",
            "content": question,
            "attachments": []
        }

        # Attach file if provided
        if file_path:
            message_file = self.client.files.create(
                file=open(file_path, "rb"), purpose="assistants"
            )
            file_id = message_file.id
            message["attachments"].append({"file_id": file_id, "tools": [{"type": "file_search"}]})

        # Create a thread with or without the file attachment
        thread = self.client.beta.threads.create(messages=[message])

        # Create and poll the run
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )
        return run
