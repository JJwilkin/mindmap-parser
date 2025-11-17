# Mindmap Content Generation Workflow

This document explains the complete workflow for generating self-contained subject JSON files for the mindmap application.

## Overview

The workflow consists of three main steps:
1. **Generate Topic JSON** - Use an LLM to create the initial topic structure with metadata
2. **Generate Relationships** - Add IDs and analyze relationships between concepts
3. **Generate Coordinates** - Add visual positioning data for the mindmap

Each step preserves the subject metadata (name, slug, description) so the final JSON file is completely self-contained.

## Prerequisites

- Python 3.x with required packages (see `requirements.txt`)
- Node.js for coordinate generation
- An LLM service (e.g., Ollama with DeepSeek)

## Step 1: Generate Topic JSON

**Script:** `generate_topic_json.py`

This script uses an LLM to generate a hierarchical structure of topics and concepts for a subject.

### Usage:

```python
# Edit the script to set your topic and description
topic_name = "data structures and algorithms"
description = "Comprehensive guide to data structures and algorithms"

# Run the script
python generate_topic_json.py
```

### Output:

Creates `{topic_name}.json` with this structure:

```json
{
  "name": "Data Structures And Algorithms",
  "slug": "data-structures-and-algorithms",
  "description": "Comprehensive guide to data structures and algorithms",
  "sections": [
    {
      "name": "Introduction and Algorithm Analysis",
      "number": "1",
      "topics": [
        {
          "name": "Fundamentals of Algorithms",
          "number": "1.1",
          "concepts": [
            {
              "name": "What is an Algorithm?",
              "description": "Definition, properties..."
            }
          ]
        }
      ]
    }
  ]
}
```

## Step 2: Generate Relationships

**Script:** `generate_relationships.py`

This script processes the topic JSON to:
- Assign unique IDs to all concepts
- Use LLM to identify relationships between concepts
- Build a hierarchical dot structure
- Generate connection lines between related concepts

### Configuration:

Edit the script to set input/output files:

```python
INPUT_FILE = 'data_structures_and_algorithms.json'
OUTPUT_FILE = 'data_structures_with_relationships.json'
MODEL = 'deepseek-v3.1:671b-cloud'
```

### Usage:

```bash
python generate_relationships.py
```

### Output:

Creates `{output_file}.json` with this structure:

```json
{
  "name": "Data Structures And Algorithms",
  "slug": "data-structures-and-algorithms",
  "description": "Comprehensive guide to data structures and algorithms",
  "dots": [
    {
      "id": 1,
      "size": 6,
      "text": "Introduction and Algorithm Analysis",
      "parentId": null,
      "details": "Introduction and Algorithm Analysis - 1",
      "fullContent": "Introduction and Algorithm Analysis",
      "connections": [],
      "children": [...]
    }
  ],
  "paths": [],
  "lines": {
    "hierarchical": [
      {"source": 1, "target": 2, "type": "hierarchical"}
    ],
    "connections": [
      {"source": 3, "target": 4, "type": "connection"}
    ]
  }
}
```

## Step 3: Generate Coordinates

**Script:** `../mindmap-frontend/src/scripts/generateCoordinates.js`

This script adds x/y coordinates to each dot for visual positioning on the canvas.

### Usage:

```bash
cd ../mindmap-frontend
node src/scripts/generateCoordinates.js \
  ../mindmap-parser/data_structures_with_relationships.json \
  src/data/data_structures_with_coordinates.json
```

### Configuration Options:

You can customize the layout by setting environment variables:

```bash
LAYOUT=circular \
PARENT_SPREAD=0.45 \
CHILD_SPREAD=0.28 \
JITTER=15 \
MIN_DISTANCE=80 \
CENTER_WEIGHT=0.7 \
node src/scripts/generateCoordinates.js input.json output.json
```

### Output:

Creates a final JSON file with coordinates added:

```json
{
  "name": "Data Structures And Algorithms",
  "slug": "data-structures-and-algorithms",
  "description": "Comprehensive guide to data structures and algorithms",
  "dots": [
    {
      "id": 1,
      "size": 6,
      "text": "Introduction and Algorithm Analysis",
      "x": "centerX + 407",
      "y": "centerY + 0",
      "color": "rgb(197, 158, 167)",
      "children": [...]
    }
  ],
  "paths": [],
  "lines": {
    "hierarchical": [...],
    "connections": [...]
  }
}
```

## Step 4: Upload to Database

**Script:** `../mindmap-backend/uploadSubject.js`

Upload the final JSON to your backend API.

### Usage:

```bash
cd ../mindmap-backend

# If JSON has metadata (recommended):
node uploadSubject.js ../mindmap-frontend/src/data/data_structures_with_coordinates.json

# Or provide metadata as arguments:
node uploadSubject.js data.json "Subject Name" "subject-slug" "Description"
```

## Complete Example

Here's the complete workflow for creating a new subject:

```bash
# 1. Generate topic structure (edit script first with your topic)
cd mindmap-parser
python generate_topic_json.py

# 2. Generate relationships and IDs
python generate_relationships.py

# 3. Add coordinates
cd ../mindmap-frontend
node src/scripts/generateCoordinates.js \
  ../mindmap-parser/data_structures_with_relationships.json \
  src/data/my_subject_with_coordinates.json

# 4. Upload to database
cd ../mindmap-backend
node uploadSubject.js ../mindmap-frontend/src/data/my_subject_with_coordinates.json
```

## Metadata Preservation

All three scripts preserve the subject metadata (name, slug, description) throughout the pipeline:

- ✅ `generate_topic_json.py` - Creates metadata
- ✅ `generate_relationships.py` - Preserves metadata
- ✅ `generateCoordinates.js` - Preserves metadata
- ✅ `uploadSubject.js` - Reads metadata from JSON

This means your final JSON file is **completely self-contained** and can be used directly in the frontend without any hardcoded values.

## Tips

1. **Customize Layout**: Adjust the coordinate generation parameters for different visual styles
2. **Preview Locally**: Copy the final JSON to `mindmap-frontend/src/data/` and set `VITE_USE_LOCAL_DATA=true` to preview
3. **Version Control**: Keep all intermediate JSON files for debugging and iteration
4. **LLM Selection**: Different models may produce different quality results for relationships

## Troubleshooting

**No coordinates showing up?**
- Make sure the coordinates JSON is in the correct format
- Check browser console for errors
- Verify the coordinate expressions evaluate correctly

**Relationships look wrong?**
- Try a different LLM model
- Adjust the relationship prompt in `prompts/relationship_prompt.py`
- Review the relationships manually in the JSON

**Upload failing?**
- Verify your backend API is running
- Check the API_URL environment variable
- Ensure the JSON structure is valid

