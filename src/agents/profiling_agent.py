try:
    from .llm_factory import OpenAILLMs
except ImportError:
    from src.agents.llm_factory import OpenAILLMs
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.runnables.config import RunnableConfig
from typing import TypeAlias

# TYPES
ValidMessageTypes: TypeAlias = SystemMessage | HumanMessage | AIMessage
AllMessageTypes: TypeAlias = ValidMessageTypes | RemoveMessage

class State(MessagesState):
    summary: str

class ProfilingAgent:
    def __init__(self):
        summarisation_llm = OpenAILLMs()
        self.summarisation_llm = summarisation_llm.get_llm()
        profiling_llm = OpenAILLMs()
        self.profiling_llm = profiling_llm.get_llm()
        self.memory = MemorySaver()

        # Define a new graph for the conversation
        self.workflow = StateGraph(State)
        self.workflow_definition()
        # Finally, we compile it!
        self.app = self.workflow.compile(checkpointer=self.memory)

    def call_model(self, state: State) -> str:
        messages = state["messages"]

        valid_messages = self.check_for_valid_messages(messages)
        response = self.summarisation_llm.invoke(valid_messages)

        # We return a list, because this will get added to the existing list
        return {"messages": [response]}
    
    def check_for_valid_messages(self, messages: list[AllMessageTypes]) -> list[ValidMessageTypes]:
        # Removing the RemoveMessage() from the list of messages
        valid_messages = []
        for message in messages:
            if message.type != 'remove':
                valid_messages.append(message)
        return valid_messages
    
    def workflow_definition(self):
        self.workflow.add_node("summarise", self.fetch_latest_history)
        self.workflow.add_node("call_llm", self.call_model)

        self.workflow.add_edge(START, "summarise")
        self.workflow.add_edge("summarise", "call_llm")
        self.workflow.add_edge("call_llm", END)
    
    def print_update(self, update: dict):
        for k, v in update.items():
            for m in v["messages"]:
                m.pretty_print()
            if "summary" in v:
                print(v["summary"])

    def pretty_response_value(self, event: dict) -> str:
        # print(event["messages"][-1])
        return event["messages"][-1].content
    
    # FETCH HISTORY FROM FILE
    def read_file(self, file_path):
        with open(file_path, 'r') as file:
            return file.read()
        
    def fetch_latest_history(self, state: State, config: RunnableConfig) -> dict:
        # get the session_id from the config
        session_id = config["configurable"].get("thread_id")
        history_path = f'../../data/fake_history/{session_id}_conversation_history.txt'
        history = self.read_file(history_path)

        history_summarisation = history + \
"""Identify the key conversational preferences of the human user in the conversation above. 
Do not to focus on the details of the conversation. """ \
        
        print(f"DEBUGGING: {history_summarisation}")

        return {"messages": [HumanMessage(content=history_summarisation)]}

# if __name__ == "__main__":
#     # TESTING
#     agent = ProfilingAgent()
#     config = {"configurable": {"thread_id": "1"}}

#     while True:
#         user_input = input("User: ")
#         if user_input.lower() in ["quit", "q"]:
#             print("Goodbye!")
#             break

#         events = agent.app.stream(
#             {"messages": [("user", user_input)]}, config, stream_mode="updates"
#         )
#         updates= agent.app.get_state(config).values["messages"]
#         print(f"DEBUGGING: {updates}")
#         for event in events:
#             agent.print_update(event)
#             # event["messages"][-1].pretty_print()