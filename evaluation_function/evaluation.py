from typing import Any
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
try:
    from .agents.chatbot_summarised_memory_agent import ChatbotAgent
    from .agents.profiling_agent import ProfilingAgent
    from .agents.no_memory_agent import ChatbotNoMemoryAgent
    from .agents.no_summary_no_memory_agent import ChatbotNoSummaryNoMemoryAgent
    from .evaluation_response import Result, Params
except ImportError:
    from evaluation_function.agents.chatbot_summarised_memory_agent import ChatbotAgent
    from evaluation_function.agents.profiling_agent import ProfilingAgent
    from evaluation_function.agents.no_memory_agent import ChatbotNoMemoryAgent
    from evaluation_function.agents.no_summary_no_memory_agent import ChatbotNoSummaryNoMemoryAgent
    from evaluation_function.evaluation_response import Result, Params
import time
import uuid

chatbot_agent = ChatbotAgent(len_memory=4)
profiling_agent = ProfilingAgent()
no_memory_agent = ChatbotNoMemoryAgent()
no_summary_no_memory_agent = ChatbotNoSummaryNoMemoryAgent()

def evaluation_function(response: Any, answer: Any, params: Params) -> Result:
    """
    Function used to evaluate a student response.
    ---
    The handler function passes three arguments to evaluation_function():

    - `response` which are the answers provided by the student.
    - `answer` which are the correct answers to compare against.
    - `params` which are any extra parameters that may be useful,
        e.g., error tolerances.

    The output of this function is what is returned as the API response
    and therefore must be JSON-encodable. It must also conform to the
    response schema.

    Any standard python library may be used, as well as any package
    available on pip (provided it is added to requirements.txt).

    The way you wish to structure you code (all in this function, or
    split into many) is entirely up to you. All that matters are the
    return types and that evaluation_function() is the main function used
    to output the evaluation response.
    """

    result = Result(is_correct=True)
    include_test_data = False
    conversation_history = []

    if "include_test_data" in params:
        include_test_data = params["include_test_data"]
    if "conversation_history" in params:
        conversation_history = params["conversation_history"]
    start_time = time.time()

    ##### External DB: user progress data into an LLM prompt prefix -> use student ID, question ID, response area ID, and other relevant data
    # student_data_prompt = model_student_data(student_id, response_area_id)

    chatbot_response = invoke_agent_no_memory(response, conversation_history, session_id=uuid.uuid4()) # TODO: to be replaced by Question ID set by web client
    end_time = time.time()

    result._processing_time = end_time - start_time
    result.add_feedback("chatbot_response", chatbot_response["output"])
    result.add_metadata("summary", chatbot_response["intermediate_steps"][0])
    result.add_metadata("conversational_style", chatbot_response["intermediate_steps"][1])
    result.add_metadata("conversation_history", chatbot_response["intermediate_steps"][2])
    result.add_processing_time(end_time - start_time)

    return result.to_dict(include_test_data=include_test_data)


# ######## INVOKE AGENTS ########

def invoke_agent_no_summary_no_memory(query: str, conversation_history: list, session_id: str):
    """ Call an agent that has no conversation memeory and expects to receive all past messages in the params and the latest human request in the query.
    """
    print(f'in invoke_agent_no_summary_no_memory(), query = {query}, thread_id = {session_id}')
    config = {"configurable": {"thread_id": session_id}}
    response_events = no_summary_no_memory_agent.app.invoke({"messages": conversation_history + [HumanMessage(content=query)]}, config=config, stream_mode="values") #updates
    pretty_printed_response = no_summary_no_memory_agent.pretty_response_value(response_events) # for last event in the response

    return {
        "input": query,
        "output": pretty_printed_response,
        "intermediate_steps": []
    }

def invoke_agent_no_memory(query: str, conversation_history: list, session_id: str):
    """ Call an agent that has no conversation memory and expects to receive all past messages in the params and the latest human request in the query.
        If conversation history longer than X, the agent will summarize the conversation and will provide a conversational style analysis.
    """
    print(f'in invoke_agent_no_memory(), query = {query}, thread_id = {session_id}')
    config = {"configurable": {"thread_id": session_id}}
    response_events = no_memory_agent.app.invoke({"messages": conversation_history + [HumanMessage(content=query)]}, config=config, stream_mode="values") #updates
    pretty_printed_response = no_memory_agent.pretty_response_value(response_events) # for last event in the response

    summary = no_memory_agent.get_summary()
    conversationalStyle = no_memory_agent.get_conversational_style()

    return {
        "input": query,
        "output": pretty_printed_response,
        "intermediate_steps": [str(summary), conversationalStyle, conversation_history]
    }

def invoke_simple_agent_with_retry(query: str, session_id: str, prompt_prefix: str = ""):
    """Retry the simple agent if a tool fails to run.
    This can help when there are intermittent connection issues to external APIs.
    """
    print(f'in invoke_simple_agent_with_retry(), query = {query}, thread_id = {session_id}')
    config = {"configurable": {"thread_id": session_id, "prompt_prefix": prompt_prefix}}
    response_events = chatbot_agent.app.invoke({"messages": [HumanMessage(content=query)]}, config=config, stream_mode="values") #updates
    # print(f'in invoke_simple_agent_with_retry(), response = {response_events}')
    pretty_printed_response = chatbot_agent.pretty_response_value(response_events) # for last event in the response
    # print(f'in invoke_simple_agent_with_retry(), pretty_printed_response = {pretty_printed_response}')

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
    """Retry the profiling agent if a tool fails to run.
    This can help when there are intermittent connection issues to external APIs.
    """
    print(f'in invoke_profiling_agent_with_retry(), session_id = {session_id}')
    config = {"configurable": {"thread_id": session_id}}
    response_events = profiling_agent.app.invoke({"messages": []}, config=config, stream_mode="values") #updates

    pretty_printed_response = profiling_agent.pretty_response_value(response_events) # for last event in the response

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

#     for response in responses:
#         llm_response = evaluation_function(response, "", {"include_test_data": True, "conversation_history": conversation_history})
#         print("AI: "+llm_response["feedback"])
#         print("Summary: ")
#         print(llm_response["metadata"]["summary"])
#         print("Conversational Style: ")
#         print(llm_response["metadata"]["conversational_style"])
#         print("Processing time: " + str(llm_response["processing_time"]))
#         print("--------------------")