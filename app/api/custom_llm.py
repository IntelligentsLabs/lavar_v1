# app/api/custom_llm.py

import os
import logging
import json
import pandas as pd
# --- Flask and Extensions Imports ---
from flask import Blueprint, request, jsonify, Response, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, decode_token
# --- ---

from pydantic import ValidationError # Keep for potential future model use

# --- Database Function Imports ---
# Import Supabase functions from the designated DB interaction file
from app.api.supabase_db import (
    check_if_user_exists,
    create_supabase_user,
    get_supabase_user_id_by_email,
    get_supabase_user_data_by_id,
    update_user_setting,
    update_user_character_detail,
    get_user_preferences as get_user_preferences_from_db # Rename DB fetch for clarity
)
# --- End Database Function Imports ---

# --- Personalization Imports ---
from app.personalization.user_preferences import (
    get_llm_context_from_session,
    generate_session_hash
    # get_user_preferences is handled by db import and cache
)
# --- End Personalization Imports ---

# --- RAG Imports ---
from app.rag import pinecone_rag # Assuming this module is correctly set up
# --- End RAG Imports ---

# --- LLM Streaming Imports ---
from app.functions.get_custom_llm_streaming import (
    client_openai, # Your configured OpenAI client instance
    generate_streaming_response,
    generate_streaming_introduction,
    provide_interaction_assistance,
    augment_system_lists
)
# --- End LLM Streaming Imports ---

# --- Constants and Setup ---
logger = logging.getLogger(__name__) # Get logger for this module
custom_llm = Blueprint('custom_llm', __name__)

# Load Atomic Habits keywords safely
try:
    # Ensure the path is relative to the project root where app.py runs
    df = pd.read_csv('data/ah_index.csv')
    atomic_habits_concept = df['concept'].tolist()
    atomic_habits_words = df['word'].tolist()
    atomic_habits_keywords = atomic_habits_concept + atomic_habits_words
    logger.info("Atomic Habits keywords loaded successfully.")
except FileNotFoundError:
    logger.error("data/ah_index.csv not found. RAG classification for Atomic Habits may fail.")
    atomic_habits_keywords = []
except Exception as e:
    logger.error(f"Error loading data/ah_index.csv: {e}", exc_info=True)
    atomic_habits_keywords = []


# Initialize Pinecone indexes (ensure pinecone_rag handles initialization)
try:
    user_index = pinecone_rag.user_index
    book_index = pinecone_rag.book_index
    if user_index and book_index:
        logger.info("Pinecone indexes obtained from rag module.")
    else:
         logger.warning("One or both Pinecone indexes (user_index, book_index) are None in pinecone_rag.")
except AttributeError:
    logger.error("Could not find user_index or book_index in app.rag.pinecone_rag. RAG will fail.")
    user_index = None
    book_index = None
except Exception as e:
    logger.error(f"Error initializing Pinecone indexes: {e}", exc_info=True)
    user_index = None
    book_index = None


# Define default preferences (used if DB fetch fails or no prefs set)
DEFAULT_PREFERENCES = {
    "speaking_rate": "normal",
    "interaction_style": "friendly",
    "explanation_detail_level": "standard",
    "discussion_depth": "moderate",
    "learning_style": "visual",
    "reading_pace": "normal",
    "preferred_complexity_level": "medium",
    "preferred_interaction_frequency": "regular"
}
# --- End Constants and Setup ---

