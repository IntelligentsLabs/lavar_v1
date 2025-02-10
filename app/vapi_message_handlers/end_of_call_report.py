# app/vapi_message_handlers/end_of_call_report.py

from app.db import store_in_database
import json
import logging
from app.models import EndOfCallReport  # Import the model

# Set up logging
logger = logging.getLogger(__name__)

async def handle_end_of_call_report(payload):
    try:
        # Parse the incoming payload into the Pydantic model for validation
        validated_payload = EndOfCallReport.model_validate(payload)
        logger.info(f"End of Call Report validated: {validated_payload}")

        # Extract relevant fields
        analysis = validated_payload.analysis
        artifact = validated_payload.artifact
        call_info = validated_payload.call
        assistant_info = validated_payload.assistant
        
        # Log the processed end-of-call report
        with open("end_of_call_report_log.txt", "a") as log_file:
            log_file.write(json.dumps(validated_payload.dict(), indent=4) + "\n")

        # Optionally store the data in the database
        # Example schema for storing call summary
        db_name = "data/databases/call_reports.db"
        table_name = "call_summary"
        schema = "id TEXT PRIMARY KEY, assistant_name TEXT, summary TEXT, success_evaluation TEXT, transcript TEXT, recording_url TEXT"
        
        success = store_in_database([(call_info.id, assistant_info.name, analysis.summary, analysis.successEvaluation, artifact.transcript, artifact.recordingUrl)], db_name, table_name, schema)
        if success:
            logger.info(f"End of call report for {call_info.id} stored successfully.")
        else:
            logger.error(f"Failed to store report for {call_info.id}.")

        return {
            "status": "success",
            "message": f"End of call report for {call_info.id} processed and stored successfully."
        }

    except Exception as e:
        logger.error(f"Error processing end-of-call report: {str(e)}")
        return {
            "status": "error",
            "message": f"An error occurred while processing the end-of-call report: {str(e)}"
        }
