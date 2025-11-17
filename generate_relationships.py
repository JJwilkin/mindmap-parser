import json
import os
import sys
from llm_wrapper import chat_complete
from prompts.relationship_prompt import relationship_prompt

# Configuration
MODEL = 'deepseek-v3.1:671b-cloud'

def assign_ids_to_concepts(data):
    """
    Flatten the nested structure and assign unique IDs to each concept.
    Returns a list of all concepts with their hierarchy information.
    """
    concepts = []
    concept_id = 1
    
    for section in data['sections']:
        # Create section as a top-level dot
        section_id = concept_id
        section_dot = {
            'id': section_id,
            'size': 6,
            'text': section['name'],
            'number': section.get('number', ''),
            'type': 'section',
            'parentId': None,
            'children_ids': []
        }
        concepts.append(section_dot)
        concept_id += 1
        
        # Process topics within the section
        for topic in section.get('topics', []):
            topic_id = concept_id
            topic_dot = {
                'id': topic_id,
                'size': 4,
                'text': topic['name'],
                'number': topic.get('number', ''),
                'type': 'topic',
                'parentId': section_id,
                'children_ids': []
            }
            concepts.append(topic_dot)
            section_dot['children_ids'].append(topic_id)
            concept_id += 1
            
            # Process concepts within the topic
            for concept in topic.get('concepts', []):
                concept_dot = {
                    'id': concept_id,
                    'size': 3,
                    'text': concept['name'],
                    'description': concept.get('description', ''),
                    'type': 'concept',
                    'parentId': topic_id,
                    'children_ids': []
                }
                concepts.append(concept_dot)
                topic_dot['children_ids'].append(concept_id)
                concept_id += 1
    
    return concepts

def prepare_concepts_for_llm(concepts):
    """
    Prepare a JSON summary of concepts for the LLM to analyze.
    """
    concept_summaries = []
    for concept in concepts:
        summary = {
            'id': concept['id'],
            'name': concept['text'],
            'type': concept['type'],
            'description': concept.get('description', ''),
            'number': concept.get('number', '')
        }
        concept_summaries.append(summary)
    
    return json.dumps(concept_summaries, indent=2)

def get_relationships_from_llm(concepts):
    """
    Use LLM to identify relationships between concepts.
    Process in batches to avoid token limits.
    """
    all_concepts_summary = prepare_concepts_for_llm(concepts)
    
    # Only analyze leaf concepts (the actual concepts, not sections/topics)
    leaf_concepts = [c for c in concepts if c['type'] == 'concept']
    
    # Process in batches
    batch_size = 15
    all_relationships = {}
    
    print(f"Analyzing {len(leaf_concepts)} concepts in batches of {batch_size}...")
    
    for i in range(0, len(leaf_concepts), batch_size):
        batch = leaf_concepts[i:i + batch_size]
        batch_json = prepare_concepts_for_llm(batch)
        
        print(f"Processing batch {i // batch_size + 1} ({len(batch)} concepts)...")
        
        prompt = relationship_prompt(batch_json, all_concepts_summary)
        
        try:
            response = chat_complete(MODEL, prompt)
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith('```'):
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]
            response = response.strip()
            
            result = json.loads(response)
            
            # Store relationships
            for rel in result.get('relationships', []):
                concept_id = rel['concept_id']
                related_ids = rel.get('related_ids', [])
                all_relationships[concept_id] = related_ids
                
        except Exception as e:
            print(f"Error processing batch: {e}")
            print(f"Response: {response[:500]}")
            # Continue with empty relationships for this batch
            for concept in batch:
                if concept['id'] not in all_relationships:
                    all_relationships[concept['id']] = []
    
    return all_relationships

def expand_concept_details_with_llm(concept, all_concepts_summary):
    """
    Use LLM to expand a concept with detailed content, implementations, and relationships.
    """
    prompt = f"""
    You are creating educational content for a data structures and algorithms curriculum.
    
    Given this concept:
    Name: {concept['text']}
    Description: {concept.get('description', 'N/A')}
    Type: {concept['type']}
    
    All concepts in curriculum:
    {all_concepts_summary}
    
    Generate the following:
    1. A brief "details" summary (1-2 sentences, max 150 chars)
    2. A "fullContent" paragraph (3-5 sentences explaining the concept in detail)
    3. A list of 3-5 "implementations" or "key aspects" (specific techniques, algorithms, or practices)
    4. A list of 3-5 "relationships" (how this relates to other concepts, described in plain text)
    
    Output ONLY valid JSON in this exact format:
    {{
        "details": "brief summary...",
        "fullContent": "detailed explanation...",
        "implementations": ["item1", "item2", "item3"],
        "relationships": ["relationship1", "relationship2", "relationship3"]
    }}
    
    Do not include markdown code blocks. Output raw JSON only.
    """
    
    try:
        response = chat_complete(MODEL, prompt)
        response = response.strip()
        if response.startswith('```'):
            response = response.split('```')[1]
            if response.startswith('json'):
                response = response[4:]
        response = response.strip()
        
        result = json.loads(response)
        return result
    except Exception as e:
        print(f"Error expanding concept {concept['id']}: {e}")
        return {
            "details": concept.get('description', concept['text'])[:150],
            "fullContent": concept.get('description', concept['text']),
            "implementations": [],
            "relationships": []
        }

