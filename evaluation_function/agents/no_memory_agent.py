try:
    from .llm_factory import OpenAILLMs
except ImportError:
    from evaluation_function.agents.llm_factory import OpenAILLMs
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str

class ChatbotNoMemoryAgent:
    def __init__(self):
        llm = OpenAILLMs()
        self.llm = llm.get_llm()
        summarisation_llm = OpenAILLMs()
        self.summarisation_llm = summarisation_llm.get_llm()

        # Define a new graph for the conversation & compile it
        self.workflow = StateGraph(State)
        self.workflow_definition()
        self.app = self.workflow.compile()

    def call_model(self, state: State) -> str:
        """Call the LLM model."""
        summary = state.get("summary", "")
        if summary:
            system_message = f"Summary of conversation earlier: {summary}"
            messages = [SystemMessage(content=system_message)] + state['messages']
        else:
            messages = state["messages"]

        valid_messages = self.check_for_valid_messages(messages)
        response = self.llm.invoke(valid_messages)

        return {"messages": [response]}
    
    def check_for_valid_messages(self, messages):
        """ Removing the RemoveMessage() from the list of messages """
        valid_messages = []
        for message in messages:
            if message.type != 'remove':
                valid_messages.append(message)
        return valid_messages
    
    def summarize_conversation(self, state: State):
        """Summarize the conversation."""
        summary = state.get("summary", "")
        if summary:
            summary_message = (
                f"This is summary of the conversation to date: {summary}\n\n"
                "Update the summary by taking into account the new messages above:"
            )
        else:
            # summary_message = "Create a summary of the conversation above:"
            summary_message = "Identify the key conversational preferences of the human user in the conversation above. Do not to focus on the details of the conversation:"

        messages = state["messages"] + [SystemMessage(content=summary_message)] 
        valid_messages = self.check_for_valid_messages(messages)
        summary_response = self.summarisation_llm.invoke(valid_messages)
        # Delete messages that are no longer wanted, except the last ones
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-3]]

        return {"summary": summary_response.content, "messages": delete_messages}
    
    def should_summarize(self, state: State) -> str:
        """Return the next node to execute.
        If there are more than X messages, then we summarize the conversation.
        Otherwise, we call the LLM."""

        messages = state["messages"]
        valid_messages = self.check_for_valid_messages(messages)
        nr_messages = len(valid_messages)
        if "system" in valid_messages[-1].type:
            nr_messages -= 1

        # always pairs of (sent, response) + 1 latest message
        if nr_messages > 11:
            return "summarize_conversation"
        return "call_llm"    

    def workflow_definition(self):
        self.workflow.add_node("call_llm", self.call_model)
        self.workflow.add_node("summarize_conversation", self.summarize_conversation)

        self.workflow.add_conditional_edges(source=START, path=self.should_summarize)
        self.workflow.add_edge("summarize_conversation", "call_llm")
        self.workflow.add_edge("call_llm", END)
    
    def print_update(self, update):
        for k, v in update.items():
            for m in v["messages"]:
                m.pretty_print()
            if "summary" in v:
                print(v["summary"])

    def pretty_response_value(self, event):
        return event["messages"][-1].content
    

if __name__ == "__main__":
    # TESTING
    agent = ChatbotNoMemoryAgent()
    # conversation_history = [
    #     HumanMessage(content="Hi, in one sentence tell me about London."),
    #     AIMessage(content="London is the capital of England."),
    #     HumanMessage(content="What about dogs?"),
    #     AIMessage(content="Dogs are the favorite pets of humans."),
    # ]

    conversation_history = [
        {"content": "Hi, in one sentence tell me about London.", "type": "human"},
        {"content": "London is the capital of England.", "type": "ai"},
        {"content": "What about dogs?", "type": "human"},
        {"content": "Dogs are the favorite pets of humans.", "type": "ai"},
        {"content": "cats", "type": "human"},
        {"content": "Cats are the second favorite pets of humans.", "type": "ai"},
        {"content": "Paris?", "type": "human"},
        {"content": "Paris is the capital of France.", "type": "ai"},
    ]

    def stream_graph_updates(user_input: str):
        for event in agent.app.stream({"messages": conversation_history + [("user", user_input)]}):
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)


    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input)
        except:
            # fallback if input() is not available
            break