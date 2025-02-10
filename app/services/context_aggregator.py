# app/services/context_aggregator.py

def aggregate_context(personal_context: str, book_contexts: list) -> str:
    """
    Aggregates personalized context and a list of book context strings into a unified context string.
    
    Parameters:
      personal_context (str): A context string coming from the personalization service.
      book_contexts (list): A list of context strings (e.g., extracted from book data via RAG).
    
    Returns:
      str: A unified context string that can be injected into an LLM prompt.
    """
    # Filter out any empty strings from the book contexts.
    valid_book_contexts = [ctx for ctx in book_contexts if ctx]
    
    # Combine the book contexts using a clear delimiter.
    combined_book_context = "\n\n---\n\n".join(valid_book_contexts)
    
    # If there's both book context and personal context, combine them with another delimiter.
    if combined_book_context and personal_context:
        unified_context = f"{combined_book_context}\n\n=== Personal Context ===\n\n{personal_context}"
    elif combined_book_context:
        unified_context = combined_book_context
    else:
        unified_context = personal_context
    
    return unified_context
