# prompts.py

def intent_analysis_prompt(message):
    """
    Structured prompt for analyzing user intent, enforcing strict JSON-only output with examples.
    """
    return f"""
You are an assistant that classifies user messages into intents and extracts relevant information.

Analyze the following user message and classify it into one of the following intents:

1. "Clarification Needed": The user's message is incomplete or lacks necessary details. The assistant needs to ask for more information to proceed.
   - **Use this intent if any required information is missing or unclear.**

2. "Action Required (Confirm)": Tasks that need the assistant to prepare something (e.g., drafting an email or processing PDFs) but require explicit confirmation before finalizing.
   - **Use this intent only if all required information is provided but confirmation is beneficial.**

3. "Action Required (Proceed)": Tasks where all information is provided, and the assistant can proceed directly without further confirmation.

4. "General Inquiry": The user is asking a question or seeking information that doesn't require any action.

Additionally, specify if the message contains "Private Data" or "Public Data".

If the intent involves any action, extract:
- "action": The action the user wants to perform (e.g., "send_email", "read_pdfs").
- **For "send_email", required fields are:**
  - "recipient_name": The name or email of the recipient. If the recipient is a name, set "requires_contact_lookup" to true; if it’s an email address, set it to false.
  - "subject": The subject of the email (if mentioned).
  - "tone": The tone conveyed in the user's message (e.g., formal, informal, urgent, friendly, concerned).

- **For "read_pdfs", required fields are:**
  - "directory_path": The directory where PDF files are located.
  - "query": Any specific request the user has regarding the PDF content (e.g., "summarize all files", "extract key points", "list document titles").
    - If the user requests a summary of all files, use "summarize" as the query.
  - If no specific query is given, assume the user will ask questions about the content after processing.

**Examples:**
- **Send Email Examples:**
  - Message: "Send an email to John about the meeting tomorrow."
    - Response: {{
        "intent": "Action Required (Confirm)",
        "privacy": "Private Data",
        "action": "send_email",
        "recipient_name": "John",
        "subject": "Meeting tomorrow",
        "tone": "informal",
        "requires_contact_lookup": true
    }}

  - Message: "Send an email to john@example.com with the project update."
    - Response: {{
        "intent": "Action Required (Confirm)",
        "privacy": "Private Data",
        "action": "send_email",
        "recipient_name": "john@example.com",
        "subject": "Project update",
        "tone": "neutral",
        "requires_contact_lookup": false
    }}

- **Read PDFs Examples:**
  - Message: "Reads PDFs"
    - Response: {{
        "intent": "Clarification Needed",
        "privacy": "Public Data",
        "action": "read_pdfs",
        "directory_path": null,
        "query": null
    }}

  - Message: "Read PDFs at this directory D:\\projects\\papers"
    - Response: {{
        "intent": "Action Required (Proceed)",
        "privacy": "Public Data",
        "action": "read_pdfs",
        "directory_path": "D:\\projects\\papers",
        "query": "What did you find in this directory?"
    }}

  - Message: "Read PDFs at this directory D:\\projects\\papers and summarize all of them."
    - Response: {{
        "intent": "Action Required (Proceed)",
        "privacy": "Public Data",
        "action": "read_pdfs",
        "directory_path": "D:\\projects\\papers",
        "query": "summarize all files"
    }}

**IMPORTANT INSTRUCTIONS:**
- **If any required field is missing or empty, set "intent" to "Clarification Needed".**
- **Do not proceed with the action if required information is missing.**
- Only respond with a JSON object in the following format and no additional explanations or comments:
{{
    "intent": "One of the intents above",
    "privacy": "Private Data" or "Public Data",
    "action": "Action to perform" (if applicable),
    "recipient_name": "Recipient's Name or Email" (if applicable),
    "subject": "Email Subject" (if applicable),
    "tone": "Tone of the email" (if applicable),
    "requires_contact_lookup": true or false (if applicable),
    "directory_path": "Directory path for PDFs" (if applicable),
    "query": "User's specific request about the PDFs, if any" (if applicable)
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
    Generates a prompt that introduces the assistant's capabilities to the model,
    allowing it to respond more intelligently based on the available features.
    """
    return (
        "You are IntelliChat, an advanced assistant capable of performing various tasks such as:\n"
        "- Reading and analyzing PDF documents\n"
        "- Sending and drafting emails on behalf of the user\n"
        "- Scheduling meetings\n"
        "- Searching the internet for information\n\n"
        "When responding to the user's message, take into account these capabilities and, if applicable, "
        "offer to use one of these features to fulfill their request. Always clarify if more information "
        "is needed to proceed with any of these actions.\n\n"
        f"User's message:\n{user_message}"
    )

def email_drafting_prompt(recipient_name, subject, user_message):
    """
    Generates a prompt to draft an email to the recipient, capturing the tone from the user's message.
    """
    return f"""
You are an assistant that drafts emails on behalf of the user.

Instructions:
- Address the email to {recipient_name}.
- Use the subject line: "{subject}".
- The body of the email should cover the points and context provided in the user's message below.
- Capture the tone from the user's message (e.g., formal, informal, urgent, friendly, concerned) and reflect it appropriately in the email.
- Write the email in the first person singular (e.g., "I am writing to inform you...").
- Ensure the email is clear, polite, and appropriate for the context.

User's message:
"{user_message}"

Draft the email below:
    """


def clarification_prompt(action, missing_info):
    """
    Generates a prompt to clarify missing information based on the action and missing details.
    """
    action_description = {
        "send_email": "sending an email",
        "read_pdfs": "reading and analyzing PDF files in a specified directory",
        "schedule_meeting": "scheduling a meeting",
        "internet_search": "performing an internet search"
    }

    action_text = action_description.get(action, "performing the required task")
    missing_details = ', '.join(missing_info)

    return f"""
You are assisting with {action_text}. Based on the conversation so far, there are some missing details:
- Required details: {missing_details}

Review the chat history and generate a clarification request asking the user to provide the necessary details for completing this action.
Use a polite tone and provide clear instructions to ensure the user knows what information is needed.
"""