import json
try:
    from .src.module import chat_module
except ImportError:
    from src.module import chat_module

def handler(event, context):
    """
    Lambda handler function
    """
    # Log the input event TODO: remove this line
    print("Received event:", json.dumps(event, indent=2))

    if "message" not in event:
        return {
            "statusCode": 400,
            "body": "Missing 'message' key in event. Please confirm the key in the json body."
        }
    if "params" not in event:
        return {
            "statusCode": 400,
            "body": "Missing 'params' key in event. Please confirm the key in the json body. Make sure it contains the necessary conversation_id."
        }
    
    message = event.get("message", None)
    params = event.get("params", None)

    try:
        chatbot_response = chat_module(message, params)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"An error occurred within the chat_module(): {str(e)}"
        }

    # Create a response
    response = {
        "statusCode": 200,
        "body": chatbot_response
    }

    return response