# ==============================================================================
# --- Authentication Route ---
# ==============================================================================
@custom_llm.route('/token', methods=['POST'])
def generate_token():
    """
    Gets user info from request, ensures user exists in Supabase (creates/updates profile),
    caches preferences, and returns JWT token with Supabase UUID.
    """
    # --- Extract ALL relevant fields from request ---
    username = request.json.get('username') # Derived from given_name/name etc. in frontend
    email = request.json.get('email')
    picture = request.json.get('picture')
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    email_verified = request.json.get('email_verified')
    auth0_sub = request.json.get('auth0_sub') # Optional Auth0 ID
    # --- End Extraction ---

    if not email or not username:
        logger.warning("Token request missing username or email.")
        return jsonify({"error": "Username and email are required."}), 400

    cache = current_app.extensions.get('cache')
    if not cache: logger.warning("Cache unavailable in /token. Proceeding without caching.")

    supabase_user_id = None
    try:
        # Prepare details dict to pass to db function
        user_details = {
            'username': username,
            'email': email,
            'picture': picture,
            'first_name': first_name,
            'last_name': last_name,
            'email_verified': email_verified,
            'auth0_sub': auth0_sub,
            # Include defaults for profile fields IF creating for first time
            # create_supabase_user handles defaults internally now for profile part
            'current_bg': 'black',
            'character': {
                 'name': '', 'alias': '', 'super_skill': None, 'weakness': '',
                 'powers': [], 'equipments': [], 'height': '', 'age': 0,
                 'birthplace': ''
            }
        }

        # Check existence and create/update user and profile in one go
        # create_supabase_user now handles both cases:
        # - If user doesn't exist -> Creates user, creates profile, returns NEW ID
        # - If user exists -> Updates user (if needed), updates profile (upsert), returns EXISTING ID
        supabase_user_id = create_supabase_user(user_details)

        if not supabase_user_id:
            # create_supabase_user logs specific reasons (duplicate username/email, DB error)
            logger.error(f"Failed to get or create Supabase user for {email}.")
            return jsonify({"error": "User processing failed."}), 500
        logger.info(f" Ensured Supabase user exists for {email} with ID: {supabase_user_id}")

        # --- Fetch and Cache Preferences ---
        user_prefs = None
        cache_key = f"user_prefs_{supabase_user_id}"
        if cache:
            try: user_prefs = cache.get(cache_key)
            except Exception as ce: logger.error(f"Cache get failed: {ce}"); user_prefs = None

        if user_prefs is None:
            logger.info(f"Cache miss/unavailable for {supabase_user_id}. Fetching prefs.")
            user_prefs = get_user_preferences_from_db(supabase_user_id)
            if cache and user_prefs is not None:
                try: cache.set(cache_key, user_prefs or DEFAULT_PREFERENCES)
                except Exception as ce: logger.error(f"Cache set failed: {ce}")
            elif not user_prefs: logger.warning(f"DB pref fetch failed for {supabase_user_id}.")
        else: logger.info(f"Cache hit for {supabase_user_id}.")
        # --- End Fetch and Cache ---

        # Create the access token using the retrieved/created Supabase UUID
        access_token = create_access_token(identity=supabase_user_id)
        return jsonify(access_token=access_token, success=True)

    except Exception as e:
         logger.error(f"Token generation error for {email}: {e}", exc_info=True)
         return jsonify({"error": "Token generation failed."}), 500
# ==============================================================================

# ==============================================================================
# --- User Profile Route ---
# ==============================================================================
@custom_llm.route('/user')
@jwt_required()
def get_user_profile():
    """Gets combined user and profile data from Supabase using JWT identity."""
    try:
        supabase_user_uuid = get_jwt_identity() # This is the Supabase UUID
        if not supabase_user_uuid:
             logger.error("JWT identity (user_id) missing after @jwt_required.")
             return jsonify({"error": "Authentication identity missing."}), 401

        logger.info(f"Fetching profile for Supabase user ID: {supabase_user_uuid}")
        user_data = get_supabase_user_data_by_id(supabase_user_uuid)

        if not user_data:
             logger.warning(f"User profile not found for Supabase ID: {supabase_user_uuid}")
             return jsonify({"error": "User profile not found."}), 404

        # Data should already be in dictionary format
        logger.debug(f"Returning user data for {supabase_user_uuid}")
        return jsonify(user=user_data, success=True)

    except Exception as e:
        # Log the specific exception
        logger.error(f"Error fetching user profile for ID {get_jwt_identity()}: {e}", exc_info=True)
        # Avoid exposing internal details in production
        return jsonify({"error": "Failed to retrieve user profile due to an internal server error."}), 500
# ==============================================================================

