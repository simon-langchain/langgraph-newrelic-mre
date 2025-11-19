"""
Minimal LangGraph Agent Example

A simple LangGraph agent that invokes an LLM with OpenTelemetry tracing to New Relic.
"""

import asyncio
import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

# Initialize OpenTelemetry tracing to New Relic
def setup_otel_tracing():
    """
    Configure OpenTelemetry to send traces to both LangSmith and New Relic via OTLP endpoint.
    Uses LangSmith's OTEL integration for proper span attributes and kinds,
    while also sending traces to New Relic.
    
    Environment variables required:
    - OTEL_EXPORTER_OTLP_ENDPOINT: New Relic OTLP endpoint (default: https://otlp.nr-data.net)
    - OTEL_EXPORTER_OTLP_HEADERS: API key header (format: "api-key=<license_key>")
    - OTEL_SERVICE_NAME: Service name for tracing (optional)
    
    Also sets:
    - LANGSMITH_OTEL_ENABLED=true: Enable LangSmith's OTEL integration for span attributes
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        
        # Set default environment variables for New Relic if not already configured
        if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://otlp.nr-data.net"
        
        if not os.getenv("OTEL_SERVICE_NAME"):
            os.environ["OTEL_SERVICE_NAME"] = "langgraph-newrelic-mre"
        
        # Enable LangSmith's OTEL integration for proper span attributes and kinds
        os.environ["LANGSMITH_OTEL_ENABLED"] = "true"
        
        # Only initialize if OTLP headers (API key) are configured
        if os.getenv("OTEL_EXPORTER_OTLP_HEADERS"):
            # Create OTLP exporter with New Relic endpoint and headers
            otlp_exporter = OTLPSpanExporter(
                timeout=10,
            )
            
            # Set up tracer provider with batch span processor
            tracer_provider = TracerProvider()
            tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            
            # Set as global tracer provider
            trace.set_tracer_provider(tracer_provider)
            
            # Enable automatic instrumentation for HTTP requests (captures LLM API calls)
            RequestsInstrumentor().instrument()
            
            print("✅ OpenTelemetry tracing to New Relic initialized")
            print("✅ LangSmith OTEL integration enabled for proper span attributes")
            print("✅ Traces sent to both LangSmith and New Relic")
            print("✅ HTTP instrumentation enabled (captures LLM API calls)")
            return True
        else:
            print("ℹ️ OTEL_EXPORTER_OTLP_HEADERS not set - OTEL tracing disabled")
            return False
    except ImportError as e:
        print(f"⚠️ OpenTelemetry packages not installed - tracing disabled: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Failed to initialize OTEL tracing: {e}")
        return False

# Initialize tracing on module load
setup_otel_tracing()


class State(TypedDict):
    """Simple state for our agent."""
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    """
    Simple chatbot node that calls an LLM.
    Traces execution to OpenTelemetry/New Relic.
    """
    messages = state["messages"]
    
    # Get tracer for this module
    tracer = None
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
    except ImportError:
        pass
    
    # Create a span for this operation
    span_context = tracer.start_as_current_span("chatbot_invoke") if tracer else None
    
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        response = llm.invoke(messages)
        
        if tracer and span_context:
            span_context.__enter__().set_attribute("llm.response.success", True)
        
        return {"messages": [response]}
    except Exception as e:
        if tracer and span_context:
            span_context.__enter__().set_attribute("llm.response.error", str(e))
        
        print(f"⚠️ LLM error: {e}")
        # Echo mode fallback
        last_message = messages[-1]
        echo_response = {
            "role": "assistant",
            "content": f"Echo: {last_message.content if hasattr(last_message, 'content') else str(last_message)}"
        }
        return {"messages": [echo_response]}
    finally:
        if span_context:
            span_context.__exit__(None, None, None)


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

