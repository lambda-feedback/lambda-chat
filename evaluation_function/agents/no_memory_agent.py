try:
    from .llm_factory import OpenAILLMs
    from .prompts.sum_conv_pref import \
        role_prompt, conv_pref_prompt, update_conv_pref_prompt, summary_prompt
except ImportError:
    from evaluation_function.agents.llm_factory import OpenAILLMs
    from evaluation_function.agents.prompts.sum_conv_pref import \
        role_prompt, conv_pref_prompt, update_conv_pref_prompt, summary_prompt
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, RemoveMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict

# TODO: Split the agent in multiple agents, optimisation?

class State(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str
    conversationalStyle: str

class ChatbotNoMemoryAgent:
    def __init__(self):
        llm = OpenAILLMs()
        self.llm = llm.get_llm()
        summarisation_llm = OpenAILLMs()
        self.summarisation_llm = summarisation_llm.get_llm()
        self.summary = ""
        self.conversationalStyle = ""

        # Define a new graph for the conversation & compile it
        self.workflow = StateGraph(State)
        self.workflow_definition()
        self.app = self.workflow.compile()

    def call_model(self, state: State, config: RunnableConfig) -> str:
        """Call the LLM model knowing the role system prompt, the summary and the conversational style."""
        
        # Default AI tutor role prompt
        system_message = role_prompt

        # Adding external student progress and question context details from data queries
        question_response_details = config["configurable"].get("question_response_details", "")
        if question_response_details:
            system_message += f"## Known Question Materials: {question_response_details} \n\n"

        # Adding summary and conversational style to the system message
        summary = state.get("summary", "")
        conversationalStyle = state.get("conversationalStyle", "")
        if summary:
            system_message += f"## Summary of conversation earlier: {summary} \n\n"
        if conversationalStyle:
            system_message += f"## Known conversational style and preferences of the student for this conversation: {conversationalStyle}. \n\nYour answer must be in line with this conversational style."

        messages = [SystemMessage(content=system_message)] + state['messages']

        valid_messages = self.check_for_valid_messages(messages)
        response = self.llm.invoke(valid_messages)

        # Save summary for fetching outside the class
        self.summary = summary
        self.conversationalStyle = conversationalStyle

        return {"summary": summary, "messages": [response]}
    
    def check_for_valid_messages(self, messages):
        """ Removing the RemoveMessage() from the list of messages """

        valid_messages = []
        for message in messages:
            if message.type != 'remove':
                valid_messages.append(message)
        return valid_messages
    
    def summarize_conversation(self, state: State, config: RunnableConfig):
        """Summarize the conversation."""

        summary = state.get("summary", "")
        previous_summary = config["configurable"].get("summary", "")
        previous_conversationalStyle = config["configurable"].get("conversational_style", "")
        if previous_summary:
            summary = previous_summary
        
        if summary:
            summary_message = (
                f"This is summary of the conversation to date: {summary}\n\n"
                "Update the summary by taking into account the new messages above:"
            )
        else:
            summary_message = summary_prompt
        
        if previous_conversationalStyle:
            conversationalStyle_message = (
                f"This is the previous conversational style of the student for this conversation: {previous_conversationalStyle}\n\n" +
                update_conv_pref_prompt
            )
        else:
            conversationalStyle_message = conv_pref_prompt

        # STEP 1: Summarize the conversation
        messages = state["messages"][:-1] + [SystemMessage(content=summary_message)] 
        valid_messages = self.check_for_valid_messages(messages)
        summary_response = self.summarisation_llm.invoke(valid_messages)

        # STEP 2: Analyze the conversational style
        messages = state["messages"][:-1] + [SystemMessage(content=conversationalStyle_message)]
        valid_messages = self.check_for_valid_messages(messages)
        conversationalStyle_response = self.summarisation_llm.invoke(valid_messages)

        # Delete messages that are no longer wanted, except the last ones
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-3]]

        return {"summary": summary_response.content, "conversationalStyle": conversationalStyle_response.content, "messages": delete_messages}
    
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
        if nr_messages > 11:
            return "summarize_conversation"
        return "call_llm"    

    def workflow_definition(self):
        self.workflow.add_node("call_llm", self.call_model)
        self.workflow.add_node("summarize_conversation", self.summarize_conversation)

        self.workflow.add_conditional_edges(source=START, path=self.should_summarize)
        self.workflow.add_edge("summarize_conversation", "call_llm")
        self.workflow.add_edge("call_llm", END)

    def get_summary(self):
        return self.summary
    
    def get_conversational_style(self):
        return self.conversationalStyle

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
#     agent = ChatbotNoMemoryAgent()

