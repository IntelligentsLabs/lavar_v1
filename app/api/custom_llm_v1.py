from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, decode_token
import logging
from app.personalization.user_preferences import get_user_preferences, get_user_interaction_context
from app.rag import pinecone_rag
from app.api.db import *
from app.functions.get_custom_llm_streaming import (
    client_openai, generate_user_uuid, generate_streaming_response,
    generate_streaming_introduction, provide_interaction_assistance,
    augment_system_lists)
import pandas as pd

df = pd.read_csv('data/ah_index.csv')
atomic_habits_concept = df['concept'].tolist()
atomic_habits_words = df['word'].tolist()

atomic_habits_keywords = atomic_habits_concept + atomic_habits_words

# Constants for Pinecone indexes
user_index = pinecone_rag.user_index
book_index = pinecone_rag.book_index

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize the Blueprint
custom_llm = Blueprint('custom_llm', __name__)

# CORS(
#     custom_llm,
#     supports_credentials=True,
#     origins=[
#         "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev:3000/authorize",
#         "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev:3000"
#     ])


@custom_llm.route('/token', methods=['POST'])
def test():
    username, email, picture = request.json.get('username'), request.json.get(
        'email'), request.json.get('picture')
    user_exists = check_if_user_exists(email)
    if not user_exists:
        result = str(
            create_user({
                'username': username,
                'email': email,
                'picture': picture,
                'current_bg': 'black',
                'notifications': [],
                'character': {
                    'name': '',
                    'alias': '',
                    'super_skill': '',
                    'weakness': '',
                    'powers': [],
                    'equipments': [],
                    'height': '',
                    'age': 0,
                    'birthplace': ''
                }
            }).inserted_id)
        access_token = create_access_token(identity=result)
        print(access_token)
    else:
        result = str(get_user_by_email(email)['_id'])
        access_token = create_access_token(identity=result)

    return jsonify(access_token=access_token, success=True)


@custom_llm.route('/user')
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    user['_id'] = str(user['_id'])
    return jsonify(user=user, success=True)


@custom_llm.route('/color', methods=['POST'])
def add_color():
    user_id = get_jwt_identity()
    color = request.json['color']
    add_color_to_user(color, user_id)
    return jsonify(success=True)


@custom_llm.route('/character', methods=['POST'])
def add_to_book():
    user_id = get_jwt_identity()
    key, value = f"{request.json['key']}", request.json['value']
    changes = {key: value}
    change_char(changes, user_id)
    return jsonify(success=True)


@custom_llm.route('/chat/completions', methods=['POST'])
def openai_advanced_chat_completions_route_new():
    """Handle POST requests for advanced OpenAI chat completions with personalization and RAG."""
    # Parse incoming request data
    request_data = request.get_json()
    if not request_data.get("model", []):
        return jsonify({"error": "No JSON data provided in the request."}), 400

    metadata = request_data.get("metadata", {})
    token = metadata.get("token", None)
    user_data = metadata.get("data", {}).get("user", {})
    # user_name = user_data.get("username", "unknown")
    email_address = user_data.get("email", "unknown")

    if not token:
        return jsonify({"error":
                        "JWT token not provided in metadata."}), 401

    try:
        decoded = decode_token(token)
        user_id = decoded['sub']
    except Exception as e:
        logger.error(f"Invalid JWT: {str(e)}")
        return jsonify({"error": "Invalid token."}), 401

    try:
        # Extract data from the request
        messages = request_data.get("messages", [])
        tools = request_data.get("tools", None)
        model_config = request_data.get("message",
                                        {}).get("assistant",
                                                {}).get("model", {})
        stream = request_data.get("message",
                                  {}).get("analysis",
                                          {}).get("streaming", True)

        if not messages:
            raise ValueError("Messages field is required in the request.")

        # Extract the user query from the last message
        query_string = messages[-1]['content']
        if query_string.lower() in ["help", "what can i ask?"]:
            assistance_text = provide_interaction_assistance()
            return Response(generate_streaming_introduction(assistance_text),
                            content_type='text/event-stream')

        # Capture user metadata from the request (assumes a metadata structure)
        # metadata = request_data.get("metadata", {})

        user_id = generate_user_uuid(user_id)
        # user_id = '01f5f562-bdb0-43e4-a907-09c8f3da9db5'



        # Retrieve additional user data and interactions
        user_interaction_context = get_user_interaction_context(user_id)  # e.g., from Supabase
        user_preferences = get_user_preferences(user_id)

        # Retrieve book-related context using RAG:
        # atomic_habits_keywords = [
        #     "habit", "Atomic Habits", "James Clear", "self-improvement",
        #     "routine", "productivity"
        # ]
        classification_result = pinecone_rag.classify(query_string,
                                                      atomic_habits_keywords)
        classification_label = classification_result.label

        book_contexts = []
        if classification_label == "PERSONAL":
            res = pinecone_rag.query_pinecone_user(
                query_string,
                user_index,
                top_k=1,
                namespace='user-data-openai-embedding')
            book_contexts.extend(
                [x['metadata']['text'] for x in res['matches']])
        elif classification_label == "ATOMIC_HABITS":
            context_strings = pinecone_rag.query_pinecone_book(
                query_string, top_k=1, namespace='ah-test')
            book_contexts.extend(context_strings)

        # Compose the system message with personalization details and prior interactions.
        system_message_content = (
            f"The user's email is: {email_address}. "
            f"User preferences: {user_preferences}. "
            f"Past interactions: {user_interaction_context}. "
            "Please remove all special characters such as #,*,&,^,%,$,! from your response."
        )
        system_message = [{
            "role": "system",
            "content": system_message_content
        }]

        # Combine the system message with incoming messages
        conversation = augment_system_lists(system_message, messages)

        # Prepare the context prompt
        prompt_end = (
            "The following information from past interactions and book content may be relevant. "
            "If it is not relevant, ignore it:\n\n")
        combined_context = "\n\n---\n\n".join(book_contexts +
                                              [user_interaction_context])
        conversation.append({
            "role":
            "user",
            "content":
            f"Using the following context, answer the query:{query_string}\n\nContext:\n{combined_context}"
        })

        # Prepare payload for the LLM client
        llm_request_data = {
            "model": "gpt-4o",  # or model_config.get("model", "gpt-4o"),
            "messages": conversation,
            "temperature": model_config.get("temperature", 0.7),
            "stream": stream,
            "tools": tools,
        }

        if stream:
            chat_completion_stream = client_openai.chat.completions.create(
                **llm_request_data)
            return Response(
                generate_streaming_response(chat_completion_stream),
                content_type='text/event-stream')
        else:
            chat_completion = client_openai.chat.completions.create(
                **llm_request_data)
            return Response(chat_completion.model_dump_json(),
                            content_type='application/json')

    except ValueError as ve:
        logger.error(f"ValueError: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify(
            {"error":
             "An unexpected error occurred. Please try again later."}), 500

    return jsonify({
        "message":
        "Model field is empty or not provided. No operation performed."
    }), 400
