"""
Minimal Reproducible Example: LangGraph + New Relic Integration

This demonstrates a simple LangGraph agent with explicit New Relic monitoring.

Note: New Relic requires a workaround for LangGraph Platform due to Uvicorn
lifecycle conflicts. The Uvicorn hook is suppressed to prevent initialization errors.
"""

import os
import sys
import asyncio

# ============================================================================
# NEW RELIC - EXPLICIT INITIALIZATION WITH UVICORN WORKAROUND
# ============================================================================
# Required workaround: Suppress New Relic's Uvicorn hook to prevent conflicts
# with LangGraph Platform's ASGI server initialization.
class DummyUvicornModule:
    """Dummy module to suppress New Relic's Uvicorn instrumentation hook."""
    def __getattr__(self, name):
        def dummy_func(*args, **kwargs):
            return None
        return dummy_func

sys.modules['newrelic.hooks.adapter_uvicorn'] = DummyUvicornModule()

# Now initialize New Relic explicitly
config_file = os.environ.get("NEW_RELIC_CONFIG_FILE", "/deps/newrelic.ini")
license_key = os.environ.get("NEW_RELIC_LICENSE_KEY")

if license_key:
    try:
        import newrelic.agent
        newrelic.agent.initialize(config_file)
        print(f"✅ New Relic agent initialized (config: {config_file})")
    except Exception as e:
        print(f"⚠️ New Relic initialization failed: {e}")
else:
    print("ℹ️ NEW_RELIC_LICENSE_KEY not set - New Relic monitoring disabled")

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

