# app/vapi_message_handlers/speech_update.py

from app.db import store_in_database
import json
import logging
from app.models import SpeechUpdate  # Import the model

# Set up logging
logger = logging.getLogger(__name__)

async def handle_speech_update(payload):
    try:
        # Parse the incoming payload into the Pydantic model for validation
        validated_payload = SpeechUpdate.model_validate(payload)
        logger.info(f"Speech Update validated: {validated_payload}")

        # Extract the relevant fields
        status = validated_payload.status
        role = validated_payload.role
        messages = validated_payload.artifact.messages

        # Log the speech update for debugging
        with open("speech_update_log.txt", "a") as log_file:
            log_file.write(json.dumps(validated_payload.dict(), indent=4) + "\n")

        # Optionally store the speech update in the database
        db_name = "data/databases/speech_updates.db"
        table_name = "speech_update_data"
        schema = "id TEXT PRIMARY KEY, status TEXT, role TEXT, messages TEXT"

        # Store the speech update data
        success = store_in_database([(status, role, json.dumps(messages))], db_name, table_name, schema)
        if success:
            logger.info(f"Speech update for {status} stored successfully.")
        else:
            logger.error(f"Failed to store speech update for {status}.")

        return {
            "status": "success",
            "message": "Speech update processed successfully."
        }

    except Exception as e:
        logger.error(f"Error processing speech update: {str(e)}")
        return {
            "status": "error",
            "message": f"An error occurred while processing the speech update: {str(e)}"
        }
