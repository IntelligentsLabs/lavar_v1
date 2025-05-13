# app/api/webhook.py
import logging
from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError
from typing import List, Optional, Dict, Any # Added Dict, Any
import os
from pathlib import Path
import asyncio
import json
# Removed sqlite3 as we are moving away from it for this handler's core logic

# --- Import the CORRECT Supabase function for getting user ID by email ---
# from app.api.supabase_db import get_supabase_user_id_by_email
from app.api.supabase_db import supabase, get_supabase_user_id_by_email
from app.vapi_message_handlers.conversation_update import ConversationUpdate
# --- ---

from app.api.supabase_db import (
    supabase, # If used directly for other things in this file, otherwise not strictly needed by this handler
    get_supabase_user_id_by_email, # Needed if user_id isn't passed directly to tool
    upsert_voice_agent_preferences,
    upsert_cognitive_preferences
)
# Import personalization functions (which now use Supabase)
from app.personalization.user_preferences import (
    get_or_create_voice_session,
    store_voice_interaction,
    update_session_end_time,
    generate_session_hash # Added for end-of-call-report example
)


# --- DEFINE LOGGER FOR THIS MODULE ---
logger = logging.getLogger(__name__)
# --- ---

# Initialize the Blueprint.
webhook = Blueprint('webhook', __name__)

# A dictionary to register tool handlers (if this pattern is still used elsewhere)
tool_handlers = {}

# --- Register Tool Handlers ---
def register_tool_handler(tool_name):
    def decorator(func):
        tool_handlers[tool_name] = func
        return func
    return decorator

# ... (init_database_directory, ensure_db_directory, store_in_database - keep if other tools use them) ...
# ... (webhook_route, extract_tool_calls, other handlers as before) ...

