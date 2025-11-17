# LangGraph + New Relic MRE

A minimal reproducible example demonstrating LangGraph integration with New Relic APM monitoring.

## Overview

This project showcases:
- A simple LangGraph agent with message handling
- New Relic APM instrumentation configured for LangGraph Platform deployment
- Proper configuration to avoid conflicts between LangGraph's ASGI lifecycle and New Relic's automatic instrumentation

## Project Structure

```
├── agent.py              # LangGraph agent definition
├── langgraph.json        # LangGraph deployment configuration
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container image definition
├── newrelic.ini          # New Relic agent configuration
├── README.md             # This file
└── .env                  # Environment variables (not in repo)
```

## Prerequisites

- Python 3.11+
- OpenAI API key (optional; the agent has fallback echo mode)
- New Relic account with a valid license key (for production monitoring)

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY=your_openai_key_here
```

### 3. Run Locally (Optional)

```bash
# Test the agent module loads correctly
python agent.py
```

## Deployment on LangSmith

### Prerequisites

- A LangSmith account (free tier available)
- GitHub repository with this code
- (Optional) New Relic account for APM monitoring

### Step 1: Push Code to GitHub

```bash
git add .
git commit -m "Initial LangGraph agent"
git push origin main
```

### Step 2: Create LangSmith Deployment

1. Go to [LangSmith](https://smith.langchain.com)
2. Navigate to the **Deployments** section
3. Click **Create Deployment**
4. Select **New Deployment from GitHub**
5. Connect your GitHub repository
6. Choose the branch (e.g., `main`)
7. Set the repository path if not in root

### Step 3: Configure Secrets

In the LangSmith deployment settings, add the following **Secrets**:

```
OPENAI_API_KEY = <your-openai-api-key>
```

**For New Relic Monitoring (Required for APM)**

```
NEW_RELIC_LICENSE_KEY = <your-new-relic-license-key>
```

### Step 4: Configure Environment Variables

In the deployment settings, set **Environment Variables**:

```
NEW_RELIC_CONFIG_FILE=/deps/newrelic.ini
NEW_RELIC_ENVIRONMENT=production
```

**How New Relic Initialization Works:**

The `agent.py` file explicitly initializes the New Relic agent at import time, before LangGraph loads. This ensures:
- New Relic instrumentation is active from startup
- No conflicts with LangGraph Platform's ASGI server lifecycle
- Automatic tracking of all transactions and LLM calls

### Step 5: Deploy

1. Click **Deploy**
2. Wait for the deployment to build and start (typically 2-5 minutes)
3. Once live, you'll get a public API endpoint

## Testing the Deployment

Once deployed, test the agent via the LangSmith API:

```bash
curl -X POST https://<your-deployment-url>/runs \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{"role": "user", "content": "Hello, world!"}]
    }
  }'
```

Or use the LangSmith UI to interact with the agent directly.

## Monitoring with New Relic

If you've configured New Relic:

1. Go to [New Relic](https://one.newrelic.com)
2. Navigate to **APM & Services**
3. Select your app (`langgraph-newrelic-mre`)
4. View transaction metrics, error rates, and performance data

## Key Configuration Files

### `langgraph.json`
Defines the graph endpoints and deployment settings:
- `graphs.agent`: Points to the compiled graph in `agent.py`
- `python_version`: Set to 3.11 for compatibility
- `dockerfile_lines`: Custom Docker commands for New Relic setup

### `newrelic.ini`
New Relic agent configuration:
- `auto_instrumentation`: Enables automatic APM tracking
- `ai_monitoring.enabled`: Tracks LLM calls (LangChain integration)
- `distributed_tracing.enabled`: Enables request tracing across services

### `Dockerfile`
LangGraph Platform builds and deploys using this image:
- Installs dependencies
- Adds New Relic config file
- Sets environment variables

## Troubleshooting

### Agent fails to load
- Ensure `OPENAI_API_KEY` is set (or accept echo mode)
- Check `requirements.txt` versions are compatible
- View logs in LangSmith deployment details

### New Relic not receiving data
- Verify `NEW_RELIC_LICENSE_KEY` is set in secrets
- Check `NEW_RELIC_CONFIG_FILE=/deps/newrelic.ini` is in environment variables
- Ensure `disable_agent_hooks = true` in `newrelic.ini` (prevents Uvicorn conflict)
- View New Relic agent logs in deployment logs

### AttributeError: 'Config' object has no attribute '_nr_loaded_app'
- This error occurs when New Relic's automatic hooks conflict with LangGraph's Uvicorn
- **Fix**: Ensure `disable_agent_hooks = true` is set in `newrelic.ini`
- The agent is manually initialized in `agent.py` with `disable_agent_hooks=True`

## Support

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Deployment Guide](https://docs.smith.langchain.com/)
- [New Relic Python Agent Docs](https://docs.newrelic.com/docs/agents/python-agent/)
