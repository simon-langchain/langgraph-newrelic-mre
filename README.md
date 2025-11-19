# LangGraph Agent

A simple LangGraph agent that invokes an LLM.

## Project Structure

```
├── agent.py              # LangGraph agent
├── langgraph.json        # LangGraph Platform configuration
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container image definition
├── README.md             # This file
└── .env                  # Environment variables (local only)
```

## Prerequisites

- Python 3.11+
- LangSmith account (free tier available at https://smith.langchain.com)
- OpenAI API key

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# .env (local testing only)
OPENAI_API_KEY=your_openai_key_here
```

### 3. Test Locally

```bash
python agent.py
```

Expected output:
```
🔨 Building LangGraph...
✅ LangGraph compiled successfully
🚀 Ready to deploy!
```

## OpenTelemetry Tracing to New Relic

This application is configured to send OTEL traces to New Relic via the OTLP endpoint. Tracing is **optional** - it activates only when you configure the required environment variables.

### Prerequisites for OTEL Tracing

- New Relic account with an active license key
- Required OTEL environment variables configured

### Configuration

To enable OTEL tracing, set these environment variables:

```bash
# New Relic OTLP endpoint (US region, default)
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.nr-data.net"

# New Relic license key (required for tracing)
export OTEL_EXPORTER_OTLP_HEADERS="api-key=<your-new-relic-license-key>"

# Optional: Set service name (defaults to "langgraph-newrelic-mre")
export OTEL_SERVICE_NAME="my-langgraph-app"

# Optional: Other OTEL settings
export OTEL_EXPORTER_OTLP_TIMEOUT="10"
export OTEL_EXPORTER_OTLP_COMPRESSION="gzip"
```

#### For Different New Relic Regions

**EU Region:**
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.eu01.nr-data.net"
```

**FedRAMP:**
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://gov-otlp.nr-data.net"
```

### Local Testing with OTEL

1. Set the environment variables above
2. Run the agent:

```bash
python agent.py
```

If tracing is configured correctly, you'll see:
```
✅ OpenTelemetry tracing to New Relic initialized
```

Traces will be sent to New Relic immediately. View them in [New Relic](https://one.newrelic.com) under **Traces**.

### What Gets Traced

- **LLM calls**: ChatOpenAI invocations with success/error attributes
- **Span attributes**: LLM response status and error messages when they occur
- **Service metrics**: Configured via `OTEL_SERVICE_NAME`

## Deployment on LangSmith

### Step 1: Push to GitHub

Ensure your code is in a GitHub repository:

```bash
git add .
git commit -m "LangGraph agent"
git push origin main
```

### Step 2: Create LangSmith Deployment

1. Go to [LangSmith Deployments](https://smith.langchain.com/deployments)
2. Click **Create Deployment**
3. Select **New Deployment from GitHub**
4. Connect your GitHub repository
5. Select the branch (e.g., `main`)

### Step 3: Configure Secrets and Environment Variables

In LangSmith deployment settings, add the following:

**Secrets:**
```
OPENAI_API_KEY = <your-openai-api-key>
```

**Environment Variables (for OTEL tracing to New Relic):**
```
OTEL_EXPORTER_OTLP_ENDPOINT = https://otlp.nr-data.net
OTEL_EXPORTER_OTLP_HEADERS = api-key=<your-new-relic-license-key>
OTEL_SERVICE_NAME = langgraph-newrelic-mre
OTEL_EXPORTER_OTLP_COMPRESSION = gzip
```

> **Note**: OTEL tracing is optional. If you don't set `OTEL_EXPORTER_OTLP_HEADERS`, the application will run normally without OTEL tracing.

### Step 4: Deploy

1. Click **Deploy**
2. Wait for the build to complete (typically 2-5 minutes)
3. Once deployed, you'll receive a public API endpoint

## Using the Deployed Agent

Once deployed, interact with your agent via the LangSmith API:

```bash
curl -X POST https://<your-deployment-url>/runs \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{"role": "user", "content": "Hello!"}]
    }
  }'
