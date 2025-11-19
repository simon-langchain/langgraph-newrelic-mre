"""
Minimal LangGraph Agent Example

A simple LangGraph agent that invokes an LLM.
"""

import asyncio
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI


class State(TypedDict):
    """Simple state for our agent."""
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    """
    Simple chatbot node that calls an LLM.
    """
    messages = state["messages"]
    
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        response = llm.invoke(messages)
        return {"messages": [response]}
    except Exception as e:
        print(f"⚠️ LLM error: {e}")
        # Echo mode fallback
        last_message = messages[-1]
        echo_response = {
            "role": "assistant",
            "content": f"Echo: {last_message.content if hasattr(last_message, 'content') else str(last_message)}"
        }
        return {"messages": [echo_response]}


# Build the graph
print("🔨 Building LangGraph...")
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph
async def compile_graph():
    def _compile():
        return graph_builder.compile()
    return await asyncio.to_thread(_compile)

graph = asyncio.run(compile_graph())

print("✅ LangGraph compiled successfully")
print("🚀 Ready to deploy!")

# This is what LangSmith/LangGraph Platform will import
__all__ = ["graph"]

