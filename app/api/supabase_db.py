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
    logging.error(
        "supabase_db.py: FATAL - SUPABASE_URL or SUPABASE_KEY environment variables not set."
    )
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Set logger after basicConfig potentially called by Flask app
        logger = logging.getLogger(__name__)
        logger.info(
            "supabase_db.py: Supabase client initialized successfully.")
    except Exception as e:
        logging.basicConfig(level=logging.ERROR)
        logging.error(
            f"supabase_db.py: Failed to initialize Supabase client: {e}",
            exc_info=True)
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
    if not supabase:
        logger.error(
            "get_supabase_user_by_email: Supabase client not available.")
        return None
    if not email:
        logger.warning("get_supabase_user_by_email: No email provided.")
        return None
    try:
        logger.debug(f"Querying Supabase for user with email: {email}")
        response: PostgrestAPIResponse = supabase.table("users").select(
            "*").eq("email", email).limit(1).execute()
        if hasattr(response, 'error') and response.error:
            logger.error(
                f"Supabase API error fetching user by email {email}: {response.error}"
            )
            return None
        if response.data:
            logger.debug(f"Found user data for email: {email}")
            return response.data[0]
        else:
            logger.debug(f"No user found for email: {email}")
            return None
    except Exception as e:
        logger.error(f"Exception fetching user by email {email}: {e}",
                     exc_info=True)
        return None


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
    Retrieves combined user data. Assumes 'users' table is primary source for
    username, email, first_name, last_name. 'user_profiles' for other details.
    """
    if not supabase:
        logging.error(
            "get_supabase_user_data_by_id: Supabase client not available.")
        return None
    if not user_id:
        logging.warning("get_supabase_user_data_by_id: No user_id provided.")
        return None

    user_info = {}
    try:
        # Get primary user data from 'users' table
        logger.debug(f"Fetching user data from 'users' for ID: {user_id}")
        user_response: PostgrestAPIResponse = supabase.table("users") \
            .select("user_id, username, email, first_name, last_name, signup_date, last_login, account_status, email_verified") \
            .eq("user_id", user_id).limit(1).execute() # Select specific fields

        if hasattr(user_response, 'error') and user_response.error:
            logger.error(
                f"Supabase API error fetching user: {user_response.error}")
            return None
        if not user_response.data:
            logger.warning(f"No user found in 'users' table for ID: {user_id}")
            return None
        user_info.update(user_response.data[0])
        # user_info.pop('password', None) # Password not selected

        # Get additional profile data from 'user_profiles'
        logger.debug(
            f"Fetching profile data from 'user_profiles' for user ID: {user_id}"
        )
        # Select fields NOT already taken from 'users' table primarily, plus others
        profile_response: PostgrestAPIResponse = supabase.table("user_profiles") \
            .select("birth_date, primary_language, secondary_languages, timezone, profile_picture_url, bio, current_bg, character") \
            .eq("user_id", user_id).limit(1).execute()

        if hasattr(profile_response, 'error') and profile_response.error:
            logger.error(
                f"Supabase API error fetching profile: {profile_response.error}"
            )
        elif profile_response.data:
            user_info.update(
                profile_response.data[0]
            )  # Add profile data, potentially overwriting if keys overlap
        else:
            logger.info(
                f"No additional profile found in 'user_profiles' for user ID: {user_id}."
            )

        return user_info
    except Exception as e:
        logger.error(
            f"Exception fetching combined user data for ID {user_id}: {e}",
            exc_info=True)
        return None


def check_if_user_exists(email: str) -> bool:
    """Checks if a user exists in the Supabase 'users' table by email."""
    return get_supabase_user_id_by_email(email) is not None


def create_supabase_user(user_details: Dict[str, Any]) -> Optional[str]:
    """
    Creates a user in Supabase 'users' table (with placeholder password, first_name, last_name)
    and then creates/updates a corresponding record in 'user_profiles'.
    """
    if not supabase:
        logging.error("create_supabase_user: Supabase client not available.")
        return None
    required_keys = ['email', 'username']
    if not all(key in user_details for key in required_keys):
        logging.error(
            f"create_supabase_user: Missing required keys ({', '.join(required_keys)})."
        )
        return None

    placeholder_password = f"external_auth_{secrets.token_hex(32)}"

    # --- User Payload for 'users' table (Includes new fields) ---
    user_payload = {
        "username": user_details['username'],
        "email": user_details['email'],
        "password": placeholder_password,
        "email_verified": user_details.get('email_verified', False),
        # --- ADD first_name and last_name HERE ---
        "first_name": user_details.get('first_name'),
        "last_name": user_details.get('last_name')
    }
    # Remove keys if their value is None, as DB might have defaults or disallow NULL
    # Be careful with keys that have NOT NULL constraints without defaults
    user_payload_cleaned = {
        k: v
        for k, v in user_payload.items() if v is not None
    }
    # Ensure required keys are present even if None (DB might handle it or error)
    if 'username' not in user_payload_cleaned:
        user_payload_cleaned['username'] = user_details['username']
    if 'email' not in user_payload_cleaned:
        user_payload_cleaned['email'] = user_details['email']
    if 'password' not in user_payload_cleaned:
        user_payload_cleaned['password'] = placeholder_password
    # --- End User Payload Modification ---

    profile_user_id: Optional[str] = None  # Will hold the Supabase user_id

    # Check if user already exists by email to avoid trying to re-insert primary user record
    existing_user_id = get_supabase_user_id_by_email(user_details['email'])

    if existing_user_id:
        logger.info(
            f"User {user_details['email']} already exists in 'users' table with ID {existing_user_id}. Will update."
        )
        profile_user_id = existing_user_id
        # Prepare update payload for existing user - only update what's provided
        update_data_for_users_table = {}
        if user_details.get(
                'username'
        ) and user_details['username'] != user_payload_cleaned.get(
                'username'):  # Assuming username can change or is from Auth0
            update_data_for_users_table['username'] = user_details['username']
        if 'email_verified' in user_details:
            update_data_for_users_table['email_verified'] = user_details[
                'email_verified']
        if user_details.get(
                'first_name') is not None:  # Allow updating first_name
            update_data_for_users_table['first_name'] = user_details[
                'first_name']
        if user_details.get(
                'last_name') is not None:  # Allow updating last_name
            update_data_for_users_table['last_name'] = user_details[
                'last_name']
        # Potentially update last_login here: update_data_for_users_table['last_login'] = "now()"

        if update_data_for_users_table:
            try:
                logger.info(
                    f"Updating existing user {profile_user_id} in 'users' table: {update_data_for_users_table}"
                )
                update_response = supabase.table("users").update(
                    update_data_for_users_table).eq("user_id",
                                                    profile_user_id).execute()
                if hasattr(update_response, 'error') and update_response.error:
                    logger.error(
                        f"Error updating existing user {profile_user_id} in 'users': {update_response.error}"
                    )
                    # Decide if this is a fatal error for the token generation
            except Exception as user_update_e:
                logger.error(
                    f"Exception updating existing user {profile_user_id} in 'users': {user_update_e}",
                    exc_info=True)
    else:
        # User does not exist, create them
        logger.info(
            f"User {user_details['email']} not found. Creating new user in 'users' table."
        )
        try:
            user_insert_response: PostgrestAPIResponse = supabase.table(
                "users").insert(user_payload_cleaned).execute()
            if hasattr(user_insert_response,
                       'data') and user_insert_response.data:
                profile_user_id = str(user_insert_response.data[0]['user_id'])
                logger.info(
                    f"Successfully created user in 'users' table with ID: {profile_user_id}"
                )
            else:  # Handle Error
                error_msg = "No data returned from 'users' insert."
                # ... (error handling for insert as before) ...
                if hasattr(user_insert_response,
                           'error') and user_insert_response.error:
                    error_info = user_insert_response.error.message if hasattr(
                        user_insert_response.error, 'message') else str(
                            user_insert_response.error)
                    error_msg = f"Supabase API error: {error_info}"
                logging.error(
                    f"Failed to create user {user_payload_cleaned.get('email')} in 'users' table: {error_msg}"
                )
                return None
        except Exception as e:
            logging.error(
                f"Exception creating user {user_payload_cleaned.get('email')} in 'users' table: {e}",
                exc_info=True)
            return None

    # --- Profile Creation/Update in 'user_profiles' table ---
    if profile_user_id:
        profile_payload = {
            "user_id": profile_user_id,
            # If first_name/last_name are primarily in 'users', you might not duplicate them here,
            # or you might keep them for denormalization/profile-specific versions.
            # For now, let's assume you might still want them in user_profiles for other reasons.
            "first_name": user_details.get('first_name'),  # From user_details
            "last_name": user_details.get('last_name'),  # From user_details
            "email": user_details.get(
                'email'),  # Storing email here too is optional/redundant
            "profile_picture_url": user_details.get('picture'),
            "current_bg": user_details.get('current_bg', 'black'),
            "character": user_details.get('character', {})
        }
        profile_payload_cleaned = {
            k: v
            for k, v in profile_payload.items()
            if v is not None or k == "user_id"
        }  # Ensure user_id is kept

        try:
            logging.info(f"Upserting 'user_profiles' for user ID {profile_user_id}")
            profile_upsert_response: PostgrestAPIResponse = supabase.table("user_profiles") \
                                          .upsert(profile_payload_cleaned, on_conflict="user_id") \
                                          .execute()
            # ... (check profile_upsert_response.error as before) ...
            if hasattr(profile_upsert_response,
                       'error') and profile_upsert_response.error:
                logging.error(
                    f"Failed to upsert profile for user {profile_user_id}: {profile_upsert_response.error}"
                )
            else:
                logging.info(
                    f"Successfully upserted profile for user {profile_user_id}"
                )
        except Exception as e:
            logging.error(
                f"Exception upserting profile for user {profile_user_id}: {e}",
                exc_info=True)

    return profile_user_id


def update_user_setting(user_id: str, setting_key: str, setting_value: Any) -> bool:
    """Updates a specific setting in the user's profile (user_profiles table)."""
    # ... (implementation remains the same as previous version) ...
    if not supabase:
        logging.error("update_user_setting: Supabase client not available.")
        return False
    if not user_id or not setting_key:
        logging.warning(
            "update_user_setting: user_id and setting_key required.")
        return False
    try:
        logging.info(
            f"Updating setting '{setting_key}' to '{setting_value}' for user {user_id}"
        )
        response: PostgrestAPIResponse = supabase.table(
            "user_profiles").update({
                setting_key: setting_value
            }).eq("user_id", user_id).execute()
        if hasattr(response, 'error') and response.error:
            logging.error(
                f"Error updating setting '{setting_key}' for user {user_id}: {response.error}"
            )
            return False
        logging.debug(
            f"Setting '{setting_key}' updated successfully for user {user_id}."
        )
        return True
    except Exception as e:
        logging.error(
            f"Exception updating setting '{setting_key}' for user {user_id}: {e}",
            exc_info=True)
        return False