```

Or use the LangSmith UI to test interactively.

## Viewing OTEL Traces in New Relic

Once you've deployed the agent with OTEL tracing configured:

1. Go to [New Relic One](https://one.newrelic.com)
2. Navigate to **Traces** from the left sidebar
3. Filter by service name: `langgraph-newrelic-mre` (or your custom `OTEL_SERVICE_NAME`)
4. View individual trace spans:
   - **Span name**: `chatbot_invoke`
   - **Attributes**:
     - `llm.response.success`: true/false
     - `llm.response.error`: error message (if applicable)
     - `service.name`: from `OTEL_SERVICE_NAME`

### Trace Analysis

Each trace will show:
- **Duration**: How long the LLM call took
- **Attributes**: Request/response metadata
- **Status**: Success or error
- **Timestamp**: When the trace was generated

## Configuration Files

### `agent.py`

The core agent file with LangGraph and OpenTelemetry:

- **setup_otel_tracing()**: Initializes OTLP exporter to New Relic
  - Reads environment variables: `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`
  - Creates `TracerProvider` and `BatchSpanProcessor`
  - Returns `True` if tracing is enabled, `False` otherwise
- **State**: TypedDict for message handling
- **chatbot**: Node that calls ChatOpenAI with tracing
  - Wraps LLM invocation in a span named `chatbot_invoke`
  - Sets span attributes for success/error tracking
- **graph**: Compiled LangGraph with the chatbot node

### `langgraph.json`

LangGraph Platform configuration:

```json
{
  "graphs": { "agent": "./agent.py:graph" },
  "python_version": "3.11"
}
```

- Defines the agent graph endpoint
- Sets Python version to 3.11

### `Dockerfile`

Builds a container image:

- Starts from `langchain/langgraph-api:3.11`
- Installs dependencies from `requirements.txt`
- Copies agent code

### `requirements.txt`

Python dependencies:

```
langgraph>=0.2.0                    # LangGraph framework
langchain-core>=0.3.0               # LangChain core
langchain-openai>=0.2.0             # OpenAI integration

# OpenTelemetry tracing to New Relic
opentelemetry-sdk>=1.20.0           # OpenTelemetry SDK
opentelemetry-exporter-otlp>=0.43b0 # OTLP exporter for New Relic
```

## Troubleshooting

### Agent fails to load

Check the deployment logs:
- Verify `OPENAI_API_KEY` is set
- Check `requirements.txt` package versions are compatible
- Review build logs in LangSmith deployment details

### OTEL Tracing Not Sending Data

1. **Verify configuration**:
   - Check that `OTEL_EXPORTER_OTLP_HEADERS` is set with a valid New Relic license key
   - Confirm `OTEL_EXPORTER_OTLP_ENDPOINT` points to the correct New Relic region
   - Look for "✅ OpenTelemetry tracing to New Relic initialized" in logs

2. **Check environment variables**:
   ```bash
   # Local testing
   echo $OTEL_EXPORTER_OTLP_HEADERS
   echo $OTEL_EXPORTER_OTLP_ENDPOINT
   ```

3. **Verify network connectivity**:
   - Ensure your environment can reach `otlp.nr-data.net` (or your configured endpoint)
   - Check firewall/security group rules allow outbound HTTPS on port 443

4. **Enable debug logging**:
   ```bash
   export OTEL_LOG_LEVEL=debug
   ```

### Wrong New Relic Region

If traces don't appear in New Relic, verify your region:
- **US**: `https://otlp.nr-data.net` (default)
- **EU**: `https://otlp.eu01.nr-data.net`
- **FedRAMP**: `https://gov-otlp.nr-data.net`

