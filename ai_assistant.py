# ai_assistant.py
import openai
import requests
from config import OPENAI_API_KEY
from logger import setup_logger

SUPPORTED_MODELS = {"gpt-4o-mini", "gpt-4-turbo", "ollama"}

class AIAssistant:
    def __init__(self, name="Personal AI Assistant", model="ollama"):
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model '{model}'. Choose from {SUPPORTED_MODELS}.")
        
        self.logger = setup_logger("AIAssistantLogger", "logs/ai_assistant.log")
        self.name = name
        self.model = model
        self.message_history = []

        # Set OpenAI API key from config
        openai.api_key = OPENAI_API_KEY if model in {"gpt-4o-mini", "gpt-4-turbo"} else None

    def query_llm(self, question, is_private=False):
        if is_private or self.model == "ollama":
            return self._query_ollama(question)
        else:
            return self._query_openai(question)

    def _query_ollama(self, question):
        try:
            response = requests.post(
                "http://127.0.0.1:8081/api/chat",  # Use /api/chat endpoint
                json={"model": "llama3.2", 
                      "messages": [{"role": "user", "content": question}],
                      "stream": False
                      }
            )
            response.raise_for_status()

            # Log the raw response text to inspect its format
            raw_response = response.text
            self.logger.info(f"Raw Ollama response: {raw_response}")

            # Attempt to parse JSON
            data = response.json()
            content = data.get("message", {}).get("content", "No response from Ollama.")
            
            # Log and store the assistant's reply in message history
            self.logger.info(f"Ollama response content: {content}")
            self.message_history.append({"role": "assistant", "content": content})

            return content
        except ValueError as json_error:
            # Handle JSON decoding errors
            self.logger.error(f"Ollama JSON decoding failed: {json_error}")
            return "Received an unexpected response format from Ollama."
        except requests.RequestException as e:
            self.logger.error(f"Ollama request failed: {e}")
            return "Error processing request with Ollama."
    def _query_openai(self, question):
        if not openai.api_key:
            return "OpenAI API key not set."

        try:
            response = openai.Completion.create(
                model="gpt-4-turbo",
                prompt=question,
                max_tokens=500
            )
            content = response.choices[0].text.strip()
            self.logger.info(f"OpenAI response: {content}")
            return content
        except Exception as e:
            self.logger.error(f"OpenAI request failed: {e}")
            return "Error processing request with OpenAI."
