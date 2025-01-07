try:
    from ..llm_factory import OpenAILLMs
    from .student_prompts import \
        base_student_prompt, curious_student_prompt, contradicting_student_prompt, reliant_student_prompt, confused_student_prompt, unrelated_student_prompt, \
        summary_prompt, update_summary_prompt
    from ..utils.types import InvokeAgentResponseType
except ImportError:
    from src.agents.llm_factory import OpenAILLMs
    from src.agents.student_agent.student_prompts import \
        base_student_prompt, curious_student_prompt, contradicting_student_prompt, reliant_student_prompt, confused_student_prompt, unrelated_student_prompt, \
        summary_prompt, update_summary_prompt
    from src.agents.utils.types import InvokeAgentResponseType

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages
from typing import Annotated, TypeAlias
from typing_extensions import TypedDict

"""
Student agent for synthetic evaluation of the other LLM tutors. This agent is designed to be a student that requires help in the conversation. 
[LLM workflow with a summarisation, and chat agent that receives an external conversation history].

This agent is designed to:
- [summarise_prompt]        summarise the conversation after 'max_messages_to_summarize' number of messages is reached in the conversation
- [role_prompt]             role of a student to ask questions on the topic  
- [student_type]            student's learning profile and comprehension level [many profiles can be chosen from the student_prompts.py]
"""

ValidMessageTypes: TypeAlias = SystemMessage | HumanMessage | AIMessage
AllMessageTypes: TypeAlias = ValidMessageTypes | RemoveMessage

class State(TypedDict):
    messages: Annotated[list[AllMessageTypes], add_messages]
    summary: str
    conversationalStyle: str

class StudentAgent:
    def __init__(self, student_type: str):
        llm = OpenAILLMs()
        self.llm = llm.get_llm()
        summarisation_llm = OpenAILLMs()
        self.summarisation_llm = summarisation_llm.get_llm()
        self.summary = ""
        self.conversationalStyle = ""
        self.type = student_type

        # Define Agent's specific Parameters
        self.max_messages_to_summarize = 11
        self.summary_prompt = summary_prompt
        self.update_summary_prompt = update_summary_prompt
        if self.type == "base":
            self.role_prompt = base_student_prompt
        elif self.type == "curious":
            self.role_prompt = curious_student_prompt
        elif self.type == "contradicting":
            self.role_prompt = contradicting_student_prompt
        elif self.type == "reliant":
            self.role_prompt = reliant_student_prompt
        elif self.type == "confused":
            self.role_prompt = confused_student_prompt
        elif self.type == "unrelated":
            self.role_prompt = unrelated_student_prompt
        else:
            raise Exception("Unknown Student Agent Type")
        # Define a new graph for the conversation & compile it
        self.workflow = StateGraph(State)
        self.workflow_definition()
        self.app = self.workflow.compile()

    def call_model(self, state: State, config: RunnableConfig) -> str:
        """Call the LLM model knowing the role system prompt, the summary and the conversational style."""
        
        # Default AI tutor role prompt
        system_message = self.role_prompt

        # Adding external student progress and question context details from data queries
        question_response_details = config["configurable"].get("question_response_details", "")
        if question_response_details:
            system_message += f"## Known Question Materials: {question_response_details} \n\n"

        # Adding summary and conversational style to the system message
        summary = state.get("summary", "")
        conversationalStyle = state.get("conversationalStyle", "")
        if summary:
            system_message += f"## Summary of conversation earlier: {summary} \n\n"

        messages = [SystemMessage(content=system_message)] + state['messages']

        valid_messages = self.check_for_valid_messages(messages)
        response = self.llm.invoke(valid_messages)

        # Save summary for fetching outside the class
        self.summary = summary

        return {"summary": summary, "messages": [response]}
    
    def check_for_valid_messages(self, messages: list[AllMessageTypes]) -> list[ValidMessageTypes]:
        """ Removing the RemoveMessage() from the list of messages """

        valid_messages: list[ValidMessageTypes] = []
        for message in messages:
            if message.type != 'remove':
                valid_messages.append(message)
        return valid_messages
    
    def summarize_conversation(self, state: State, config: RunnableConfig) -> dict:
        """Summarize the conversation."""

        summary = state.get("summary", "")
        previous_summary = config["configurable"].get("summary", "")
        if previous_summary:
            summary = previous_summary
        
        if summary:
            summary_message = (
                f"This is summary of the conversation to date: {summary}\n\n" +
                self.update_summary_prompt
            )
        else:
            summary_message = self.summary_prompt

        # STEP 1: Summarize the conversation
        messages = state["messages"][:-1] + [SystemMessage(content=summary_message)] 
        valid_messages = self.check_for_valid_messages(messages)
        summary_response = self.summarisation_llm.invoke(valid_messages)

        # Delete messages that are no longer wanted, except the last ones
        delete_messages: list[AllMessageTypes] = [RemoveMessage(id=m.id) for m in state["messages"][:-3]]

        return {"summary": summary_response.content, "messages": delete_messages}
    
    def should_summarize(self, state: State) -> str:
        """
        Return the next node to execute. 
        If there are more than X messages, then we summarize the conversation.
        Otherwise, we call the LLM.
        """

        messages = state["messages"]
        valid_messages = self.check_for_valid_messages(messages)
        nr_messages = len(valid_messages)
        if "system" in valid_messages[-1].type:
            nr_messages -= 1

        # always pairs of (sent, response) + 1 latest message
        if nr_messages > self.max_messages_to_summarize:
            return "summarize_conversation"
        return "call_llm"    

    def workflow_definition(self) -> None:
        self.workflow.add_node("call_llm", self.call_model)
        self.workflow.add_node("summarize_conversation", self.summarize_conversation)

        self.workflow.add_conditional_edges(source=START, path=self.should_summarize)
        self.workflow.add_edge("summarize_conversation", "call_llm")
        self.workflow.add_edge("call_llm", END)

    def get_summary(self) -> str:
        return self.summary

    def print_update(self, update: dict) -> None:
        for k, v in update.items():
            for m in v["messages"]:
                m.pretty_print()
            if "summary" in v:
                print(v["summary"])

    def pretty_response_value(self, event: dict) -> str:
        return event["messages"][-1].content
    
def invoke_student_agent(query: str, conversation_history: list, summary: str, student_type:str, question_response_details: str, session_id: str) -> InvokeAgentResponseType:
    """
    Call a base student agents that forms a basic conversation with the tutor agent.
    """
    print(f'in invoke_base_student_agent(), query = {query}, thread_id = {session_id}')
    agent = StudentAgent(student_type=student_type)

    config = {"configurable": {"thread_id": session_id, "summary": summary, "question_response_details": question_response_details}}
    response_events = agent.app.invoke({"messages": conversation_history + [HumanMessage(content=query)]}, config=config, stream_mode="values") #updates
    pretty_printed_response = agent.pretty_response_value(response_events) # get last event/ai answer in the response

    # Gather Metadata from the agent
    summary = agent.get_summary()

    return {
        "input": query,
        "output": pretty_printed_response,
        "intermediate_steps": [str(summary), conversation_history]
    }