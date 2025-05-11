#%%
import getpass 
import os 
from typing import Annotated
from pydantic import BaseModel
from typing import List
from langchain_core.messages import SystemMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.tools.tavily_search import TavilySearchResults
import json
from langchain_core.messages import ToolMessage
# from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from IPython.display import Image, display
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3



template = """You are a helpful AI assistant designed to guide users through transactions on the Solana blockchain.
Your job is to interact conversationally with users, and collect the following essential details:

Transaction Type: Ask the user whether they want to send, stake, swap, or receive SOL or tokens.

Transaction Amount: Confirm the exact amount they want to transact.

Recipient Wallet Address: If applicable (e.g. for sending or staking), collect the correct Solana wallet address where the transaction will be sent.

Once all information is gathered, summarize the transaction details clearly and ask for user confirmation before proceeding.

Be polite, concise, and ensure the wallet address is in valid Solana format (base58, typically 32–44 characters). Do not execute or simulate real transactions—only gather and summarize data.."""

#%%
sqlite_conn = sqlite3.connect("ussd.sqlite3", check_same_thread=False)

memory =SqliteSaver(sqlite_conn)

#%%
# memory = MemorySaver()
class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    
tool = TavilySearchResults(max_results=2, tavily_api_key= "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")
tools = [tool]
# tool.invoke("What's a 'node' in LangGraph?")
#%%

def get_messages_info(messages):
    return [SystemMessage(content=template)] + messages


class PromptInstructions(BaseModel):
    """Instructions on how to prompt the LLM."""

    objective: str
    variables: List[str]
    constraints: List[str]
    requirements: List[str]
    



GROQ_API_KEY = "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"
# Initialize LLM
llm = ChatGroq(temperature=0, model="meta-llama/llama-4-maverick-17b-128e-instruct", groq_api_key=GROQ_API_KEY)
llm_with_tool = llm.bind_tools([PromptInstructions])


def info_chain(state):
    messages = get_messages_info(state["messages"])
    response = llm_with_tool.invoke(messages)
    return {"messages": [response]}

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# New system prompt
prompt_system = """Based on the following requirements, write the summary:

{reqs}"""


# Function to get the messages for the prompt
# Will only get messages AFTER the tool call
def get_prompt_messages(messages: list):
    tool_call = None
    other_msgs = []
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            tool_call = m.tool_calls[0]["args"]
        elif isinstance(m, ToolMessage):
            continue
        elif tool_call is not None:
            other_msgs.append(m)
    return [SystemMessage(content=prompt_system.format(reqs=tool_call))] + other_msgs


def prompt_gen_chain(state):
    messages = get_prompt_messages(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [response]}

from typing import Literal

from langgraph.graph import END


def get_state(state):
    messages = state["messages"]
    if isinstance(messages[-1], AIMessage) and messages[-1].tool_calls:
        return "add_tool_message"
    elif not isinstance(messages[-1], HumanMessage):
        return END
    return "info"




class State(TypedDict):
    messages: Annotated[list, add_messages]


workflow = StateGraph(State)
workflow.add_node("info", info_chain)
workflow.add_node("prompt", prompt_gen_chain)


@workflow.add_node
def add_tool_message(state: State):
    return {
        "messages": [
            ToolMessage(
                content="Prompt generated!",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        ]
    }


workflow.add_conditional_edges("info", get_state, ["add_tool_message", "info", END])
workflow.add_edge("add_tool_message", "prompt")
workflow.add_edge("prompt", END)
workflow.add_edge(START, "info")
graph = workflow.compile(checkpointer=memory)


# try:
#     display(Image(graph.get_graph().draw_mermaid_png()))
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass
#%%

# def stream_graph_updates(user_input: str,  phone_number: str):
#     config = {"configurable": {"thread_id": phone_number}}
#     response = graph.invoke({"messages": [{"role": "user", "content": user_input}]},
#                             config)
#     text = response["messages"][-1].content
#     return text


def stream_graph_updates(user_input: str,  phone_number: str):
    config = {"configurable": {"thread_id": phone_number}}
    response = graph.invoke({"messages": [{"role": "user", "content": user_input}]},
                            config)
    text = response["messages"][-1].content
    return text

#%%
while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        print(stream_graph_updates(user_input, "+2347037378217"))
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input, "+2347037378217")
        break

# %%

# %%