def build_hierarchical_structure(concepts, relationships):
    """
    Build the final hierarchical structure with all details.
    """
    # Create a lookup dictionary
    concepts_by_id = {c['id']: c for c in concepts}
    
    # Build the tree structure
    dots = []
    
    # Only include top-level (section) dots in the main array
    for concept in concepts:
        if concept['type'] == 'section':
            # Build the full dot structure
            dot = build_dot(concept, concepts_by_id, relationships)
            dots.append(dot)
    
    return dots

def build_dot(concept, concepts_by_id, relationships):
    """
    Recursively build a dot with all its children.
    """
    dot = {
        'id': concept['id'],
        'size': concept['size'],
        'text': concept['text'],
        'parentId': concept['parentId']
    }
    
    # Add description fields based on type
    if concept['type'] == 'concept':
        # These would be filled by LLM but for now use placeholders
        dot['details'] = concept.get('description', concept['text'])[:150] + "..."
        dot['fullContent'] = concept.get('description', concept['text'])
        dot['implementations'] = []
        dot['relationships'] = []
    else:
        # For sections and topics, create simplified content
        dot['details'] = f"{concept['text']} - {concept.get('number', '')}"
        dot['fullContent'] = concept['text']
        dot['implementations'] = []
        dot['relationships'] = []
    
    # Add connections (non-hierarchical relationships)
    if concept['id'] in relationships:
        dot['connections'] = relationships[concept['id']]
    else:
        dot['connections'] = []
    
    # Build children
    children = []
    for child_id in concept.get('children_ids', []):
        child_concept = concepts_by_id[child_id]
        child_dot = build_dot(child_concept, concepts_by_id, relationships)
        children.append(child_dot)
    
    if children:
        dot['children'] = children
    
    return dot

def collect_hierarchical_lines(dots):
    """
    Collect all parent-child relationships as lines.
    """
    lines = []
    
    def process_dot(dot):
        if 'children' in dot:
            for child in dot['children']:
                lines.append({
                    'source': dot['id'],
                    'target': child['id'],
                    'type': 'hierarchical'
                })
                process_dot(child)
    
    for dot in dots:
        process_dot(dot)
    
    return lines

def collect_connection_lines(dots):
    """
    Collect all non-hierarchical relationships as connection lines.
    """
    lines = []
    processed_pairs = set()
    
    def process_dot(dot):
        if 'connections' in dot:
            for target_id in dot['connections']:
                # Avoid duplicate lines
                pair = tuple(sorted([dot['id'], target_id]))
                if pair not in processed_pairs:
                    processed_pairs.add(pair)
                    lines.append({
                        'source': dot['id'],
                        'target': target_id,
                        'type': 'connection'
                    })
        
        if 'children' in dot:
            for child in dot['children']:
                process_dot(child)
    
    for dot in dots:
        process_dot(dot)
    
    return lines

def main():
    # Check if input file is provided as command line argument
    if len(sys.argv) < 2:
        print("Usage: python generate_relationships.py <input_file.json>")
        print("Example: python generate_relationships.py data_structures_and_algorithms.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Generate output filename by inserting '_relationships' before '.json'
    if input_file.endswith('.json'):
        output_file = input_file[:-5] + '_relationships.json'
    else:
        output_file = input_file + '_relationships.json'
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    print("\nLoading input data...")
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: File '{input_file}' is not valid JSON.")
        sys.exit(1)
    
    # Extract metadata (if present)
    name = data.get('name', 'Untitled Subject')
    slug = data.get('slug', 'untitled-subject')
    description = data.get('description', 'No description provided')
    
    print(f"Subject: {name}")
    print(f"Slug: {slug}")
    
    print("\nAssigning IDs to concepts...")
    concepts = assign_ids_to_concepts(data)
    print(f"Total concepts: {len(concepts)}")
    
    print("\nGetting relationships from LLM...")
    relationships = get_relationships_from_llm(concepts)
    
    print("\nBuilding hierarchical structure...")
    dots = build_hierarchical_structure(concepts, relationships)
    
    print("Collecting lines...")
    hierarchical_lines = collect_hierarchical_lines(dots)
    connection_lines = collect_connection_lines(dots)
    
    # Build final output structure with metadata
    output = {
        'name': name,
        'slug': slug,
        'description': description,
        'dots': dots,
        'paths': [],
        'lines': {
            'hierarchical': hierarchical_lines,
            'connections': connection_lines
        }
    }
    
    print(f"\nWriting output to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Done!")
    print(f"  - Subject: {name}")
    print(f"  - {len(dots)} top-level sections")
    print(f"  - {hierarchical_lines.__len__()} hierarchical relationships")
    print(f"  - {connection_lines.__len__()} cross-concept connections")

if __name__ == "__main__":
    main()

