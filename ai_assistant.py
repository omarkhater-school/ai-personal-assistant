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
from config_loader import get_email_config


def send_email(recipient_name, subject, body):
    logger = setup_logger("EmailModuleLogger", "logs/email_module.log")
    logger.info(f"Simulating email sending to {recipient_name} with subject: {subject} and body: {body}")
    return "Simulated email sending successful."
    
def read_pdfs(directory_path, query):
    logger = setup_logger("PDFModuleLogger", "logs/pdf_module.log")
    logger.info(f"Simulating PDF reading from directory: {directory_path} with query: {query}")
    return "Simulated PDF reading successful."

def internet_search(query):
    logger = setup_logger("InternetSearchModuleLogger", "logs/internet_search_module.log")
    logger.info(f"Simulating internet search with query: {query}")
    return "Simulated internet search successful."

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
        Processes user messages and handles tool calls if defined in the response.
        """
        self.set_status("Processing your request...")
        try:
            # Query the model with tools enabled
            response = self.query_llm(message, self.get_tools())
            content = response.get("message", {}).get("content")
            # Handle response content and tool calls
            tool_calls = response.get("message", {}).get("tool_calls", [])
            if tool_calls:
                concatenated_result = ""
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    self.logger.info(f"Executing {tool_name} tool with arguments: {arguments}")
                    if tool_name not in self.supported_tools:
                        self.logger.info(f"Unknown tool requested: {tool_name}")
                        continue
                    else:
                        # use the tool name to call the appropriate function
                        result = globals()[tool_name](**arguments)
                    # Concatenate the result of each tool call
                    concatenated_result += f"{result}\n"

            if not content:
                # Handle the case where the model returned an empty response (when tools are used)
                # Use the original message and the concatenated result to prompt the model to explain what it did
                prompt = f"""
                Based on this message: {message}\n\n and the following tools used: {tool_calls}, I can see the result is: 
                
                {concatenated_result}
                
                Respond to the original message in a normal tone, don't mention the tools you used or the result.
                
                """
                response = self.query_llm(prompt)
                content = response.get("message", {}).get("content")

            return content, False
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
