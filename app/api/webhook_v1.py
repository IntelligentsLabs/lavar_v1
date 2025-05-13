# app/api/webhook.py
import json
import logging
import traceback
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from typing import List, Optional
import os
from pathlib import Path
import asyncio
import sqlite3
from app.api.supabase_db import get_supabase_user_id_by_email

from app.vapi_message_handlers.conversation_update import ConversationUpdate
from app.personalization.user_preferences import (
    get_or_create_voice_session, # Changed from lookup_voice_session_id
    store_voice_interaction,
    update_session_end_time
)
# Example imports for additional functionalities.
# These should exist in your project; if not, create stub modules.
from app.functions.schedule_clickup import generate_schedule, process_schedule, transform_llm_output
# from app.vapi_message_handlers.conversation_update import ConversationUpdate
from app.vapi_message_handlers.end_of_call_report import EndOfCallReport
from app.vapi_message_handlers.model_output import ModelOutput
from app.vapi_message_handlers.speech_update import SpeechUpdate
from app.vapi_message_handlers.transcript import Transcript

# Constants for logging and database paths.
LOG_FILE_PATH = "app/response_data/webhook_logs.txt"
LOG_TOOL_PATH = "app/response_data/tool_logs.txt"
DB_BASE_PATH = "data/databases"

logger = logging.getLogger(__name__)

# Initialize the Blueprint.
webhook = Blueprint('webhook', __name__)

# A dictionary to register tool handlers.
tool_handlers = {}


# ------------------------------
# Database helper functions
# ------------------------------
def init_database_directory():
    """Initialize the database directory at startup."""
    Path(DB_BASE_PATH).mkdir(parents=True, exist_ok=True)


def ensure_db_directory(db_path):
    """Ensure the directory for the database exists."""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        Path(db_dir).mkdir(parents=True, exist_ok=True)


def store_in_database(data, db_name, table_name, schema):
    """
    Store extracted data into a SQLite database with dynamic table creation.
    Handles AUTOINCREMENT columns automatically.
    Converts list of dictionaries to list of tuples for executemany.
    """
    try:
        # ensure_db_directory(db_name) # Keep if needed
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
        except sqlite3.OperationalError as e:
            logging.error(f"Error creating table {table_name}: {e}")
            conn.close()
            return False

        if data:
            # --- Determine column names in the correct order ---
            # Filter out AUTOINCREMENT columns and get just the names
            column_names = [col.strip().split()[0]
                            for col in schema.split(",")
                            if "AUTOINCREMENT" not in col.upper().strip()]
            columns_sql = ", ".join(column_names) # SQL fragment for column list
            placeholders = ", ".join("?" for _ in column_names) # Positional placeholders

            # --- Convert list of dicts to list of tuples in the correct order ---
            try:
                data_as_tuples = [
                    tuple(row_dict[col_name] for col_name in column_names)
                    for row_dict in data # Iterate through list of dictionaries
                ]
            except KeyError as ke:
                logging.error(f"Data dictionary is missing key: {ke}. Check schema vs data keys.")
                conn.close()
                return False
            # --- End data conversion ---

            try:
                # --- Use the list of tuples ---
                cursor.executemany(
                    f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})",
                    data_as_tuples # Pass the list of tuples here
                )
                conn.commit()
            except sqlite3.Error as e:
                # More specific error logging
                logging.error(f"Error inserting data into {table_name} ({columns_sql}): {e}")
                logging.error(f"Data attempted (first row tuple): {data_as_tuples[0] if data_as_tuples else 'N/A'}")
                conn.rollback()
                conn.close()
                return False
        conn.close()
        return True
    except sqlite3.Error as e:
        logging.error(f"Database connection or setup error: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error in store_in_database: {e}")
        # Optional: Add traceback for unexpected errors
        # import traceback
        # logging.error(traceback.format_exc())
        return False


