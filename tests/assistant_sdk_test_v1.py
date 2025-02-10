import os
from vapi import Vapi, OpenAiModel, CreateFunctionToolDto

# Initialize VAPI client
# Initialize VAPI client
api_key = os.getenv("00170a87-42d6-4ed4-a31a-2d1e27cc7d62")
client = Vapi(token=api_key)


# Define the transcription tool (optional, if you want to use transcription)
transcription_tool = CreateFunctionToolDto(
    type="function",
    function_name="custom-transcriber",  # Define a function for the transcription tool
    metadata={"server_url": "ws://your-transcription-server.com", "language": "en", "wordBoost": ["special_word"]}
)

# Define the assistant model
assistant_model = OpenAiModel(
    assistant_id="your_assistant_id_here",  # You need to provide an existing assistant ID
    messages=[{"role": "system", "content": "You are a helpful assistant."}],
    provider="openai",
    model="gpt-4",
    tools=[transcription_tool]  # Use this tool if needed
)

# Function to send user input to the assistant and get a response
def chat_with_assistant(user_input):
    # Use assistant_model to handle the conversation (not the Vapi client directly)
    assistant_response = assistant_model.chat_completions.create(
        model="gpt-4",  # Use GPT-4 to generate the response
        messages=[{"role": "user", "content": user_input}]  # Pass the user input to the assistant
    )
    
    # Get the response and return the assistant's answer
    return assistant_response["choices"][0]["message"]["content"]

# Main loop for chatting with the assistant in terminal
def start_chat():
    print("Chat with your assistant. Type 'exit' to end the conversation.\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == 'exit':
            print("Ending the chat. Goodbye!")
            break
        
        # Get assistant's response using assistant_model
        response = chat_with_assistant(user_input)
        
        # Print the assistant's response
        print(f"Assistant: {response}")

if __name__ == '__main__':
    start_chat()
