# app/services/query_processor.py

import logging
from typing import Dict, Any, List
from app.rag import pinecone_rag
from app.personalization.personalization_service import get_personalized_context

logger = logging.getLogger(__name__)

def process_query(user_id: str, query_string: str, messages: List[Dict[str, Any]], 
                  tools: Dict[str, Any], model_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a raw user query by aggregating personalized context and book content, then returns
    a complete conversation prompt along with the payload for the LLM.

    Parameters:
      user_id (str): The unique identifier for the user.
      query_string (str): The user's query text.
      messages (List[Dict[str, Any]]): The current conversation messages.
      tools (Dict[str, Any]): Any tools to be passed to the LLM.
      model_config (Dict[str, Any]): Configuration parameters for the LLM (e.g., model name, temperature, stream flag).

    Returns:
      Dict[str, Any]: A dictionary containing:
         - "conversation": The list of messages (system and user) to be sent to the LLM.
         - "llm_request_data": The payload (including model, messages, temperature, stream, tools) to be sent to the LLM.
    """
    try:
        # Define keywords for classifying the query.
        atomic_habits_keywords = ["habit", "Atomic Habits", "James Clear", "self-improvement", "routine", "productivity"]

        # Classify the query to determine whether to retrieve personal or book-related context.
        classification_result = pinecone_rag.classify(query_string, atomic_habits_keywords)
        classification_label = classification_result.label

        book_contexts: List[str] = []
        if classification_label == "PERSONAL":
            # Query the user index for context.
            res = pinecone_rag.query_pinecone_user(query_string, pinecone_rag.user_index, top_k=1, namespace='user-data-openai-embedding')
            if res and res.get("matches"):
                book_contexts.extend([x['metadata']['text'] for x in res['matches']])
        elif classification_label == "ATOMIC_HABITS":
            # Query the book index for context.
            context_strings = pinecone_rag.query_pinecone_book(query_string, pinecone_rag.book_index, top_k=1, namespace='ah-test')
            if context_strings:
                book_contexts.extend(context_strings)

        # Retrieve personalized context from the personalization service.
        personalized_context = get_personalized_context(user_id)

        # Build a system message that includes personalized context.
        system_message_content = f"User personalized context: {personalized_context}"
        system_message = {"role": "system", "content": system_message_content}

        # Start the conversation with the system message followed by existing messages.
        conversation = [system_message] + messages

        # Prepare an additional context prompt combining book context and personalized context.
        prompt_end = "Additional context:\n\n"
        # Combine contexts; if book_contexts is empty, the personalized context is still included.
        combined_context = "\n\n---\n\n".join(book_contexts + [personalized_context])
        # Append a message that instructs the LLM to answer using the provided context.
        conversation.append({
            "role": "user",
            "content": f"Answer the query: {query_string}\n\n{prompt_end}{combined_context}"
        })

        # Construct the final payload for the LLM client.
        llm_request_data = {
            "model": model_config.get("model", "gpt-4o"),
            "messages": conversation,
            "temperature": model_config.get("temperature", 0.7),
            "stream": model_config.get("stream", False),
            "tools": tools,
        }

        return {
            "conversation": conversation,
            "llm_request_data": llm_request_data,
        }

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise e