# ==============================================================================
# --- User Setting Update Route ---
# ==============================================================================
@custom_llm.route('/color', methods=['POST'])
@jwt_required()
def update_user_color():
    """Updates the user's background color setting in Supabase user_profiles."""
    supabase_user_uuid = get_jwt_identity()
    if not supabase_user_uuid: return jsonify({"error": "Authentication identity missing."}), 401

    color = request.json.get('color')
    if not color or not isinstance(color, str):
        logger.warning(f"Color update request missing/invalid color value for user {supabase_user_uuid}")
        return jsonify({"error": "Valid color value is required."}), 400

    # Access cache via extensions
    cache = current_app.extensions.get('cache')

    logger.info(f"Updating 'current_bg' to '{color}' for Supabase user ID: {supabase_user_uuid}")
    try:
        success = update_user_setting(supabase_user_uuid, 'current_bg', color)
        if not success:
             logger.error(f"Failed to update color setting in DB for user {supabase_user_uuid}.")
             return jsonify({"error": "Failed to update color setting."}), 500

        # --- Invalidate Cache ---
        if cache: # Check if cache object is valid
            try:
                cache_key = f"user_prefs_{supabase_user_uuid}"
                cache.delete(cache_key)
                logger.info(f"Invalidated preferences cache for user {supabase_user_uuid} after color update.")
            except Exception as cache_err:
                logger.error(f"Failed to invalidate cache key {cache_key} after color update: {cache_err}")
        else:
            logger.warning("Cache not available, skipping cache invalidation for color update.")
        # --- End Invalidate Cache ---

        return jsonify(success=True)
    except Exception as e:
        logger.error(f"Error processing color update for user {supabase_user_uuid}: {e}", exc_info=True)
        return jsonify({"error": "Failed to update color setting due to an internal server error."}), 500
# ==============================================================================

# ==============================================================================
# --- User Character Update Route ---
# ==============================================================================
@custom_llm.route('/character', methods=['POST'])
@jwt_required()
def update_user_character():
    """Updates character details in the user_profiles JSONB column via Supabase."""
    supabase_user_uuid = get_jwt_identity()
    if not supabase_user_uuid: return jsonify({"error": "Authentication identity missing."}), 401

    key = request.json.get('key')
    value = request.json.get('value') # Value can be string, number, boolean, list item, etc.

    if not key or not isinstance(key, str):
        logger.warning(f"Character update request missing/invalid key for user {supabase_user_uuid}")
        return jsonify({"error": "Valid key is required for character update."}), 400

    # Access cache via extensions
    cache = current_app.extensions.get('cache')

    logger.info(f"Updating character field '{key}' for Supabase user ID: {supabase_user_uuid}")
    try:
        success = update_user_character_detail(supabase_user_uuid, key, value)
        if not success:
             logger.error(f"Failed to update character detail '{key}' in DB for user {supabase_user_uuid}.")
             return jsonify({"error": "Failed to update character detail."}), 500

        # --- Invalidate Cache ---
        if cache: # Check if cache object is valid
            try:
                cache_key = f"user_prefs_{supabase_user_uuid}"
                cache.delete(cache_key)
                logger.info(f"Invalidated preferences cache for user {supabase_user_uuid} after character update.")
            except Exception as cache_err:
                 logger.error(f"Failed to invalidate cache key {cache_key} after character update: {cache_err}")
        else:
             logger.warning("Cache not available, skipping cache invalidation for character update.")
        # --- End Invalidate Cache ---

        return jsonify(success=True)
    except Exception as e:
        logger.error(f"Error processing character update for user {supabase_user_uuid}: {e}", exc_info=True)
        return jsonify({"error": "Failed to update character detail due to an internal server error."}), 500
# ==============================================================================


# ==============================================================================
# --- Chat Completions Route ---
# ==============================================================================