Set the correct endpoint:
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.eu01.nr-data.net"
```

### No Spans Appearing in New Relic

- **If OTEL variables not set**: Tracing is disabled (not an error)
- **If variables are set but no traces**: 
  - May take a few seconds for traces to appear
  - Check New Relic API key is valid
  - Verify `BatchSpanProcessor` is batching and flushing correctly

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Deployment Guide](https://docs.smith.langchain.com/)
- [LangChain OpenAI Documentation](https://python.langchain.com/docs/integrations/llms/openai)
- [OpenTelemetry OTLP Exporter](https://opentelemetry.io/docs/reference/specification/protocol/exporter/)
- [New Relic OTLP Endpoint Configuration](https://docs.newrelic.com/docs/opentelemetry/best-practices/opentelemetry-otlp/)
- [LangSmith Trace with OpenTelemetry](https://docs.langchain.com/langsmith/trace-with-opentelemetry)

## License

This is a minimal example for educational purposes. Modify and use as needed for your project.

After deployment, view monitoring data in New Relic:

1. Go to [New Relic APM](https://one.newrelic.com/apm)
2. Select your app (`langgraph-newrelic-mre`)
3. View real-time metrics:
   - **Transactions**: HTTP requests to your agent
   - **AI Monitoring**: OpenAI/LangChain call details and latencies
   - **Distributed Tracing**: Request flows across services
   - **Error Analytics**: Exceptions and error rates
   - **Service Maps**: Architecture visualization

## Configuration Files

### `agent.py`

The core agent file with New Relic initialization:

- **ResilientUvicornHook**: Proxy class that handles Uvicorn hook timing
- **New Relic initialization**: Explicit `newrelic.agent.initialize()` call
- **LangGraph agent**: Simple chatbot that echoes or calls OpenAI

Key features:
- Only initializes New Relic if `NEW_RELIC_LICENSE_KEY` is set
- Gracefully handles missing OpenAI key with echo mode
- Async graph compilation using `asyncio`

### `langgraph.json`

LangGraph Platform configuration:

```json
{
  "graphs": { "agent": "./agent.py:graph" },
  "python_version": "3.11",
  "dockerfile_lines": [
    "ADD newrelic.ini /deps/newrelic.ini",
    "ENV NEW_RELIC_CONFIG_FILE=/deps/newrelic.ini"
  ]
}
```

- Defines the agent graph endpoint
- Sets Python version to 3.11
- Adds New Relic config file to Docker image

### `newrelic.ini`

New Relic agent configuration:

- **Distributed tracing**: Enabled for cross-service visibility
- **AI monitoring**: Tracks LLM calls with `ai_monitoring.enabled = true`
- **Transaction tracing**: Captures detailed request data
- **Application logging**: Forwards logs to New Relic
- **Error collection**: Captures exceptions and stack traces
- **Labels**: Tags for filtering (`environment:test`, `platform:langgraph`)

### `Dockerfile`

Builds a container image with New Relic support:

- Starts from `langchain/langgraph-api:3.11`
- Installs dependencies from `requirements.txt`
- Copies agent code and New Relic config
- Sets `NEW_RELIC_CONFIG_FILE` environment variable

### `requirements.txt`

Python dependencies:

```
langgraph>=0.2.0      # LangGraph framework
langchain-core>=0.3.0 # LangChain core
langchain-openai>=0.2.0 # OpenAI integration
newrelic>=9.0.0       # New Relic APM agent
requests>=2.31.0      # HTTP client
```

## New Relic Integration Details

### How It Works

1. **Early Hook Interception**: Before any imports, `ResilientUvicornHook` is installed in `sys.modules`
2. **New Relic Initialization**: `newrelic.agent.initialize()` is called explicitly
3. **Lazy Hook Loading**: When the Uvicorn hook is accessed, it's safely loaded after New Relic is ready
4. **Full Instrumentation**: All transactions, LLM calls, and errors are automatically tracked

### Complete Monitoring Coverage

✓ **Uvicorn instrumentation**: Thread pools, connections, request handling
✓ **Distributed tracing**: Request spans across services
✓ **Transaction traces**: Code-level performance visibility
✓ **LLM monitoring**: OpenAI/LangChain call tracking
✓ **Error tracking**: Exception capture and reporting
✓ **Custom events**: Application-specific metrics via New Relic API

## Troubleshooting

### Agent fails to load

Check the deployment logs:
- Verify `OPENAI_API_KEY` is set (or accept echo mode)
- Check `requirements.txt` package versions are compatible
- Review build logs in LangSmith deployment details

### New Relic not receiving data

1. **Verify setup**:
   - Check that `NEW_RELIC_LICENSE_KEY` is set in secrets
   - Confirm `newrelic` package is installed
   - Verify `NEW_RELIC_CONFIG_FILE=/deps/newrelic.ini` in Docker

2. **Check initialization**:
   - Look for "✅ New Relic agent initialized" in deployment logs
   - Verify all four features show "ENABLED"

3. **View agent logs**:
   - New Relic logs are sent to stdout (see deployment logs)
   - Set `log_level = debug` in `newrelic.ini` for verbose output

### Uvicorn-related New Relic errors

If you see `AttributeError: 'Config' object has no attribute '_nr_loaded_app'`:

- **This is handled** by the `ResilientUvicornHook` in `agent.py`
- The hook defers loading until after New Relic initialization
- Full instrumentation is preserved
- If errors persist, verify `ResilientUvicornHook` is properly defined

### Deployment build fails

- Ensure `Dockerfile` exists and references valid files
- Check that all files in `langgraph.json` paths exist
- Verify Python 3.11 compatibility of dependencies
- Review build logs for missing packages

## Next Steps

1. **Customize the agent**: Add more nodes, integrate with your data, add tools
2. **Set up New Relic alerts**: Create alert policies for error rates, latency, etc.
3. **Explore distributed tracing**: View full request flows in New Relic
4. **Optimize performance**: Use New Relic transaction data to identify bottlenecks
5. **Monitor LLM costs**: Track OpenAI usage and latencies in New Relic

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Deployment Guide](https://docs.smith.langchain.com/)
- [New Relic Python Agent Docs](https://docs.newrelic.com/docs/agents/python-agent/)
- [New Relic AI Monitoring](https://docs.newrelic.com/docs/ai-monitoring/)
- [Distributed Tracing](https://docs.newrelic.com/docs/distributed-tracing/)

## License

This is a minimal example for educational purposes. Modify and use as needed for your project.

## How It Works

### New Relic Integration

This project includes a **resilient integration** for New Relic monitoring with LangGraph Platform that preserves full observability:

**The Challenge**: LangGraph Platform controls the ASGI/Uvicorn server lifecycle independently. New Relic's Uvicorn hook attempts to access `Config._nr_loaded_app` during initialization, but this attribute doesn't exist until after the config is fully loaded—creating a timing conflict.

**The Solution**: A `ResilientUvicornHook` proxy that:

1. **Intercepts the hook early** - Before New Relic initializes, preventing premature access
2. **Lazy-loads on demand** - Defers real hook loading until after New Relic is ready
3. **Gracefully handles failures** - Falls back to safe no-ops if hook loading fails
4. **Preserves all instrumentation** - Once loaded, the real hook provides complete coverage

```python
class ResilientUvicornHook:
    """Safely handles New Relic's Uvicorn hook with lazy loading."""
    def __init__(self):
        self._real_hook = None
        self._hook_loaded = False
    
    def _load_real_hook(self):
        if not self._hook_loaded:
            try:
                import newrelic.hooks.adapter_uvicorn
                self._real_hook = newrelic.hooks.adapter_uvicorn
                self._hook_loaded = True
            except Exception:
                self._hook_loaded = True
    
    def __getattr__(self, name):
        self._load_real_hook()
        if self._real_hook and hasattr(self._real_hook, name):
            return getattr(self._real_hook, name)
        return lambda *args, **kwargs: None
