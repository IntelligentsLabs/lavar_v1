# app/api/supabase_db.py

import os
import logging
import secrets
from typing import Optional, Dict, Any, List
from supabase import create_client, Client, PostgrestAPIResponse
from dotenv import load_dotenv

# --- Initialize Supabase Client ---
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Optional[Client] = None
if not SUPABASE_URL or not SUPABASE_KEY:
    logging.basicConfig(level=logging.ERROR)
    logging.error("supabase_db.py: FATAL - SUPABASE_URL or SUPABASE_KEY environment variables not set.")
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Set logger after basicConfig potentially called by Flask app
        logger = logging.getLogger(__name__)
        logger.info("supabase_db.py: Supabase client initialized successfully.")
    except Exception as e:
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"supabase_db.py: Failed to initialize Supabase client: {e}", exc_info=True)
# Get logger instance - relies on Flask app having configured basicConfig
logger = logging.getLogger(__name__)
# --- End Initialize Supabase Client ---

# ==============================================================================
# --- User Management Functions ---
# ==============================================================================

def get_supabase_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the full user record from the Supabase 'users' table based on email.
    """
    if not supabase: logger.error("get_supabase_user_by_email: Supabase client not available."); return None
    if not email: logger.warning("get_supabase_user_by_email: No email provided."); return None
    try:
        logger.debug(f"Querying Supabase for user with email: {email}")
        response: PostgrestAPIResponse = supabase.table("users").select("*").eq("email", email).limit(1).execute()
        if hasattr(response, 'error') and response.error: logger.error(f"Supabase API error fetching user by email {email}: {response.error}"); return None
        if response.data: logger.debug(f"Found user data for email: {email}"); return response.data[0]
        else: logger.debug(f"No user found for email: {email}"); return None
    except Exception as e: logger.error(f"Exception fetching user by email {email}: {e}", exc_info=True); return None

def get_supabase_user_id_by_email(email: str) -> Optional[str]:
    """
    Retrieves the user's UUID string from the Supabase 'users' table based on email.
    """
    user_data = get_supabase_user_by_email(email)
    if user_data and 'user_id' in user_data:
        user_id_value = user_data['user_id']
        return str(user_id_value) if user_id_value is not None else None
    return None

def get_supabase_user_data_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves combined user data from 'users' and 'user_profiles' tables
    based on the Supabase user UUID string.
    """
    if not supabase: logger.error("get_supabase_user_data_by_id: Supabase client not available."); return None
    if not user_id: logger.warning("get_supabase_user_data_by_id: No user_id provided."); return None
    user_info = {}
    try:
        logger.debug(f"Fetching user data for ID: {user_id}")
        user_response: PostgrestAPIResponse = supabase.table("users").select("*").eq("user_id", user_id).limit(1).execute()
        if hasattr(user_response, 'error') and user_response.error: logger.error(f"Supabase API error fetching user data for ID {user_id}: {user_response.error}"); return None
        if not user_response.data: logger.warning(f"No user found in 'users' table for ID: {user_id}"); return None
        user_info.update(user_response.data[0])
        user_info.pop('password', None) # Don't return placeholder password

        logger.debug(f"Fetching profile data for user ID: {user_id}")
        profile_response: PostgrestAPIResponse = supabase.table("user_profiles").select("*").eq("user_id", user_id).limit(1).execute()
        if hasattr(profile_response, 'error') and profile_response.error: logger.error(f"Supabase API error fetching profile for user ID {user_id}: {profile_response.error}") # Log error but continue
        elif profile_response.data:
            profile_data = profile_response.data[0]
            profile_data.pop('user_id', None); profile_data.pop('user_profile_id', None) # Remove redundant/internal keys
            user_info.update(profile_data)
        else: logger.info(f"No profile found in 'user_profiles' for user ID: {user_id}.")
        return user_info
    except Exception as e: logger.error(f"Exception fetching combined user data for ID {user_id}: {e}", exc_info=True); return None


def check_if_user_exists(email: str) -> bool:
    """Checks if a user exists in the Supabase 'users' table by email."""
    return get_supabase_user_id_by_email(email) is not None


