# app/personalization/user_preferences.py

import os
from typing import Dict
from supabase import create_client, Client

# Initialize the Supabase client using environment variables.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_interaction_context(user_id: str) -> str:
    """
    Retrieve the user's recent interactions from the voice_interactions and 
    user_book_interactions tables in Supabase, then summarize them into a single string.
    """
    context_entries = []
    try:
        # Query recent voice interactions.
        voice_response = (
            supabase.table("voice_interactions")
            .select("agent_response, timestamp")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .limit(5)
            .execute()
        )
        if voice_response.data:
            for row in voice_response.data:
                timestamp = row.get("timestamp")
                agent_response = row.get("agent_response")
                context_entries.append(f"At {timestamp}, agent said: {agent_response}")
        
        # Query recent user book interactions (for example, any notes the user made).
        book_response = (
            supabase.table("user_book_interactions")
            .select("notes, start_time, end_time")
            .eq("user_id", user_id)
            .order("start_time", desc=True)
            .limit(3)
            .execute()
        )
        if book_response.data:
            for row in book_response.data:
                notes = row.get("notes")
                if notes:
                    start_time = row.get("start_time")
                    end_time = row.get("end_time")
                    context_entries.append(
                        f"Book interaction note (from {start_time} to {end_time}): {notes}"
                    )
    except Exception as e:
        print(f"Error fetching user interaction context for user {user_id}: {e}")
    
    if context_entries:
        return "\n".join(context_entries)
    else:
        return "No prior interactions found."

def get_user_preferences(user_id: str) -> Dict[str, str]:
    """
    Retrieve user preferences from the voice_agent_preferences and cognitive_preferences tables in Supabase.
    Returns a dictionary with keys like 'speaking_rate', 'interaction_style', etc.
    If no record is found for the given user_id, default values are returned.
    """
    preferences = {}
    try:
        # Query voice agent preferences.
        agent_response = (
            supabase.table("voice_agent_preferences")
            .select("speaking_rate, interaction_style, explanation_detail_level, discussion_depth")
            .eq("user_id", user_id)
            .execute()
        )
        if agent_response.data and len(agent_response.data) > 0:
            row = agent_response.data[0]
            preferences["speaking_rate"] = str(row.get("speaking_rate", "normal"))
            preferences["interaction_style"] = row.get("interaction_style", "friendly")
            preferences["explanation_detail_level"] = row.get("explanation_detail_level", "standard")
            preferences["discussion_depth"] = row.get("discussion_depth", "moderate")
        
        # Query cognitive preferences.
        cognitive_response = (
            supabase.table("cognitive_preferences")
            .select("learning_style, reading_pace, preferred_complexity_level, preferred_interaction_frequency")
            .eq("user_id", user_id)
            .execute()
        )
        if cognitive_response.data and len(cognitive_response.data) > 0:
            row = cognitive_response.data[0]
            preferences["learning_style"] = row.get("learning_style", "visual")
            preferences["reading_pace"] = str(row.get("reading_pace", "normal"))
            preferences["preferred_complexity_level"] = str(row.get("preferred_complexity_level", "medium"))
            preferences["preferred_interaction_frequency"] = row.get("preferred_interaction_frequency", "regular")
    except Exception as e:
        print(f"Error fetching user preferences for user {user_id}: {e}")
    
    # Return default preferences if none were found.
    if not preferences:
        preferences = {
            "speaking_rate": "normal",
            "interaction_style": "friendly",
            "explanation_detail_level": "standard",
            "discussion_depth": "moderate",
            "learning_style": "visual",
            "reading_pace": "normal",
            "preferred_complexity_level": "medium",
            "preferred_interaction_frequency": "regular"
        }
    return preferences
