import json

def lambda_handler(event, context):
    # Check if the HTTP method is POST
    http_method = event.get("requestContext", {}).get("http", {}).get("method")
    
    if http_method == "GET":
        # Return a simple response for GET requests
        return {
            "statusCode": 200,
            "body": json.dumps("hello world")
        }
    
    elif http_method == "POST":
        # Parse the body from the event, assuming it's a JSON string
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            print("Error parsing JSON from the event body")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid JSON format"})
            }

        # Check if the message structure matches the criteria
        if body.get("message", {}).get("type") == "tool-calls":
            tool_calls = body["message"].get("toolCalls", [])
            
            # Ensure we have at least one tool call and it matches the function criteria
            if tool_calls and tool_calls[0].get("type") == "function":
                func = tool_calls[0].get("function", {})
                
                if func.get("name") == "storeQuestionsAndAnswers":
                    # Extract and print the argument values
                    arguments = func.get("arguments", {})
                    print("Arguments:")
                    for key, value in arguments.items():
                        print(f"{key}: {value}")
                    
                    
                    if all(key in arguments and arguments[key] for key in ['Question', 'Answer', 'EmailAddress']):
                        print("Going to store these!! Yaay!!!!")
                    else:
                        print("One or more required keys are missing or empty.")

                    # Return a success response with extracted arguments
                    return {
                        "statusCode": 200,
                        "body": json.dumps({"arguments": arguments})
                    }

        # Return a response if criteria are not met
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Function call 'storeQuestionsAndAnswers' not found"})
        }

    else:
        # Return a 405 Method Not Allowed response for any other HTTP method
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method Not Allowed"})
        }
