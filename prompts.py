# prompts.py

def intent_analysis_prompt(message):
    """
    Structured prompt for analyzing user intent, enforcing strict JSON-only output.
    """
    return f"""
You are an assistant that classifies user messages into intents.
Analyze the following user message and classify it into one of the following intents:

1. "Clarification Needed": The user's message is incomplete or lacks necessary details. The assistant needs to ask for more information to proceed. Use this intent when critical details are missing, or clarification is required.
   Examples:
   - "Write an email" ---> "To whom should I send the email, and what should it say?"
   - "Schedule a meeting" ---> "What time and date should I schedule the meeting for?"
   - "Analyze pdfs in the folder" ---> "Which folder specifically?"

2. "Action Required (Confirm)": Tasks that need the assistant to prepare something (e.g., drafting an email) but require explicit confirmation before finalizing.
   Examples:
   - "Draft an email to Alex about tomorrow’s meeting" ---> "Draft the email but wait for confirmation to send it."
   - "Schedule a meeting with John for Thursday at 3 PM" ---> "Prepare the meeting invite, but confirm before sending."

3. "Action Required (Proceed)": Tasks where all information is provided, and the assistant can proceed directly without further confirmation (e.g., analyzing PDF content).
   Examples:
   - "Analyze the pdf content at this directory D:\\projects\\papers and be ready for answering questions" ---> "Analyze the PDFs and prepare for questions."
   - "Search the internet for the latest AI research publications" ---> "Perform the search and retrieve results."

4. "General Inquiry": The user is asking a question or seeking information that doesn't require any action, or requires providing general advice or instructions.
   Examples:
   - "How do I send an email with this assistant?" ---> "Provide instructions for sending an email."
   - "What is AI?" ---> "Explain the basics of artificial intelligence."

Additionally, specify if the message contains "Private Data" or "Public Data". Consider any personal, sensitive, or confidential information as "Private Data".

**IMPORTANT:** Only respond with a JSON object in the following format and no additional explanations or comments:
{{
    "intent": "One of the intents above",
    "privacy": "Private Data" or "Public Data"
}}
Message: "{message}"
"""

def pdf_query_prompt(question, file_names):
    """
    Generates a prompt for querying the nature or content of PDF files
    based on pre-generated embeddings and includes file names for context.
    """
    file_list = "\n".join(f"- {name}" for name in file_names)
    
    return (
        "The following file names represent the documents analyzed:\n"
        f"{file_list}\n\n"
        "These file names may provide context about the types of documents (e.g., 'report', 'summary', 'presentation'). "
        "You also have access to embeddings generated from these files, representing the core content characteristics. "
        "Analyze these embeddings to answer the user's question with details about document types, structures, and any notable content elements.\n\n"
        "User's question:\n"
        f"{question}\n\n"
        "In your response, focus on identifying document types (e.g., academic papers, reports) and content structures (e.g., text-heavy, with images, diagrams, or tables). "
        "Use specific examples where relevant, and consider any clues from the file names provided."
    )

def assistant_query_prompt(user_message):
    """
    Constructs a prompt to guide the assistant in responding naturally to the user's message after intent analysis.
    """
    return (
        "You are a helpful assistant interacting with a user. Here is the user's message:\n\n"
        f"Message: '{user_message}'\n\n"
        "Respond directly to the user's query in a natural and concise manner. "
        "If the query involves specific instructions (like analyzing documents or answering questions based on processed data), "
        "focus on fulfilling the request using any available context or pre-existing information. "
        "Be clear and direct in your response, aiming to provide the most relevant information or action."
    )