# Overview
The ai_assistant.py and app.py files create a Flask-based personal assistant application that leverages language models and various APIs to perform complex tasks such as reading PDFs, conducting internet searches, sending emails, and scheduling meetings. The assistant interacts with users through a web interface and processes requests with an underlying language model.

The assistant supports four main tools, each with its own function and parameters. These tools can be invoked based on the user’s input, allowing the assistant to offer versatile, task-specific responses.
## PDF Analyzer
The function read_pdfs extracts text and generates embeddings. The user query is parsed to give information about the analyzed content. Please note that basic embeddings analyzing is coded as a proof of concept.
## Internet Research
The app can executes internet search using Tavily API. The function internet_search encapsulates the logic needed to do the search.
## Email Drafting and Sending
The function send_email is trying to look up the recipient by name in a contacts file or using a direct email address.
## Schedule Meetings
The function schedule_meeting schedule meeting through Zoho Calendar, creating events and adding participant.


# Privacy Handling
To ensure privacy, only local LLM is used which is Ollama. The Python API library is used to interact with models all while ensuring that no sensitive data is sent over the internet.

# Clarification Handling
The chat API from python Ollama is used to ensure that the assistant can keep conversation style with the user.

# Setup Instructions
Note: The application & setup instruction has been tested with Python 3.10 and PowerShell on Windows 11.

1. [Optional] Create & Activate Python Virtual Environment by running the following in the terminal.
```sh
python -m venv test_env
.\test_env\Scripts\activate
```

2. Install requirements.txt
```sh
pip-compile requirements.in && pip-sync requirements.txt
```
3. Run the Flask application by using the following command
```sh
python app.py

```

4. Create the custom assistant from the model file
```sh
ollama create mymodel -f ./Modelfile1.
```

5. Open the local server on any browser

```
http://127.0.0.1:5000/
```

Have fun with IntelliChat!
