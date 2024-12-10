"""
 STEP 1: Read the USER INFO from the WEB client from a file
"""

import json
try:
    from .module import chat_module, invoke_agent_no_memory
except ImportError:
    from src.module import chat_module, invoke_agent_no_memory

# File path for the input text
path = "src/agents/data/"
input_file = path + "example_input_3.json"

# Step 1: Read the input file
with open(input_file, "r") as file:
    raw_text = file.read()
    
# Step 5: Parse into JSON
try:
    parsed_json = json.loads(raw_text)

    """
      STEP 2: Extract the parameters from the JSON
    """
    # NOTE: #### This is the testing message!! #####
    message = "tell me about fourier series" 
    # NOTE: ########################################

    # replace "mock" in the message and conversation history with the actual message
    parsed_json["message"] = message
    parsed_json["params"]["conversation_history"][-1]["content"] = message

    params = parsed_json["params"]

    if "include_test_data" in params:
        include_test_data = params["include_test_data"]
    if "conversation_history" in params:
        conversation_history = params["conversation_history"]
    if "summary" in params:
        summary = params["summary"]
    if "conversational_style" in params:
        conversationalStyle = params["conversational_style"]
    if "question_response_details" in params:
        question_response_details = params["question_response_details"]
    if "conversation_id" in params:
        conversation_id = params["conversation_id"]
    else:
        raise Exception("Internal Error: The conversation id is required in the parameters of the chat module.")

    """
      STEP 3: Call the LLM agent to get a response to the user's message
    """
    response = invoke_agent_no_memory(query=message, \
                                                conversation_history=conversation_history, \
                                                summary=summary, \
                                                conversationalStyle=conversationalStyle, \
                                                question_response_details=question_response_details, \
                                                session_id=conversation_id)
    print("AI Response:", response)
    

except json.JSONDecodeError as e:
    print("Error decoding JSON:", e)



