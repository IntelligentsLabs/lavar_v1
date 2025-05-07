# app/api/supabase_db.py

import os
import logging
import secrets # Import secrets for generating random tokens
from typing import Optional, Dict, Any, List
from supabase import create_client, Client, PostgrestAPIResponse
from dotenv import load_dotenv

# --- Initialize Supabase Client ---
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Optional[Client] = None
if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("supabase_db.py: SUPABASE_URL or SUPABASE_KEY environment variables not set.")
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("supabase_db.py: Supabase client initialized successfully.")
    except Exception as e:
        logging.error(f"supabase_db.py: Failed to initialize Supabase client: {e}")

# --- Supabase User Interaction Functions ---

def get_supabase_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the full user record from the Supabase 'users' table based on email.
    """
    if not supabase: logging.error("get_supabase_user_by_email: Supabase client not available."); return None
    if not email: logging.warning("get_supabase_user_by_email: No email provided."); return None

    try:
        response: PostgrestAPIResponse = supabase.table("users").select("*").eq("email", email).limit(1).execute()
        if response.data:
            logging.debug(f"Found user data for email: {email}")
            return response.data[0]
        else:
            logging.debug(f"No user found for email: {email}")
            return None
    except Exception as e:
        logging.error(f"Error fetching user by email {email}: {e}", exc_info=True)
        return None

def get_supabase_user_id_by_email(email: str) -> Optional[str]:
    """
    Retrieves the user's UUID string from the Supabase 'users' table based on email.
    """
    user_data = get_supabase_user_by_email(email)
    if user_data and 'user_id' in user_data:
        return str(user_data['user_id'])
    return None

def get_supabase_user_data_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves combined user data from 'users' and 'user_profiles' tables
    based on the Supabase user UUID string.
    """
    if not supabase: logging.error("get_supabase_user_data_by_id: Supabase client not available."); return None
    if not user_id: logging.warning("get_supabase_user_data_by_id: No user_id provided."); return None

    user_info = {}
    try:
        # Get user data
        user_response: PostgrestAPIResponse = supabase.table("users").select("*").eq("user_id", user_id).limit(1).execute()
        if not user_response.data:
            logging.warning(f"No user found in 'users' table for ID: {user_id}")
            return None
        user_info.update(user_response.data[0])
        # Don't return the placeholder password to the client
        user_info.pop('password', None)

        # Get profile data
        profile_response: PostgrestAPIResponse = supabase.table("user_profiles").select("*").eq("user_id", user_id).limit(1).execute()
        if profile_response.data:
            profile_data = profile_response.data[0]
            # Avoid overwriting user_id from users table or exposing serial PK
            profile_data.pop('user_id', None)
            profile_data.pop('user_profile_id', None)
            user_info.update(profile_data)
        else:
            logging.debug(f"No profile found in 'user_profiles' for user ID: {user_id}.")

        return user_info

    except Exception as e:
        logging.error(f"Error fetching combined user data for ID {user_id}: {e}", exc_info=True)
        return None


def check_if_user_exists(email: str) -> bool:
    """
    Checks if a user exists in the Supabase 'users' table by email.
    """
    return get_supabase_user_id_by_email(email) is not None


