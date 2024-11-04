import json
import os
import traceback
from config_loader import get_app_custom
from logger import setup_logger
import ollama
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config_loader import get_email_config, get_search_api_key
from tavily import TavilyClient
import PyPDF2

def query_llm(prompt):
        """
        Sends a prompt to the language model and returns the response.
        """
        response = ollama.chat(
            model="IntelliChat",
            messages=[{"role": "user", "content": prompt}]
        )
        return response

def send_email(recipient_name, subject, body):
    """
    Sends an email with the specified recipient, subject, and body.
    Looks up the recipient's email in contacts if only a name is provided.
    """
    logger = setup_logger("EmailModuleLogger", "logs/email_module.log")
    # Load email configuration
    email_config = get_email_config()
    smtp_server = email_config.get('smtp_server')
    smtp_port = email_config.get('smtp_port')
    username = email_config.get('username')
    password = email_config.get('password')
    from_addr = email_config.get('default_from_address')

    # Load contacts
    contacts_file = 'contacts.json'
    contacts = {}
    if os.path.exists(contacts_file):
        with open(contacts_file, 'r') as f:
            contacts = json.load(f)
    else:
        logger.warning("Contacts file not found.")

    # Find the recipient's email address
    to_addr = contacts.get(recipient_name) if not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_name) else recipient_name
    if not to_addr:
        logger.error("Recipient email not found.")
        return "Recipient email not found."

    # Compose the email
    message = MIMEMultipart()
    message["From"] = from_addr
    message["To"] = to_addr
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_addr, to_addr, message.as_string())
        logger.info("Email sent successfully.")
        return "Email sent successfully."
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error occurred: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        logger.error(error_msg)
        return error_msg

