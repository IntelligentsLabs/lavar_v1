#!/bin/bash
# setup_project.sh
# This script sets up the basic folder structure and files for the project.

# Create directories
mkdir -p app/api
mkdir -p app/books
mkdir -p app/personalization
mkdir -p app/services
mkdir -p app/rag
mkdir -p app/tools
mkdir -p app/types
mkdir -p app/vapi_message_handlers
mkdir -p data/books
mkdir -p data/databases
mkdir -p tests

# Create __init__.py files for package initialization
touch app/__init__.py
touch app/api/__init__.py
touch app/books/__init__.py
touch app/personalization/__init__.py
touch app/services/__init__.py
touch app/rag/__init__.py
touch app/tools/__init__.py
touch app/types/__init__.py
touch app/vapi_message_handlers/__init__.py
touch tests/__init__.py

# Create placeholder files for API endpoints
touch app/api/custom_llm.py
touch app/api/webhook.py

# Create the book module files with integrated code

# app/books/book_schema.py
cat << 'EOF' > app/books/book_schema.py
from pydantic import BaseModel
from typing import List, Optional, Dict

class Resource(BaseModel):
    title: str
    url: str

class Category(BaseModel):
    content: str
    relevance_score: float

class Paragraph(BaseModel):
    paragraph_id: str
    page_number: int
    content: str
    summary: str
    categories: Optional[Dict[str, List[Category]]] = None
    user_annotations: Optional[str] = ""

class Section(BaseModel):
    section_id: str
    title: str
    summary: str
    estimated_reading_time: int
    complexity_score: float
    associated_concepts: List[str]
    learning_objectives: Optional[List[str]] = []
    key_takeaways: Optional[List[str]] = []
    reflection_prompts: Optional[List[str]] = []
    actionable_steps: Optional[List[str]] = []
    interactive_elements: Optional[List[str]] = []
    emotional_tone: Optional[str] = None
    related_resources: Optional[List[Resource]] = []
    recommended_next_sections: Optional[List[str]] = []
    paragraphs: List[Paragraph]

class ContentVariant(BaseModel):
    variant_id: str
    description: str

class Book(BaseModel):
    book_id: str
    title: str
    author: str
    learning_objectives: List[str]
    key_takeaways: List[str]
    content_variants: Optional[Dict[str, ContentVariant]] = {}
    sections: List[Section]
EOF

# app/books/book_repository.py
cat << 'EOF' > app/books/book_repository.py
import json
import os
from app.books.book_schema import Book

DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/books')

def load_book(book_filename: str) -> Book:
    """
    Load a book JSON file and parse it into a Book object.
    """
    file_path = os.path.join(DATA_DIR, book_filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return Book.parse_obj(data)

def list_books() -> list:
    """
    List all book JSON files in the data/books directory.
    """
    return [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
EOF

# Create placeholder files for personalization module
touch app/personalization/personalization_service.py
touch app/personalization/user_preferences.py

# Create placeholder files for services module
touch app/services/query_processor.py
touch app/services/context_aggregator.py
touch app/services/llm_client.py

# Create placeholder file for the Pinecone Rag module
touch app/rag/pinecone_rag.py

# Create placeholder file for tools
touch app/tools/various_tool_handlers.py

# Create placeholder files for VAPI message handlers
touch app/vapi_message_handlers/conversation_update.py
touch app/vapi_message_handlers/end_of_call_report.py
touch app/vapi_message_handlers/model_output.py
touch app/vapi_message_handlers/speech_update.py
touch app/vapi_message_handlers/transcript.py

# Create root-level project files
touch pyproject.toml
touch poetry.lock
touch README.md

echo "Project structure created successfully."