@custom_llm.route('/chat/completions', methods=['POST'])
def openai_advanced_chat_completions_route_new():
    """
    Handle POST requests for OpenAI chat completions, incorporating user context,
    preferences (cached), RAG results, and streaming capability.
    Logs detailed information about the LLM request context.
    """
    logger.info("Received request for /chat/completions")
    request_data = request.get_json()
    if not request_data:
        logger.error("No JSON data provided in chat request.")
        return jsonify({"error": "No JSON data provided"}), 400

    # --- Metadata and Authentication ---
    # Extract data assuming OpenAI-like structure + metadata Vapi sends
    messages_from_request = request_data.get("messages", [])
    tools_from_request = request_data.get("tools")
    model_name_from_request = request_data.get("model", "gpt-4o")
    stream_flag = request_data.get("stream", True)
    temperature_from_request = request_data.get("temperature", 0.7)
    max_tokens_from_request = request_data.get("max_tokens")

    # Extract call_id and token from the 'call.assistantOverrides.metadata' structure
    token = None
    call_id = None
    try:
        call_object = request_data.get("call", {})
        if isinstance(call_object, dict):
            call_id = call_object.get("id")
            assistant_overrides = call_object.get("assistantOverrides", {})
            if isinstance(assistant_overrides, dict):
                metadata_object = assistant_overrides.get("metadata", {})
                if isinstance(metadata_object, dict):
                    token = metadata_object.get("token")
    except Exception as e:
        logger.error(f"Error parsing call_id or token from request_data: {e}", exc_info=True)

    if not call_id:
        logger.error("'call.id' not found in request payload.")
        logger.debug(f"Received request keys for /chat/completions: {list(request_data.keys())}")
        return jsonify({"error": "call_id is required in the request payload."}), 400
    if not token:
        logger.warning("JWT token not found in request payload at call.assistantOverrides.metadata.token.")
        return jsonify({"error": "Authentication token not found in expected location."}), 401

    # Access cache via Flask's application context's extensions registry
    cache = current_app.extensions.get('cache')
    if not cache:
        logger.warning("Cache unavailable in /chat/completions (current_app.extensions['cache'] is None). Proceeding without preference caching.")

    try:
        # Decode token to get Supabase User UUID
        decoded = decode_token(token)
        user_id = decoded['sub'] # This is the Supabase UUID string
        logger.info(f"Authenticated Supabase user ID for chat: {user_id}")
    except Exception as e:
        logger.error(f"Invalid JWT provided in chat request: {str(e)}")
        return jsonify({"error": "Invalid or expired token."}), 401
    # --- End Authentication ---

    try:
        # --- Generate Session Hash ---
        session_id_hash = generate_session_hash(call_id, user_id)
        if not session_id_hash:
            logger.error(f"Failed to generate session hash for call {call_id}, user {user_id}")
            return jsonify({"error": "Failed to generate session identifier."}), 500
        logger.info(f"Using session hash for chat: {session_id_hash[:8]}...")
        # --- End Session Hash ---

        # --- Retrieve Context and CACHED Preferences ---
        try:
            llm_context = get_llm_context_from_session(session_id_hash, max_turns=5)
        except Exception as context_err:
            logger.error(f"Error fetching LLM context for session {session_id_hash}: {context_err}", exc_info=True)
            llm_context = "Error retrieving past interactions." # Fallback

        user_preferences = None
        cache_key = f"user_prefs_{user_id}"
        if cache:
            try:
                user_preferences = cache.get(cache_key)
                if user_preferences is not None: logger.info(f"Preferences cache HIT for {user_id}")
            except Exception as cache_err:
                logger.error(f"Error getting from cache for user {user_id}: {cache_err}")
                user_preferences = None # Treat as miss

        if user_preferences is None:
            log_msg = f"Preferences cache MISS for user {user_id}."
            if not cache: log_msg = "Cache unavailable."
            logger.info(f"{log_msg} Fetching fallback.")
            user_preferences = get_user_preferences_from_db(user_id)
            if cache and user_preferences is not None:
                 try:
                     cache.set(cache_key, user_preferences or DEFAULT_PREFERENCES)
                     logger.info(f"Cached preferences for user {user_id} after fallback fetch.")
                 except Exception as cache_err: logger.error(f"Error setting cache for user {user_id} after fallback: {cache_err}")
            elif not user_preferences: logger.warning(f"Fallback preference fetch failed for user {user_id}. Using defaults.")

        user_preferences = user_preferences or DEFAULT_PREFERENCES
        logger.debug(f"Using preferences for chat: {user_preferences}")
        # --- End Context/Preferences Retrieval ---

        # --- Process Messages & RAG ---
        if not messages_from_request: return jsonify({"error": "Messages field required."}), 400
        last_message_from_request = messages_from_request[-1]
        query_string = last_message_from_request.get('content', '') if isinstance(last_message_from_request, dict) else ''
        if not query_string: return jsonify({"error": "Last message has no content or is malformed."}), 400

        if query_string.lower() in ["help", "what can i ask?"]:
            assistance_text = provide_interaction_assistance()
            return Response(generate_streaming_introduction(assistance_text), content_type='text/event-stream')

        book_contexts = []
        if user_index and book_index and atomic_habits_keywords:
            try:
                classification_result = pinecone_rag.classify(query_string, atomic_habits_keywords)
                classification_label = classification_result.label
                logger.info(f"RAG classification for query: {classification_label}")
                if classification_label == "PERSONAL":
                    res = pinecone_rag.query_pinecone_user(query_string, user_index, top_k=1, namespace='user-data-openai-embedding')
                    if res and res.get('matches'): book_contexts.extend([x.get('metadata', {}).get('text', '') for x in res['matches']])
                elif classification_label == "ATOMIC_HABITS":
                    context_strings = pinecone_rag.query_pinecone_book(query_string, top_k=1, namespace='ah-test')
                    book_contexts.extend(context_strings)
                logger.debug(f"Retrieved {len(book_contexts)} RAG context snippets.")
            except Exception as rag_e:
                logger.error(f"Error during RAG query: {rag_e}", exc_info=True)
                book_contexts = []
        else:
            logger.warning("RAG components not available. Skipping RAG query.")
        # --- End Process Messages & RAG ---

        # --- Prepare Prompt for LLM ---
        base_system_prompt = (
            "You are a helpful assistant knowledgeable about Atomic Habits. "
            "Tailor your responses based on the user's preferences and past conversation history provided below. "
            "Avoid using special characters like #,*,&,^,%,$,! unless part of necessary code or examples."
        )
        try:
            prefs_to_serialize = {k: str(v) for k, v in user_preferences.items()}
            prefs_json = json.dumps(prefs_to_serialize)
        except TypeError:
            logger.warning("Could not serialize user preferences to JSON. Using raw dict string.")
            prefs_json = str(user_preferences)
            
        system_message_content_with_prefs = f"{base_system_prompt}\nUser Preferences: {prefs_json}"

        # Build conversation history for LLM
        # Start with the system prompt containing preferences
        conversation_for_llm = [{"role": "system", "content": system_message_content_with_prefs}]

        # Add message history from request, ensuring structure is correct
        valid_messages = [msg for msg in messages_from_request if isinstance(msg, dict) and 'role' in msg and 'content' in msg]
        conversation_for_llm.extend(valid_messages)

        # Combine and potentially truncate RAG + LLM history context
        all_context_parts = [ctx for ctx in book_contexts + [llm_context] if ctx and ctx.strip()]
        combined_context_for_llm = "\n---\n".join(all_context_parts) if all_context_parts else "No additional context available."
        MAX_CONTEXT_LEN = 3000
        if len(combined_context_for_llm) > MAX_CONTEXT_LEN:
             logger.warning(f"Combined context length ({len(combined_context_for_llm)}) exceeds limit {MAX_CONTEXT_LEN}, truncating.")
             combined_context_for_llm = "... (truncated) ..." + combined_context_for_llm[-MAX_CONTEXT_LEN:]

        # Inject this combined context as a new system message before the final user query
        # or after the initial system prompt with preferences.
        context_injection_message = {"role": "system", "content": f"Relevant Context for the current query:\n{combined_context_for_llm}"}

        # Find the index of the last user message to insert context before it,
        # OR insert after the first system message. For simplicity, let's insert after the first system message.
        if len(conversation_for_llm) > 1: # If there's more than just the initial system prompt
            conversation_for_llm.insert(1, context_injection_message)
        else: # Only initial system prompt exists, append context then re-append user query if any
            conversation_for_llm.append(context_injection_message)
            # Re-ensure the last message is the user's actual query if valid_messages wasn't empty
            if valid_messages and valid_messages[-1]['role'] == 'user':
                if conversation_for_llm[-1] != valid_messages[-1]:
                    conversation_for_llm.append(valid_messages[-1])
            elif not valid_messages: # Should have been caught by "Messages field required"
                 logger.error("Logic error: No valid messages from request to construct LLM prompt.")
                 return jsonify({"error": "Internal error constructing LLM prompt."}), 500

        # --- DETAILED LOGGING OF LLM REQUEST ---
        logger.info("--- Preparing LLM Request ---")
        logger.info(f"Target Model: {model_name_from_request}")
        logger.info("Messages being sent to LLM:")
        for i, msg_llm in enumerate(conversation_for_llm):
            role_llm = msg_llm.get('role', 'unknown_role')
            content_llm = msg_llm.get('content', '')
            content_preview_llm = (content_llm[:200] + '...') if len(content_llm) > 203 else content_llm
            logger.info(f"  MSG {i+1} | ROLE: {role_llm} | CONTENT PREVIEW: {content_preview_llm.replace(os.linesep, ' ')}")
            # Uncomment to log full content of specific messages for deeper debugging:
            if "Relevant Context" in content_llm:
                logger.debug(f"    FULL CONTEXT CONTENT:\n{content_llm}")
            if "User Preferences" in content_llm:
                logger.debug(f"    FULL PREFERENCES CONTENT:\n{content_llm}")

        # if tools_from_request:
        #     logger.info(f"Tools for LLM: {json.dumps(tools_from_request, indent=2)}")
        logger.info(f"Temperature: {temperature_from_request}")
        logger.info(f"Stream: {stream_flag}")
        if max_tokens_from_request: logger.info(f"Max Tokens: {max_tokens_from_request}")
        logger.info("--- End LLM Request Preparation ---")
        # --- END DETAILED LOGGING ---

        # --- Prepare and Call LLM ---
        llm_request_data = {
            "model": model_name_from_request,
            "messages": conversation_for_llm,
            "temperature": temperature_from_request,
            "stream": stream_flag,
        }
        if max_tokens_from_request: llm_request_data["max_tokens"] = max_tokens_from_request
        if tools_from_request: llm_request_data["tools"] = tools_from_request

        if not client_openai:
             logger.error("OpenAI client (client_openai) is not initialized.")
             return jsonify({"error": "LLM client not configured."}), 500

        if stream_flag:
            try:
                chat_completion_stream = client_openai.chat.completions.create(**llm_request_data)
                return Response(generate_streaming_response(chat_completion_stream), content_type='text/event-stream')
            except Exception as llm_err:
                 logger.error(f"Error during LLM streaming call: {llm_err}", exc_info=True)
                 return jsonify({"error": "Failed to get streaming response from LLM."}), 500
        else:
            try:
                chat_completion = client_openai.chat.completions.create(**llm_request_data)
                return Response(chat_completion.model_dump_json(indent=2), content_type='application/json')
            except Exception as llm_err:
                logger.error(f"Error during LLM non-streaming call: {llm_err}", exc_info=True)
                return jsonify({"error": "Failed to get response from LLM."}), 500
        # --- End Call LLM ---

    # --- Error Handling ---
    except ValidationError as ve:
        logger.error(f"Pydantic Validation Error in chat: {str(ve)}")
        return jsonify({"error": f"Invalid data structure: {ve}"}), 400
    except ValueError as ve:
        logger.error(f"ValueError processing chat completion request: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in chat completions route: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected internal error occurred processing the chat request."}), 500

