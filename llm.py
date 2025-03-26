#%%
import getpass 
import os 

# def _set_env(var: str):
#     if not os.environ.get(var):
#         os.environ[var] = getpass.getpass(f"{var}: ")


# _set_env("GROQ_API_KEY")


#%%
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages



class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)
#%%
from langchain_groq import ChatGroq

GROQ_API_KEY = "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"
# Initialize LLM
llm = ChatGroq(temperature=0, model="llama-3.1-8b-instant", groq_api_key=GROQ_API_KEY)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)
#%%
graph_builder.add_edge(START, "chatbot")

graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

# from IPython.display import Image, display

# try:
#     display(Image(graph.get_graph().draw_mermaid_png()))
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass
#%%
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            response_text += value["messages"][-1].content + "\n"  # Append messages

            
    return response_text.strip() if response_text else "END Sorry, no response available."

# Ensure the script only runs when executed directly, not when imported
# if __name__ == "__main__":


#%%