def read_pdfs(directory_path, query="Please summarize the content of the PDFs."):
    """
    Processes all PDF files in the specified directory by extracting text, generating embeddings,
    and answering the provided query based on those embeddings.

    Parameters:
        directory_path (str): Path to the directory containing PDF files.
        query (str): The question or query to answer based on the content of the PDFs.

    Returns:
        str: A response string with answers based on PDF embeddings.
    """
    logger = setup_logger("PDFModuleLogger", "logs/pdf_module.log")
    if not directory_path:
        logger.error("No directory path provided.")
        return "Please specify a directory path to analyze PDF files."
    
    # Verify directory and gather PDF files
    pdf_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logger.info("No PDF files found in the specified directory.")
        return "No PDF files found in the specified directory."

    file_embeddings = {}

    # Process each PDF file to extract text and generate embeddings
    for pdf_file in pdf_files:
        text = ""
        try:
            with open(pdf_file, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            logger.info(f"Text extracted from {pdf_file}.")
        except Exception as e:
            logger.error(f"Failed to read {pdf_file}: {e}")
            continue

        # Generate embeddings for the extracted text and store them
        try:
            embeddings = ollama.embed(model="llama3.2", input=text)
            # Ensure embeddings is list-like, otherwise convert or handle accordingly
            file_embeddings[os.path.basename(pdf_file)] = list(embeddings) if not isinstance(embeddings, list) else embeddings
            logger.info(f"Embeddings generated for {pdf_file}.")
        except Exception as e:
            logger.error(f"Failed to generate embeddings for {pdf_file}: {e}")
            continue

    if not file_embeddings:
        logger.info("No valid text extracted from any PDFs.")
        return "No valid text extracted from any PDFs."

    # Generate an answer to the query based on the embeddings
    embeddings_prompt = "\n".join(
        f"File: {file_name}, Embeddings Summary: {str(embeddings[:3])}..."  # Only take the first 3 items for summary
        for file_name, embeddings in file_embeddings.items()
    )
    full_prompt = (
        f"The following files have been processed with embeddings:\n{embeddings_prompt}\n\n"
        f"Based on these files, please answer the question:\n{query}"
    )

    # Query the assistant with the embeddings and query
    try:
        logger.info(f"Querying the model with prompt: {full_prompt}")
        response = query_llm(full_prompt)
        
        response_content = response.get("message", {}).get("content", "No response generated.")
        return f"Query Response:\n{response_content}"
    except Exception as e:
        logger.error(f"Error querying with question '{query}': {e}")
        return "Error processing your query based on the available documents."


def internet_search(query):
    """
    Performs an internet search using the Tavily API and generates a response.
    If search fails, it returns an error message.

    Parameters:
        query (str): The search query string.
        
    Returns:
        str: A formatted response based on search results or an error message.
    """
    # Initialize logger
    logger = setup_logger("InternetSearchModuleLogger", "logs/internet_search_module.log")
    
    # Load API key and initialize Tavily client
    search_api_key = get_search_api_key()
    try:
        tavily_client = TavilyClient(api_key=search_api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Tavily client: {e}")
        return "Unable to initialize search client."

    # Perform the search query
    try:
        search_results = tavily_client.get_search_context(query)
        if isinstance(search_results, str):  # Return if API directly gives an error message
            return search_results
    except Exception as e:
        logger.error(f"Failed to fetch search results: {e}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return "Unable to retrieve search results at this time."

    # Generate response using LLM through self.query_llm
    try:
        prompt = f"Here are some search results: {search_results}. Based on these, answer the query: '{query}'."
        return query_llm(prompt)
    except Exception as e:
        logger.error(f"Error generating response from LLM: {e}")
        logger.error(traceback.format_exc())
        return "Unable to generate a response based on search results."

def schedule_meeting(participants, start_time, end_time):
    logger = setup_logger("MeetingSchedulerModuleLogger", "logs/meeting_scheduler_module.log")
    logger.info(f"Simulating meeting scheduling with participants: {participants}, start time: {start_time}, end time: {end_time}")
    return "Simulated meeting scheduling successful."

class AIAssistant:
    def __init__(self, name="IntelliChat"):
        self.name = get_app_custom().get("model_name")
        self.logger = setup_logger("AIAssistantLogger", "logs/ai_assistant.log")
        self.status_message = "Ready to assist with your requests."
        self.model = self._create_model()
        self.supported_tools = self.get_supported_tools()

    def set_status(self, message):
        self.status_message = message
        self.logger.info(f"Status updated: {message}")

    def get_status(self):
        return self.status_message

    def query_llm(self, prompt, tools= None):
        """
        Sends a prompt to the language model and returns the response.
        """
        self.logger.info(f"querying the model {self.name} with prompt: {prompt}")
        if tools:
            response = ollama.chat(
                model=self.name,
                messages=[{"role": "user", "content": prompt}],
                tools=tools
            )
        else:
            response = ollama.chat(
                model=self.name,
                messages=[{"role": "user", "content": prompt}]
            )
        
        # Log the response in a readable format without converting it to a string
        self.logger.info(f"model {self.name} responded with: {json.dumps(response, indent=4)}")

        return response

    def get_tools(self):
        """
        Defines the tools available for the assistant to use.
        """
        return [
            {
                'type': 'function',
                'function': {
                    'name': 'send_email',
                    'description': 'Send an email',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'recipient_name': {
                                'type': 'string', 
                                'description': 'Name or email of the recipient'
                                },
                            'subject': {
                                'type': 'string', 
                                'description': 'Subject of the email'
                                },
                            'body': {
                                'type': 'string', 
                                'description': 'Body of the email'},
                        },
                        'required': ['recipient_name', 'subject', 'body'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'read_pdfs',
                    'description': 'Read and analyze PDF files in a directory',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'directory_path': {'type': 'string', 'description': 'Path to directory with PDFs'},
                            'query': {'type': 'string', 'description': 'Query about PDF contents'},
                        },
                        'required': ['directory_path'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'internet_search',
                    'description': 'Search the internet for information',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string', 'description': 'Search query'},
                        },
                        'required': ['query'],
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'schedule_meeting',
                    'description': 'Schedule a meeting',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'participants': {'type': 'string', 'description': 'Participants in the meeting'},
                        },
                    },
                },
            },
        ]

    def get_supported_tools(self):
        tools = self.get_tools()
        return [tool['function']['name'] for tool in tools]

    def handle_message(self, message):
        """
        Processes user messages, checks for missing parameters, and handles tool calls if defined in the response.
        """
        self.set_status("Processing your request...")
        try:
            # Query the model with tools enabled
            response = self.query_llm(message, self.get_tools())
            content = response.get("message", {}).get("content")
            
            # Handle tool calls if present
            tool_calls = response.get("message", {}).get("tool_calls", [])
            concatenated_result = ""
            
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    
                    if tool_name == "read_pdfs" and "query" not in arguments:
                        arguments["query"] = "Please summarize the content of the PDFs."

                    # Check for missing parameters
                    missing_params = self._check_missing_params(tool_name, arguments)
                    if missing_params:
                        # Prompt user to provide missing parameters
                        missing_info_prompt = (
                            f"It seems I'm missing some information to complete your request. "
                            f"Please provide the following details for the `{tool_name}` action: {', '.join(missing_params)}."
                        )
                        response = self.query_llm(missing_info_prompt)
                        content = response.get("message", {}).get("content", missing_info_prompt)
                        return content, False  # Exit after prompting for missing details

                    self.logger.info(f"Executing {tool_name} tool with arguments: {arguments}")
                    if tool_name not in self.supported_tools:
                        self.logger.info(f"Unknown tool requested: {tool_name}")
                        continue
                    
                    # Call the appropriate function using a mapping of tool names to functions
                    result = globals()[tool_name](**arguments) if tool_name in globals() else "Unsupported tool."
                    concatenated_result += f"{result}\n"

            # If no content from initial response, generate a natural summary if tool calls were made
            if not content and concatenated_result:
                prompt = (
                    f"Based on this message: '{message}' and the following actions taken:\n\n{concatenated_result}\n\n"
                    "Provide a friendly response summarizing the actions without mentioning the tools."
                )
                response = self.query_llm(prompt)
                content = response.get("message", {}).get("content", concatenated_result.strip())
            
            return content or concatenated_result.strip(), False

        except Exception as e:
            self.logger.error(f"Error in processing message: {e}")
            self.logger.error(traceback.format_exc())
            return "An error occurred while processing your request.", False




    def _list_models(self):
        """
        Lists available models.
        """
        existing_models = ollama.list()['models']
        names = [model['name'].split(":")[0] for model in existing_models]

        self.logger.info(f"found the following models: {names}")
        return names

    def _create_model(self, exists_ok=True):
        """
        Creates the model if it does not exist, or if exists_ok is set to False.
        """
        if exists_ok and self._model_exists():
            self.logger.info(f"Model {self.name} already exists, skipping creation.")
            return

        self.logger.info(f"Model {self.name} not found or creation forced, initiating model creation.")
        
        # Define the model specification
        modelfile = self._generate_model_definition()

        # Attempt to create the model using Ollama
        try:
            creation_response = ollama.create(model=self.name, modelfile=modelfile)
            if creation_response.get("status") == "success":
                self.logger.info(f"Model {self.name} created successfully.")
            else:
                self.logger.error(f"Error creating model: {creation_response}")
        except Exception as e:
            self.logger.error(f"Error during model creation: {e}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")

    def _model_exists(self):
        """
        Checks if the model already exists in the system.
        """
        existing_models = self._list_models()
        return self.name in existing_models

    def _generate_model_definition(self):
        """
        Generates the model definition for the assistant.
        """
        return f'''
        FROM llama3.2

        PARAMETER temperature 0.5
        PARAMETER num_ctx 4096

        SYSTEM """
        You are {self.name}, an advanced personal assistant for Omar Khater.
        Your purpose is to carry out various actions based on user input, such as reading PDFs, sending emails, scheduling meetings, and searching the internet.

        You have access to the following tools:
        1. **Email** - Send emails (requires recipient details and a subject).
        2. **PDF Reading** - Read and analyze PDF files from a specified directory.
        3. **Internet Search** - Search for information online, such as current events, latest trends, stocks, and weather.
        4. **Meeting Scheduling** - Schedule a meeting with participants and timing information.

        For each request:
        
        1. Identify the correct tool based on the user’s input.
        2. Call the tool with the required parameters (provided as part of the input).
        3. Explain what you did and the tools you used.
        """
        '''

    def _check_missing_params(self, tool_name, arguments):
        """
        Checks for missing required parameters based on tool definitions in get_tools.
        
        Returns:
            list: Missing parameter names if any, otherwise an empty list.
        """
        for tool in self.get_tools():
            if tool["function"]["name"] == tool_name:
                required_params = tool["function"]["parameters"]["required"]
                missing_params = [param for param in required_params if param not in arguments or not arguments[param]]
                return missing_params
        return []
