import json
import boto3
from botocore.exceptions import ClientError

# Initialize clients
dynamodb = boto3.resource('dynamodb')
table_name = 'user_info'  # Replace with your actual table name
bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
bedrock = boto3.client('bedrock', region_name='us-east-1') 

# List available models
#response = bedrock.list_foundation_models()

# Print model information
# for model in response['modelSummaries']:
#     print(f"Model Name: {model['modelName']}")
#     print(f"Model ID: {model['modelId']}")
#     print(f"Provider: {model['providerName']}")
#     print(f"Input Modalities: {model['inputModalities']}")
#     print(f"Output Modalities: {model['outputModalities']}")
#     print(f"Customizable: {model['customizationsSupported']}")
#     print("---")

# Define the model ID for Claude Sonnet 3.5
CLAUDE_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"

def store_question_answer(email_address, question, answer):
    if not email_address or not question or not answer:
        print("Invalid input values!")
        return False
    
    table = dynamodb.Table(table_name)
    
    try:
        # Attempt to retrieve existing item
        response = table.get_item(Key={'email_address': email_address})
        qna_dict = response['Item'].get('questions_answers', {}) if 'Item' in response else {}
    except ClientError as e:
        print(f"Error retrieving data: {e.response['Error']['Message']}")
        return False

    # Update questions and answers
    qna_dict[question] = answer

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


def get_questions_answers(email_address):
    print(f"Getting questions and answers for: {email_address}")
    
    if not email_address:
        return {"status_code": 400, "message": "Email address not specified."}
    
    table = dynamodb.Table(table_name)
    
    try:
        # Attempt to retrieve the item
        response = table.get_item(Key={'email_address': email_address})
        print(f"DynamoDB response: {response}")
        
        if 'Item' not in response:
            return {"status_code": 404, "message": "Email address not found in the database."}
        
        # Extract questions and answers
        data = response['Item'].get('questions_answers', {})
        print(f"Data retrieved: {data}")
        return {"status_code": 200, "data": data}
    
    except ClientError as e:
        print(f"ClientError: {e.response['Error']['Message']}")
        return {"status_code": 500, "message": f"Internal server error: {e.response['Error']['Message']}"}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"status_code": 500, "message": "An unexpected error occurred."}


def assess_psychology(email_address):
    # Fetch the questions and answers
    result = get_questions_answers(email_address)
    if result["status_code"] != 200:
        return result
    
    questions_answers = result["data"]
    
    # Construct the prompt
    qa_string = "\n".join([f"Q: {q}\nA: {a}" for q, a in questions_answers.items()])
    prompt = (
        f"Using the following questions and answers, create a psychological assessment:\n\n"
        f"{qa_string}\n\n"
        f"Provide a detailed, structured assessment that includes strengths, weaknesses, and "
        f"potential areas for growth based on the responses."
    )
    
    request_body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })

    # Send the prompt to Claude Sonnet 3.5
    try:
        # response = bedrock_client.invoke_model(
        #     modelId=CLAUDE_MODEL_ID,
        #     contentType='application/json',
        #     accept='application/json',
        #     body=json.dumps({"inputText": prompt})
        # )

        response = bedrock_runtime.invoke_model(
            modelId=CLAUDE_MODEL_ID,
            body=request_body
        )
    
        # Parse and print the response
        response_body = json.loads(response['body'].read())
        
        print(response_body)

        print("Response:", response_body['content'][0])
        
        # Parse the model response
        # model_output = json.loads(response_body['content'][0])
        return {"status_code": 200, "assessment": response_body}
    except ClientError as e:
        print(f"Error invoking Claude model: {e.response['Error']['Message']}")
        return {"status_code": 500, "message": f"Error invoking Claude model: {e.response['Error']['Message']}"}
    except Exception as e:
        print(f"Unexpected error invoking Claude model: {e}")
        return {"status_code": 500, "message": "An unexpected error occurred while invoking Claude model."}


def lambda_handler(event, context):
    # Check the HTTP method and path
    http_method = event.get("requestContext", {}).get("http", {}).get("method")
    resource_path = event.get("rawPath", "")
    
    if http_method == "GET" and resource_path == "/assess":
        # Handle 'assess' path
        query_params = event.get("queryStringParameters", {})
        email_address = query_params.get("email_address") if query_params else None
        
        result = assess_psychology(email_address)
        
        if result["status_code"] == 200:
            return {
                "statusCode": 200,
                "body": json.dumps({"assessment": result["assessment"]})
            }
        else:
            return {
                "statusCode": result["status_code"],
                "body": json.dumps({"error": result["message"]})
            }
    
    elif http_method == "GET":
        # Handle other GET requests
        query_params = event.get("queryStringParameters", {})
        email_address = query_params.get("email_address") if query_params else None
        
        result = get_questions_answers(email_address)
        if result["status_code"] == 200:
            return {
                "statusCode": 200,
                "body": json.dumps(result["data"])
            }
        else:
            return {
                "statusCode": result["status_code"],
                "body": json.dumps({"error": result["message"]})
            }
    
    elif http_method == "POST":
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            print("Error parsing JSON from the event body")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid JSON format"})
            }

        # Handle "storeQuestionsAndAnswers" function calls
        if body.get("message", {}).get("type") == "tool-calls":
            tool_calls = body["message"].get("toolCalls", [])
            
            if tool_calls and tool_calls[0].get("type") == "function":
                func = tool_calls[0].get("function", {})
                
                if func.get("name") == "storeQuestionsAndAnswers":
                    arguments = func.get("arguments", {})
                    if all(key in arguments and arguments[key] for key in ['Question', 'Answer', 'EmailAddress']):
                        print("Storing the question and answer.")
                        success = store_question_answer(
                            arguments['EmailAddress'], 
                            arguments['Question'], 
                            arguments['Answer']
                        )
                        if success:
                            return {
                                "statusCode": 200,
                                "body": json.dumps({"message": "Successfully stored the question and answer."})
                            }
                        else:
                            return {
                                "statusCode": 500,
                                "body": json.dumps({"error": "Failed to store the question and answer."})
                            }
                    else:
                        return {
                            "statusCode": 400,
                            "body": json.dumps({"error": "Missing or invalid arguments."})
                        }
        
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Function call 'storeQuestionsAndAnswers' not found"})
        }

    else:
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method Not Allowed"})
        }
