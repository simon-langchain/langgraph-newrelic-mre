# Dockerfile for LangGraph Agent
# Uses official LangGraph API image from public Docker Hub

FROM langchain/langgraph-api:3.11

# Add requirements
ADD requirements.txt /deps/requirements.txt
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r /deps/requirements.txt

# Add agent code
ADD agent.py /deps/agent.py

# Set working directory
WORKDIR /deps

