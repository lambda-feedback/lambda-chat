from typing import Any
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
try:
    from .agents.chatbot_summarised_memory_agent import ChatbotAgent
    from .agents.profiling_agent import ProfilingAgent
    from .agents.no_memory_agent import ChatbotNoMemoryAgent
    from .agents.no_summary_no_memory_agent import ChatbotNoSummaryNoMemoryAgent
    from .module_response import Result, Params
except ImportError:
    from src.agents.chatbot_summarised_memory_agent import ChatbotAgent
    from src.agents.profiling_agent import ProfilingAgent
    from src.agents.no_memory_agent import ChatbotNoMemoryAgent
    from src.agents.no_summary_no_memory_agent import ChatbotNoSummaryNoMemoryAgent
    from src.module_response import Result, Params
import time

chatbot_agent = ChatbotAgent(len_memory=4)
profiling_agent = ProfilingAgent()
no_memory_agent = ChatbotNoMemoryAgent()
no_summary_no_memory_agent = ChatbotNoSummaryNoMemoryAgent()

def chat_module(message: Any, params: Params) -> Result:
    """
    Function used by student to converse with a chatbot.
    ---
    The handler function passes three arguments to module():

    - `message` which is the message sent by the student.
    - `params` which are any extra parameters that may be useful,
        e.g., conversation history and summary, conversational style of user, conversation id.

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
    question_response_details = ""

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
    
    start_time = time.time()

    chatbot_response = invoke_agent_no_memory(query=message, \
                                                conversation_history=conversation_history, \
                                                summary=summary, \
                                                conversationalStyle=conversationalStyle, \
                                                question_response_details=question_response_details, \
                                                session_id=conversation_id)
    end_time = time.time()

    result._processing_time = end_time - start_time
    result.add_response("chatbot_response", chatbot_response["output"])
    result.add_metadata("summary", chatbot_response["intermediate_steps"][0])
    result.add_metadata("conversational_style", chatbot_response["intermediate_steps"][1])
    result.add_metadata("conversation_history", chatbot_response["intermediate_steps"][2])
    result.add_processing_time(end_time - start_time)

    return result.to_dict(include_test_data=include_test_data)


# ######## INVOKE AGENTS ########

def invoke_agent_no_summary_no_memory(query: str, conversation_history: list, session_id: str):
    """
    Call an agent that has no conversation memeory and expects to receive all past messages in the params and the latest human request in the query.
    """
    print(f'in invoke_agent_no_summary_no_memory(), query = {query}, thread_id = {session_id}')

    config = {"configurable": {"thread_id": session_id}}
    response_events = no_summary_no_memory_agent.app.invoke({"messages": conversation_history + [HumanMessage(content=query)]}, config=config, stream_mode="values")
    pretty_printed_response = no_summary_no_memory_agent.pretty_response_value(response_events) # for last event in the response

    return {
        "input": query,
        "output": pretty_printed_response,
        "intermediate_steps": []
    }

def invoke_agent_no_memory(query: str, conversation_history: list, summary: str, conversationalStyle: str, question_response_details: str, session_id: str):
    """
    Call an agent that has no conversation memory and expects to receive all past messages in the params and the latest human request in the query.
    If conversation history longer than X, the agent will summarize the conversation and will provide a conversational style analysis.
    """
    print(f'in invoke_agent_no_memory(), query = {query}, thread_id = {session_id}')

    config = {"configurable": {"thread_id": session_id, "summary": summary, "conversational_style": conversationalStyle, "question_response_details": question_response_details}}
    response_events = no_memory_agent.app.invoke({"messages": conversation_history + [HumanMessage(content=query)]}, config=config, stream_mode="values") #updates
    pretty_printed_response = no_memory_agent.pretty_response_value(response_events) # get last event/ai answer in the response

    # Gather Metadata from the agent
    summary = no_memory_agent.get_summary()
    conversationalStyle = no_memory_agent.get_conversational_style()

    return {
        "input": query,
        "output": pretty_printed_response,
        "intermediate_steps": [str(summary), conversationalStyle, conversation_history]
    }

def invoke_simple_agent_with_retry(query: str, session_id: str, prompt_prefix: str = ""):
    """
    Retry the simple agent if a tool fails to run.
    This can help when there are intermittent connection issues to external APIs.
    """
    print(f'in invoke_simple_agent_with_retry(), query = {query}, thread_id = {session_id}')

    config = {"configurable": {"thread_id": session_id, "prompt_prefix": prompt_prefix}}
    response_events = chatbot_agent.app.invoke({"messages": [HumanMessage(content=query)]}, config=config, stream_mode="values")
    pretty_printed_response = chatbot_agent.pretty_response_value(response_events) # get last event/ai answer in the response

    # Gather Metadata from the agent
    summary = chatbot_agent.get_summary(config)
    nr_messages = len(chatbot_agent.app.get_state(config).values["messages"])
    nr_valid_messages = len([m for m in chatbot_agent.app.get_state(config).values["messages"] if m.type != "remove"])
    if "system" in chatbot_agent.app.get_state(config).values["messages"][-1].type:
        nr_valid_messages -= 1
    nr_human_messages = len([m for m in chatbot_agent.app.get_state(config).values["messages"] if m.type == "human"])
    # NOTE: intermediate_steps is expected to be a list
    intermediate_steps = ["Number of messages sent: "+ str(nr_human_messages), "Number of remembered messages:"+str(nr_valid_messages), "Number of total messages in the conversation: "+ str(nr_messages)]
    if summary:
        intermediate_steps.append("Summary: "+ str(summary))
    
    return {
        "input": query,
        "output": pretty_printed_response,
        "intermediate_steps": intermediate_steps
    }

def invoke_profiling_agent_with_retry(session_id: str):
    """
    Retry the profiling agent if a tool fails to run.
    This can help when there are intermittent connection issues to external APIs.
    """
    print(f'in invoke_profiling_agent_with_retry(), session_id = {session_id}')

    config = {"configurable": {"thread_id": session_id}}
    response_events = profiling_agent.app.invoke({"messages": []}, config=config, stream_mode="values")
    pretty_printed_response = profiling_agent.pretty_response_value(response_events) # get last event/ai answer in the response

    return {
        "input": "History of the conversation",
        "output": pretty_printed_response,
        "intermediate_steps": []
    }

# if __name__ == "__main__":
#     conversation_history = [
#         {"content": "Hi, in one word tell me about London.", "type": "human"},
#         {"content": "diverse", "type": "ai"},
#         {"content": "What about dogs?", "type": "human"},
#         {"content": "loyal", "type": "ai"},
#         {"content": "cats", "type": "human"},
#         {"content": "curious", "type": "ai"},
#         {"content": "Paris?", "type": "human"},
#         {"content": "romantic", "type": "ai"},
#         {"content": "What about the weather?", "type": "human"},
#         {"content": "unpredictable", "type": "ai"},
#         {"content": "food?", "type": "human"},
#         {"content": "delicious", "type": "ai"},
#     ]
#     responses = ["what about birds?", "Berlin?"]

#     for message in responses:
#         try:
#             llm_response = chat_module(message, {"include_test_data": True, "conversation_history": conversation_history, "conversation_id": "test1234"})
        
#             print(llm_response)
#             print("AI: "+llm_response["chatbot_response"])
#             print("Summary: ")
#             print(llm_response["metadata"]["summary"])
#             print("Conversational Style: ")
#             print(llm_response["metadata"]["conversational_style"])
#             print("Processing time: " + str(llm_response["processing_time"]))
#             print("--------------------")
#         except Exception as e:
#             print("An error occurred within the chat_module(): " + str(e))