# --- NEW TOOL HANDLER for Updating Preferences ---
async def tool_call_handler(payload: Dict[str, Any]) -> Dict[str, Any]: # Vapi expects a single tool_results object for function-call
    """
    Generalized handler for processing 'function-call' or 'tool-calls' events from Vapi.
    Extracts tool call information, finds the Supabase user UUID,
    dispatches to the registered handler, and prepares the result for Vapi.
    Vapi's 'function-call' event sends a single 'functionCall' object.
    """
    logger.info(f"Processing tool_call_handler for payload type: {payload.get('type')}")

    # For Vapi's 'function-call' event type, the tool call is under 'functionCall'
    tool_call_data = payload.get('functionCall') 
    # If it were an OpenAI-style 'tool_calls' array, you'd iterate,
    # but Vapi's 'function-call' is singular.
    # tool_calls_list = payload.get('tool_calls', []) 

    if not tool_call_data or not isinstance(tool_call_data, dict):
        logger.error(f"Invalid or missing 'functionCall' data in payload: {str(payload)[:300]}")
        return {"toolCallResult": json.dumps({"status": "error", "message": "Invalid tool call structure in request."})}


    # --- Extract User Context (Supabase User UUID) ---
    # This is crucial for tools that operate on user-specific data, like preference updates.
    # Vapi's 'function-call' payload should still contain the 'call' object with metadata.
    call_context = payload.get('call', {})
    user_email_from_payload = None
    try:
        user_email_from_payload = call_context.get('assistantOverrides',{}).get('metadata',{}).get('data',{}).get('user',{}).get('email')
        if not user_email_from_payload and payload.get('assistant',{}).get('metadata'): # Fallback
            user_email_from_payload = payload.get('assistant',{}).get('metadata',{}).get('data',{}).get('user',{}).get('email')
    except Exception as e:
        logger.warning(f"Could not extract user_email for tool call context: {e}")

    supabase_user_uuid_for_tool = None
    if user_email_from_payload:
        supabase_user_uuid_for_tool = get_supabase_user_id_by_email(user_email_from_payload)

    if not supabase_user_uuid_for_tool:
        logger.warning(f"Could not determine Supabase user ID for tool call. Some tools may fail if they require user_id.")
        # For update_user_preferences_tool, this is a critical failure.


    # --- Process the single tool call from 'functionCall' ---
    # Vapi 'function-call' has `toolCallId` at the top level of the payload
    # and the function details under `functionCall`.
    tool_call_id_from_vapi = payload.get("toolCallId", 
                                         f"unknown_tool_call_{generate_session_hash(payload.get('call',{}).get('id','call'),                                                                         str(payload.get('timestamp','time')))[:8]}")

    function_details = tool_call_data # This is the content of 'functionCall'
    tool_name = function_details.get("name")
    arguments_str = function_details.get("arguments", "{}") # Arguments are a JSON string

    arguments_dict = {}
    try:
        arguments_dict = json.loads(arguments_str)
        logger.info(f"Executing tool: {tool_name} with ID: {tool_call_id_from_vapi}, Args: {arguments_dict}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in arguments for tool {tool_name}: {arguments_str}")
        tool_result_content = json.dumps({"status": "error", "message": "Invalid arguments format."})
        return {"toolCallResult": {"toolCallId": tool_call_id_from_vapi, "result": tool_result_content}}


    handler = tool_handlers.get(tool_name)
    tool_result_content = "" # This will be the JSON string content for the tool result

    if handler:
        try:
            # Prepare arguments for the specific handler
            handler_args = {"tool_call_id": tool_call_id_from_vapi} # Vapi expects this ID back

            if tool_name == "update_user_preferences_tool":
                if not supabase_user_uuid_for_tool:
                    msg = "User context (user_id) not found for update_user_preferences_tool."
                    logger.error(msg)
                    tool_result_content = json.dumps({"status": "error", "message": msg})
                else:
                    # Extract specific args for this tool
                    handler_args["user_id"] = supabase_user_uuid_for_tool
                    handler_args["preference_key"] = arguments_dict.get("preference_key")
                    handler_args["preference_value"] = arguments_dict.get("preference_value")
                    # handler_args["preference_type"] = arguments_dict.get("preference_type") # If you use it

                    if not (handler_args["preference_key"] and handler_args["preference_value"] is not None):
                        msg = "Missing preference_key or preference_value for update_user_preferences_tool."
                        logger.error(f"{msg} Args: {arguments_dict}")
                        tool_result_content = json.dumps({"status": "error", "message": msg})
                    else:
                        # Call the handler (which itself returns a dict with tool_call_id and content)
                        # The handler's returned 'content' is already a JSON string.
                        # So, the result_dict from the handler will be like:
                        # {"tool_call_id": "...", "content": "{\"status\": \"success\", ...}"}
                        result_dict_from_handler = await handler(**handler_args) if asyncio.iscoroutinefunction(handler) else handler(**handler_args)
                        tool_result_content = result_dict_from_handler.get("content", 
                                                                           json.dumps({"status":"error", "message":"Handler did not return content."}))
            else:
                # Generic handler call for other tools, passing all parsed arguments
                if asyncio.iscoroutinefunction(handler):
                    result_dict_from_handler = await handler(**handler_args, **arguments_dict)
                else:
                    result_dict_from_handler = handler(**handler_args, **arguments_dict)
                tool_result_content = result_dict_from_handler.get("content", json.dumps({"status":"error", "message":"Handler did not return content."}))
        except Exception as e:
            logger.error(f"Error during execution of tool {tool_name}: {e}", exc_info=True)
            tool_result_content = json.dumps({"status": "error", "message": f"Execution error in tool {tool_name}: {str(e)}"})
    else:
        logger.warning(f"No handler registered for tool {tool_name}")
        tool_result_content = json.dumps({"status": "error", "message": f"No handler for tool {tool_name}."})

    # Vapi expects a specific response format for 'function-call' results
    # It's typically a top-level object with a 'toolCallResult' key
    # containing the 'toolCallId' and 'result' (which is the JSON string content).
    return {"toolCallResult": {"toolCallId": tool_call_id_from_vapi, "result": tool_result_content}}

# --- End New Tool Handler ---

