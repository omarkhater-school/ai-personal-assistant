import traceback
from tavily import TavilyClient
from logger import setup_logger
from config_loader import get_search_api_key

class InternetSearchModule:
    def __init__(self, assistant_query_llm):
        self.query_llm = assistant_query_llm
        self.logger = setup_logger("InternetSearchModuleLogger", "logs/internet_search_module.log")
        self.search_api_key = get_search_api_key()
        self.tavily_client = TavilyClient(api_key=self.search_api_key)

    def perform_search(self, query):
        try:
            response = self.tavily_client.get_search_context(query)
            return response
        except Exception as e:
            self.logger.error(f"Failed to fetch search results: {e}")
            self.logger.error(f"Error details: {traceback.format_exc()}")
            return "Unable to retrieve search results at this time."

    def generate_response(self, query):
        search_results = self.perform_search(query)
        if isinstance(search_results, str):
            return search_results  # If an error message was returned

        prompt = f"Here are some search results: {search_results}. Answer: {query}"
        return self.query_llm(prompt, is_private=False)
