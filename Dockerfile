# Minimal Dockerfile for New Relic + LangGraph MRE
# Uses official LangGraph API image from public Docker Hub

FROM langchain/langgraph-api:3.11

# Add requirements
ADD requirements-minimal.txt /deps/requirements.txt
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r /deps/requirements.txt

# Add agent code
ADD agent.py /deps/agent.py
ADD newrelic.ini /deps/newrelic.ini

# Set working directory
WORKDIR /deps

# Set New Relic environment variables (will be overridden by LangSmith)
ENV NEW_RELIC_APP_NAME=langgraph-newrelic-mre
ENV NEW_RELIC_LOG_LEVEL=info

# Note: NEW_RELIC_LICENSE_KEY should be set via LangSmith secrets

