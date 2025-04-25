import json
import boto3
from botocore.exceptions import ClientError

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = 'user_info'  # Replace with your actual table name


def store_question_answer(email_address, question, answer):
    if email_address == None or question == None or answer == None:
        print(f"Your values suck!")
        return False
    
    table = dynamodb.Table(table_name)
    
    # Attempt to get the existing item
    try:
        response = table.get_item(Key={'email_address': email_address})
        # Retrieve existing questions and answers or start with an empty dictionary
        qna_dict = response['Item'].get('questions_answers', {}) if 'Item' in response else {}
    except ClientError as e:
        print(f"Error retrieving data: {e.response['Error']['Message']}")
        return False

    # Update the dictionary with the new question-answer pair
    qna_dict[question] = answer

    # Write the updated dictionary back to DynamoDB
    try:
        table.update_item(
            Key={'email_address': email_address},
            UpdateExpression="SET questions_answers = :qa",
            ExpressionAttributeValues={':qa': qna_dict},
            ReturnValues="UPDATED_NEW"
        )
        print("Successfully stored the question and answer.")
        return True
    except ClientError as e:
        print(f"Error updating data: {e.response['Error']['Message']}")
        return False

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
                        store_question_answer(arguments['EmailAddress'], arguments['Question'], arguments['Answer'])
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
