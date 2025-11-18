"""
Minimal Reproducible Example: LangGraph + New Relic Integration Issue

This demonstrates the conflict between LangGraph Platform's ASGI server lifecycle
and New Relic's automatic instrumentation hooks.

Problem: LangGraph Platform controls how Uvicorn is initialized, causing direct
conflicts with New Relic's automatic instrumentation hooks.
"""

import os
import sys
import asyncio

# Conditionally import New Relic for instrumentation
try:
    import newrelic.agent
    NEW_RELIC_AVAILABLE = True
except ImportError:
    NEW_RELIC_AVAILABLE = False

# ============================================================================
# NEW RELIC - Using environment variable configuration only
# ============================================================================
# Note: For LangGraph Platform deployment, New Relic initialization happens
# via environment variables set in LangSmith deployment settings:
#   NEW_RELIC_CONFIG_FILE=/deps/newrelic.ini
#   NEW_RELIC_ENVIRONMENT=production
#   NEW_RELIC_LICENSE_KEY=<your-key>
#   NEW_RELIC_APP_NAME=<your-app-name>
# This avoids conflicts with LangGraph's Uvicorn initialization.
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

_base_graph = asyncio.run(compile_graph())


# Wrap graph to add New Relic transaction naming
class InstrumentedGraph:
    """Wrapper for compiled graph that adds New Relic transaction naming."""
    
    def __init__(self, base_graph):
        self._graph = base_graph
    
    def __getattr__(self, name):
        """Delegate all other attributes to the underlying graph."""
        return getattr(self._graph, name)
    
    def invoke(self, *args, **kwargs):
        """Wrap invoke to set New Relic transaction name."""
        if NEW_RELIC_AVAILABLE:
            newrelic.agent.set_transaction_name('LangGraph/agent/invoke', group='Function')
        return self._graph.invoke(*args, **kwargs)
    
    async def ainvoke(self, *args, **kwargs):
        """Wrap ainvoke to set New Relic transaction name."""
        if NEW_RELIC_AVAILABLE:
            newrelic.agent.set_transaction_name('LangGraph/agent/invoke', group='Function')
        return await self._graph.ainvoke(*args, **kwargs)
    
    def stream(self, *args, **kwargs):
        """Wrap stream to set New Relic transaction name."""
        if NEW_RELIC_AVAILABLE:
            newrelic.agent.set_transaction_name('LangGraph/agent/stream', group='Function')
        return self._graph.stream(*args, **kwargs)
    
    async def astream(self, *args, **kwargs):
        """Wrap astream to set New Relic transaction name."""
        if NEW_RELIC_AVAILABLE:
            newrelic.agent.set_transaction_name('LangGraph/agent/stream', group='Function')
        return self._graph.astream(*args, **kwargs)


graph = InstrumentedGraph(_base_graph)

print("✅ LangGraph compiled successfully")
print("=" * 80)
print("🚀 Ready to deploy!")
print("=" * 80)

# This is what LangSmith/LangGraph Platform will import
__all__ = ["graph"]

