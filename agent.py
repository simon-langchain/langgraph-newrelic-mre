"""
Minimal Reproducible Example: LangGraph + New Relic Integration Issue

This demonstrates the conflict between LangGraph Platform's ASGI server lifecycle
and New Relic's automatic instrumentation hooks.

Solution: Initialize New Relic with disable_agent_hooks to prevent conflicts
with LangGraph Platform's Uvicorn initialization.
"""

import os
import sys
import asyncio

# ============================================================================
# NEW RELIC - EXPLICIT INITIALIZATION WITH HOOK DISABLE
# ============================================================================
# Initialize New Relic agent before any other imports
# Use disable_agent_hooks to prevent conflicts with LangGraph's Uvicorn
config_file = os.environ.get("NEW_RELIC_CONFIG_FILE", "/deps/newrelic.ini")
if os.path.exists(config_file):
    import newrelic.agent
    # Disable automatic hooks to prevent Uvicorn conflict
    newrelic.agent.initialize(config_file, disable_agent_hooks=True)
    print(f"✅ New Relic agent initialized from {config_file}")
else:
    print(f"⚠️ New Relic config not found at {config_file} - running without APM")
# ============================================================================

# ============================================================================
# LANGGRAPH AGENT - Minimal Example
# ============================================================================

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
    Simple chatbot node that echoes back messages.
    In a real scenario, this would call an LLM.
    """
    messages = state["messages"]
    
    # Use ChatOpenAI if available, otherwise echo
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        response = llm.invoke(messages)
        return {"messages": [response]}
    except Exception as e:
        print(f"⚠️ LLM not available, using echo mode: {e}")
        # Echo mode for testing without OpenAI API key
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

# Compile the graph in a thread using async
async def compile_graph():
    def _compile():
        return graph_builder.compile()
    return await asyncio.to_thread(_compile)

graph = asyncio.run(compile_graph())

print("✅ LangGraph compiled successfully")
print("=" * 80)
print("🚀 Ready to deploy!")
print("=" * 80)

# This is what LangSmith/LangGraph Platform will import
__all__ = ["graph"]