# --- Modify tool_call_handler to correctly extract arguments for the new tool ---
@register_tool_handler("update_user_preferences_tool")
async def handle_update_user_preferences(tool_call_id: str, user_id: str,
                                         preference_key: str, preference_value: Any) -> Dict[str, Any]:
    """
    Handler for 'update_user_preferences_tool'.
    Updates specific user preference in Supabase and invalidates cache.
    Returns a dictionary in the format expected by the calling tool_call_handler
    (i.e., with 'tool_call_id' and 'content' as a JSON string).
    """
    logger.info(f"Executing tool: update_user_preferences_tool for user_id '{user_id}', Key: '{preference_key}', Value: '{preference_value}'")

    if not supabase:
        logger.error("Supabase client not available in handle_update_user_preferences.")
        return {"tool_call_id": tool_call_id, "content": json.dumps({"status": "error", "message": "Database client unavailable."})}
    if not user_id:
        logger.error(f"User ID is missing for preference update (tool_call_id: {tool_call_id})")
        return {"tool_call_id": tool_call_id, "content": json.dumps({"status": "error", "message": "User ID missing."})}

    success = False
    data_to_update = {preference_key: preference_value}

    VOICE_PREF_KEYS = ["voice_id", "speaking_rate", "interaction_style", 
                       "explanation_detail_level", "discussion_depth", "preferred_analogies_type"]
    COGNITIVE_PREF_KEYS = ["learning_style", "reading_pace", "preferred_complexity_level", 
                           "preferred_interaction_frequency", "preferred_question_types", 
                           "preferred_discussion_topics", "comprehension_check_frequency"]

    if preference_key in VOICE_PREF_KEYS:
        logger.info(f"Attempting to update 'voice_agent_preferences' for key: {preference_key} of user {user_id}")
        success = upsert_voice_agent_preferences(user_id, data_to_update)
    elif preference_key in COGNITIVE_PREF_KEYS:
        logger.info(f"Attempting to update 'cognitive_preferences' for key: {preference_key} of user {user_id}")
        success = upsert_cognitive_preferences(user_id, data_to_update)
    else:
        logger.error(f"Unknown preference_key for update: '{preference_key}' for user {user_id}")
        return {"tool_call_id": tool_call_id, "content": json.dumps({"status": "error", "message": f"Unknown preference key: {preference_key}"})}

    response_content_dict: Dict[str, Any]
    if success:
        logger.info(f"Successfully updated preference '{preference_key}' for user {user_id}.")
        cache = current_app.extensions.get('cache')
        if cache:
            cache_key = f"user_prefs_{user_id}"
            try:
                cache.delete(cache_key)
                logger.info(f"Invalidated preferences cache for user {user_id} after tool update.")
            except Exception as cache_err:
                logger.error(f"Failed to invalidate cache for user {user_id}: {cache_err}")
        else: logger.warning("Cache not available, skipping cache invalidation for preference update.")
        response_content_dict = {"status": "success", "message": f"Preference '{preference_key}' updated to '{preference_value}'."}
    else:
        logger.error(f"Failed to update preference '{preference_key}' for user {user_id} in database.")
        response_content_dict = {"status": "error", "message": "Failed to update preference in database."}

    return {"tool_call_id": tool_call_id, "content": json.dumps(response_content_dict)}

