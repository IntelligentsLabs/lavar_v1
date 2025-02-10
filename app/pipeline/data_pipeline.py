import os
import json
import base64
from typing import List, Dict, Optional
from pydantic import BaseModel
import openai
import instructor
from app.books.modified_book_schema import IndexEntry, CategoryItem, Category, Paragraph, Section, UserInteraction, Book

# Apply instructor patch to OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
client_openai = openai.OpenAI(api_key=api_key)
client_openai_instructor = instructor.from_openai(client_openai)

# Function to encode the image to base64
def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# OpenAI API function to process images into a Section using GPT-4 Vision
def process_image_with_openai(image_path: str) -> Section:
    try:
        base64_image = encode_image(image_path)
        response = client_openai_instructor.chat.completions.create(
            model="gpt-4o-mini",
            response_model=Section,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract structured data from this book page. Return a JSON object with the following fields:\n"
                                "- section_id: A unique identifier for the section.\n"
                                "- title: The title of the section.\n"
                                "- paragraphs: A list of paragraphs, where each paragraph has:\n"
                                "  - paragraph_id: A unique identifier for the paragraph.\n"
                                "  - content: The actual text content of the paragraph.\n"
                                "  - related_concepts: A list of key concepts related to the paragraph.\n"
                                "  - summary: A concise summary of the paragraph.\n"
                                "  - categories: Categories such as analogies, core principles, or actionable steps, "
                                "with each category containing relevant content and a relevance score.\n"
                                "- summary: A concise summary of the section.\n"
                                "- associated_concepts: A list of key concepts associated with the section.\n"
                                "- complexity_score: A score indicating the complexity of the section (0-1).\n"
                                "- estimated_reading_time: Estimated reading time in minutes.\n"
                                "- user_queries: A list of past user queries related to this section."
                            )
                        },
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
            max_tokens=3000,
        )
        # (Optional) Transform category data if needed
        for paragraph in response.paragraphs:
            for category_name, category_data in paragraph.categories.items():
                if isinstance(category_data, dict):
                    paragraph.categories[category_name] = [CategoryItem(**category_data)]
        return response
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return Section(
            section_id=os.path.splitext(os.path.basename(image_path))[0],
            title=f"Error Title for {os.path.basename(image_path)}",
            paragraphs=[],
            summary="Error in generating summary.",
            associated_concepts=[],
            complexity_score=0.0,
            estimated_reading_time=0,
            user_queries=[]
        )

# Main function to create a book from images
def create_book_from_images(image_folder: str, output_folder: str, index_data: Dict[str, IndexEntry], book_id: str, title: str, author: str, topics: List[str]):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    sections = {}

    # Process each image in the folder sequentially
    for image_file in sorted(os.listdir(image_folder), key=lambda x: int(x.split('_')[-1].split('.')[0])):
        if image_file.lower().endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(image_folder, image_file)
            section_data = process_image_with_openai(image_path)
            sections[section_data.section_id] = section_data

            # Save individual JSON file for each section
            output_file = os.path.join(output_folder, f"{section_data.section_id}.json")
            with open(output_file, "w") as f:
                json.dump(section_data.dict(), f, indent=2)

    # Assemble the full book schema
    book = Book(
        book_id=book_id,
        title=title,
        author=author,
        topics=topics,
        sections=sections,
        categories={},  # Populate dynamically as needed
        index=index_data,
        user_interaction=UserInteraction(
            user_id="default_user",
            current_section="",
            queried_categories={},
            queried_concepts=[],
            queried_examples=[],
            completion_progress=0.0,
            preferences={}
        ),
        embedding_index=None
    )

    # Save the complete book JSON
    book_output_path = os.path.join(output_folder, "book.json")
    with open(book_output_path, "w") as f:
        json.dump(book.dict(), f, indent=2)

    print(f"Book schema saved to {book_output_path}")

def main():
    image_folder = "data/images"
    output_folder = "output"
    index_data = {
        "habit formation": {"term": "habit formation", "references": ["1", "2"]},
        "automation": {"term": "automation", "references": ["3", "4"]}
    }
    
    create_book_from_images(
        image_folder=image_folder,
        output_folder=output_folder,
        index_data=index_data,
        book_id="123",
        title="Atomic Habits",
        author="James Clear",
        topics=["Habits", "Behavioral Psychology"]
    )

if __name__ == "__main__":
    main()