# ------------------------------
# Main webhook route
# ------------------------------
@webhook.route('/', methods=['POST'])
async def webhook_route():
    """
    Main webhook route handler.
    Processes incoming JSON payloads from VAPI.
    """
    try:
        request_data = request.get_json()
        payload = request_data.get('message')

        if not payload:
            return jsonify({"error": "No message in payload"}), 400

        # Log payload information for debugging.
        log_entry = (f"Payload Type: {payload.get('type')}\n"
                     f"Payload Keys: {list(payload.keys())}\n"
                     f"Payload Content: {payload}\n"
                     f"{'='*50}\n")
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(log_entry)

        # Map payload types to their respective handler functions.
        handlers = {
            "function-call": function_call_handler,
            "tool-calls": tool_call_handler,
            "status-update": status_update_handler,
            "conversation-update": conversation_update_handler,
            "transcript": transcript_handler,
            "assistant-request": assistant_request_handler,
            "end-of-call-report": end_of_call_report_handler,
            "speech-update": speech_update_handler,
            "hang": hang_event_handler,
            "voice-input": voice_input_handler,
            "model-output": lambda p: p
        }

        payload_type = payload.get('type')
        handler = handlers.get(payload_type)

        if handler:
            if asyncio.iscoroutinefunction(handler):
                response = await handler(payload)
            else:
                response = handler(payload)

            if payload_type == "tool-calls":
                await process_tool_calls(payload)
            return jsonify(response), 201
        else:
            logging.warning(f"Unhandled message type: {payload_type}")
            return jsonify({"error": "Unhandled message type"}), 400

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({"error": "An unexpected error occurred."}), 500


# ------------------------------
# Tool handler registration
# ------------------------------
def register_tool_handler(tool_name):
    """
    Decorator to register tool handlers.
    """

    def decorator(func):
        tool_handlers[tool_name] = func
        return func

    return decorator


def extract_tool_calls(payload):
    """
    Extract tool call data from the payload and categorize it by tool type.
    """
    extracted_data = {}
    tool_calls = payload.get("toolCalls", [])

    for call in tool_calls:
        function_data = call.get("function", {})
        tool_name = function_data.get("name")
        arguments = function_data.get("arguments", {})

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                logging.error(
                    f"Invalid JSON in arguments for tool {tool_name}")
                continue

        if tool_name not in extracted_data:
            extracted_data[tool_name] = []

        if tool_name == "collect_user_info":
            key = arguments.get("key")
            value = arguments.get("value")
            description = f"Preference for {key} is '{value}'." if key and value else None
            extracted_data[tool_name].append((key, value, description))
        elif tool_name == "finalizeDetails":
            question = arguments.get("question")
            answer = arguments.get("answer")
            extracted_data[tool_name].append((question, answer))
        elif tool_name == "getCharacterInspiration":
            theme = arguments.get("theme")
            setting = arguments.get("setting")
            traits = json.dumps(arguments.get("traits", []))
            extracted_data[tool_name].append((theme, setting, traits))
        elif tool_name == 'note_taking_tool':
            action = arguments.get('action')
            tags = arguments.get('tags')
            priority = arguments.get('priority')
            note_content = arguments.get('note_content')
            context_window = arguments.get('context_window')
            extracted_data[tool_name].append(
                (action, tags, priority, note_content, context_window))
    return extracted_data


async def tool_call_handler(payload):
    """
    Generalized handler for processing tool calls in a payload.
    """
    artifact_messages = payload.get("artifact", {}).get("messages", [])
    results = []

    for message in artifact_messages:
        tool_calls = message.get("toolCalls", [])
        for call in tool_calls:
            tool_call_id = call.get("id", "")
            function = call.get("function", {})
            tool_name = function.get("name")
            arguments = function.get("arguments", {})

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    logging.error(
                        f"Invalid JSON in arguments for tool {tool_name}")
                    continue

            handler = tool_handlers.get(tool_name)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(tool_call_id, **arguments)
                else:
                    result = handler(tool_call_id, **arguments)
                results.append(result)
            else:
                logging.warning(f"No handler registered for tool {tool_name}")

    return results