# @custom_llm.route('/chat/completions', methods=['POST'])
# def openai_advanced_chat_completions_route_new():
#     """
#     Handle POST requests for OpenAI chat completions, incorporating user context,
#     preferences (cached), RAG results, and streaming capability.
#     """
#     request_data = request.get_json()
#     print(request_data)
#     if not request_data:
#         logger.error("No JSON data provided in chat request.")
#         return jsonify({"error": "No JSON data provided"}), 400

#     # --- Metadata and Authentication ---
#     metadata = request_data.get("metadata", {})
#     token = metadata.get("token", None)
#     call_id = request_data.get("call", {}).get("id") # VAPI Call ID expected here

#     if not call_id:
#         logger.error("'call_id' not found in request metadata.")
#         return jsonify({"error": "call_id is required in metadata."}), 400
#     if not token:
#         logger.warning("JWT token not provided in chat request metadata.")
#         return jsonify({"error": "Authentication token not provided."}), 401

#     # Access cache via extensions
#     cache = current_app.extensions.get('cache')
#     if not cache:
#         logger.error("Cache unavailable in /chat/completions (current_app.extensions['cache'] is None). Check app setup.")
#         # Proceeding without cache, fallback will trigger DB read.

#     try:
#         # Decode token to get Supabase User UUID
#         decoded = decode_token(token)
#         user_id = decoded['sub'] # This is the Supabase UUID string
#         logger.info(f"Authenticated Supabase user ID for chat: {user_id}")
#     except Exception as e:
#         logger.error(f"Invalid JWT provided in chat request: {str(e)}")
#         return jsonify({"error": "Invalid or expired token."}), 401
#     # --- End Authentication ---