def create_supabase_user(user_details: Dict[str, Any]) -> Optional[str]:
    """
    Creates a user in Supabase 'users' (with placeholder password)
    and optionally 'user_profiles'.

    Args:
        user_details: A dictionary containing user info. Expected keys:
                      'username', 'email' (required).
                      Optional: 'picture', 'current_bg', 'character', etc.

    Returns:
        The new user's UUID string on success, None on failure.
    """
    if not supabase: logging.error("create_supabase_user: Supabase client not available."); return None
    if not user_details.get('email') or not user_details.get('username'):
        logging.error("create_supabase_user: Email and username are required.")
        return None

    # --- MODIFICATION: Add Placeholder Password ---
    # Generate a secure, random, unusable placeholder password string
    # This satisfies the NOT NULL constraint for externally authenticated users
    placeholder_password = f"external_auth_{secrets.token_hex(32)}"
    # --- End Modification ---

    # --- User Creation Payload ---
    user_payload = {
        "username": user_details['username'],
        "email": user_details['email'],
        "password": placeholder_password # Assign the placeholder
    }
    # No need to pop 'password' anymore

    new_user_id: Optional[str] = None
    try:
        logging.info(f"Attempting to create user: {user_payload.get('email')} with placeholder password")
        user_insert_response: Optional[PostgrestAPIResponse] = supabase.table("users").insert(user_payload).execute()

        # Check response (Supabase client specific checks might be needed)
        if hasattr(user_insert_response, 'data') and user_insert_response.data:
            new_user_id = str(user_insert_response.data[0]['user_id'])
            logging.info(f"Successfully created user with ID: {new_user_id}")
        else:
            error_msg = "No data returned from insert"
            if hasattr(user_insert_response, 'error') and user_insert_response.error:
                 error_msg = str(user_insert_response.error)
                 # Check for duplicate email/username constraints
                 if 'duplicate key value violates unique constraint "users_email_key"' in error_msg:
                     logging.warning(f"User with email {user_payload.get('email')} already exists.")
                     # If duplicate email means user already exists, retrieve and return existing ID
                     return get_supabase_user_id_by_email(user_payload.get('email'))
                 elif 'duplicate key value violates unique constraint "users_username_key"' in error_msg:
                     logging.warning(f"User with username {user_payload.get('username')} already exists.")
                     return None # Indicate failure due to username conflict

            logging.error(f"Failed to create user {user_payload.get('email')}: {error_msg}")
            return None # Failed insertion

    except Exception as e:
        # Catch potential database errors or other issues
        logging.error(f"Exception creating user {user_payload.get('email')}: {e}", exc_info=True)
        return None

    # --- Profile Creation (if user creation succeeded) ---
    if new_user_id:
        profile_payload = {
            "user_id": new_user_id,
            "profile_picture_url": user_details.get('picture'),
            "current_bg": user_details.get('current_bg', 'black'), # Use default
            "character": user_details.get('character', {}), # Use default empty dict
            "first_name": user_details.get('username')
            # Add other profile fields if provided in user_details
        }
        # Remove None values before inserting profile
        profile_payload = {k: v for k, v in profile_payload.items() if v is not None}

        try:
            logging.info(f"Creating profile for user ID: {new_user_id}")
            profile_insert_response: PostgrestAPIResponse = supabase.table("user_profiles").insert(profile_payload).execute()

            # Check profile insert response (less critical than user insert failure)
            if hasattr(profile_insert_response, 'error') and profile_insert_response.error:
                logging.error(f"Failed to create profile for user {new_user_id}: {profile_insert_response.error}")
            elif profile_insert_response.data:
                 logging.info(f"Successfully created profile for user ID: {new_user_id}")
            else:
                 logging.warning(f"Profile insert for user {new_user_id} did not return data (may be normal).")

        except Exception as e:
            logging.error(f"Exception creating profile for user {new_user_id}: {e}", exc_info=True)
            # User created, but profile failed. Log error but still return user_id.

    return new_user_id # Return the UUID string


def update_user_setting(user_id: str, setting_key: str, setting_value: Any) -> bool:
    """
    Updates a specific setting in the user's profile (user_profiles table).
    """
    if not supabase: logging.error("update_user_setting: Supabase client not available."); return False
    if not user_id or not setting_key: logging.warning("update_user_setting: user_id and setting_key required."); return False

    try:
        logging.info(f"Updating setting '{setting_key}' for user {user_id}")
        response: PostgrestAPIResponse = supabase.table("user_profiles") \
                       .update({setting_key: setting_value}) \
                       .eq("user_id", user_id) \
                       .execute()

        if hasattr(response, 'error') and response.error:
            logging.error(f"Error updating setting '{setting_key}' for user {user_id}: {response.error}")
            return False
        # Optional: Check if rows were affected if Supabase client provides count
        # elif response.count == 0: ...

        logging.debug(f"Setting '{setting_key}' updated successfully for user {user_id}.")
        return True

    except Exception as e:
        logging.error(f"Exception updating setting '{setting_key}' for user {user_id}: {e}", exc_info=True)
        return False


