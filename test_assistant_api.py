from openai import OpenAI

# Initialize OpenAI Client
client = OpenAI()

# Define the Assistant with capabilities
assistant = client.beta.assistants.create(
    name="Personal AI Assistant",
    instructions="You are a personal assistant capable of managing tasks such as writing emails, reading PDF files, scheduling meetings, and conducting searches. Use the tools provided when necessary.",
    tools=[
        {"type": "code_interpreter"},
        {"type": "file_search"},
        {"type": "function_calling"}
    ],
    model="gpt-4-turbo"  # Adjust based on your needs and available model
)