#     try:
#         # --- Generate Session Hash ---
#         session_id_hash = generate_session_hash(call_id, user_id)
#         if not session_id_hash:
#             logger.error(f"Failed to generate session hash for call {call_id}, user {user_id}")
#             return jsonify({"error": "Failed to generate session identifier."}), 500
#         logger.info(f"Using session hash for chat: {session_id_hash[:8]}...")
#         # --- End Session Hash ---

#         # --- Retrieve Context and CACHED Preferences ---
#         try:
#             # Fetch recent interaction history for context
#             llm_context = get_llm_context_from_session(session_id_hash, max_turns=5)
#         except Exception as context_err:
#             logger.error(f"Error fetching LLM context for session {session_id_hash}: {context_err}", exc_info=True)
#             llm_context = "Error retrieving past interactions." # Fallback context

#         # Get preferences FROM CACHE
#         user_preferences = None
#         cache_key = f"user_prefs_{user_id}"
#         if cache: # Check if cache object exists and is usable
#             try:
#                 user_preferences = cache.get(cache_key)
#                 if user_preferences is not None: logger.info(f"Preferences cache HIT for {user_id}")
#             except Exception as cache_err:
#                 logger.error(f"Error getting from cache for user {user_id}: {cache_err}")
#                 user_preferences = None # Treat as miss

