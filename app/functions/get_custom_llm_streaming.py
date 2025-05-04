# app/functions/get_custom_llm_streaming.py

import uuid
import json
import logging
from flask import Response
from dotenv import load_dotenv
import openai
import os

load_dotenv()

# Set OpenAI API key and initialize clients.
openai.api_key = os.getenv("OPENAI_API_KEY")
client_openai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)


def generate_user_uuid(user_id):
    """
    Generate a unique user ID based on the user's name and email.
    This implementation uses UUID version 5 with a DNS namespace.
    """
    namespace = uuid.NAMESPACE_DNS
    unique_string = f"{user_id}"
    return uuid.uuid5(namespace, unique_string)


def generate_streaming_response(data):
    for message in data:
        json_data = message.model_dump_json()
        # logger.info(f"JSON data: {json.dumps(json_data, indent=2)}")
        yield f"data: {json_data}\n\n"


# def generate_streaming_response(chat_completion_stream) -> str:
#     """
#     Convert the streaming response from the LLM into a Server-Sent Events (SSE)
#     formatted string. This function returns a generator that yields SSE-formatted data.
#     """

#     def event_stream():
#         try:
#             for chunk in chat_completion_stream:
#                 if chunk.choices[0].delta.content is not None:
#                     yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
#         except Exception as e:
#             logger.error(f"Error in streaming response: {e}")

#     return event_stream()


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


def augment_system_lists(system_messages: list,
                         incoming_messages: list) -> list:
    """
    Combine system messages with incoming messages.
    This simple implementation prepends the system messages to the list of incoming messages.
    """
    return system_messages + incoming_messages
