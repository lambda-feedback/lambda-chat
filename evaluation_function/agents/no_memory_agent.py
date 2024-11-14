try:
    from .llm_factory import OpenAILLMs
    from .prompts.sum_conv_pref import prompt as sum_conv_pref_prompt
except ImportError:
    from evaluation_function.agents.llm_factory import OpenAILLMs
    from evaluation_function.agents.prompts.sum_conv_pref import prompt as sum_conv_pref_prompt
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
        self.summary = ""

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

        # Save summary for fetching outside the class
        self.summary = summary

        return {"summary": summary, "messages": [response]}
    
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
            summary_message = sum_conv_pref_prompt

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

    def get_summary(self, state: State):
        return self.summary
    
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

    conversation_one_word = [
        {"content": "Hi, in one word tell me about London.", "type": "human"},
        {"content": "diverse", "type": "ai"},
        {"content": "What about dogs?", "type": "human"},
        {"content": "loyal", "type": "ai"},
        {"content": "cats", "type": "human"},
        {"content": "curious", "type": "ai"},
        {"content": "Paris?", "type": "human"},
        {"content": "romantic", "type": "ai"},
        {"content": "What about the weather?", "type": "human"},
        {"content": "unpredictable", "type": "ai"},
        {"content": "food?", "type": "human"},
        {"content": "delicious", "type": "ai"},
    ]
    conversation_computing = [
        {"content": "What’s the difference between a stack and a queue?", "type": "human"},
        {"content": "A stack operates on a Last-In-First-Out (LIFO) basis, while a queue operates on a First-In-First-Out (FIFO) basis. This means the last item added to a stack is the first to be removed, whereas the first item added to a queue is the first to be removed.", "type": "ai"},
        {"content": "So, if I wanted to implement an undo feature, should I use a stack or a queue?", "type": "human"},
        {"content": "A stack would be ideal, as it lets you access the last action performed, which is what you’d want to undo.", "type": "ai"},
        {"content": "How would I implement a stack in Python?", "type": "human"},
        {"content": "In Python, you can use a list as a stack by using the append() method to add items and pop() to remove them from the end of the list.", "type": "ai"},
        {"content": "What about a queue? Would a list work for that too?", "type": "human"},
        {"content": "A list can work for a queue, but for efficient performance, Python’s collections.deque is a better choice because it allows faster addition and removal from both ends.", "type": "ai"},
        {"content": "Could I use a queue for a breadth-first search in a graph?", "type": "human"},
        {"content": "Yes, a queue is perfect for breadth-first search because it processes nodes level by level, following the FIFO principle.", "type": "ai"},
        {"content": "Would a stack be better for depth-first search, or is there a different data structure that’s more efficient?", "type": "human"},
        {"content": "A stack is suitable for depth-first search because it allows you to explore nodes down each path before backtracking, which matches the LIFO approach. Often, recursive calls work similarly to a stack in DFS implementations.", "type": "ai"},
        # {"content": "Are there specific applications where DFS is preferred over BFS?", "type": "human"}
    ]
    conversation_biology = [
        {"content": "Could you explain what dominant and recessive alleles are?", "type": "human"},
        {"content": "Dominant alleles are versions of a gene that show their effect even if there’s only one copy, while recessive alleles only show their effect if two copies are present.", "type": "ai"},
        {"content": "So if someone has one dominant allele and one recessive allele for a trait, which one will be expressed?", "type": "human"},
        {"content": "The dominant allele will be expressed, while the recessive one will not show in the physical traits.", "type": "ai"},
        {"content": "Why is it that recessive traits sometimes reappear in families after generations?", "type": "human"},
        {"content": "Recessive traits can reappear if both parents carry the recessive allele. Even if they don’t show it, they can pass it on, and if both pass on the recessive allele, it can appear in their child.", "type": "ai"},
        {"content": "Could two parents with brown eyes have a child with blue eyes?", "type": "human"},
        {"content": "Yes, if both parents carry the recessive allele for blue eyes, there’s a chance it could show up in their child.", "type": "ai"},
        {"content": "How does this work with other traits, like blood type?", "type": "human"},
        {"content": "Blood type is controlled by multiple alleles: A and B are co-dominant, and O is recessive. So the combinations depend on which alleles the parents carry.", "type": "ai"},
        {"content": "Is it possible to predict traits like height with genetics, or is that more complex?", "type": "human"},
        {"content": "Predicting traits like height is more complex because it’s influenced by multiple genes, environmental factors, and genetic interactions rather than a single pair of alleles.", "type": "ai"},
        # {"content": "Are there any other examples of traits influenced by multiple genes?", "type": "human"}
    ]
    conversation_physics = [
        {"content": "If I throw a ball upward with a velocity of 15 m/s, how long will it take to reach its highest point?", "type": "human"},
        {"content": "To find the time to reach the highest point, you can use the formula t = v/g, where v is the initial velocity and g is the acceleration due to gravity (9.8 m/s²). In this case, it will take about 1.53 seconds.", "type": "ai"},
        {"content": "What happens to the velocity at the top of its path? Does it become zero?", "type": "human"},
        {"content": "Yes, at the highest point, the velocity momentarily becomes zero before gravity pulls it back down.", "type": "ai"},
        {"content": "Once it starts falling back down, does it accelerate at the same rate as when it went up?", "type": "human"},
        {"content": "Exactly. Gravity acts with the same acceleration of 9.8 m/s² in both directions, so the ball accelerates down at the same rate.", "type": "ai"},
        {"content": "Does the ball reach the ground at the same speed it was initially thrown?", "type": "human"},
        {"content": "If air resistance is ignored, yes. It will reach the ground with the same speed of 15 m/s but in the opposite direction.", "type": "ai"},
        {"content": "How would I calculate the total time the ball spends in the air?", "type": "human"},
        {"content": "Since it takes 1.53 seconds to reach the top, the total time to hit the ground would be double that, or about 3.06 seconds.", "type": "ai"},
        {"content": "If I were to throw the ball at an angle instead, would these calculations change a lot?", "type": "human"},
        {"content": "Yes, for a projectile thrown at an angle, you would need to separate the initial velocity into horizontal and vertical components and calculate the time, height, and range separately for each component.", "type": "ai"},
        # {"content": "How do I find the horizontal and vertical components of the velocity?", "type": "human"}
    ]

    # SELECT THE CONVERSATION TO USE
    conversation_history = conversation_computing

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