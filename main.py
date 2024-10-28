# main.py
from ai_assistant import AIAssistant
from modules.pdf_module import PDFModule

# Initialize main AI Assistant
ai_assistant = AIAssistant()

# Initialize PDF module with the shared assistant instance
pdf_module = PDFModule(ai_assistant)

# Step 1: Upload all PDFs in a directory
directory_path = "D:\\projects\\papers"
file_batch = pdf_module.upload_directory_to_vector_store(directory_path)
if file_batch:
    print("File Batch Status:", file_batch.status)

# # With a file
# result_with_file = pdf_module.query_pdf("What is the revenue for Q4?", "path/to/your/file.pdf")

# Without a file
result_without_file = pdf_module.query_pdf("Can you summarize the tree of thoughts paper?")

print(result_without_file)