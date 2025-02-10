# app/functions/get_custom_llm_streaming.py

import uuid
import json
import logging
from flask import Response

logger = logging.getLogger(__name__)

def generate_user_uuid(user_name: str, email_address: str) -> str:
    """
    Generate a unique user ID based on the user's name and email.
    This implementation uses UUID version 5 with a DNS namespace.
    """
    namespace = uuid.NAMESPACE_DNS
    unique_string = f"{user_name}-{email_address}"
    return str(uuid.uuid5(namespace, unique_string))

def generate_streaming_response(chat_completion_stream) -> str:
    """
    Convert the streaming response from the LLM into a Server-Sent Events (SSE)
    formatted string. This function returns a generator that yields SSE-formatted data.
    """
    def event_stream():
        try:
            # Assuming chat_completion_stream is an iterable of chunks.
            for chunk in chat_completion_stream:
                # Each chunk is converted to JSON and formatted as an SSE event.
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
    return event_stream()

def generate_streaming_introduction(assistance_text: str) -> str:
    """
    Wrap the provided assistance text in SSE format so it can be streamed to the client.
    """
    return f"data: {assistance_text}\n\n"

def provide_interaction_assistance() -> str:
    """
    Return a default assistance message to guide the user in what they can ask.
    """
    return (
        "You can ask me questions about building better habits, improving productivity, "
        "or any self-improvement topics. For example, 'How do I build a daily habit?'"
    )

def augment_system_lists(system_messages: list, incoming_messages: list) -> list:
    """
    Combine system messages with incoming messages.
    This simple implementation prepends the system messages to the list of incoming messages.
    """
    return system_messages + incoming_messages
