# app/rag/pinecone_rag.py

import os
import json
import requests
import openai
import tiktoken
from datetime import datetime, date
from typing import List, Literal
from pydantic import BaseModel, Field
import instructor
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Pinecone client using your API key.
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Initialize indexes
user_index = pc.Index("user-data-openai-embedding")
book_index = pc.Index("ah-test")

# Set OpenAI API key and initialize clients.
openai.api_key = os.getenv("OPENAI_API_KEY")
client_openai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = instructor.from_openai(client_openai)  # Apply patch to the OpenAI client

# --- Classification model ---
class ClassificationResponse(BaseModel):
    label: Literal["ATOMIC_HABITS", "PERSONAL", "WEB_SEARCH"] = Field(
        ...,
        description="The predicted class label.",
    )

def classify(data: str, keywords: List[str]) -> ClassificationResponse:
    """
    Perform single-label classification on the input text.
    If any keyword appears in the data, the classification should be ATOMIC_HABITS.
    """
    return client.chat.completions.create(
        model='gpt-4o',
        response_model=ClassificationResponse,
        messages=[
            {
                'role': 'system',
                'content': f'Use these keywords to determine the appropriate classification if any match the data: {" ".join(keywords)}'
            },
            {
                "role": "user",
                "content": f"Classify the following text: {data}",
            },
        ],
    )

# --- Embedding functions ---

def get_embedding(text: str, model: str = "text-embedding-ada-002"):
    """
    Get embedding for a given text using the OpenAI embeddings API.
    """
    print("Embedding text:", text)
    response = client_openai.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

# --- Pinecone Query Functions ---

def query_pinecone_user(query_string: str,
                        index,
                        top_k: int = 10,
                        namespace: str = "",
                        filter: dict = {"user_id": "fake_user_id"}):
    """
    Query the user Pinecone index using the query string.
    """
    xc = get_embedding(query_string)
    result = user_index.query(
        vector=xc,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace,
        filter=filter
    )
    return result

def query_pinecone_book(query_string: str,
                        index,
                        top_k: int = 1,
                        namespace: str = "default-namespace"):
    """
    Query the book Pinecone index and combine strings from the top similarity match and the next two sequential indices.
    Returns a list of context strings from the metadata.
    """
    xc = get_embedding(query_string)
    result = index.query(
        vector=xc,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )
    if not result or not result.matches:
        return "No results found."
    
    # Get the top match ID (assuming IDs are numeric strings)
    top_match = result.matches[0]
    top_index = int(top_match.id)
    
    # If top_index is beyond a threshold (e.g., 1452 vectors), restrict output.
    if top_index >= 1452:
        return f"Top index {top_index} is restricted. No combined string returned."
    
    # Fetch strings for indices: top_index, top_index + 1, top_index + 2.
    indices_to_fetch = [top_index, top_index + 1, top_index + 2]
    combined_strings = []
    for idx in indices_to_fetch:
        individual_result = book_index.fetch(ids=[str(idx)], namespace=namespace)
        if individual_result:
            text = individual_result['vectors'][str(idx)]['metadata'].get('text', '')
            print("Fetched text for index", idx, ":", text)
            if text:
                combined_strings.append(text)
    return combined_strings

# --- Helper Functions for Conversation Management ---

def get_context_string(contexts: List[str]) -> str:
    """Combine a list of context strings into a single string."""
    return " ".join(contexts)

async def manage_conversation_tokens(conversation: List[str], call_id: str) -> List[str]:
    """
    Manage the token count of a conversation. If the conversation exceeds the token limit,
    remove earlier messages until within limit. Optionally, summarize the conversation.
    """
    def num_tokens_from_messages(messages, tkmodel="cl100k_base"):
        encoding = tiktoken.get_encoding(tkmodel)
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # Each message has overhead tokens.
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens -= 1  # Adjust if name is provided.
        return num_tokens + 2  # Additional tokens for priming.
    
    conv_history_tokens = num_tokens_from_messages(conversation)
    print("Total conversation tokens:", conv_history_tokens)
    token_limit = 32000
    max_response_tokens = 300
    
    # Remove earlier messages until under token limit.
    while (conv_history_tokens + max_response_tokens >= token_limit) and len(conversation) > 1:
        del conversation[1]
        conv_history_tokens = num_tokens_from_messages(conversation)
    
    # If still over limit, summarize the conversation.
    if conv_history_tokens + max_response_tokens >= token_limit:
        summarization = summarize_conversation(conversation)
        summary_embedding = get_embedding(summarization)
        idv = "id_this_is_a_temp_id"
        user_index.upsert(vectors=[{
            "id": idv, 
            "values": summary_embedding, 
            "metadata": {'text': summarization, 'user_id': call_id}
        }], namespace='user-data-openai-embedding')
        return [summarization]
    
    return conversation

def summarize_conversation(context: List[str]) -> str:
    """
    Summarize the conversation using the LLM.
    """
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    today = date.today()
    date_string = str(today)
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        prompt=f"Summarize the following conversation that occurred at {current_time} on {date_string}:\n{context}",
        temperature=0.3,
        max_tokens=300,
        top_p=0.9,
        presence_penalty=0
    )
    summarization = completion.choices[0].text.strip()
    return summarization