def update_user_character_detail(user_id: str, key: str, value: Any) -> bool:
    """Updates a detail within the 'character' JSONB column in user_profiles."""
    # ... (implementation remains the same as previous version, using fetch-modify-update) ...
    if not supabase:
        logging.error(
            "update_user_character_detail: Supabase client not available.")
        return False
    if not user_id or not key:
        logging.warning(
            "update_user_character_detail: user_id and key required.")
        return False
    try:
        # 1. Fetch existing character data
        logging.debug(
            f"Fetching character data for user {user_id} to update key '{key}'"
        )
        fetch_response: Optional[PostgrestAPIResponse] = supabase.table(
            "user_profiles").select("character").eq(
                "user_id", user_id).maybe_single().execute()
        if hasattr(fetch_response, 'error') and fetch_response.error:
            logging.error(
                f"Error fetching character data for user {user_id}: {fetch_response.error}"
            )
            return False
        character_data = fetch_response.data.get(
            'character') if fetch_response.data else None
        if character_data is None or not isinstance(character_data, dict):
            character_data = {}
        # 2. Modify data
        if key in ['powers', 'equipments']:  # Array appends
            if not isinstance(character_data.get(key), list):
                character_data[key] = []
            if value not in character_data[key]:
                character_data[key].append(value)
                logging.debug(f"Appended '{value}' to character.{key}")
            else:
                logging.debug(
                    f"Value '{value}' already exists in character.{key}.")
                return True  # Already correct state
        else:  # Simple key-value updates
            character_data[key] = value
            logging.debug(f"Set character.{key} to '{value}'")
        # 3. Update entire character JSONB column
        logging.info(f"Updating full character data for user {user_id}")
        update_response: PostgrestAPIResponse = supabase.table(
            "user_profiles").update({
                "character": character_data
            }).eq("user_id", user_id).execute()
        if hasattr(update_response, 'error') and update_response.error:
            logging.error(
                f"Error updating character data for user {user_id}: {update_response.error}"
            )
            return False
        logging.info(
            f"Successfully updated character.{key} for user {user_id}")
        return True
    except Exception as e:
        logging.error(
            f"Exception updating character detail for user {user_id}, key '{key}': {e}",
            exc_info=True)
        return False


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
    if not supabase:
        logging.error("get_user_preferences: Supabase client not available.")
        return None
    if not user_id:
        logging.warning("get_user_preferences: No user_id provided.")
        return None

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
        voice_pref_keys = [
            "speaking_rate", "interaction_style", "explanation_detail_level",
            "discussion_depth"
        ]
        agent_resp: PostgrestAPIResponse = supabase.table("voice_agent_preferences") \
            .select(",".join(voice_pref_keys)) \
            .eq("user_id", user_id).limit(1).execute()

        if hasattr(agent_resp, 'error') and agent_resp.error:
            # Log error but continue to cognitive prefs
            error_info = agent_resp.error.message if hasattr(
                agent_resp.error, 'message') else str(agent_resp.error)
            logging.error(
                f"Supabase API error fetching voice prefs for user {user_id}: {error_info}"
            )
        elif agent_resp.data:
            row = agent_resp.data[0]
            # Update only the keys fetched
            for key in voice_pref_keys:
                if key in row and row[
                        key] is not None:  # Check if key exists and is not null
                    preferences[key] = row[key]
        else:
            logging.info(
                f"No voice agent preferences found for user: {user_id}.")
        # --- End query voice agent preferences ---

        # --- Query cognitive preferences ---
        logging.debug(f"Fetching cognitive preferences for user: {user_id}")
        # Define keys expected from this table
        cognitive_pref_keys = [
            "learning_style", "reading_pace", "preferred_complexity_level",
            "preferred_interaction_frequency"
        ]
        cognitive_resp: Optional[PostgrestAPIResponse] = supabase.table("cognitive_preferences") \
            .select(",".join(cognitive_pref_keys)).eq("user_id", user_id).limit(1).execute()

        if hasattr(cognitive_resp, 'error') and cognitive_resp.error:
            error_info = cognitive_resp.error.message if hasattr(
                cognitive_resp.error, 'message') else str(cognitive_resp.error)
            logging.error(
                f"Supabase API error fetching cognitive preferences for user {user_id}: {error_info}"
            )
        elif cognitive_resp.data:
            row = cognitive_resp.data[0]
            # Update only the keys fetched
            for key in cognitive_pref_keys:
                if key in row and row[
                        key] is not None:  # Check if key exists and is not null
                    preferences[key] = row[key]
        else:
            logging.info(
                f"No cognitive preferences found for user: {user_id}.")
        # --- End query cognitive preferences ---

    except Exception as e:
        logging.error(
            f"Unexpected error fetching user preferences for user {user_id}: {e}",
            exc_info=True)
        # Return None on major error, let caller handle defaults
        return None

    # Consolidate and apply defaults, converting to string as per type hint
    final_preferences: Dict[str, str] = {}
    for key, default_value in defaults.items():
        # Get value from fetched preferences dict, falling back to default if key is missing
        value = preferences.get(key, default_value)
        # Ensure final value is string, handle potential None values from DB get/default
        final_preferences[key] = str(value) if value is not None else str(
            default_value)

    logging.debug(f"Final preferences for user {user_id}: {final_preferences}")
    return final_preferences

