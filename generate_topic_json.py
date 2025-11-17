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

def strip_markdown_code_blocks(text):
    """
    Strip markdown code block markers (```json, ```, etc.) from text.
    
    Args:
        text: The text that may contain markdown code blocks
    
    Returns:
        Text with code block markers removed
    """
    text = text.strip()
    # Remove opening code block markers (```json, ```, etc.)
    if text.startswith('```'):
        # Find the first newline after the opening ```
        first_newline = text.find('\n')
        if first_newline != -1:
            text = text[first_newline + 1:]
    # Remove closing code block markers
    if text.endswith('```'):
        text = text[:-3].rstrip()
    return text.strip()

def generate_slug(name):
    """
    Generate a URL-friendly slug from a topic name.
    
    Args:
        name: The topic name
    
    Returns:
        URL-friendly slug
    """
    return name.lower().replace(" ", "-").replace("_", "-")

def generate_topic_json(topic_name, description=None):
    """
    Generate json content for a given topic.
    
    Args:
        topic_name: The name of the topic to generate content for
        description: Optional description for the topic
    
    Returns:
        Generated json content as a dict with metadata
    """
    import json
    
    prompt = markdown_prompt(topic_name)
    output = chat_complete(model, prompt)
    # Strip any markdown code block markers that might have been added
    output = strip_markdown_code_blocks(output)
    
    # Parse the JSON to wrap it with metadata
    parsed_output = json.loads(output)
    
    # Create the final structure with metadata
    final_output = {
        "name": topic_name.title(),  # Capitalize properly
        "slug": generate_slug(topic_name),
        "description": description or f"Explore {topic_name} concepts",
        "sections": parsed_output.get("sections", [])
    }
    
    return final_output

topic_name = "operation systems"
description = "Comprehensive guide to operation systems, covering fundamental concepts, analysis techniques, and practical implementations"
output = generate_topic_json(topic_name, description)

filename = topic_name.replace(" ", "_")
import json
with open(f"{filename}.json", "w") as f:
    json.dump(output, f, indent=2)
