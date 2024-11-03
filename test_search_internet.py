from tavily import TavilyClient

# Initialize the Tavily client with your API key
tavily_client = TavilyClient(api_key="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")

# Define a function to perform a search query
def web_search(query):
    response = tavily_client.search(query)
    return response['results']

# Example usage
results = web_search("Latest advancements in AI")
for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Content: {result['content']}\n")