def upsert_user_preference(user_id: str, preference_table: str, preference_data: Dict[str, Any]) -> bool:
    """
    Generic helper to upsert a single preference or a set for a user
    in either 'voice_agent_preferences' or 'cognitive_preferences'.
    Assumes preference_data keys match column names.
    """
    if not supabase: logging.error(f"Supabase client N/A for upsert_user_preference ({preference_table})"); return False
    if not user_id or not preference_table or not preference_data:
        logging.warning("upsert_user_preference: Missing args."); return False

    data_to_upsert = {"user_id": user_id, **preference_data}
    # Remove serial PK if present, as it shouldn't be set on insert/upsert
    data_to_upsert.pop('preference_id', None)

    try:
        logger.info(f"Upserting to {preference_table} for user {user_id}: {data_to_upsert}")
        response: PostgrestAPIResponse = supabase.table(preference_table) \
                                          .upsert(data_to_upsert, on_conflict="user_id") \
                                          .execute()
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error upserting to {preference_table} for {user_id}: {response.error}")
            return False
        logger.info(f"{preference_table} upserted for {user_id}.")
        return True
    except Exception as e:
        logger.error(f"Exception upserting to {preference_table} for {user_id}: {e}", exc_info=True)
        return False
# You can call the generic one from your tool handler or create specific ones:
def _internal_upsert_preference(user_id: str, table_name: str, data_to_upsert: Dict[str, Any]) -> bool:
    """Internal helper for upserting to a preference table."""
    if not supabase: logging.error(f"Supabase client N/A for upserting to {table_name}"); return False

    payload = {"user_id": user_id, **data_to_upsert}
    # Remove serial PK 'preference_id' if present in data_to_upsert, as it's auto-generated
    payload.pop('preference_id', None)

    try:
        logger.info(f"Upserting to {table_name} for user {user_id}: {payload}")
        response: PostgrestAPIResponse = supabase.table(table_name) \
                                          .upsert(payload, on_conflict="user_id") \
                                          .execute()
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error upserting to {table_name} for {user_id}: {response.error}")
            return False
        logger.info(f"{table_name} upserted successfully for {user_id}.")
        return True
    except Exception as e:
        logger.error(f"Exception upserting to {table_name} for {user_id}: {e}", exc_info=True)
        return False

