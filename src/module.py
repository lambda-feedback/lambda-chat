import json
from typing import Any

try:
    from .module_response import Result, Params
    from .agents.utils.parse_json_to_prompt import parse_json_to_prompt
    from .agents.informational_agent.informational_agent import invoke_informational_agent
    from .agents.socratic_agent.socratic_agent import invoke_socratic_agent
except ImportError:
    from src.module_response import Result, Params
    from src.agents.utils.parse_json_to_prompt import parse_json_to_prompt
    from src.agents.informational_agent.informational_agent import invoke_informational_agent
    from src.agents.socratic_agent.socratic_agent import invoke_socratic_agent
import time

def chat_module(message: Any, params: Params) -> Result:
    """
    Function used by student to converse with a chatbot.
    ---
    The handler function passes three arguments to module():

    - `message` which is the message sent by the student.
    - `params` which are any extra parameters that may be useful,
        e.g., conversation history and summary, conversational style of user, conversation id, agent type.

    The output of this function is what is returned as the API response
    and therefore must be JSON-encodable. It must also conform to the
    response schema.

    Any standard python library may be used, as well as any package
    available on pip (provided it is added to requirements.txt).

    The way you wish to structure you code (all in this function, or
    split into many) is entirely up to you. All that matters are the
    return types and that module() is the main function used
    to output the Chatbot response.
    """

    result = Result()
    include_test_data = False
    conversation_history = []
    summary = ""
    conversationalStyle = ""
    question_response_details_prompt = ""
    agent_type = "informational" # default

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
        question_submission_summary = question_response_details["questionSubmissionSummary"] if "questionSubmissionSummary" in question_response_details else []
        question_information = question_response_details["questionInformation"] if "questionInformation" in question_response_details else {}
        question_access_information = question_response_details["questionAccessInformation"] if "questionAccessInformation" in question_response_details else {}
        question_response_details_prompt = parse_json_to_prompt(
            question_submission_summary,
            question_information,
            question_access_information
        )
    if "agent_type" in params:
        agent_type = params["agent_type"]
    if "conversation_id" in params:
        conversation_id = params["conversation_id"]
    else:
        raise Exception("Internal Error: The conversation id is required in the parameters of the chat module.")
    
    
    
    start_time = time.time()
   
    if agent_type == "socratic":
        invoke = invoke_socratic_agent
    elif agent_type == "informational":
        invoke = invoke_informational_agent
    else:
        raise Exception("Input Parameter Error: Unknown Chat Agent Type")

    chatbot_response = invoke(query=message, \
                            conversation_history=conversation_history, \
                            summary=summary, \
                            conversationalStyle=conversationalStyle, \
                            question_response_details=question_response_details_prompt, \
                            session_id=conversation_id)

    end_time = time.time()

    result._processing_time = end_time - start_time
    result.add_response("chatbot_response", chatbot_response["output"])
    result.add_metadata("summary", chatbot_response["intermediate_steps"][0])
    result.add_metadata("conversational_style", chatbot_response["intermediate_steps"][1])
    result.add_metadata("conversation_history", chatbot_response["intermediate_steps"][2])
    result.add_processing_time(end_time - start_time)

    return result.to_dict(include_test_data=include_test_data)