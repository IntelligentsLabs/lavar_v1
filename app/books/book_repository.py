import json
import os
from app.books.book_schema import Book

DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/books/schema')

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
