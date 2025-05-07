# app/personalization/user_preferences.py

import os
import logging
import hashlib # For SHA256 hashing
from typing import Dict, Optional, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Optional[Client] = None
if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("Error: SUPABASE_URL or SUPABASE_KEY environment variables not set.")
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Supabase client initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Supabase client: {e}")

# --- Hashing Utility ---

def generate_session_hash(call_uuid: str, user_id: str) -> Optional[str]:
    """Generates a deterministic SHA256 hash for the session ID."""
    if not call_uuid or not user_id:
        logging.warning("Cannot generate session hash: call_uuid or user_id is missing.")
        return None
    # Create a stable string representation
    combined_id = f"{call_uuid}-{user_id}"
    # Hash the string
    hash_object = hashlib.sha256(combined_id.encode('utf-8'))
    # Return the hexadecimal representation
    return hash_object.hexdigest()

# --- Supabase Interaction Functions (Updated) ---

def get_or_create_voice_session(call_uuid: str, user_id: str, book_id: Optional[int] = None) -> Optional[str]:
    """
    Calculates the session hash and ensures a corresponding session record exists
    in voice_agent_sessions. If not, creates it.

    Args:
        call_uuid: The unique identifier for the call (VAPI call.id).
        user_id: The UUID of the user.
        book_id: Optional book ID associated with the session.

    Returns:
        The session hash string (session_id) if successful, otherwise None.
    """
    if not supabase:
        logging.error("get_or_create_voice_session: Supabase client not initialized.")
        return None

    session_id_hash = generate_session_hash(call_uuid, user_id)
    if not session_id_hash:
        return None # Error logged in generate_session_hash

    try:
        # 1. Check if session already exists
        # Use count='exact' for potentially better performance than fetching data
        response = supabase.table("voice_agent_sessions") \
                           .select("session_id", count='exact') \
                           .eq("session_id", session_id_hash) \
                           .limit(1) \
                           .execute()

        # Check for API errors first
        if hasattr(response, 'error') and response.error:
            logging.error(f"Supabase error checking session {session_id_hash}: {response.error}")
            return None

        # If count is 0, the session doesn't exist
        if response.count == 0:
            logging.info(f"Session {session_id_hash} not found, creating...")
            # 2. Create the session if it doesn't exist
            session_data = {
                "session_id": session_id_hash,
                "user_id": user_id,
                "call_uuid": call_uuid, # Store the original call ID
                "book_id": book_id,
                "session_type": "voice_agent_interaction" # Or determine dynamically
                # start_time defaults to now() in the schema
            }
            # Remove None values if your schema handles defaults well
            session_data = {k: v for k, v in session_data.items() if v is not None}

            insert_response = supabase.table("voice_agent_sessions").insert(session_data).execute()

            if hasattr(insert_response, 'error') and insert_response.error:
                # Handle potential race condition: Maybe another process created it just now?
                if "duplicate key value violates unique constraint" in str(insert_response.error):
                     logging.warning(f"Session {session_id_hash} likely created by concurrent process. Proceeding.")
                     # It exists now, so we can return the hash
                else:
                    logging.error(f"Supabase error creating session {session_id_hash}: {insert_response.error}")
                    return None # Failed to create
            elif not insert_response.data:
                 logging.warning(f"Supabase session insert for {session_id_hash} did not return data.")
                 # Decide if this is an error, but likely okay if no error attribute.

        # Session exists (either found or just created)
        return session_id_hash

    except Exception as e:
        logging.error(f"Exception in get_or_create_voice_session for hash {session_id_hash}: {e}")
        return None