def create_supabase_user(user_details: Dict[str, Any]) -> Optional[str]:
    """
    Creates a user in Supabase 'users' table (with placeholder password)
    and then CREATES OR UPDATES a corresponding record in 'user_profiles' using UPSERT.

    Args:
        user_details: Dict containing 'username', 'email' (required) and
                      optionally 'picture', 'first_name', 'last_name',
                      'email_verified', 'current_bg', 'character', 'auth0_sub'.
    Returns:
        The user's UUID string (new or existing) on success, None on failure.
    """
    if not supabase: logger.error("create_supabase_user: Supabase client not available."); return None
    required_keys = ['email', 'username']
    if not all(key in user_details for key in required_keys):
        logger.error(f"create_supabase_user: Missing required keys ({', '.join(required_keys)}).")
        return None

    # --- Determine User ID (Create or Fetch Existing) ---
    existing_user_id = get_supabase_user_id_by_email(user_details['email'])
    profile_user_id: Optional[str] = None # This will hold the definitive user ID

    if existing_user_id:
        logger.info(f"User {user_details['email']} already exists with ID {existing_user_id}. Will update profile.")
        profile_user_id = existing_user_id
        # Optionally update fields in the 'users' table if they can change (e.g., username, email_verified)
        update_payload = {}
        if user_details.get('username') and user_details['username'] != get_supabase_user_by_email(user_details['email']).get('username'): # Example check
             update_payload['username'] = user_details['username']
        if 'email_verified' in user_details:
             update_payload['email_verified'] = user_details['email_verified']
        if update_payload:
            try:
                logger.info(f"Updating existing user {profile_user_id} in 'users' table: {update_payload}")
                supabase.table("users").update(update_payload).eq("user_id", profile_user_id).execute()
            except Exception as user_update_e:
                 logger.error(f"Exception updating existing user {profile_user_id} in 'users' table: {user_update_e}", exc_info=True)
                 # Continue to profile update even if this fails? Or return None? Decide based on requirements.

    else:
        # User does not exist, create them
        logger.info(f"User {user_details['email']} not found. Creating...")
        placeholder_password = f"external_auth_{secrets.token_hex(32)}"
        user_payload = {
            "username": user_details['username'],
            "email": user_details['email'],
            "password": placeholder_password,
            "email_verified": user_details.get('email_verified', False)
        }
        try:
            user_insert_response: PostgrestAPIResponse = supabase.table("users").insert(user_payload).execute()
            if hasattr(user_insert_response, 'data') and user_insert_response.data:
                profile_user_id = str(user_insert_response.data[0]['user_id'])
                logger.info(f"Successfully created user in 'users' table with ID: {profile_user_id}")
            else:
                error_msg = "No data returned from 'users' insert."
                if hasattr(user_insert_response, 'error') and user_insert_response.error:
                     error_info = user_insert_response.error.message if hasattr(user_insert_response.error, 'message') else str(user_insert_response.error)
                     error_msg = f"Supabase API error: {error_info}"
                     # Duplicates should have been caught by check_if_user_exists, but handle defensively
                     if 'duplicate key value violates unique constraint' in error_info:
                         logging.error(f"Duplicate error during user creation for {user_payload.get('email')} despite existence check: {error_info}")
                         # Try fetching ID again as a recovery attempt
                         return get_supabase_user_id_by_email(user_payload.get('email'))
                logging.error(f"Failed to create user {user_payload.get('email')} in 'users' table: {error_msg}")
                return None # Failed insertion
        except Exception as e:
            logging.error(f"Exception creating user {user_payload.get('email')} in 'users' table: {e}", exc_info=True)
            return None

    # --- Profile Creation/Update ---
    if profile_user_id:
        # Prepare payload with all potential profile fields
        profile_payload = {
            "user_id": profile_user_id, # MUST include for upsert conflict resolution
            "email": user_details.get('email'), # Store email here too if desired/needed
            "first_name": user_details.get('first_name'),
            "last_name": user_details.get('last_name'),
            "profile_picture_url": user_details.get('picture'),
            "current_bg": user_details.get('current_bg'), # Let upsert handle null if needed
            "character": user_details.get('character') # Pass character dict
            # Optionally store auth0_sub if needed for debugging/linking
            # "auth0_sub": user_details.get('auth0_sub')
        }
        # It's generally better to let upsert handle nulls based on DB schema
        # than removing keys here, UNLESS a value of None explicitly means "don't update".
        # profile_payload_cleaned = {k: v for k, v in profile_payload.items() if v is not None}
        # Ensure user_id is present
        # profile_payload_cleaned["user_id"] = profile_user_id

        try:
            action = "Upserting" # Use upsert term
            logging.info(f"{action} profile in 'user_profiles' for user ID {profile_user_id}")
            # Log payload before cleaning Nones if you cleaned them
            # logging.debug(f"Profile payload for upsert: {profile_payload_cleaned}")

            # Use upsert to handle both creation (if profile missing) and update
            profile_upsert_response: PostgrestAPIResponse = supabase.table("user_profiles") \
                                          .upsert(profile_payload, on_conflict="user_id") \
                                          .execute()

            if hasattr(profile_upsert_response, 'error') and profile_upsert_response.error:
                error_info = profile_upsert_response.error.message if hasattr(profile_upsert_response.error, 'message') else str(profile_upsert_response.error)
                logging.error(f"Failed to {action.lower()} profile for user {profile_user_id}: {error_info}")
                # Decide if profile failure should prevent returning user_id
            elif profile_upsert_response.data:
                 logging.info(f"Successfully {action.lower()}d profile for user ID: {profile_user_id}")
            else:
                 logging.info(f"Profile {action.lower()} for user {profile_user_id} completed (no data returned is normal for upsert).")

        except Exception as e:
            logging.error(f"Exception {action.lower()}ing profile for user {profile_user_id}: {e}", exc_info=True)
            # User exists/created, but profile upsert failed. Log error but proceed.

    # Return the Supabase user ID (either existing or newly created)
    return profile_user_id


