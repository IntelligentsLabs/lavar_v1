# test_speech_update.py

from datetime import datetime
from pydantic import BaseModel, ValidationError
from app.vapi_message_handlers.speech_update import SpeechUpdate

# Sample payload based on expected structure from 'speech_update.py'
sample_payload = {
    "timestamp": 1735580385287,
    "type": "speech-update",
    "status": "stopped",
    "role": "assistant",
    "artifact": {
        "messages": [
            {
                "role": "system",
                "message": "This is a test system message.",
                "time": 1735580370550,
                "secondsFromStart": 0
            },
            {
                "role": "bot",
                "message": "Hello!",
                "time": 1735580372255,
                "endTime": 1735580372995,
                "secondsFromStart": 1.36,
                "duration": 740,
                "source": ""
            }
        ],
        "messagesOpenAIFormatted": [
            {"role": "system", "content": "This is a test OpenAI message."},
            {"role": "assistant", "content": "Hello!"}
        ]
    },
    "call": {
        "id": "07587321-0342-4e16-94ed-15e2a53792ae",
        "orgId": "bf389f00-a6ab-4e59-b031-fb09510545d1",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "type": "webCall",
        'assistantOverrides': {
            'clientMessages': ['transfer-update', 'transcript']
        }
    },
    "assistant": {
        "id": "b33d016a-db85-4e34-801b-5f7a175a077e",
        "name": "Test Assistant",
        "voice": {"model": "sonic-english", "voiceId": "248be419-c632-4f23-adf1-5324ed7dbf1d", "provider": "cartesia", "fillerInjectionEnabled": False},
        "firstMessage": "Hi there!"
    }
}

def main():
    try:
        # Validate and parse the sample payload
        validated_payload = SpeechUpdate(**sample_payload)
        print("Validation successful! Here is the parsed object:")
        print(validated_payload.json(indent=4))
    except ValidationError as e:
        print("Validation failed with error:", e)

if __name__ == '__main__':
    main()