async def process_tool_calls(payload):
    """
    Process tool calls: extract data and store it in respective databases.
    """
    extracted_data = extract_tool_calls(payload)

    db_mappings = {
        "collect_user_info": {
            "db":
            f"{DB_BASE_PATH}/preferences.db",
            "table":
            "user_preferences",
            "schema":
            "id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, value TEXT, description TEXT",
        },
        "finalizeDetails": {
            "db":
            f"{DB_BASE_PATH}/details.db",
            "table":
            "finalized_details",
            "schema":
            "id INTEGER PRIMARY KEY AUTOINCREMENT, summary TEXT, details TEXT",
        },
        "getCharacterInspiration": {
            "db":
            f"{DB_BASE_PATH}/characters.db",
            "table":
            "character_inspirations",
            "schema":
            "id INTEGER PRIMARY KEY AUTOINCREMENT, theme TEXT, setting TEXT, traits TEXT",
        },
    }

    for tool_name, data in extracted_data.items():
        if tool_name in db_mappings:
            db_info = db_mappings[tool_name]
            success = store_in_database(data,
                                        db_name=db_info["db"],
                                        table_name=db_info["table"],
                                        schema=db_info["schema"])
            if success:
                logging.info(
                    f"Data for '{tool_name}' stored in {db_info['db']} -> {db_info['table']}."
                )
            else:
                logging.error(
                    f"Failed to store data for '{tool_name}' in {db_info['db']}."
                )
        else:
            logging.warning(f"No database mapping found for tool: {tool_name}")


# ------------------------------
# Tool Handlers
# ------------------------------
@register_tool_handler("finalizeDetails")
async def handle_finalize_details(tool_call_id, question, answer):
    """Handler for the finalizeDetails tool."""
    try:
        with open("finalize_details_log.txt", "a") as log_file:
            log_file.write(
                json.dumps(
                    {
                        "id": tool_call_id,
                        "question": question,
                        "answer": answer
                    },
                    indent=4) + "\n")
    except Exception as e:
        logging.error(f"Error writing to file: {e}")
    return {
        "tool": "finalizeDetails",
        "status": "processed",
        "summary": question,
        "details": answer
    }


@register_tool_handler("collect_user_info")
async def handle_collect_user_info(tool_call_id, key, value):
    """Handler for the collect_user_info tool."""
    description = f"Preference for {key} is '{value}'."
    try:
        with open("user_info_log.txt", "a") as log_file:
            log_file.write(
                json.dumps(
                    {
                        "id": tool_call_id,
                        "key": key,
                        "value": value,
                        "description": description
                    },
                    indent=4) + "\n")
    except Exception as e:
        logging.error(f"Error writing to file: {e}")
    return {
        "tool": "collect_user_info",
        "key": key,
        "value": value,
        "description": description
    }


@register_tool_handler("getCharacterInspiration")
async def handle_get_character_inspiration(tool_call_id,
                                           theme=None,
                                           setting=None,
                                           traits=None):
    """Handler for the getCharacterInspiration tool."""
    inspiration = {
        "theme": theme or "heroic",
        "setting": setting or "medieval fantasy",
        "traits": traits or ["brave", "loyal", "determined"]
    }
    return {"tool": "getCharacterInspiration", "inspiration": inspiration}


@register_tool_handler("schedule_clickup")
async def handle_schedule_clickup(tool_call_id,
                                  goal,
                                  timeline,
                                  resources,
                                  space_id=90112974722):
    """
    Handler for schedule_clickup tool.
    Generates a schedule using an LLM and integrates it with ClickUp.
    """
    try:
        prompt = goal + timeline + resources
        raw_schedule = await generate_schedule(prompt)
        validated_schedule = transform_llm_output(raw_schedule)
        await process_schedule(space_id=space_id, schedule=validated_schedule)
        return {
            "tool":
            "schedule_clickup",
            "status":
            "success",
            "schedule_name":
            validated_schedule.schedule_name,
            "message":
            f"Schedule '{validated_schedule.schedule_name}' successfully created in ClickUp."
        }
    except Exception as e:
        logging.error(f"Error in handle_schedule_clickup: {e}")
        return {
            "tool": "schedule_clickup",
            "status": "error",
            "message": str(e)
        }