#         if user_preferences is None: # Cache miss or error or cache unavailable
#             log_msg = f"Preferences cache MISS for user {user_id}."
#             if not cache: log_msg = "Cache unavailable."
#             logger.info(f"{log_msg} Fetching fallback.")

#             # Fallback: Fetch directly from DB
#             user_preferences = get_user_preferences_from_db(user_id)
#             if cache and user_preferences is not None: # Cache if fetch worked AND cache exists
#                  try:
#                      # Cache the retrieved prefs OR the defaults if DB returned nothing/error
#                      cache.set(cache_key, user_preferences or DEFAULT_PREFERENCES)
#                      logger.info(f"Cached preferences for user {user_id} after fallback fetch.")
#                  except Exception as cache_err:
#                      logger.error(f"Error setting cache for user {user_id} after fallback: {cache_err}")
#             elif not user_preferences:
#                  logger.warning(f"Fallback preference fetch failed for user {user_id}. Using defaults.")

#         # Ensure user_preferences is a dict, using defaults as final fallback
#         user_preferences = user_preferences or DEFAULT_PREFERENCES
#         logger.debug(f"Using preferences for chat: {user_preferences}")
#         # --- End Context/Preferences Retrieval ---

#         # --- Process Messages & RAG ---
#         messages = request_data.get("messages", [])
#         tools = request_data.get("tools")
#         # Safely access nested model config
#         model_config = request_data.get("assistant", {}).get("model", {}).get("model")
#         if not isinstance(model_config, dict): model_config = {}
#         # Safely access streaming flag
#         stream = request_data.get("stream", True)

#         if not messages: return jsonify({"error": "Messages field is required."}), 400
#         # Ensure the last message has content
#         last_message = messages[-1]
#         query_string = last_message.get('content', '') if isinstance(last_message, dict) else ''
#         if not query_string: return jsonify({"error": "Last message has no content or is malformed."}), 400

#         # Handle help request
#         if query_string.lower() in ["help", "what can i ask?"]:
#             assistance_text = provide_interaction_assistance()
#             return Response(generate_streaming_introduction(assistance_text), content_type='text/event-stream')

#         # RAG Queries
#         book_contexts = []
#         if user_index and book_index and atomic_habits_keywords: # Check if RAG components are ready
#             try:
#                 classification_result = pinecone_rag.classify(query_string, atomic_habits_keywords)
#                 classification_label = classification_result.label
#                 logger.info(f"RAG classification for query: {classification_label}")
#                 if classification_label == "PERSONAL":
#                     res = pinecone_rag.query_pinecone_user(query_string, user_index, top_k=1, namespace='user-data-openai-embedding')
#                     if res and res.get('matches'): book_contexts.extend([x.get('metadata', {}).get('text', '') for x in res['matches']])
#                 elif classification_label == "ATOMIC_HABITS":
#                     context_strings = pinecone_rag.query_pinecone_book(query_string, top_k=1, namespace='ah-test')
#                     book_contexts.extend(context_strings)
#                 logger.debug(f"Retrieved {len(book_contexts)} RAG context snippets.")
#             except Exception as rag_e:
#                 logger.error(f"Error during RAG query: {rag_e}", exc_info=True)
#                 book_contexts = [] # Proceed without RAG context
#         else:
#             logger.warning("RAG components not available. Skipping RAG query.")
#         # --- End Process Messages & RAG ---

#         # --- Prepare Prompt for LLM ---
#         base_system_prompt = (
#             "You are a helpful assistant knowledgeable about Atomic Habits. "
#             "Tailor your responses based on the user's preferences and past conversation history provided below. "
#             "Avoid using special characters like #,*,&,^,%,$,! unless part of necessary code or examples."
#         )
#         try:
#             # Ensure preferences is serializable - convert values to string
#             prefs_to_serialize = {k: str(v) for k, v in user_preferences.items()}
#             prefs_json = json.dumps(prefs_to_serialize)
#         except TypeError:
#             logger.warning("Could not serialize user preferences to JSON. Using raw dict string.")
#             prefs_json = str(user_preferences) # Fallback
#         system_message_content = f"{base_system_prompt}\nUser Preferences: {prefs_json}"