def update_user_character_detail(user_id: str, key: str, value: Any) -> bool:
    """
    Updates a detail within the 'character' JSONB column in user_profiles.
    """
    if not supabase: logging.error("update_user_character_detail: Supabase client not available."); return False
    if not user_id or not key: logging.warning("update_user_character_detail: user_id and key required."); return False

    try:
        # 1. Fetch existing character data
        logging.debug(f"Fetching character data for user {user_id} to update key '{key}'")
        response: Optional[PostgrestAPIResponse] = supabase.table("user_profiles").select("character").eq("user_id", user_id).maybe_single().execute()

        if hasattr(response, 'error') and response.error:
            logging.error(f"Error fetching character data for user {user_id}: {response.error}")
            return False

        character_data = response.data.get('character') if response.data else None
        if character_data is None or not isinstance(character_data, dict):
            character_data = {} # Initialize if null/not dict or profile doesn't exist yet

        # 2. Modify the data in Python
        if key in ['powers', 'equipments']: # Handle array appends
            if not isinstance(character_data.get(key), list):
                character_data[key] = [] # Initialize as list if not already
            if value not in character_data[key]: # Avoid duplicates
                 character_data[key].append(value)
                 logging.debug(f"Appended value to character.{key} for user {user_id}")
            else:
                 logging.debug(f"Value already exists in character.{key} for user {user_id}. No change.")
                 return True # State is already correct
        else: # Handle simple key-value updates
            character_data[key] = value
            logging.debug(f"Set character.{key} for user {user_id}")

        # 3. Update the entire character JSONB column
        logging.info(f"Updating full character data for user {user_id}")
        update_response: PostgrestAPIResponse = supabase.table("user_profiles") \
                               .update({"character": character_data}) \
                               .eq("user_id", user_id) \
                               .execute()

        if hasattr(update_response, 'error') and update_response.error:
            logging.error(f"Error updating character data for user {user_id}: {update_response.error}")
            return False
        # Optional: Check count if available

        logging.info(f"Successfully updated character.{key} for user {user_id}")
        return True

    except Exception as e:
        logging.error(f"Exception updating character detail for user {user_id}: {e}", exc_info=True)
        return False