# ------------------------------
# Other VAPI Message Handlers
# ------------------------------
async def function_call_handler(payload):
    """Handle function calls."""
    function_call = payload.get('toolCall')
    if not function_call:
        raise ValueError("Invalid Request.")

    name = function_call.get('name')
    parameters = function_call.get('parameters')

    if name == 'getCharacterInspiration':
        from app.tools.get_character_inspiration import get_character_inspiration
        return get_character_inspiration(**parameters)
    elif name == 'getRandomName':
        from app.tools.get_random_name import get_random_name, NameParams
        params = NameParams(gender="male", nat="US")
        return get_random_name(params)
    return None


# In app/vapi_message_handlers/conversation_update.py


def conversation_update_handler(payload: dict):
    """
    Handler for 'conversation-update' webhook message.
    Uses deterministic session hash IDs.
    """
    try:
        # --- Pydantic Validation ---
        # This assumes ConversationUpdate is your Pydantic model for this payload
        # and that it correctly reflects the Vapi 'conversation-update' structure
        validated_payload = ConversationUpdate.model_validate(payload)
        print("********THIS IS VALIDATION TYPE*******",type(validated_payload))
        logger.debug("Webhook 'conversation-update' payload validated successfully.")
        # --- End Validation ---

        # --- Extract User Email from Validated Payload ---
        # Path to email might vary slightly based on your Pydantic model structure
        # This assumes 'assistant.metadata.data.user.email' as derived from your example
        user_email = None
        try:
            if (validated_payload.assistant and
                validated_payload.assistant.metadata and
                validated_payload.assistant.metadata.data and
                validated_payload.assistant.metadata.data.user):
                user_email = validated_payload.assistant.metadata.data.user.email
            # Alternative path if 'assistantOverrides' is more reliable for this event
            elif (validated_payload.call and
                  validated_payload.call.assistant_overrides and
                  validated_payload.call.assistant_overrides.metadata and
                  validated_payload.call.assistant_overrides.metadata.data and
                  validated_payload.call.assistant_overrides.metadata.data.user):
                user_email = validated_payload.call.assistant_overrides.metadata.data.user.email

        except AttributeError:
             logger.warning("Could not find user email in expected webhook payload paths via Pydantic model.")
        except Exception as e:
             logger.error(f"Unexpected error extracting email from Pydantic model: {e}")


        if not user_email:
             logger.error("User email not found in conversation-update payload.")
             # Acknowledge webhook to prevent Vapi retries, but note the error
             return jsonify({"status": "acknowledged_with_error", "message": "User email missing from payload."}), 200

        # --- Get CORRECT Supabase User UUID using the imported function ---
        supabase_user_uuid = get_supabase_user_id_by_email(user_email)
        if not supabase_user_uuid:
            logger.error(
                f"Could not find Supabase user UUID for email: {user_email} (received in webhook).User might not exist in Supabase users table."
                        )
            return jsonify({"status": "acknowledged_with_error", "message": "User not found in database."}), 200
            
        logger.info(f"Webhook: Matched email {user_email} to Supabase user ID: {supabase_user_uuid}")
        # --- End Get User UUID ---

        # --- Get Call ID ---
        call_id = None
        try:
            call_id = validated_payload.call.id
        except AttributeError:
             logger.error("Call ID not found in conversation-update payload (validated_payload.call.id).")
        if not call_id:
             return jsonify({"status": "acknowledged_with_error", "message": "Call ID missing."}), 200
        # --- End Get Call ID ---

        # --- Get/Create Voice Session using CORRECT Supabase UUID ---
        # book_id might need to be determined from payload/context if relevant for this session
        book_id = None # Placeholder, determine if needed
        session_id_hash = get_or_create_voice_session(
            call_uuid=call_id,
            user_id=supabase_user_uuid, # Pass the CORRECT Supabase UUID
            book_id=book_id
        )
        if not session_id_hash:
            logger.error(f"Failed to get/create voice session for call {call_id} and user {supabase_user_uuid}.")
            return jsonify({"status": "acknowledged_with_error", "message": "Session handling failed."}), 200
        logger.info(f"Webhook: Using session hash {session_id_hash[:8]}... for call {call_id}")
        # --- End Get/Create Session ---

        # --- Extract and Store Interactions ---
        conversation_list = validated_payload.conversation
        last_user_speech: Optional[str] = None
        last_agent_response: Optional[str] = None

        if conversation_list: # Ensure it's not None or empty
             for entry in reversed(conversation_list):
                if entry.role == 'user' and last_user_speech is None:
                    last_user_speech = entry.content
                elif entry.role == 'assistant' and last_agent_response is None:
                    last_agent_response = entry.content
                # Stop if we found the most recent of both
                if last_user_speech is not None and last_agent_response is not None:
                    break
        else:
            logger.info(f"Webhook: Conversation list is empty for session {session_id_hash[:8]}...")

        # Store interactions using CORRECT Supabase UUID
        if last_user_speech:
            store_voice_interaction(session_id_hash, supabase_user_uuid, "user_utterance", user_speech=last_user_speech)
        if last_agent_response:
             store_voice_interaction(session_id_hash, supabase_user_uuid, "agent_response", agent_response=last_agent_response)

        if not last_user_speech and not last_agent_response:
            logger.info(f"Webhook: No new user or assistant turns to store for session {session_id_hash[:8]}...")
        # --- End Store Interactions ---

        # --- Update End Time if Call Ended ---
        call_status = None
        try:
            call_status = validated_payload.call.status
        except AttributeError:
             logger.warning("Call status not found in conversation-update payload.")

        if call_status == 'ended': # Or your specific status for ended calls
            logger.info(f"Webhook: Call {call_id} ended. Updating session end time for {session_id_hash[:8]}...")
            update_session_end_time(session_id_hash)
        # --- End Update End Time ---

        # Acknowledge Vapi quickly
        return jsonify({"status": "received", "message": "Conversation update processed."}), 201

    except ValidationError as ve:
        logger.error(f"Webhook 'conversation-update' payload validation failed: {ve}")
        # It's often best to return 400 for invalid payloads if Vapi doesn't retry excessively
        return jsonify({"status": "error", "message": "Invalid payload structure."}), 400
    except Exception as e:
        logger.error(f"Error processing 'conversation-update' webhook: {e}", exc_info=True)
        # Still return 2xx to Vapi to prevent retries for internal errors, but log thoroughly
        return jsonify({"status": "error_processing", "message": "Internal error handling webhook."}), 200


