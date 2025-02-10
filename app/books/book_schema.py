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
