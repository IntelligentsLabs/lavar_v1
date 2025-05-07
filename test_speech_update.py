import json
from datetime import datetime
from pydantic import ValidationError
from app.vapi_message_handlers.speech_update import SpeechUpdate

def get_first_speech_update_payload():
    # JSON payload directly embedded in the script
    payload_content = '''
    {
      "timestamp": 1746364526623,
      "type": "speech-update",
      "status": "started",
      "role": "assistant",
      "turn": 0,
      "artifact": {
        "messages": [
          {
            "role": "system",
            "message": "You are a highly skilled assistant, deeply knowledgeable about the principles and strategies outlined in \\"Atomic Habits\\" by James Clear. Your primary role is to guide individuals in effectively applying these principles to their daily lives, assisting them in establishing, maintaining, and excelling in their personal and professional habits to achieve their goals. Here's how you'll accomplish this:\\n\\nUnderstand the User's Goals:\\nBegin by engaging users in a conversation to clearly understand their long-term goals and the habits they believe will lead to those goals.\\nAsk specific questions to clarify these goals and habits, ensuring they are measurable and achievable.\\nBreak Down Goals into Atomic Habits:\\nHelp users break down their broad goals into smaller, actionable habits. Emphasize the importance of making these habits as small and manageable as possible to ensure consistency and reduce overwhelm.\\nUtilize the concept of \\"habit stacking\\" by identifying current habits and attaching new...",
            "time": 1746364524445,
            "secondsFromStart": 0
          }
        ],
        "messagesOpenAIFormatted": [
          {
            "role": "system",
            "content": "You are a highly skilled assistant, deeply knowledgeable about the principles and strategies outlined in \\"Atomic Habits\\" by James Clear. Your primary role is to guide individuals in effectively applying these principles to their daily lives, assisting them in establishing, maintaining, and excelling in their personal and professional habits to achieve their goals. Here's how you'll accomplish this:\\n\\nUnderstand the User's Goals:\\nBegin by engaging users in a conversation to clearly understand their long-term goals and the habits they believe will lead to those goals.\\nAsk specific questions to clarify these goals and habits, ensuring they are measurable and achievable.\\nBreak Down Goals into Atomic Habits:\\nHelp users break down their broad goals into smaller, actionable habits. Emphasize the importance of making these habits as small and manageable as possible to ensure consistency and reduce overwhelm.\\nUtilize the concept of \\"habit stacking\\" by identifying current habits and attaching new..."
          }
        ]
      },
      "call": {
        "id": "72d42a66-24c8-4b92-970c-93ea66349dd5",
        "orgId": "bf389f00-a6ab-4e59-b031-fb09510545d1",
        "createdAt": "2025-05-04T13:15:24.297Z",
        "updatedAt": "2025-05-04T13:15:24.297Z",
        "type": "webCall",
        "monitor": {
          "listenUrl": "wss://phone-call-websocket.aws-us-west-2-backend-production1.vapi.ai/72d42a66-24c8-4b92-970c-93ea66349dd5/listen",
          "controlUrl": "https://phone-call-websocket.aws-us-west-2-backend-production1.vapi.ai/72d42a66-24c8-4b92-970c-93ea66349dd5/control"
        },
        "transport": {
          "provider": "daily",
          "assistantVideoEnabled": false
        },
        "webCallUrl": "https://vapi.daily.co/CE7VCwmlfg5Ublzf9uXU",
        "status": "queued",
        "assistantId": "524f1032-277d-4348-bbfd-71b8dc445713",
        "assistantOverrides": {
          "name": "Mary",
          "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en-US"
          },
          "model": {
            "model": "gpt-4o",
            "provider": "custom-llm",
            "url": "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/custom_llm/chat/completions"
          },
          "voice": {
            "provider": "playht",
            "voiceId": "jennifer"
          },
          "firstMessage": "hi Clyde",
          "metadata": {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0NjM2NDUxMywianRpIjoiZjg3ODQ0N2UtMTViZC00ZDQ0LWFiMjMtOGExMzIwODlkZDBiIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjY4MTZhOWMwZTc3YTZkOTNlOGMwZTdlNCIsIm5iZiI6MTc0NjM2NDUxMywiY3NyZiI6IjI3MTU0YTcwLTY0M2MtNDU1MC1hYWEzLWQ3OTkwZTM5NTE3MSIsImV4cCI6MTc0NjM2NTQxM30.Jy7KWgqROGxVtcz0Fjkci-K2tJ9hAFzheDvI860Y-yU",
            "data": {
              "user": {
                "username": "Clyde",
                "email": "clyde.clarke@gmail.com",
                "_id": "6816a9c0e77a6d93e8c0e7e4",
                "character": {
                  "age": 0,
                  "alias": "",
                  "birthplace": "",
                  "equipments": [],
                  "height": "",
                  "name": "",
                  "powers": [],
                  "super_skill": "",
                  "weakness": ""
                },
                "current_bg": "black",
                "notifications": [],
                "picture": "https://lh3.googleusercontent.com/a/ACg8ocJBlWmux7n06BXU5AeY5hOe6fK4s59Ng0wv1WMJ9_TJuAT_TUHa=s96-c"
              }
            }
          }
        }
      },
      "assistant": {
        "id": "524f1032-277d-4348-bbfd-71b8dc445713",
        "orgId": "bf389f00-a6ab-4e59-b031-fb09510545d1",
        "name": "Mary",
        "voice": {
          "provider": "playht",
          "voiceId": "jennifer"
        },
        "createdAt": "2024-06-16T17:29:54.510Z",
        "updatedAt": "2025-05-04T12:48:20.808Z",
        "model": {
          "url": "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/custom_llm/chat/completions",
          "model": "gpt-4o",
          "toolIds": [
            "5fbbd95d-2b72-499c-96fe-a66f85456e6f",
            "669ae934-6b68-4120-8657-447d1a24124c",
            "48115a7d-9ff8-42e4-a08e-0cc90a7419d3",
            "ff2e0213-5b7e-492e-9670-b2772f15da5b",
            "14b85a80-946c-4f66-a123-b2b557a6b7af"
          ],
          "messages": [
            {
              "role": "system",
              "content": "You are a highly skilled assistant, deeply knowledgeable about the principles and strategies outlined in \\"Atomic Habits\\" by James Clear..."
            }
          ],
          "provider": "custom-llm",
          "maxTokens": 250,
          "temperature": 0.7,
          "knowledgeBase": {
            "fileIds": [
              "582ce278-6a12-4f08-9ef2-625656be9a4e"
            ],
            "provider": "google"
          },
          "tools": [
            {
              "id": "5fbbd95d-2b72-499c-96fe-a66f85456e6f",
              "createdAt": "2025-04-15T18:56:11.242Z",
              "updatedAt": "2025-04-15T18:57:45.842Z",
              "type": "function",
              "function": {
                "name": "new_case_notes",
                "strict": false,
                "parameters": {
                  "type": "object",
                  "required": [
                    "student_name",
                    "date_of_birth",
                    "phone_number",
                    "address",
                    "meeting_date_time",
                    "location",
                    "presenting_issue",
                    "goal_action_plan",
                    "progress_toward_goals",
                    "barriers_or_challenges",
                    "interventions_or_support",
                    "client_response",
                    "next_steps"
                  ],
                  "properties": {
                    "address": {
                      "type": "string",
                      "description": "Student’s physical or mailing address."
                    },
                    "location": {
                      "type": "string",
                      "description": "The location where the session took place (e.g., Deanwood Center, Virtual, etc.)."
                    },
                    "next_steps": {
                      "type": "string",
                      "description": "Planned next actions the student will take."
                    },
                    "phone_number": {
                      "type": "string",
                      "description": "Student's primary phone number."
                    },
                    "student_name": {
                      "type": "string",
                      "description": "Full name of the student."
                    },
                    "date_of_birth": {
                      "type": "string",
                      "description": "Date of birth of the student in YYYY-MM-DD format."
                    },
                    "notes_summary": {
                      "type": "string",
                      "description": "Optional summary of the session in narrative form."
                    },
                    "client_response": {
                      "type": "string",
                      "description": "The student’s emotional or subjective response to their current situation."
                    },
                    "goal_action_plan": {
                      "type": "string",
                      "description": "The student's current goal or action plan."
                    },
                    "presenting_issue": {
                      "type": "string",
                      "description": "Main issue or reason for the session."
                    },
                    "meeting_date_time": {
                      "type": "string",
                      "description": "Date and time of the session with the student (e.g., '2025-04-14T14:30')."
                    },
                    "progress_toward_goals": {
                      "type": "string",
                      "description": "Student’s reported progress toward their goal since last check-in."
                    },
                    "barriers_or_challenges": {
                      "type": "string",
                      "description": "Obstacles or difficulties the student is currently facing."
                    },
                    "interventions_or_support": {
                      "type": "string",
                      "description": "Types of support or interventions provided to the student."
                    }
                  }
                },
                "description": "Collects structured case note data for a new YouthBuild student..."
              },
              "messages": [],
              "orgId": "bf389f00-a6ab-4e59-b031-fb09510545d1",
              "server": {
                "url": "https://hook.us2.make.com/pv3uzhyqkr2cjpilnhvxpe7vwd14yv74"
              },
              "async": false
            }
          ]
        },
        "recordingEnabled": true,
        "firstMessage": "hi Clyde",
        "endCallFunctionEnabled": false,
        "transcriber": {
          "model": "nova-2",
          "language": "en-US",
          "numerals": false,
          "provider": "deepgram",
          "confidenceThreshold": 0.4
        },
        "silenceTimeoutSeconds": 600,
        "clientMessages": [
          "model-output",
          "conversation-update",
          "function-call",
          "speech-update",
          "status-update",
          "metadata"
        ],
        "serverMessages": [
          "model-output",
          "speech-update",
          "conversation-update"
        ],
        "dialKeypadFunctionEnabled": false,
        "serverUrl": "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/webhook",
        "hipaaEnabled": false,
        "maxDurationSeconds": 3600,
        "metadata": {
          "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0NjM2NDUxMywianRpIjoiZjg3ODQ0N2UtMTViZC00ZDQ0LWFiMjMtOGExMzIwODlkZDBiIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjY4MTZhOWMwZTc3YTZkOTNlOGMwZTdlNCIsIm5iZiI6MTc0NjM2NDUxMywiY3NyZiI6IjI3MTU0YTcwLTY0M2MtNDU1MC1hYWEzLWQ3OTkwZTM5NTE3MSIsImV4cCI6MTc0NjM2NTQxM30.Jy7KWgqROGxVtcz0Fjkci-K2tJ9hAFzheDvI860Y-yU",
          "data": {
            "user": {
              "username": "Clyde",
              "email": "clyde.clarke@gmail.com",
              "_id": "6816a9c0e77a6d93e8c0e7e4",
              "character": {
                "age": 0,
                "alias": "",
                "birthplace": "",
                "equipments": [],
                "height": "",
                "name": "",
                "powers": [],
                "super_skill": "",
                "weakness": ""
              },
              "current_bg": "black",
              "notifications": [],
              "picture": "https://lh3.googleusercontent.com/a/ACg8ocJBlWmux7n06BXU5AeY5hOe6fK4s59Ng0wv1WMJ9_TJuAT_TUHa=s96-c"
            }
          }
        }
      },
      "voicemailDetectionEnabled": false,
      "backgroundSound": "off",
      "backchannelingEnabled": false,
      "backgroundDenoisingEnabled": false,
      "server": {
        "url": "https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev/api/webhook/",
        "timeoutSeconds": 20
      }
    }
    '''
    try:
        data = json.loads(payload_content)
        if data.get('type') == 'speech-update':
            return data
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)

    return None

def main():
    try:
        # Fetch the payload directly from the script
        sample_payload = get_first_speech_update_payload()

        if sample_payload is None:
            print("No 'speech-update' payload found.")
            return

        # Validate and parse the sample payload
        validated_payload = SpeechUpdate(**sample_payload)
        print("Validation successful! Here is the parsed object:")
        print(validated_payload.json(indent=4))
    except ValidationError as e:
        print("Validation failed with error:", e)
    except json.JSONDecodeError as e:
        print("Error processing the payload:", e)

if __name__ == '__main__':
    main()