def update_user_setting(user_id: str, setting_key: str, setting_value: Any) -> bool:
    """Updates a specific setting in the user's profile (user_profiles table)."""
    # ... (implementation remains the same as previous version) ...
    if not supabase: logging.error("update_user_setting: Supabase client not available."); return False
    if not user_id or not setting_key: logging.warning("update_user_setting: user_id and setting_key required."); return False
    try:
        logging.info(f"Updating setting '{setting_key}' to '{setting_value}' for user {user_id}")
        response: PostgrestAPIResponse = supabase.table("user_profiles").update({setting_key: setting_value}).eq("user_id", user_id).execute()
        if hasattr(response, 'error') and response.error: logging.error(f"Error updating setting '{setting_key}' for user {user_id}: {response.error}"); return False
        logging.debug(f"Setting '{setting_key}' updated successfully for user {user_id}.")
        return True
    except Exception as e: logging.error(f"Exception updating setting '{setting_key}' for user {user_id}: {e}", exc_info=True); return False


def update_user_character_detail(user_id: str, key: str, value: Any) -> bool:
    """Updates a detail within the 'character' JSONB column in user_profiles."""
    # ... (implementation remains the same as previous version, using fetch-modify-update) ...
    if not supabase: logging.error("update_user_character_detail: Supabase client not available."); return False
    if not user_id or not key: logging.warning("update_user_character_detail: user_id and key required."); return False
    try:
        # 1. Fetch existing character data
        logging.debug(f"Fetching character data for user {user_id} to update key '{key}'")
        fetch_response: Optional[PostgrestAPIResponse] = supabase.table("user_profiles").select("character").eq("user_id", user_id).maybe_single().execute()
        if hasattr(fetch_response, 'error') and fetch_response.error: logging.error(f"Error fetching character data for user {user_id}: {fetch_response.error}"); return False
        character_data = fetch_response.data.get('character') if fetch_response.data else None
        if character_data is None or not isinstance(character_data, dict): character_data = {}
        # 2. Modify data
        if key in ['powers', 'equipments']: # Array appends
            if not isinstance(character_data.get(key), list): character_data[key] = []
            if value not in character_data[key]: character_data[key].append(value); logging.debug(f"Appended '{value}' to character.{key}")
            else: logging.debug(f"Value '{value}' already exists in character.{key}."); return True # Already correct state
        else: # Simple key-value updates
            character_data[key] = value; logging.debug(f"Set character.{key} to '{value}'")
        # 3. Update entire character JSONB column
        logging.info(f"Updating full character data for user {user_id}")
        update_response: PostgrestAPIResponse = supabase.table("user_profiles").update({"character": character_data}).eq("user_id", user_id).execute()
        if hasattr(update_response, 'error') and update_response.error: logging.error(f"Error updating character data for user {user_id}: {update_response.error}"); return False
        logging.info(f"Successfully updated character.{key} for user {user_id}")
        return True
    except Exception as e: logging.error(f"Exception updating character detail for user {user_id}, key '{key}': {e}", exc_info=True); return False


