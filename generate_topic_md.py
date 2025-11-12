import sys
from pathlib import Path

# # Add mindmap-parser directory to Python path
# mindmap_parser_path = Path(__file__).parent / "mindmap-parser"
# sys.path.insert(0, str(mindmap_parser_path))

from prompts.markdown_prompt import markdown_prompt
from llm_wrapper import chat_complete

# Initialize LLM client - change provider and model as needed
# For Ollama (default):
model = "deepseek-v3.1:671b-cloud"

def generate_topic_md(topic_name):
    """
    Generate markdown content for a given topic.
    
    Args:
        topic_name: The name of the topic to generate content for
        client: Optional LLMClient instance. If None, uses the default client.
    
    Returns:
        Generated markdown content as a string
    """
    prompt = markdown_prompt(topic_name)
    output = chat_complete(model, prompt)
    return output

topic_name = "data structures and algorithms"
output = generate_topic_md(topic_name)
with open(f"{topic_name}.md", "w") as f:
    f.write(output)
