# app/services/llm_client.py

import logging
from app.functions.get_custom_llm_streaming import generate_streaming_response, client_openai

logger = logging.getLogger(__name__)

def call_llm(llm_request_data: dict) -> dict:
    """
    Calls the LLM client for a non-streaming response.
    
    Parameters:
      llm_request_data (dict): The payload to be sent to the LLM (e.g., model, messages, temperature, stream flag, tools).
    
    Returns:
      dict: The JSON response from the LLM.
    """
    try:
        response = client_openai.chat.completions.create(**llm_request_data)
        # Assuming the response has a method to convert to JSON, such as model_dump_json()
        return response.model_dump_json()
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise e

def call_llm_stream(llm_request_data: dict):
    """
    Calls the LLM client for a streaming response.
    
    Parameters:
      llm_request_data (dict): The payload to be sent to the LLM.
    
    Returns:
      generator: A generator that yields streaming events formatted as Server-Sent Events (SSE).
    """
    try:
        stream = client_openai.chat.completions.create(**llm_request_data)
        return generate_streaming_response(stream)
    except Exception as e:
        logger.error(f"Error calling LLM in streaming mode: {e}")
        raise e
