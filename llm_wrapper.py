import os
from dotenv import load_dotenv
from ollama import Client

# Load environment variables from .env file
load_dotenv()

# Get API key with fallback to empty string if not set
api_key = os.environ.get('OLLAMA_API_KEY', '')

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + api_key} if api_key else None
)

def chat_complete(model, messages, stream=False):
    """
    Complete a chat conversation using Ollama.
    
    Args:
        model: The model name to use (e.g., 'gpt-oss:120b')
        messages: Either a string prompt or a list of message dictionaries with 'role' and 'content'
        stream: Whether to stream the response (default: False)
    
    Returns:
        The complete response message content as a string
    """
    # Convert string prompt to messages format if needed
    if isinstance(messages, str):
        messages = [{'role': 'user', 'content': messages}]
    
    response = client.chat(model=model, messages=messages, stream=stream)
    
    if stream:
        # If streaming, collect all chunks
        full_content = ''
        for part in response:
            full_content += part['message']['content']
        return full_content
    else:
        # If not streaming, return the message content directly
        return response['message']['content']


# Example usage:
if __name__ == "__main__":
    messages = [
        {
            'role': 'user',
            'content': 'Why is the sky blue?',
        },
    ]
    
    output = chat_complete('deepseek-v3.1:671b-cloud', messages)
    print(output)