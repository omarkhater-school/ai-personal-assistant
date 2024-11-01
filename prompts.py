# prompts.py

def intent_analysis_prompt(message):
    """
    Structured prompt for analyzing user intent, enforcing strict JSON-only output.
    """
    return f"""
You are an assistant that classifies user messages into intents.
Analyze the following user message and classify it into one of the following intents:

1. "Clarification Needed": The user's message is incomplete or lacks necessary details. The assistant needs to ask for more information to proceed. Examples include requests where specific information is missing.
   Examples:
   - "Analyze pdf directory"
   - "Schedule a meeting"
   - "Set a reminder"
   - "Book a flight"
   - "Order food"

2. "Action Required": The user's message contains all the necessary information to perform an action without needing further clarification.
   Examples:
   - "Send an email to John about the meeting tomorrow at 10 AM"
   - "Set a reminder to call the doctor at 3 PM today"
   - "Book a flight to New York on December 5th at 5 PM from JFK Airport"
   - "Order a pepperoni pizza from Pizza Place to be delivered to 123 Main St"

3. "General Inquiry": The user is asking a question or seeking information that doesn't require any action.
   Examples:
   - "What's the weather like today?"
   - "Tell me about the history of the Eiffel Tower"
   - "How do I reset my password?"
   - "What is the capital of France?"

Additionally, specify if the message contains "Private Data" or "Public Data". Consider any personal, sensitive, or confidential information as "Private Data".

**IMPORTANT:** Only respond with a JSON object in the following format and no additional explanations or comments:
{{
    "intent": "One of the intents above",
    "privacy": "Private Data" or "Public Data"
}}
Message: "{message}"
"""