# ------------------------------
# Webhook Route and Core Logic
# ------------------------------
@webhook.route('/', methods=['POST'])
async def webhook_route():
    """
    Main webhook route handler.
    Processes incoming JSON payloads from VAPI.
    """
    payload = request.get_json()
    if not payload:
        logger.warning("Webhook received no JSON payload.")
        return jsonify({"error": "No JSON payload"}), 400

    event_payload = payload.get('message', payload)
    if not event_payload or not isinstance(event_payload, dict):
        logger.error(f"Webhook: 'message' field missing or not a dict: {str(payload)[:200]}")
        return jsonify({"error": "Invalid payload structure."}), 400

    event_type = event_payload.get('type')
    logger.info(f"Webhook: Received event type '{event_type or 'N/A'}'")
    logger.debug(f"Webhook Full Event Payload for type '{event_type}': {str(event_payload)[:500]}") # Log snippet

    # Ensure handlers are defined for all expected types
    handlers = {
        "conversation-update": conversation_update_handler,
        "end-of-call-report": end_of_call_report_handler, # Now returns a dict
        "speech-update": speech_update_handler,
        "status-update": status_update_handler,
        "function-call": function_call_handler,
        "tool-calls": tool_call_handler, # If used
        "assistant-request": assistant_request_handler,
        "hang": hang_event_handler,
        "transcript": transcript_handler,
        "model-output": model_output_handler
    }
    handler = handlers.get(event_type)

    response_data: Dict[str, Any] = {} # Ensure response_data is always a dict
    status_code = 200 # Default success acknowledgement

    if handler:
        try:
            if asyncio.iscoroutinefunction(handler):
                response_data = await handler(event_payload)
            else:
                response_data = handler(event_payload)

            # Ensure handler returned a dict
            if not isinstance(response_data, dict):
                logger.error(f"Handler for '{event_type}' returned type {type(response_data)}, expected dict. Response: {str(response_data)[:200]}")
                response_data = {"status": "handler_error", "message": "Handler returned unexpected data type."}
                status_code = 200 # Acknowledge, but note internal error

            # Check 'status' key in the response_data from the handler
            if response_data.get("status") == "error_validation":
                status_code = 400
            elif response_data.get("status") == "error_processing" or response_data.get("status") == "handler_error":
                status_code = 200 # Still acknowledge to Vapi, but indicates internal processing issue
            else: # Default to 200 or 201 for successful processing
                status_code = response_data.get("http_status_code", 200) # Allow handler to suggest status

        except Exception as e:
            logger.error(f"Error executing handler for event type '{event_type}': {e}", exc_info=True)
            response_data = {"status": "error_in_handler_execution", "message": f"Internal server error processing {event_type}."}
            status_code = 200 # Acknowledge Vapi to prevent retries
    else:
        logger.warning(f"Webhook: No specific handler for event type '{event_type}'. Acknowledging receipt.")
        response_data = {"status": "received_unhandled_type", "message": f"Event type '{event_type}' received."}
        status_code = 200

    return jsonify(response_data), status_code

# ------------------------------
# Specific VAPI Message Handlers
# ------------------------------

