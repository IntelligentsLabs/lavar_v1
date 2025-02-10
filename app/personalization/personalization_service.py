# app/personalization/personalization_service.py

import os
import logging
from typing import Dict

# Import helper functions from our Supabase-based user preferences module.
from app.personalization.user_preferences import get_user_preferences, get_user_interaction_context

# Set up logging
logger = logging.getLogger(__name__)

def get_personalized_context(user_id: str) -> str:
    """
    Aggregates the user's preferences and recent interactions to form a personalized context string.
    
    Returns a string that summarizes:
      - User preferences (e.g., speaking rate, interaction style, etc.)
      - Recent interactions (from voice_interactions and user_book_interactions)
    """
    try:
        # Retrieve preferences and interaction context from Supabase.
        preferences: Dict[str, str] = get_user_preferences(user_id)
        interactions: str = get_user_interaction_context(user_id)
        
        # Convert the preferences dictionary into a readable string.
        preferences_str = ", ".join(f"{key}: {value}" for key, value in preferences.items())
        
        # Combine both pieces of information.
        personalized_context = (
            f"User Preferences: {preferences_str}\n"
            f"Recent Interactions: {interactions}"
        )
        return personalized_context
    except Exception as e:
        logger.error(f"Error generating personalized context for user {user_id}: {e}")
        return "No personalized context available."

def update_user_interaction(user_id: str, new_interaction: Dict) -> bool:
    """
    Updates the user's interaction record in Supabase.
    
    This is a stub implementation that inserts a new record into a 'voice_interactions' table.
    The new_interaction dictionary should contain the fields expected by your table schema.
    
    Returns True on success, or False if an error occurs.
    """
    try:
        from supabase import create_client, Client
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Insert the new interaction record (make sure new_interaction matches your table schema)
        response = supabase.table("voice_interactions").insert({
            **new_interaction,
            "user_id": user_id
        }).execute()

        if response.get("status_code") in (200, 201):
            return True
        else:
            logger.error(f"Failed to update interaction for user {user_id}: {response}")
            return False
    except Exception as e:
        logger.error(f"Error updating user interaction for user {user_id}: {e}")
        return False

# You can add additional functions here, such as updating user preferences,
# processing feedback to adjust personalization, or combining additional data sources.
