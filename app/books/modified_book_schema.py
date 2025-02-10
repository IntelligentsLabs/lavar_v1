from pydantic import BaseModel
from typing import List, Dict, Optional

class IndexEntry(BaseModel):
    term: str
    references: List[str]

class CategoryItem(BaseModel):
    content: str
    relevance_score: float

class Category(BaseModel):
    category_type: str
    items: List[CategoryItem]

class Paragraph(BaseModel):
    paragraph_id: str
    content: str
    related_concepts: List[str]
    summary: str
    categories: Dict[str, List[Category]]  # Each category contains relevant items with a relevance score

class Section(BaseModel):
    section_id: str
    title: str
    paragraphs: List[Paragraph]
    summary: str
    associated_concepts: List[str]
    complexity_score: float
    estimated_reading_time: int
    user_queries: List[Dict[str, str]]  # Placeholder for query metadata

class UserInteraction(BaseModel):
    user_id: str
    current_section: str
    queried_categories: Dict[str, List[str]]
    queried_concepts: List[str]
    queried_examples: List[str]
    completion_progress: float
    preferences: Dict[str, str]

class Book(BaseModel):
    book_id: str
    title: str
    author: str
    topics: List[str]
    sections: Dict[str, Section]
    categories: Dict[str, Category]
    index: Dict[str, IndexEntry]
    user_interaction: UserInteraction
    embedding_index: Optional[str]