def store_voice_interaction(session_id: str, user_id: str, interaction_type: str,
                             user_speech: Optional[str] = None, agent_response: Optional[str] = None,
                             **kwargs) -> bool:
    """
    Stores a single voice interaction turn.
    Accepts session_id as a string (hash).
    """
    # Input validation and Supabase client check remain the same...
    if not supabase: logging.error("store_voice_interaction: Supabase client not initialized."); return False
    if not session_id or not user_id or not interaction_type: logging.warning("store_voice_interaction: Missing required args."); return False

    interaction_data = {
        "session_id": session_id, # This is now the hash string
        "user_id": user_id,
        "interaction_type": interaction_type,
        "user_speech": user_speech,
        "agent_response": agent_response,
        **kwargs
    }
    interaction_data = {k: v for k, v in interaction_data.items() if v is not None}

    try:
        logging.info(f"Inserting interaction for session (hash) {session_id[:8]}...: Type={interaction_type}") # Log truncated hash
        response = supabase.table("voice_interactions").insert(interaction_data).execute()

        if hasattr(response, 'error') and response.error:
             logging.error(f"Supabase insert error for session (hash) {session_id[:8]}...: {response.error}")
             return False
        if not response.data:
            logging.warning(f"Supabase interaction insert for session (hash) {session_id[:8]}... did not return data.")
            # return False # Decide if error

        return True
    except Exception as e:
        logging.error(f"Exception storing voice interaction for session (hash) {session_id[:8]}...: {e}")
        return False


def update_session_end_time(session_id: str) -> bool:
    """
    Updates the end_time of a session using its hash string ID.
    """
    # Input validation and Supabase client check remain the same...
    if not supabase: logging.error("update_session_end_time: Supabase client not initialized."); return False
    if not session_id: logging.warning("update_session_end_time: Missing session_id hash."); return False

    try:
        logging.info(f"Updating end_time for session_id (hash) {session_id[:8]}...")
        response = supabase.table("voice_agent_sessions") \
                         .update({"end_time": "now()"}) \
                         .eq("session_id", session_id) \
                         .execute()

        if hasattr(response, 'error') and response.error:
             logging.error(f"Supabase update error for session (hash) {session_id[:8]}...: {response.error}")
             return False
        # Check if update affected any rows might be useful via response if available
        # if response.count == 0: # Or similar check based on actual response structure
        #     logging.warning(f"Update end_time for session (hash) {session_id[:8]}... affected 0 rows.")

        return True
    except Exception as e:
        logging.error(f"Exception updating session end time for session (hash) {session_id[:8]}...: {e}")
        return False


def get_llm_context_from_session(session_id: str, max_turns: int = 5) -> str:
    """
    Retrieve recent interactions using the session hash string ID.
    """
    # Input validation and Supabase client check remain the same...
    if not supabase: logging.error("get_llm_context_from_session: Supabase client not initialized."); return "Context unavailable."
    if not session_id: logging.warning("get_llm_context_from_session: Missing session_id hash."); return "Context unavailable."

    context_lines = []
    try:
        limit = max_turns * 2 + 2
        logging.debug(f"Fetching context for session (hash) {session_id[:8]}...")
        response = supabase.table("voice_interactions") \
                           .select("interaction_type, user_speech, agent_response, timestamp") \
                           .eq("session_id", session_id) \
                           .order("timestamp", desc=True) \
                           .limit(limit) \
                           .execute()

        # Processing logic remains the same...
        if response.data:
            interactions = sorted(response.data, key=lambda x: x.get('timestamp', ''))
            user_turns_added = 0
            for row in interactions:
                if user_turns_added >= max_turns: break
                # ... (rest of the logic to build context_lines) ...
                interaction_type = row.get("interaction_type")
                user_speech = row.get("user_speech")
                agent_response = row.get("agent_response")
                if interaction_type == 'user_utterance' and user_speech:
                    context_lines.append(f"User: {user_speech}")
                    user_turns_added += 1
                elif interaction_type == 'agent_response' and agent_response:
                    context_lines.append(f"Agent: {agent_response}")
            while len(context_lines) > max_turns * 2 : context_lines.pop(0)

        if context_lines:
            return "\n".join(context_lines)
        else:
            logging.info(f"No interactions found for session (hash) {session_id[:8]}... to generate context.")
            return "No previous conversation history available for this session."

    except Exception as e:
        logging.error(f"Error fetching LLM context for session (hash) {session_id[:8]}...: {e}")
        return "Error retrieving context."