# --- Get User Preferences (Moved from user_preferences.py for consolidation - depends on preference) ---
# Or keep it in user_preferences.py and import supabase client there
def get_user_preferences(user_id: str) -> Optional[Dict[str, str]]:
    """
    Retrieve user preferences from Supabase voice_agent_preferences and cognitive_preferences.
    Returns combined preferences dict, or None if error/no user.
    Applies defaults if specific records/values are missing.
    """
    if not supabase: logging.error("get_user_preferences: Supabase client not available."); return None
    if not user_id: logging.warning("get_user_preferences: No user_id provided."); return None

    preferences = {}
    defaults = {
        "speaking_rate": "normal", "interaction_style": "friendly",
        "explanation_detail_level": "standard", "discussion_depth": "moderate",
        "learning_style": "visual", "reading_pace": "normal",
        "preferred_complexity_level": "medium", "preferred_interaction_frequency": "regular"
    }

    try:
        # Query voice agent preferences
        logging.debug(f"Fetching voice agent preferences for user: {user_id}")
        agent_resp: PostgrestAPIResponse = supabase.table("voice_agent_preferences") \
            .select("speaking_rate, interaction_style, explanation_detail_level, discussion_depth") \
            .eq("user_id", user_id).limit(1).execute()

        if hasattr(agent_resp, 'error') and agent_resp.error:
            logging.error(f"Supabase error fetching voice prefs for user {user_id}: {agent_resp.error}")
        elif agent_resp.data:
            row = agent_resp.data[0]
            preferences["speaking_rate"] = str(row.get("speaking_rate", defaults["speaking_rate"]))
            preferences["interaction_style"] = str(row.get("interaction_style", defaults["interaction_style"]))
            preferences["explanation_detail_level"] = str(row.get("explanation_detail_level", defaults["explanation_detail_level"]))
            preferences["discussion_depth"] = str(row.get("discussion_depth", defaults["discussion_depth"]))
        else:
            logging.info(f"No voice agent preferences found for user: {user_id}.")

        # Query cognitive preferences
        logging.debug(f"Fetching cognitive preferences for user: {user_id}")
        cognitive_resp: PostgrestAPIResponse = supabase.table("cognitive_preferences") \
            .select("learning_style, reading_pace, preferred_complexity_level, preferred_interaction_frequency") \
            .eq("user_id", user_id).limit(1).execute()

        if hasattr(cognitive_resp, 'error') and cognitive_resp.error:
             logging.error(f"Supabase error fetching cognitive prefs for user {user_id}: {cognitive_resp.error}")
        elif cognitive_resp.data:
            row = cognitive_resp.data[0]
            preferences["learning_style"] = str(row.get("learning_style", defaults["learning_style"]))
            preferences["reading_pace"] = str(row.get("reading_pace", defaults["reading_pace"]))
            preferences["preferred_complexity_level"] = str(row.get("preferred_complexity_level", defaults["preferred_complexity_level"]))
            preferences["preferred_interaction_frequency"] = str(row.get("preferred_interaction_frequency", defaults["preferred_interaction_frequency"]))
        else:
            logging.info(f"No cognitive preferences found for user: {user_id}.")

    except Exception as e:
        logging.error(f"Unexpected error fetching user preferences for user {user_id}: {e}", exc_info=True)
        # Return None on major error, let caller handle defaults
        return None

    # Ensure all default keys are present before returning
    final_preferences = {}
    for key, default_value in defaults.items():
        final_preferences[key] = preferences.get(key, default_value)

    return final_preferences

# app/api/supabase_db.py
# ... (other imports and supabase client) ...

def upsert_voice_agent_preferences(user_id: str, preferences_data: Dict[str, Any]) -> bool:
    """
    Inserts or updates voice agent preferences for a user.
    Args:
        user_id: The user's Supabase UUID string.
        preferences_data: A dictionary of preferences to set.
                          Keys should match column names in 'voice_agent_preferences'.
    Returns:
        True on success, False on failure.
    """
    if not supabase: logging.error("upsert_voice_agent_preferences: Supabase client not available."); return False
    if not user_id or not preferences_data: logging.warning("upsert_voice_agent_preferences: user_id and data required."); return False

    # Ensure user_id is included for the upsert operation if it's not part of a composite PK
    # but is the primary way to identify the row to update or insert.
    # For upsert, the primary key or unique constraint columns must be in the data.
    # If user_id is the PK (or part of a unique constraint used for conflict resolution),
    # it should be in preferences_data or added.
    # Assuming 'user_id' is the column on which conflict should be checked for upsert.
    data_to_upsert = {"user_id": user_id, **preferences_data}
    # Remove any keys from preferences_data that are not columns in the table
    # (e.g. 'preference_id' if it's serial and should not be manually set on insert)
    data_to_upsert.pop('preference_id', None)


    try:
        logging.info(f"Upserting voice agent preferences for user {user_id}: {data_to_upsert}")
        # Use 'user_id' as the column for conflict resolution if it's unique or PK
        response: PostgrestAPIResponse = supabase.table("voice_agent_preferences") \
                                          .upsert(data_to_upsert, on_conflict="user_id") \
                                          .execute()

        if hasattr(response, 'error') and response.error:
            error_info = response.error.message if hasattr(response.error, 'message') else str(response.error)
            logging.error(f"Error upserting voice agent preferences for user {user_id}: {error_info}")
            return False
        logging.info(f"Voice agent preferences upserted successfully for user {user_id}.")
        return True
    except Exception as e:
        logging.error(f"Exception upserting voice agent preferences for user {user_id}: {e}", exc_info=True)
        return False

# Similar function for upsert_cognitive_preferences