def upsert_voice_agent_preferences(user_id: str, preferences_data: Dict[str, Any]) -> bool:
    """
    Inserts or updates voice agent preferences for a user.
    Args:
        user_id: The user's Supabase UUID string.
        preferences_data: Dict of preferences (e.g., {"speaking_rate": 120}).
    Returns: True on success, False on failure.
    """
    VOICE_PREF_COLUMNS = ["voice_id", "speaking_rate", "interaction_style", "explanation_detail_level", "discussion_depth", "preferred_analogies_type"]
    valid_data = {k: v for k, v in preferences_data.items() if k in VOICE_PREF_COLUMNS}
    if not valid_data:
        logger.warning(f"No valid voice preference keys provided for user {user_id} to update: {preferences_data}")
        return False # Or True if no valid keys means "nothing to do" is a success
    return _internal_upsert_preference(user_id, "voice_agent_preferences", valid_data)

def upsert_cognitive_preferences(user_id: str, preferences_data: Dict[str, Any]) -> bool:
    """
    Inserts or updates cognitive preferences for a user.
    Args:
        user_id: The user's Supabase UUID string.
        preferences_data: Dict of preferences (e.g., {"learning_style": "kinesthetic"}).
    Returns: True on success, False on failure.
    """
    COGNITIVE_PREF_COLUMNS = ["learning_style", "reading_pace", "preferred_complexity_level", "preferred_interaction_frequency", "preferred_question_types", "preferred_discussion_topics", "comprehension_check_frequency"]
    valid_data = {k: v for k, v in preferences_data.items() if k in COGNITIVE_PREF_COLUMNS}
    if not valid_data:
        logger.warning(f"No valid cognitive preference keys provided for user {user_id} to update: {preferences_data}")
        return False # Or True
    return _internal_upsert_preference(user_id, "cognitive_preferences", valid_data)