# --- Existing Functions (Keep if needed) ---
# def get_user_preferences(user_id: str) -> Dict[str, str]: ...
def get_user_preferences(user_id: str) -> Dict[str, str]:
    """
    Retrieve user preferences from the voice_agent_preferences and
    cognitive_preferences tables in Supabase using the user's UUID string.

    Args:
        user_id: The UUID string of the user.

    Returns:
        A dictionary containing user preferences. Applies defaults if specific
        preferences are not found in the database. Returns an empty dictionary
        if the Supabase client is not available or a major error occurs.
    """
    if not supabase:
        logging.error("get_user_preferences: Supabase client not initialized.")
        # Return default preferences dictionary directly if client fails
        return {
            "speaking_rate": "normal", "interaction_style": "friendly",
            "explanation_detail_level": "standard", "discussion_depth": "moderate",
            "learning_style": "visual", "reading_pace": "normal",
            "preferred_complexity_level": "medium", "preferred_interaction_frequency": "regular"
        }
    if not user_id:
        logging.warning("get_user_preferences: No user_id provided.")
        # Return defaults if no user ID is given
        return {
            "speaking_rate": "normal", "interaction_style": "friendly",
            "explanation_detail_level": "standard", "discussion_depth": "moderate",
            "learning_style": "visual", "reading_pace": "normal",
            "preferred_complexity_level": "medium", "preferred_interaction_frequency": "regular"
        }

    preferences: Dict[str, str] = {}
    defaults = {
        "speaking_rate": "normal",
        "interaction_style": "friendly",
        "explanation_detail_level": "standard",
        "discussion_depth": "moderate",
        "learning_style": "visual",
        "reading_pace": "normal",
        "preferred_complexity_level": "medium",
        "preferred_interaction_frequency": "regular"
    }

    try:
        # Query voice agent preferences.
        logging.debug(f"Fetching voice agent preferences for user: {user_id}")
        agent_response = supabase.table("voice_agent_preferences").select(
            "speaking_rate, interaction_style, explanation_detail_level, discussion_depth"
        ).eq("user_id", user_id).limit(1).execute()

        if hasattr(agent_response, 'error') and agent_response.error:
            logging.error(f"Supabase error fetching voice preferences for user {user_id}: {agent_response.error}")
        elif agent_response.data:
            row = agent_response.data[0]
            preferences["speaking_rate"] = str(row.get("speaking_rate", defaults["speaking_rate"]))
            preferences["interaction_style"] = str(row.get("interaction_style", defaults["interaction_style"]))
            preferences["explanation_detail_level"] = str(row.get("explanation_detail_level", defaults["explanation_detail_level"]))
            preferences["discussion_depth"] = str(row.get("discussion_depth", defaults["discussion_depth"]))
        else:
             logging.info(f"No voice agent preferences found for user: {user_id}. Defaults will be used for these.")

        # Query cognitive preferences.
        logging.debug(f"Fetching cognitive preferences for user: {user_id}")
        cognitive_response = supabase.table("cognitive_preferences").select(
            "learning_style, reading_pace, preferred_complexity_level, preferred_interaction_frequency"
        ).eq("user_id", user_id).limit(1).execute()

        if hasattr(cognitive_response, 'error') and cognitive_response.error:
             logging.error(f"Supabase error fetching cognitive preferences for user {user_id}: {cognitive_response.error}")
        elif cognitive_response.data:
            row = cognitive_response.data[0]
            preferences["learning_style"] = str(row.get("learning_style", defaults["learning_style"]))
            preferences["reading_pace"] = str(row.get("reading_pace", defaults["reading_pace"]))
            preferences["preferred_complexity_level"] = str(row.get("preferred_complexity_level", defaults["preferred_complexity_level"]))
            preferences["preferred_interaction_frequency"] = str(row.get("preferred_interaction_frequency", defaults["preferred_interaction_frequency"]))
        else:
            logging.info(f"No cognitive preferences found for user: {user_id}. Defaults will be used for these.")

    except Exception as e:
        logging.error(f"Unexpected error fetching user preferences for user {user_id}: {e}", exc_info=True)
        # In case of error, return defaults to avoid breaking downstream logic
        return defaults

    # Ensure all default keys are present using setdefault
    for key, value in defaults.items():
        preferences.setdefault(key, value) # Adds key with default value ONLY if key is not already present

    logging.debug(f"Final preferences for user {user_id}: {preferences}")
    return preferences