#         # Build conversation history for LLM
#         conversation = [{"role": "system", "content": system_message_content}]
#         # Add message history from request, ensuring structure is correct
#         valid_messages = [msg for msg in messages if isinstance(msg, dict) and 'role' in msg and 'content' in msg]
#         conversation.extend(valid_messages)

#         # Combine and potentially truncate context
#         all_context_parts = [ctx for ctx in book_contexts + [llm_context] if ctx and ctx.strip()]
#         combined_context = "\n---\n".join(all_context_parts) if all_context_parts else "No additional context available."
#         MAX_CONTEXT_LEN = 3000 # Example limit - adjust as needed
#         if len(combined_context) > MAX_CONTEXT_LEN:
#              logger.warning(f"Combined context length ({len(combined_context)}) exceeds limit {MAX_CONTEXT_LEN}, truncating.")
#              combined_context = "... (truncated) ..." + combined_context[-MAX_CONTEXT_LEN:]

#         # Inject context as a system message before the last user message (or append)
#         context_injection_message = {"role": "system", "content": f"Relevant Context:\n{combined_context}"}
#         # Find the index of the last user message to insert context before it
#         last_user_msg_index = -1
#         for i in range(len(conversation) - 1, -1, -1):
#             if conversation[i].get('role') == 'user':
#                 last_user_msg_index = i
#                 break

#         if last_user_msg_index != -1:
#              conversation.insert(last_user_msg_index, context_injection_message)
#         else:
#              # Append if no user message found (shouldn't normally happen with valid input)
#              conversation.append(context_injection_message)
#              logger.warning("No user message found in conversation history; appending context at the end.")

#         # --- End Prompt Preparation ---

#         # --- Prepare and Call LLM ---
#         llm_request_data = {
#             "model": model_config.get("model", "gpt-4o"),
#             "messages": conversation,
#             "temperature": model_config.get("temperature", 0.7),
#             "stream": stream,
#         }
#         # Add tools only if they exist and are not empty
#         if tools:
#             llm_request_data["tools"] = tools
#             # llm_request_data["tool_choice"] = "auto" # Or specific choice if needed

#         logger.info(f"Sending request to LLM: Model={llm_request_data['model']}, Stream={stream}, NumMessages={len(conversation)}")
#         # logger.debug(f"LLM Payload Messages: {json.dumps(conversation)}") # Use caution logging PII/large data

#         # Ensure OpenAI client is available
#         if not client_openai:
#              logger.error("OpenAI client (client_openai) is not initialized.")
#              return jsonify({"error": "LLM client not configured."}), 500

#         if stream:
#             # Generate streaming response
#             try:
#                 chat_completion_stream = client_openai.chat.completions.create(**llm_request_data)
#                 return Response(generate_streaming_response(chat_completion_stream), content_type='text/event-stream')
#             except Exception as llm_err:
#                  logger.error(f"Error during LLM streaming call: {llm_err}", exc_info=True)
#                  return jsonify({"error": "Failed to get streaming response from LLM."}), 500
#         else:
#             # Generate non-streaming response
#             try:
#                 chat_completion = client_openai.chat.completions.create(**llm_request_data)
#                 # Use model_dump_json() for Pydantic v2 objects from openai>=1.0
#                 return Response(chat_completion.model_dump_json(indent=2), content_type='application/json')
#             except Exception as llm_err:
#                 logger.error(f"Error during LLM non-streaming call: {llm_err}", exc_info=True)
#                 return jsonify({"error": "Failed to get response from LLM."}), 500
#         # --- End Call LLM ---

#     # --- Error Handling ---
#     except ValidationError as ve: # Catch Pydantic validation errors if models were used
#         logger.error(f"Pydantic Validation Error: {str(ve)}")
#         return jsonify({"error": f"Invalid data structure: {ve}"}), 400
#     except ValueError as ve: # Catch other value errors
#         logger.error(f"ValueError processing chat completion request: {str(ve)}")
#         return jsonify({"error": str(ve)}), 400
#     except Exception as e:
#         # Catch-all for any other unexpected errors during processing
#         logger.error(f"Unexpected error in chat completions route: {str(e)}", exc_info=True)
#         return jsonify({"error": "An unexpected internal error occurred processing the chat request."}), 500
# ==============================================================================