def get_user_preferences(user_id: str) -> Optional[Dict[str, str]]:
    """
    Retrieves user preferences from Supabase voice_agent_preferences and cognitive_preferences.
    Returns a combined dictionary of preferences, applying defaults if specific
    records or values are missing. Returns None if Supabase client is unavailable
    or a major error occurs during fetching.
    Args:
        user_id: The UUID string of the user.
    Returns:
        A dictionary of preferences, or None if a critical error occurs.
    """
    if not supabase: logging.error("get_user_preferences: Supabase client not available."); return None
    if not user_id: logging.warning("get_user_preferences: No user_id provided."); return None

    preferences: Dict[str, Any] = {}

    # --- Define the ACTUAL defaults here ---
    defaults = {
        "speaking_rate": "normal",
        "interaction_style": "friendly",
        "explanation_detail_level": "standard",
        "discussion_depth": "moderate",
        "learning_style": "visual",
        "reading_pace": "normal",
        "preferred_complexity_level": "medium",
        "preferred_interaction_frequency": "regular"
        # Add any other preferences your application uses with their defaults
    }
    # --- End defaults definition ---

    try:
        # --- Query voice agent preferences ---
        logging.debug(f"Fetching voice agent preferences for user: {user_id}")
        # Define keys expected from this table
        voice_pref_keys = ["speaking_rate", "interaction_style", "explanation_detail_level", "discussion_depth"]
        agent_resp: PostgrestAPIResponse = supabase.table("voice_agent_preferences") \
            .select(",".join(voice_pref_keys)) \
            .eq("user_id", user_id).limit(1).execute()

        if hasattr(agent_resp, 'error') and agent_resp.error:
            # Log error but continue to cognitive prefs
            error_info = agent_resp.error.message if hasattr(agent_resp.error, 'message') else str(agent_resp.error)
            logging.error(f"Supabase API error fetching voice prefs for user {user_id}: {error_info}")
        elif agent_resp.data:
            row = agent_resp.data[0]
            # Update only the keys fetched
            for key in voice_pref_keys:
                if key in row and row[key] is not None: # Check if key exists and is not null
                    preferences[key] = row[key]
        else:
            logging.info(f"No voice agent preferences found for user: {user_id}.")
        # --- End query voice agent preferences ---

        # --- Query cognitive preferences ---
        logging.debug(f"Fetching cognitive preferences for user: {user_id}")
        # Define keys expected from this table
        cognitive_pref_keys = ["learning_style", "reading_pace", "preferred_complexity_level", "preferred_interaction_frequency"]
        cognitive_resp: Optional[PostgrestAPIResponse] = supabase.table("cognitive_preferences") \
            .select(",".join(cognitive_pref_keys)).eq("user_id", user_id).limit(1).execute()

        if hasattr(cognitive_resp, 'error') and cognitive_resp.error:
             error_info = cognitive_resp.error.message if hasattr(cognitive_resp.error, 'message') else str(cognitive_resp.error)
             logging.error(f"Supabase API error fetching cognitive preferences for user {user_id}: {error_info}")
        elif cognitive_resp.data:
            row = cognitive_resp.data[0]
            # Update only the keys fetched
            for key in cognitive_pref_keys:
                 if key in row and row[key] is not None: # Check if key exists and is not null
                     preferences[key] = row[key]
        else:
            logging.info(f"No cognitive preferences found for user: {user_id}.")
        # --- End query cognitive preferences ---

    except Exception as e:
        logging.error(f"Unexpected error fetching user preferences for user {user_id}: {e}", exc_info=True)
        # Return None on major error, let caller handle defaults
        return None

    # Consolidate and apply defaults, converting to string as per type hint
    final_preferences: Dict[str, str] = {}
    for key, default_value in defaults.items():
        # Get value from fetched preferences dict, falling back to default if key is missing
        value = preferences.get(key, default_value)
        # Ensure final value is string, handle potential None values from DB get/default
        final_preferences[key] = str(value) if value is not None else str(default_value)

    logging.debug(f"Final preferences for user {user_id}: {final_preferences}")
    return final_preferences