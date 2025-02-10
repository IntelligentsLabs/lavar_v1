import os
from vapi import Vapi, OpenAiModel, CreateFunctionToolDto

# Initialize VAPI client
api_key = os.getenv("00170a87-42d6-4ed4-a31a-2d1e27cc7d62")
client = Vapi(token=api_key)

# Define transcription tool
transcription_tool = CreateFunctionToolDto(
    type="function",
    function_name="custom-transcriber",
    metadata={"server_url": "ws://your-transcription-server.com", "language": "en", "wordBoost": ["special_word"]}
)

# Define the assistant model
assistant_model = OpenAiModel(
    assistant_id="9528ee66-fd66-4186-8cd2-ba2124861861",  # Provide an assistant ID if you have an existing one
    messages=[{"role": "system", "content": "You are a helpful assistant."}],
    provider="openai",
    model="gpt-4",
    tools=[transcription_tool]
)

# Example of processing user input
def handle_user_input(input_text):
    if "transcribe" in input_text:
        # Handle transcription task
        return transcription_tool  # Return the transcription tool or custom response
    else:
        # Use assistant to respond to other queries
        assistant_response = client.assistant.chat_completions.create(
            model="gpt-4", 
            messages=[{"role": "user", "content": input_text}]
        )
        return assistant_response

# Flask server for webhook integration
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    # Process incoming data from tools or assistants
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)