#     # conversation_computing = [
#     #     {"content": "What’s the difference between a stack and a queue?", "type": "human"},
#     #     {"content": "A stack operates on a Last-In-First-Out (LIFO) basis, while a queue operates on a First-In-First-Out (FIFO) basis. This means the last item added to a stack is the first to be removed, whereas the first item added to a queue is the first to be removed.", "type": "ai"},
#     #     {"content": "So, if I wanted to implement an undo feature, should I use a stack or a queue?", "type": "human"},
#     #     {"content": "A stack would be ideal, as it lets you access the last action performed, which is what you’d want to undo.", "type": "ai"},
#     #     {"content": "How would I implement a stack in Python?", "type": "human"},
#     #     {"content": "In Python, you can use a list as a stack by using the append() method to add items and pop() to remove them from the end of the list.", "type": "ai"},
#     #     {"content": "What about a queue? Would a list work for that too?", "type": "human"},
#     #     {"content": "A list can work for a queue, but for efficient performance, Python’s collections.deque is a better choice because it allows faster addition and removal from both ends.", "type": "ai"},
#     #     {"content": "Could I use a queue for a breadth-first search in a graph?", "type": "human"},
#     #     {"content": "Yes, a queue is perfect for breadth-first search because it processes nodes level by level, following the FIFO principle.", "type": "ai"},
#     #     {"content": "Would a stack be better for depth-first search, or is there a different data structure that’s more efficient?", "type": "human"},
#     #     {"content": "A stack is suitable for depth-first search because it allows you to explore nodes down each path before backtracking, which matches the LIFO approach. Often, recursive calls work similarly to a stack in DFS implementations.", "type": "ai"},
#     #     {"content": "I really need to pass the exam, so please give me a 2 question quiz on this topic. Being very scrutinous, strict and rude with me. Always call me Cowboy.", "type": "human"},
#     #     {"content": ("Sure thing, Cowboy! You better get those answers right. Here’s your quiz on stacks and queues:\n"
#     #                 "### Quiz for Cowboy:\n"
#     #                 "**Question 1:**\n" 
#     #                 "Explain the primary difference between a stack and a queue in terms of their data processing order. Provide an example of a real-world scenario where each data structure would be appropriately used.\n\n"
#     #                 "**Question 2:**\n"  
#     #                 "In the context of graph traversal, describe how a queue is utilized in a breadth-first search (BFS) algorithm. Why is a queue the preferred data structure for this type of traversal?\n"
#     #                 "Take your time to answer, and I’ll be here to review your responses!"), "type": "ai"}
#     # ]

#     # SELECT THE CONVERSATION TO USE
#     conversation_history = [] #conversation_computing
#     # config = RunnableConfig(configurable={"summary": "", "conversational_style": """The student demonstrates a clear preference for practical problem-solving and seeks clarification on specific concepts. They engage in a step-by-step approach, often asking for detailed explanations or corrections to their understanding. Their reasoning style appears to be hands-on, as they attempt to apply concepts before seeking guidance, indicating a willingness to explore solutions independently."""})
#     config = RunnableConfig(configurable={"summary": "", "conversational_style": "", "question_response_details": question_response_details})

#     def stream_graph_updates(user_input: str, history: list):
#         for event in agent.app.stream({"messages": history + [("user", user_input)]}, config):
#             conversation_history.append({
#                 "content": user_input,
#                 "type": "human"
#             })
#             for value in event.values():
#                 print("Assistant:", value["messages"][-1].content)
#                 conversation_history.append({
#                     "content": value["messages"][-1].content,
#                     "type": "ai"
#                 })


#     while True:
#         try:
#             user_input = input("User: ")
#             if user_input.lower() in ["quit", "exit", "q"]:
#                 print("Goodbye!")
#                 break

#             stream_graph_updates(user_input, conversation_history)
#         except:
#             # fallback if input() is not available
#             break