async def status_update_handler(payload):
    """Handle status updates."""
    return {}


async def voice_input_handler(payload):
    """Handle voice-input calls."""
    return {}


async def end_of_call_report_handler(payload):
    """Handle end-of-call reports."""
    user_id = payload.get('assistant', {}).get('metadata',
                                               {}).get('user_id', "unknown")
    summarization = payload.get('summary')
    print(summarization)
    return [summarization]


async def speech_update_handler(payload):
    """Handle speech updates."""
    return {}


async def transcript_handler(payload):
    """Handle transcripts."""
    return {}


async def hang_event_handler(payload):
    """Handle hang events."""
    return {}


async def assistant_request_handler(payload):
    """Handle assistant requests."""
    if payload and 'call' in payload:
        assistant = {
            'name': 'Paula',
            'model': {
                'provider':
                'openai',
                'model':
                'gpt-3.5-turbo',
                'temperature':
                0.7,
                'systemPrompt':
                ("You're Paula, an AI assistant who can help users draft beautiful emails "
                 "to their clients. Then call the sendEmail function to actually send the email."
                 ),
                'functions': [{
                    'name': 'sendEmail',
                    'description':
                    'Send email to the given email address with the provided content.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'email': {
                                'type': 'string',
                                'description':
                                'Email address to send the content.'
                            },
                            'content': {
                                'type': 'string',
                                'description': 'The email content.'
                            }
                        },
                        'required': ['email']
                    }
                }]
            },
            'voice': {
                'provider': '11labs',
                'voiceId': 'paula'
            },
            'firstMessage': "Hi, I'm Paula, your personal email assistant."
        }
        return {'assistant': assistant}

    raise ValueError('Invalid call details provided.')


# Initialize the database directory when the module loads.
init_database_directory()
