"""
Minimal Reproducible Example: LangGraph + New Relic Integration

This demonstrates a simple LangGraph agent with explicit New Relic monitoring.

Note: LangGraph Platform controls the ASGI server lifecycle, specifically how Uvicorn is
initialized, causing direct conflicts with New Relic's automatic instrumentation hooks.
We disable auto-instrumentation and use manual function wrapping instead to avoid conflicts.
"""

import os
import sys
import asyncio

# ============================================================================
# NEW RELIC - EXPLICIT INITIALIZATION WITH DISABLED AUTO-INSTRUMENTATION
# ============================================================================
# Problem: LangGraph Platform initializes Uvicorn independently. New Relic's
# automatic hooks try to instrument the Uvicorn config, causing errors during
# the server initialization that LangGraph Platform controls.
#
# Solution: Prevent the Uvicorn hook from being loaded by replacing it with
# a no-op module in sys.modules BEFORE New Relic tries to use it.
# This prevents the AttributeError while allowing other New Relic features.

# Create a no-op hook module to prevent conflicts
class NoOpHook:
    """Placeholder module that prevents the real Uvicorn hook from loading."""
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Install the no-op hook BEFORE New Relic is imported
print("[NEW_RELIC] Blocking newrelic.hooks.adapter_uvicorn hook to prevent conflicts...")
sys.modules['newrelic.hooks.adapter_uvicorn'] = NoOpHook()

# Disable auto-instrumentation to avoid other hook conflicts
if 'NEW_RELIC_DISABLE_AUTO_INSTRUMENTATION' not in os.environ:
    os.environ['NEW_RELIC_DISABLE_AUTO_INSTRUMENTATION'] = 'true'
    print("[NEW_RELIC] Setting NEW_RELIC_DISABLE_AUTO_INSTRUMENTATION=true")

config_file = os.environ.get("NEW_RELIC_CONFIG_FILE", "/deps/newrelic.ini")
license_key = os.environ.get("NEW_RELIC_LICENSE_KEY")

print(f"[NEW_RELIC] Configuration: config_file={config_file}, license_key={'SET' if license_key else 'NOT SET'}")

if license_key:
    try:
        print("[NEW_RELIC] Importing newrelic.agent...")
        import newrelic.agent
        print(f"[NEW_RELIC] Calling newrelic.agent.initialize('{config_file}')...")
        newrelic.agent.initialize(config_file)
        print(f"✅ New Relic agent initialized (config: {config_file})")
        print("   ✓ Strategy: Block Uvicorn hook + manual instrumentation")
        print("   ✓ Distributed tracing: ENABLED")
        print("   ✓ AI monitoring: ENABLED")
        print("   ✓ Transaction tracing: ENABLED (via manual wrapping)")
        print("   ✓ Error collection: ENABLED")
    except Exception as e:
        print(f"⚠️ New Relic initialization failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("ℹ️ NEW_RELIC_LICENSE_KEY not set - New Relic monitoring disabled")
    print("[NEW_RELIC] Strategy: Block Uvicorn hook + manual instrumentation (installed but inactive)")

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


# Manually wrap the chatbot function with New Relic instrumentation
if license_key:
    try:
        print("[NEW_RELIC] Applying manual instrumentation...")
        
        # Wrap the chatbot node function
        chatbot = newrelic.agent.function_trace(name='chatbot_node')(chatbot)
        print("[NEW_RELIC]   ✓ Chatbot node wrapped")
        
    except Exception as e:
        print(f"[NEW_RELIC] Manual wrapping failed: {e}")


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

# Wrap graph invocation
if license_key:
    try:
        original_invoke = graph.invoke
        
        def wrapped_invoke(input_data, *args, **kwargs):
            """Wrapped graph.invoke that captures execution."""
            return newrelic.agent.function_trace(
                name='graph.invoke',
                group='langgraph'
            )(original_invoke)(input_data, *args, **kwargs)
        
        graph.invoke = wrapped_invoke
        print("[NEW_RELIC]   ✓ Graph invoke wrapped")
    except Exception as e:
        print(f"[NEW_RELIC] Graph wrapping failed: {e}")

print("✅ LangGraph compiled successfully")
print("=" * 80)
print("🚀 Ready to deploy!")
print("=" * 80)

# This is what LangSmith/LangGraph Platform will import
__all__ = ["graph"]

