import json
try:
    from .src.module import chat_module
except ImportError:
    from src.module import chat_module

def handler(event, context):
    """
    Lambda handler function
    """
    # Log the input event
    print("Received event:", json.dumps(event, indent=2))

    if "answer" not in event:
        return {
            "statusCode": 400,
            "body": "Missing 'answer' key in event"
        }
    if "response" not in event:
        return {
            "statusCode": 400,
            "body": "Missing 'response' key in event"
        }
    if "params" not in event:
        return {
            "statusCode": 400,
            "body": "Missing 'params' key in event"
        }
    
    answer = event.get("answer", None)
    response = event.get("response", None)
    params = event.get("params", None)

    chatbot_response = chat_module(response, answer, params)

    # Create a response
    response = {
        "statusCode": 200,
        "body": chatbot_response
    }

    return response
