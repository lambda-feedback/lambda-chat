"""
 STEP 1: Read the USER INFO from the WEB client from a file
"""

import json
try:
    from ..base_agent.base_agent import invoke_base_agent
    from ..informational_agent.informational_agent import invoke_informational_agent
    from ..socratic_agent.socratic_agent import invoke_socratic_agent
except ImportError:
    from src.agents.base_agent.base_agent import invoke_base_agent
    from src.agents.informational_agent.informational_agent import invoke_informational_agent
    from src.agents.socratic_agent.socratic_agent import invoke_socratic_agent

# File path for the input text
path = "src/agents/utils/example_inputs/"
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
    if "agent_type" in params:
        agent_type = params["agent_type"]
    if "conversation_id" in params:
        conversation_id = params["conversation_id"]
    else:
        raise Exception("Internal Error: The conversation id is required in the parameters of the chat module.")

    """
      STEP 3: Call the LLM agent to get a response to the user's message
    """
    # NOTE: ### SET the agent type to use ###
    agent_type = "informational" 
    # NOTE: #################################

    if agent_type == "socratic":
        invoke = invoke_socratic_agent
    elif agent_type == "informational":
        invoke = invoke_informational_agent
    else:
        # default to 'base'
        invoke = invoke_base_agent

    response = invoke(query=message, \
                            conversation_history=conversation_history, \
                            summary=summary, \
                            conversationalStyle=conversationalStyle, \
                            question_response_details=question_response_details, \
                            session_id=conversation_id)
    
    print("AI Response:", response)
    

except json.JSONDecodeError as e:
    print("Error decoding JSON:", e)



