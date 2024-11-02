# ai_assistant.py

import requests
from config_loader import get_endpoint
from logger import setup_logger
import json

SUPPORTED_MODELS = {"gpt-4o-mini", "gpt-4-turbo", "ollama"}

class AIAssistant:
    def __init__(self, name="Personal AI Assistant", model="ollama"):
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model '{model}'. Choose from {SUPPORTED_MODELS}.")
        
        self.logger = setup_logger("AIAssistantLogger", "logs/ai_assistant.log")
        self.name = name
        self.model = model
        self.message_history = []  # Store all message history for /api/chat requests

    def query_llm(self, question, is_private=False):
        """
        Query the appropriate language model based on privacy requirements and selected model.
        """
        if is_private or self.model == "ollama":
            return self._query_ollama_chat(question)
        else:
            return self._query_openai(question)

    def _query_ollama_chat(self, question):
        try:
            # Add the user's question to the message history
            self.message_history.append({"role": "user", "content": question})

            # Use get_endpoint to retrieve the URL for the chat API
            ollama_chat_url = get_endpoint("ollama_chat")
            
            # Prepare the payload for the /api/chat endpoint with full message history
            payload = {
                "model": "llama3.2",
                "messages": self.message_history,
                "stream": False
            }
            
            response = requests.post(ollama_chat_url, json=payload, timeout=300)
            response.raise_for_status()

            # Log the raw response to inspect its format
            raw_response = response.text
            self.logger.info(f"Raw Ollama response: {raw_response}")

            # Parse JSON response
            data = response.json()
            content = data.get("message", {}).get("content", "No response from Ollama.")

            # Log the response content and update message history
            self.logger.info(f"Ollama response content: {content}")
            self.message_history.append({"role": "assistant", "content": content})

            # If the response is a JSON structure for internal analysis, return the parsed JSON
            try:
                json_content = json.loads(content)
                if isinstance(json_content, dict) and "intent" in json_content and "privacy" in json_content:
                    return json_content  # Return JSON for intent analysis processing
            except json.JSONDecodeError:
                pass  # If content is not JSON, continue to return it as text

            return content
        except ValueError as json_error:
            self.logger.error(f"Ollama JSON decoding failed: {json_error}")
            return "Received an unexpected response format from Ollama."
        except requests.RequestException as e:
            self.logger.error(f"Ollama request failed: {e}")
            return "Error processing request with the local model."

    def _query_ollama_intent_analysis(self, prompt):
        """
        Query Ollama for intent analysis without modifying the main message history.
        """
        try:
            # Use get_endpoint to retrieve the URL for the chat API
            ollama_chat_url = get_endpoint("ollama_chat")
            
            # Prepare the payload for the /api/chat endpoint without message history
            payload = {
                "model": "llama3.2",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
            
            response = requests.post(ollama_chat_url, json=payload, timeout=300)
            response.raise_for_status()

            # Log the raw response to inspect its format
            raw_response = response.text
            self.logger.info(f"Raw Ollama response (Intent Analysis): {raw_response}")

            # Parse JSON response
            data = response.json()
            content = data.get("message", {}).get("content", "No response from Ollama.")

            # Log the response content
            self.logger.info(f"Ollama intent analysis content: {content}")

            # Parse content as JSON
            intent_data = json.loads(content)
            return intent_data  # Return JSON for intent analysis processing
        except (ValueError, json.JSONDecodeError) as json_error:
            self.logger.error(f"Ollama JSON decoding failed during intent analysis: {json_error}")
            return {"intent": "general inquiry", "privacy": "public data"}
        except requests.RequestException as e:
            self.logger.error(f"Ollama request failed during intent analysis: {e}")
            return {"intent": "general inquiry", "privacy": "public data"}

    def clear_history(self):
        """ Clears the conversation history. """
        self.message_history = []