def conversation_update_handler(payload: dict) -> Dict[str, Any]: # Changed from async
    """
    Handler for 'conversation-update' webhook message.
    Uses Supabase to fetch user ID and store session/interaction data.
    """
    logger.info(f"Processing 'conversation-update' for call: {payload.get('call', {}).get('id')}")
    try:
        validated_payload = ConversationUpdate.model_validate(payload)
        logger.debug("Webhook 'conversation-update' payload validated (or bypassed).")

        user_email = None
        try:
            # Prioritize assistantOverrides for user context passed at call start
            if (validated_payload.call and validated_payload.call.assistant_overrides and
                validated_payload.call.assistant_overrides.metadata and
                validated_payload.call.assistant_overrides.metadata.data and
                validated_payload.call.assistant_overrides.metadata.data.user):
                user_email = validated_payload.call.assistant_overrides.metadata.data.user.email
            # Fallback to general assistant metadata
            elif (validated_payload.assistant and validated_payload.assistant.metadata and
                  validated_payload.assistant.metadata.data and
                  validated_payload.assistant.metadata.data.user):
                user_email = validated_payload.assistant.metadata.data.user.email
        except AttributeError as ae:
             logger.warning(f"Could not find user email in conversation-update payload: {ae}")
        except Exception as e:
             logger.error(f"Unexpected error extracting email from conversation-update payload: {e}", exc_info=True)


        if not user_email:
             logger.error("User email not found in conversation-update payload. Cannot link to Supabase user.")
             return {"status": "acknowledged_with_error", "message": "User email missing for DB operations."}

        supabase_user_uuid = get_supabase_user_id_by_email(user_email)
        if not supabase_user_uuid:
            logger.error(f"Supabase user UUID not found for email: {user_email} (from webhook).")
            return {"status": "acknowledged_with_error", "message": "User not found in Supabase."}
        logger.info(f"Webhook: Matched email {user_email} to Supabase user ID: {supabase_user_uuid}")

        call_id = validated_payload.call.id if validated_payload.call else None
        if not call_id:
             logger.error("Call ID not found in conversation-update payload.")
             return {"status": "acknowledged_with_error", "message": "Call ID missing."}

        book_id = None # Determine if/how book_id is available in this payload
        session_id_hash = get_or_create_voice_session(call_uuid=call_id, user_id=supabase_user_uuid, book_id=book_id)
        if not session_id_hash:
            logger.error(f"Failed to get/create voice session for call {call_id}")
            return {"status": "acknowledged_with_error", "message": "Session handling failed."}
        logger.info(f"Webhook: Using session hash {session_id_hash[:8]}... for call {call_id}")

        conversation_list = validated_payload.conversation if hasattr(validated_payload, 'conversation') else []
        last_user_speech: Optional[str] = None
        last_agent_response: Optional[str] = None

        if conversation_list:
             for entry in reversed(conversation_list):
                if hasattr(entry, 'role') and hasattr(entry, 'content'):
                    if entry.role == 'user' and last_user_speech is None: last_user_speech = entry.content
                    elif entry.role in ['assistant', 'bot'] and last_agent_response is None: last_agent_response = entry.content
                    if last_user_speech is not None and last_agent_response is not None: break
        else: logger.info(f"Webhook: Conversation list empty for session {session_id_hash[:8]}...")

        if last_user_speech:
            store_voice_interaction(session_id_hash, supabase_user_uuid, "user_utterance", user_speech=last_user_speech)
        if last_agent_response:
            store_voice_interaction(session_id_hash, supabase_user_uuid, "agent_response", agent_response=last_agent_response)
        if not last_user_speech and not last_agent_response:
            logger.info(f"Webhook: No new user/assistant turns found to store for session {session_id_hash[:8]}...")

        call_status = validated_payload.call.status if hasattr(validated_payload, 'call') and hasattr(validated_payload.call, 'status') else None
        if call_status == 'ended':
            logger.info(f"Webhook: Call {call_id} ended. Updating session end time for {session_id_hash[:8]}...")
            update_session_end_time(session_id_hash)

        return {"status": "received", "message": "Conversation update processed."}

    except ValidationError as ve:
        logger.error(f"Webhook 'conversation-update' Pydantic validation failed: {ve}", exc_info=True)
        return {"status": "error_validation", "message": f"Invalid payload structure: {str(ve)}"}
    except Exception as e:
        logger.error(f"Error processing 'conversation-update' webhook: {e}", exc_info=True)
        return {"status": "error_processing", "message": f"Internal error: {str(e)}"}

# --- Stubs/Placeholders for other handlers ---
async def function_call_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Received 'function-call': {str(payload)[:200]}")
    # Implement actual function call logic or routing to tool handlers
    return {"status": "received_function_call"}



async def status_update_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Received 'status-update': Status {payload.get('status')} for call {payload.get('call',{}).get('id')}")
    call_id = payload.get('call',{}).get('id')
    status = payload.get('status')
    if status == 'ended' and call_id:
        # Need user_id to form session_id_hash
        # This event might not have full user context directly, you might need to fetch it
        # or assume the session was already created by conversation-update
        logger.info(f"Call {call_id} ended via status-update. Attempting to update session end time.")
        # This is tricky without user_id. If session hash is purely call_id based, it's simpler.
        # If session hash includes user_id, you must fetch user_id first if not in this payload.
        # For now, assuming you might only log or have a different way to get session_id_hash
        # update_session_end_time(session_id_hash_from_call_id_only) # If applicable
    return {"status": "received_status_update"}

async def transcript_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Received 'transcript' for call: {payload.get('call',{}).get('id')}, Type: {payload.get('transcriptType')}")
    logger.debug(f"Transcript: {payload.get('transcript')}")
    return {"status": "received_transcript"}