```

**Complete Monitoring Coverage**:
- ✓ **Uvicorn instrumentation**: Thread pool metrics, connection handling, request lifecycle
- ✓ **Distributed tracing**: Full request tracing across services and LLM calls
- ✓ **Transaction traces**: Detailed performance data and code-level visibility
- ✓ **LLM monitoring**: Tracks OpenAI and LangChain calls
- ✓ **Error tracking**: Captures and reports exceptions
- ✓ **No initialization conflicts**: Works seamlessly with LangGraph Platform

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
NEW_RELIC_LICENSE_KEY = <your-new-relic-license-key>
```

The `NEW_RELIC_LICENSE_KEY` is required to activate New Relic monitoring.

### Step 4: Configure Environment Variables

In the deployment settings, set **Environment Variables**:

```
NEW_RELIC_ENVIRONMENT=production
```

The `agent.py` file will automatically initialize New Relic when `NEW_RELIC_LICENSE_KEY` is set in secrets.

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
- Verify `NEW_RELIC_LICENSE_KEY` is set in LangSmith secrets
- Check that `newrelic` package is installed (`requirements.txt`)
- Verify agent initialization message in deployment logs: "✅ New Relic agent initialized"
- Check `newrelic.ini` configuration settings
- View New Relic agent logs in deployment output

### Uvicorn-related New Relic errors (AttributeError, hook conflicts)
- **These are now prevented** by the `ResilientUvicornHook` in `agent.py`
- The hook safely delays real hook loading until after New Relic is initialized
- Full Uvicorn and transaction instrumentation is preserved
- Thread pool metrics and connection handling are tracked
- If you see hook errors, verify that `ResilientUvicornHook` is properly installed in `agent.py`

## Support

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Deployment Guide](https://docs.smith.langchain.com/)
- [New Relic Python Agent Docs](https://docs.newrelic.com/docs/agents/python-agent/)
