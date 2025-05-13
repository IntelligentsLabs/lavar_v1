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
    Handle POST requests from Vapi (structured like OpenAI API + call/assistant info)
    for chat completions with personalization and RAG.
    Logs detailed information about the LLM request context.
    """
    logger.info("Received request for /chat/completions")
    request_data = request.get_json()
    if not request_data:
        logger.error("No JSON data provided in chat request.")
        return jsonify({"error": "No JSON data provided"}), 400

    # --- Extract data assuming Vapi sends OpenAI-like structure for main LLM call ---
    # and additional Vapi-specific context in 'call' and 'metadata' (passed by you).
    messages_from_vapi_request = request_data.get("messages", [])
    tools_from_vapi_request = request_data.get("tools")
    model_name_from_vapi_request = request_data.get("model", "gpt-4o") # Model requested by Vapi for this turn
    stream_flag_from_vapi_request = request_data.get("stream", True)
    temperature_from_vapi_request = request_data.get("temperature", 0.7)
    max_tokens_from_vapi_request = request_data.get("max_tokens")

    # --- Extract Vapi Call ID and Your Custom Metadata (including JWT Token) ---
    token = None
    call_id = None
    user_data_from_vapi_metadata = {} # Store user data from Vapi metadata if needed

    # The Vapi request payload (as printed) shows 'call' and 'metadata' at the top level.
    # Your custom token and user data seem to be nested within call.assistantOverrides.metadata
    # AND also potentially at request_data.metadata (from your Vapi assistant setup).
    # Let's prioritize the one from request_data.metadata if you set it up.
    # If not, we try the one nested under request_data.call.assistantOverrides.metadata.

    top_level_metadata = request_data.get("metadata", {})
    if isinstance(top_level_metadata, dict):
        token = top_level_metadata.get("token")
        call_id = top_level_metadata.get("call_id") # Assuming you pass call_id in top-level metadata
        user_data_from_vapi_metadata = top_level_metadata.get("data", {}).get("user", {})


    # Fallback or primary: Check within the 'call' object structure Vapi sends
    if not call_id: # If not found in top-level metadata
        call_object_from_vapi = request_data.get("call", {})
        if isinstance(call_object_from_vapi, dict):
            call_id = call_object_from_vapi.get("id")
            if not token: # If token wasn't in top-level metadata
                try:
                    token = call_object_from_vapi.get("assistantOverrides", {}) \
                                                .get("metadata", {}) \
                                                .get("token")
                    if not user_data_from_vapi_metadata: # If user data wasn't in top-level metadata
                         user_data_from_vapi_metadata = call_object_from_vapi.get("assistantOverrides", {}) \
                                                                    .get("metadata", {}) \
                                                                    .get("data", {}).get("user", {})
                except AttributeError:
                    logger.warning("Error accessing token/user_data from call.assistantOverrides.metadata")


    if not call_id:
        logger.error("'call_id' not found in request payload or expected metadata.")
        logger.debug(f"Received request keys for /chat/completions: {list(request_data.keys())}")
        return jsonify({"error": "call_id is required."}), 400
    if not token:
        logger.warning("JWT token not found in request payload.")
        return jsonify({"error": "Authentication token not found."}), 401

    # Access cache
    cache = current_app.extensions.get('cache')
    if not cache:
        logger.warning("Cache unavailable in /chat/completions. Proceeding without preference caching for this request.")

    try:
        # Decode token to get Supabase User UUID
        decoded = decode_token(token)
        user_id = decoded['sub'] # Supabase UUID string
        logger.info(f"Authenticated Supabase user ID for chat: {user_id}")
    except Exception as e:
        logger.error(f"Invalid JWT provided in chat request: {str(e)}")
        return jsonify({"error": "Invalid or expired token."}), 401
    # --- End Authentication & Core Data Extraction ---

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
            llm_context = "Error retrieving past interactions."

        user_preferences = None
        cache_key = f"user_prefs_{user_id}"
        if cache:
            try:
                user_preferences = cache.get(cache_key)
                if user_preferences is not None: logger.info(f"Preferences cache HIT for {user_id}")
            except Exception as cache_err:
                logger.error(f"Error getting from cache for user {user_id}: {cache_err}")
                user_preferences = None

        if user_preferences is None:
            log_msg = f"Preferences cache MISS for user {user_id}." if cache else "Cache unavailable."
            logger.info(f"{log_msg} Fetching fallback from DB.")
            user_preferences = get_user_preferences_from_db(user_id)
            if cache and user_preferences is not None:
                 try:
                     cache.set(cache_key, user_preferences or DEFAULT_PREFERENCES)
                     logger.info(f"Cached preferences for user {user_id} after fallback fetch.")
                 except Exception as cache_err: logger.error(f"Error setting cache for user {user_id} after fallback: {cache_err}")
            elif not user_preferences: logger.warning(f"Fallback preference fetch failed for user {user_id}. Using defaults.")

        user_preferences = user_preferences or DEFAULT_PREFERENCES
        logger.info(f"Using preferences for chat: {user_preferences}")
        # --- End Context/Preferences Retrieval ---

        # --- Process Messages & RAG ---
        if not messages_from_vapi_request: return jsonify({"error": "Messages field required."}), 400
        last_message_from_vapi = messages_from_vapi_request[-1]
        query_string = last_message_from_vapi.get('content', '') if isinstance(last_message_from_vapi, dict) else ''
        if not query_string and not last_message_from_vapi.get('tool_calls'): # Query can be empty if it's an assistant turn with tool_calls
             if not any(msg.get('tool_calls') for msg in messages_from_vapi_request if isinstance(msg, dict)): # Check if any message has tool_calls
                logger.warning("Last message has no content and no tool_calls found in history.")
                # Allow proceeding if there are tool_calls in the history Vapi sent
            # If it's a user message with no content, it might be an error state from Vapi or an empty user utterance
            # else: return jsonify({"error": "Last user message has no content."}), 400


        if query_string and query_string.lower() in ["help", "what can i ask?"]: # Handle help request
            assistance_text = provide_interaction_assistance()
            return Response(generate_streaming_introduction(assistance_text), content_type='text/event-stream')

        book_contexts = []
        if user_index and book_index and atomic_habits_keywords and query_string: # RAG only if there's a query string
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
        elif not query_string:
            logger.info("No query string for RAG (likely an assistant turn with tool_calls or tool_response). Skipping RAG.")
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
        system_message_with_prefs = {"role": "system", "content": f"{base_system_prompt}\nUser Preferences: {prefs_json}"}

        # Build conversation history for LLM
        conversation_for_llm = [system_message_with_prefs]

        # RAG and LLM History Context (from Letta/Supabase)
        all_context_parts = [ctx for ctx in book_contexts + [llm_context] if ctx and ctx.strip()]
        combined_context_for_llm = "\n---\n".join(all_context_parts) if all_context_parts else "No additional relevant context found."
        MAX_CONTEXT_LEN = 3000
        if len(combined_context_for_llm) > MAX_CONTEXT_LEN:
             logger.warning(f"Combined context length ({len(combined_context_for_llm)}) exceeds limit {MAX_CONTEXT_LEN}, truncating.")
             combined_context_for_llm = "... (truncated context) ..." + combined_context_for_llm[-MAX_CONTEXT_LEN + 25:] # Keep end part

        # Inject this combined context as a new system message
        context_injection_message = {"role": "system", 
                                     "content": f"Consider the following relevant context for the user's query:\n{combined_context_for_llm}"}
        conversation_for_llm.append(context_injection_message)

        # Add message history from Vapi's request AFTER your system prompts
        # This 'messages_from_vapi_request' should already be correctly formatted by Vapi
        # if it's managing tool calls and results. The OpenAI error indicates it might not be.
        # We pass it as is; if OpenAI errors, it's likely due to Vapi's structure for tool calls/results.
        valid_messages = [
            msg for msg in messages_from_vapi_request
            if isinstance(msg, dict) and 'role' in msg and ('content' in msg or 'tool_calls' in msg or 'tool_call_id' in msg)
        ]
        conversation_for_llm.extend(valid_messages)

        # --- DETAILED LOGGING OF LLM REQUEST ---
        logger.info("--- Preparing LLM Request ---")
        logger.info(f"Target Model: {model_name_from_vapi_request}")
        logger.info("Messages being sent to LLM:")
        for i, msg_llm in enumerate(conversation_for_llm):
            role_llm = msg_llm.get('role', 'unknown_role')
            content_llm = msg_llm.get('content', '')
            tool_calls_llm = msg_llm.get('tool_calls')
            tool_call_id_llm = msg_llm.get('tool_call_id')

            log_line = f"  MSG {i+1} | ROLE: {role_llm}"
            if content_llm is not None: # Content can be null for assistant tool calls
                content_preview_llm = (str(content_llm)[:150] + '...') if len(str(content_llm)) > 153 else str(content_llm)
                log_line += f" | CONTENT PREVIEW: {content_preview_llm.replace(os.linesep, ' ')}"
            if tool_calls_llm:
                log_line += f" | TOOL_CALLS: {json.dumps(tool_calls_llm)}"
            if tool_call_id_llm:
                log_line += f" | TOOL_CALL_ID: {tool_call_id_llm}"
            logger.info(log_line)

        if tools_from_vapi_request: logger.info(f"Tools for LLM: {json.dumps(tools_from_vapi_request, indent=2)}")
        logger.info(f"Temperature: {temperature_from_vapi_request}")
        logger.info(f"Stream: {stream_flag_from_vapi_request}")
        if max_tokens_from_vapi_request: logger.info(f"Max Tokens: {max_tokens_from_vapi_request}")
        logger.info("--- End LLM Request Preparation ---")
        # --- END DETAILED LOGGING ---

        # --- Prepare and Call LLM ---
        llm_request_data = {
            "model": model_name_from_vapi_request,
            "messages": conversation_for_llm,
            "temperature": temperature_from_vapi_request,
            "stream": stream_flag_from_vapi_request,
        }
        if max_tokens_from_vapi_request: llm_request_data["max_tokens"] = max_tokens_from_vapi_request
        if tools_from_vapi_request: llm_request_data["tools"] = tools_from_vapi_request

        if not client_openai:
             logger.error("OpenAI client (client_openai) is not initialized.")
             return jsonify({"error": "LLM client not configured."}), 500

        if stream_flag_from_vapi_request:
            try:
                chat_completion_stream = client_openai.chat.completions.create(**llm_request_data)
                return Response(generate_streaming_response(chat_completion_stream), content_type='text/event-stream')
            except Exception as llm_err:
                 logger.error(f"Error during LLM streaming call: {llm_err}", exc_info=True)
                 # Try to return the error message from OpenAI if available
                 error_detail = str(llm_err)
                 if hasattr(llm_err, 'response') and hasattr(llm_err.response, 'json'):
                     try: error_detail = llm_err.response.json()
                     except: pass
                 return jsonify({"error": "Failed to get streaming response from LLM.", "detail": error_detail}), 500
        else:
            try:
                chat_completion = client_openai.chat.completions.create(**llm_request_data)
                return Response(chat_completion.model_dump_json(indent=2), content_type='application/json')
            except Exception as llm_err:
                logger.error(f"Error during LLM non-streaming call: {llm_err}", exc_info=True)
                error_detail = str(llm_err)
                if hasattr(llm_err, 'response') and hasattr(llm_err.response, 'json'):
                     try: error_detail = llm_err.response.json()
                     except: pass
                return jsonify({"error": "Failed to get response from LLM.", "detail": error_detail}), 500
        # --- End Call LLM ---

    # --- Error Handling ---
    except ValidationError as ve:
        logger.error(f"Pydantic Validation Error in chat (should not happen with direct parsing): {str(ve)}")
        return jsonify({"error": f"Invalid data structure: {ve}"}), 400
    except ValueError as ve: # Catch other value errors
        logger.error(f"ValueError processing chat completion request: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        # Catch-all for any other unexpected errors during processing
        logger.error(f"Unexpected error in chat completions route: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected internal error occurred processing the chat request."}), 500
# ==============================================================================