async def assistant_request_handler(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    logger.info(f"Received 'assistant-request': {str(payload)[:200]}")
    # This handler is typically used if Vapi expects you to define the assistant on the fly
    # Your current setup defines assistant in Vapi dashboard, so this might not be used often
    # or only for dynamic assistant modifications.
    # The example code to return an assistant config can be kept if needed.
    return {"message": "Assistant request received, no dynamic change implemented."} # Or return assistant config

async def end_of_call_report_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles 'end-of-call-report' and updates the corresponding voice_agent_session
    in Supabase with summary and recording URLs.
    """
    call_id_from_payload = payload.get('call', {}).get('id', 'N/A')
    logger.info(f"Processing 'end-of-call-report' for call: {call_id_from_payload}")
    summary = payload.get('summary', 'No summary provided.')
    logger.info(f"Call Summary: {summary}")

    call_id = payload.get('call', {}).get('id')  # Top-level call object in this payload
    user_email = None
    try:
        # Extract user_email from payload
        user_email = payload.get('call',{}).get('assistantOverrides',{}).get('metadata',{}).get('data',{}).get('user',{}).get('email')
        if not user_email and payload.get('assistant',{}).get('metadata'):  # Fallback to assistant block if present
            user_email = payload.get('assistant',{}).get('metadata',{}).get('data',{}).get('user',{}).get('email')
    except Exception as e:
        logger.warning(f"Could not extract user_email from end-of-call report: {e}")

    if call_id and user_email:
        supabase_user_uuid = get_supabase_user_id_by_email(user_email)
        if supabase_user_uuid:
            session_id_hash = generate_session_hash(call_id, supabase_user_uuid)
            update_payload = {
                "session_summary": summary,
                "end_time": payload.get('endedAt', "now()")  # Use endedAt from report, or fallback
            }
            # Extract recording URLs from the 'artifact' object
            artifact = payload.get('artifact', {})
            if isinstance(artifact, dict):
                # Check for recording URLs
                update_payload["recording_url"] = artifact.get('recording_url') or artifact.get('recordingUrl')
                update_payload["stereo_recording_url"] = artifact.get('stereo_recording_url') or artifact.get('stereoRecordingUrl')

            if payload.get('transcript'):
                update_payload["full_transcript"] = payload.get('transcript')

            if supabase:  # Ensure Supabase client is initialized
                try:
                    logger.info(f"Attempting to update session {session_id_hash[:8]} with end-of-call data: {update_payload}")
                    response = supabase.table("voice_agent_sessions").update(update_payload).eq("session_id", session_id_hash).execute()

                    if hasattr(response, 'error') and response.error:
                        logger.error(f"Supabase error updating session {session_id_hash[:8]} with EOCR: {response.error}")
                        return {"status": "error_db_update", "message": "Failed to update session summary in DB."}
                    else:
                        logger.info(f"Updated session {session_id_hash[:8]} with end-of-call report details.")
                        return {"status": "processed", "summary_stored": True, "session_id": session_id_hash}
                except Exception as e:
                    logger.error(f"Failed to update session {session_id_hash[:8]} with EOCR summary: {e}", exc_info=True)
                    return {"status": "error_processing", "message": "Internal error updating session summary."}
            else:
                logger.error("Supabase client (imported) is None. Cannot update end-of-call report.")
                return {"status": "error_db_unavailable", "message": "Database client not configured."}
        else:
            logger.warning(f"Could not find Supabase user for email '{user_email}' from end-of-call report. Cannot link session.")
            return {"status": "acknowledged_user_not_found", "message": "User not found to link session."}
    else:
        logger.warning(f"Missing call_id or user_email in end-of-call report. Cannot update session. Call ID: {call_id}, Email: {user_email}")
        return {"status": "acknowledged_missing_data", "message": "Call ID or User Email missing from report."}

    # Ensure a fallback return statement if none of the earlier conditions are met
    # return {"status": "processed_partially", "summary_received": summary}
    
async def speech_update_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug(f"Received 'speech-update': Status {payload.get('status')}")
    return {"status": "received_speech_update"}

async def hang_event_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Received 'hang' event for call: {payload.get('call',{}).get('id')}")
    # Could also trigger session end time update here
    return {"status": "received_hang_event"}

def model_output_handler(payload: Dict[str, Any]) -> Dict[str, Any]: # Not async
    logger.info(f"Received 'model-output': {str(payload.get('output'))[:100]}")
    # This payload comes from Vapi AFTER your LLM responds.
    # You typically just acknowledge this.
    return {"status": "received_model_output"}

# Initialize the database directory (for SQLite if still used by other tools)
# init_database_directory() # Comment out if no SQLite is used by any registered tool handler