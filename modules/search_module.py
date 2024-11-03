import os
import traceback
from tavily import TavilyClient
from logger import setup_logger
from prompts import internet_search_prompt
from config_loader import get_search_api_key
import re
class InternetSearchModule:
    def __init__(self, assistant_query_llm):
        self.query_llm = assistant_query_llm
        self.logger = setup_logger("InternetSearchModuleLogger", "logs/internet_search_module.log")
        self.search_api_key = get_search_api_key()
        if not self.search_api_key:
            self.logger.error("TAVILY_API_KEY environment variable is not set.")
        self.tavily_client = TavilyClient(api_key=self.search_api_key)

    def perform_search(self, query):
        """
        Fetches search results based on the user's question.
        """
        if self.scan_for_sensitive_data(query):
            return "I'm sorry, but I can't perform this search as it contains sensitive data."
        try:
            response = self.tavily_client.get_search_context(query)
            self.logger.info("Search results fetched successfully.")
            self.logger.info(f"Search results: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to fetch search results: {e}")
            self.logger.error(f"Error details: {traceback.format_exc()}")
            return "Unable to retrieve search results at this time."

    def scan_for_sensitive_data(self, text):
        """
        Scans the text for patterns that might indicate sensitive data.
        """
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b' # Social Security Number
        cc_pattern = r'\b(?:\d[ -]*?){13,16}\b' # Credit Card Number
        patterns = {"SSN": ssn_pattern, "Credit Card Number": cc_pattern}
        for name, pattern in patterns.items():
            if re.search(pattern, text):
                self.logger.info(f"Sensitive data detected: {name}")
                return True
        return False
    def generate_response(self, query):
        """
        Generates a response by combining search results with the user question.
        """
        # Perform the search
        search_results = self.perform_search(query)
        
        # Formulate a prompt based on the search results and question
        prompt = internet_search_prompt(query, search_results)
        # Generate response using the local LLM
        answer = self.query_llm(prompt, is_private=False)  # Pass `is_private=False` as it’s public data
        self.logger.info(f"Generated answer: {answer} for query '{query}'.")
        return answer
