try:
    from .llm_factory import OpenAILLMs
except ImportError:
    from src.agents.llm_factory import OpenAILLMs
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]

class ChatbotNoSummaryNoMemoryAgent:
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
    

    def workflow_definition(self):
        self.workflow.add_node("call_llm", self.call_model)

        self.workflow.add_edge(START, "call_llm")
        self.workflow.add_edge("call_llm", END)
    
    def print_update(self, update):
        for k, v in update.items():
            for m in v["messages"]:
                m.pretty_print()
            if "summary" in v:
                print(v["summary"])

    def pretty_response_value(self, event):
        return event["messages"][-1].content
    

# if __name__ == "__main__":
#     # TESTING
#     agent = ChatbotNoSummaryNoMemoryAgent()
#     conversation_history = [
#         HumanMessage(content="Hi, in one sentence tell me about London."),
#         AIMessage(content="London is the capital of England."),
#         HumanMessage(content="What about dogs?"),
#         AIMessage(content="Dogs are the favorite pets of humans."),
#     ]

#     def stream_graph_updates(user_input: str):
#         for event in agent.app.stream({"messages": conversation_history + [("user", user_input)]}):
#             for value in event.values():
#                 print("Assistant:", value["messages"][-1].content)


#     while True:
#         try:
#             user_input = input("User: ")
#             if user_input.lower() in ["quit", "exit", "q"]:
#                 print("Goodbye!")
#                 break

#             stream_graph_updates(user_input)
#         except:
#             # fallback if input() is not available
#             break