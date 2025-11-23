# TraceMind-AI - Technical Architecture

This document provides a deep technical dive into the TraceMind-AI architecture, implementation details, and system design.

## Table of Contents

- [System Overview](#system-overview)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [MCP Client Architecture](#mcp-client-architecture)
- [Agent Framework Integration](#agent-framework-integration)
- [Data Flow](#data-flow)
- [Authentication & Authorization](#authentication--authorization)
- [Screen Navigation](#screen-navigation)
- [Job Submission Architecture](#job-submission-architecture)
- [Deployment](#deployment)
- [Performance Optimization](#performance-optimization)

---

## System Overview

TraceMind-AI is a comprehensive Gradio-based web application for evaluating AI agent performance. It serves as the user-facing platform in the TraceMind ecosystem, demonstrating enterprise MCP client usage (Track 2: MCP in Action).

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **UI Framework** | Gradio | 5.49.1 | Web interface with components |
| **MCP Client** | MCP Python SDK | Latest | Connect to MCP servers |
| **Agent Framework** | smolagents | 1.22.0+ | Autonomous agent with MCP tools |
| **Data Source** | HuggingFace Datasets | Latest | Load evaluation results |
| **Authentication** | HuggingFace OAuth | - | User authentication |
| **Job Platforms** | HF Jobs + Modal | - | Evaluation job submission |
| **Language** | Python | 3.10+ | Core implementation |

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ User Browser                                                 │
│  - Gradio Interface (React-based)                           │
│  - OAuth Flow (HuggingFace)                                 │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ HTTP/WebSocket
               ↓
┌─────────────────────────────────────────────────────────────┐
│ TraceMind-AI (Gradio App) - Track 2                         │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Screen Layer (screens/)                             │   │
│  │  - Leaderboard                                       │   │
│  │  - Agent Chat                                        │   │
│  │  - New Evaluation                                    │   │
│  │  - Job Monitoring                                    │   │
│  │  - Trace Detail                                      │   │
│  │  - Settings                                          │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────┴────────────────────────────────────────┐   │
│  │ Component Layer (components/)                       │   │
│  │  - Leaderboard Table (Custom HTML)                  │   │
│  │  - Analytics Charts                                  │   │
│  │  - Metric Displays                                   │   │
│  │  - Report Cards                                      │   │
│  └────────────┬────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────┴────────────────────────────────────────┐   │
│  │ Service Layer                                        │   │
│  │  ┌──────────────────┐  ┌──────────────────┐        │   │
│  │  │ MCP Client       │  │ Data Loader      │        │   │
│  │  │ (mcp_client/)    │  │ (data_loader.py) │        │   │
│  │  └──────────────────┘  └──────────────────┘        │   │
│  │  ┌──────────────────┐  ┌──────────────────┐        │   │
│  │  │ Agent (smolagents│  │ Job Submission   │        │   │
│  │  │ screens/chat.py) │  │ (utils/)         │        │   │
│  │  └──────────────────┘  └──────────────────┘        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└───────────┬───────────────────────────────────┬─────────────┘
            │                                   │
            ↓                                   ↓
┌───────────────────────┐         ┌───────────────────────┐
│ TraceMind MCP Server  │         │ External Services     │
│ (Track 1)             │         │  - HF Datasets        │
│  - 11 AI Tools        │         │  - HF Jobs            │
│  - 3 Resources        │         │  - Modal              │
│  - 3 Prompts          │         │  - LLM APIs           │
└───────────────────────┘         └───────────────────────┘
```

---

## Project Structure

```
TraceMind-AI/
├── app.py                          # Main entry point, Gradio app
│
├── screens/                        # UI screens (6 tabs)
│   ├── __init__.py
│   ├── leaderboard.py             # Screen 1: Leaderboard with AI insights
│   ├── chat.py                    # Screen 2: Agent Chat (smolagents)
│   ├── dashboard.py               # Screen 3: New Evaluation
│   ├── job_monitoring.py          # Screen 4: Job Status Tracking
│   ├── trace_detail.py            # Screen 5: Trace Visualization
│   ├── settings.py                # Screen 6: API Key Configuration
│   ├── compare.py                 # Screen 7: Run Comparison (optional)
│   ├── documentation.py           # Screen 8: API Documentation
│   └── mcp_helpers.py             # Shared MCP client helpers
│
├── components/                     # Reusable UI components
│   ├── __init__.py
│   ├── leaderboard_table.py       # Custom HTML table component
│   ├── analytics_charts.py        # Performance charts (Plotly)
│   ├── metric_displays.py         # Metric cards and badges
│   ├── report_cards.py            # Summary report cards
│   └── thought_graph.py           # Agent reasoning visualization
│
├── mcp_client/                     # MCP client implementation
│   ├── __init__.py
│   ├── client.py                  # Async MCP client
│   └── sync_wrapper.py            # Synchronous wrapper for Gradio
│
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── auth.py                    # HuggingFace OAuth
│   ├── navigation.py              # Screen navigation state
│   ├── hf_jobs_submission.py      # HuggingFace Jobs integration
│   └── modal_job_submission.py    # Modal integration
│
├── styles/                         # Custom styling
│   ├── __init__.py
│   └── tracemind_theme.py         # Gradio theme customization
│
├── data_loader.py                  # Dataset loading and caching
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore
├── README.md                       # Project documentation
└── USER_GUIDE.md                   # Complete user guide

Total: ~35 files, ~8,000 lines of code
```

### File Breakdown

| Directory | Files | Lines | Purpose |
|-----------|-------|-------|---------|
| `screens/` | 9 | ~3,500 | UI screen implementations |
| `components/` | 5 | ~1,200 | Reusable UI components |
| `mcp_client/` | 3 | ~800 | MCP client integration |
| `utils/` | 4 | ~1,500 | Authentication, jobs, navigation |
| `styles/` | 2 | ~300 | Custom theme and CSS |
| Root | 3 | ~700 | Main app, data loader, config |

---

## Core Components

### 1. app.py - Main Application

**Purpose**: Entry point, orchestrates all screens and manages global state.

**Architecture**:

```python
# app.py structure
import gradio as gr
from screens import *
from mcp_client.sync_wrapper import get_sync_mcp_client
from utils.auth import auth_ui
from data_loader import DataLoader

# 1. Initialize services
mcp_client = get_sync_mcp_client()
mcp_client.initialize()
data_loader = DataLoader()

# 2. Create Gradio app
with gr.Blocks(theme=tracemind_theme) as app:
    # Global state
    gr.State(...)  # User session, navigation, etc.

    # Authentication (if not disabled)
    if not DISABLE_OAUTH:
        auth_ui()

    # Main tabs
    with gr.Tabs():
        with gr.Tab("📊 Leaderboard"):
            leaderboard_screen()

        with gr.Tab("🤖 Agent Chat"):
            chat_screen()

        with gr.Tab("🚀 New Evaluation"):
            dashboard_screen()

        with gr.Tab("📈 Job Monitoring"):
            job_monitoring_screen()

        with gr.Tab("⚙️ Settings"):
            settings_screen()

# 3. Launch
if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
```

**Key Responsibilities**:
- Initialize MCP client and data loader (global instances)
- Create tabbed interface with all screens
- Manage authentication flow
- Handle global state (user session, API keys)

---

### 2. Screen Layer (screens/)

Each screen is a self-contained module that returns a Gradio component tree.

#### screens/leaderboard.py

**Purpose**: Display evaluation results with AI-powered insights.

**Components**:
- Load button
- AI insights panel (Markdown) - powered by MCP server
- Leaderboard table (custom HTML component)
- Filter controls (agent type, provider)

**MCP Integration**:
```python
def load_leaderboard(mcp_client):
    # 1. Load dataset
    ds = load_dataset("kshitijthakkar/smoltrace-leaderboard")
    df = pd.DataFrame(ds)

    # 2. Get AI insights from MCP server
    insights = mcp_client.analyze_leaderboard(
        metric_focus="overall",
        time_range="last_week",
        top_n=5
    )

    # 3. Render table with custom component
    table_html = render_leaderboard_table(df)

    return insights, table_html
```

#### screens/chat.py

**Purpose**: Autonomous agent interface with MCP tool access.

**Agent Setup**:
```python
from smolagents import ToolCallingAgent, MCPClient, HfApiModel

# Initialize agent with MCP client
def create_agent():
    mcp_client = MCPClient(MCP_SERVER_URL)

    model = HfApiModel(
        model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
        token=os.getenv("HF_TOKEN")
    )

    agent = ToolCallingAgent(
        tools=[],  # MCP tools loaded automatically
        model=model,
        mcp_client=mcp_client,
        max_steps=10
    )

    return agent

# Chat interaction
def agent_chat(message, history, show_reasoning):
    if show_reasoning:
        agent.verbosity_level = 2  # Show tool execution
    else:
        agent.verbosity_level = 0  # Only final answer

    response = agent.run(message)
    history.append((message, response))

    return history, ""
```

**MCP Tool Access**:
Agent automatically discovers and uses all 11 MCP tools from TraceMind MCP Server.

#### screens/dashboard.py

**Purpose**: Submit evaluation jobs to HuggingFace Jobs or Modal.

**Key Functions**:
- Model selection (text input)
- Infrastructure choice (HF Jobs / Modal)
- Hardware selection (auto / manual)
- Cost estimation (MCP-powered)
- Job submission

**Cost Estimation Flow**:
```python
def estimate_cost_click(model, agent_type, num_tests, hardware, mcp_client):
    # Call MCP server for cost estimate
    estimate = mcp_client.estimate_cost(
        model=model,
        agent_type=agent_type,
        num_tests=num_tests,
        hardware=hardware
    )

    return estimate  # Display in dialog
```

**Job Submission Flow**:
```python
def submit_job(model, agent_type, hardware, infrastructure, api_keys):
    if infrastructure == "HuggingFace Jobs":
        job_id = submit_hf_job(model, agent_type, hardware, api_keys)
    elif infrastructure == "Modal":
        job_id = submit_modal_job(model, agent_type, hardware, api_keys)

    return f"✅ Job submitted: {job_id}"
```

#### screens/job_monitoring.py

**Purpose**: Track status of submitted jobs.

**Data Source**: HuggingFace Jobs API or Modal API

**Refresh Strategy**:
- Manual refresh button
- Auto-refresh every 30 seconds (optional)

#### screens/trace_detail.py

**Purpose**: Visualize OpenTelemetry traces with GPU metrics.

**Components**:
- Waterfall diagram (spans timeline)
- Span details panel
- GPU metrics overlay (for GPU jobs)
- MCP-powered Q&A

**Trace Loading**:
```python
def load_trace(trace_id, traces_repo):
    # Load trace dataset
    ds = load_dataset(traces_repo)
    trace_data = ds.filter(lambda x: x["trace_id"] == trace_id)[0]

    # Render waterfall
    waterfall_html = render_waterfall(trace_data["spans"])

    return waterfall_html
```

**MCP Q&A**:
```python
def ask_trace_question(trace_id, traces_repo, question, mcp_client):
    # Call MCP server to debug trace
    answer = mcp_client.debug_trace(
        trace_id=trace_id,
        traces_repo=traces_repo,
        question=question
    )

    return answer
```

#### screens/settings.py

**Purpose**: Configure API keys and preferences.

**Security**:
- Keys stored in Gradio State (session-only, not server-side)
- All forms use `api_name=False` (not exposed via API)
- HTTPS encryption for all API calls

**Configuration Options**:
- Gemini API Key
- HuggingFace Token
- Modal Token ID + Secret
- LLM Provider Keys (OpenAI, Anthropic, etc.)

---

### 3. Component Layer (components/)

Reusable UI components that can be used across multiple screens.

#### components/leaderboard_table.py

**Purpose**: Custom HTML table with sorting, filtering, and styling.

**Why Custom Component?**:
- Gradio's default Dataframe component lacks advanced styling
- Need clickable rows for navigation
- Custom sorting and filtering logic
- Badge rendering for metrics

**Implementation**:
```python
def render_leaderboard_table(df: pd.DataFrame) -> str:
    """Render leaderboard as interactive HTML table"""

    html = """
    <style>
        .leaderboard-table { ... }
        .metric-badge { ... }
    </style>
    <table class="leaderboard-table">
        <thead>
            <tr>
                <th onclick="sortTable(0)">Model</th>
                <th onclick="sortTable(1)">Success Rate</th>
                <th onclick="sortTable(2)">Cost</th>
                ...
            </tr>
        </thead>
        <tbody>
    """

    for idx, row in df.iterrows():
        html += f"""
            <tr onclick="selectRun('{row['run_id']}')">
                <td>{row['model']}</td>
                <td><span class="badge success">{row['success_rate']}%</span></td>
                <td>${row['total_cost_usd']:.4f}</td>
                ...
            </tr>
        """

    html += """
        </tbody>
    </table>
    <script>
        function sortTable(col) { ... }
        function selectRun(runId) {
            // Trigger Gradio event to navigate to run detail
            document.dispatchEvent(new CustomEvent('runSelected', {detail: runId}));
        }
    </script>
    """

    return html
```

**Integration with Gradio**:
```python
# In leaderboard screen
table_html = gr.HTML()

load_btn.click(
    fn=lambda: render_leaderboard_table(df),
    outputs=table_html
)
```

#### components/analytics_charts.py

**Purpose**: Performance charts using Plotly.

**Charts Provided**:
- Success rate over time (line chart)
- Cost comparison (bar chart)
- Duration distribution (histogram)
- CO2 emissions by model (pie chart)

**Example**:
```python
import plotly.graph_objects as go

def create_cost_comparison_chart(df):
    fig = go.Figure(data=[
        go.Bar(
            x=df['model'],
            y=df['total_cost_usd'],
            marker_color='indianred'
        )
    ])

    fig.update_layout(
        title="Cost Comparison by Model",
        xaxis_title="Model",
        yaxis_title="Total Cost (USD)"
    )

    return fig
```

#### components/thought_graph.py

**Purpose**: Visualize agent reasoning steps (for Agent Chat).

**Visualization**:
- Graph nodes: Reasoning steps, tool calls
- Edges: Flow between steps
- Annotations: Tool results, errors

---

### 4. MCP Client Layer (mcp_client/)

#### mcp_client/client.py - Async MCP Client

**Purpose**: Connect to TraceMind MCP Server via MCP protocol.

**Implementation**: (See [MCP_INTEGRATION.md](MCP_INTEGRATION_TRACEMIND_AI.md) for full code)

**Key Methods**:
- `connect()`: Establish SSE connection to MCP server
- `call_tool(tool_name, arguments)`: Call an MCP tool
- `analyze_leaderboard(**kwargs)`: Wrapper for analyze_leaderboard tool
- `estimate_cost(**kwargs)`: Wrapper for estimate_cost tool
- `debug_trace(**kwargs)`: Wrapper for debug_trace tool

#### mcp_client/sync_wrapper.py - Synchronous Wrapper

**Purpose**: Provide synchronous API for Gradio event handlers.

**Why Needed?**: Gradio event handlers are synchronous, but MCP client is async.

**Pattern**:
```python
class SyncMCPClient:
    def __init__(self, mcp_server_url):
        self.async_client = AsyncMCPClient(mcp_server_url)

    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def analyze_leaderboard(self, **kwargs):
        """Synchronous wrapper"""
        return self._run_async(self.async_client.analyze_leaderboard(**kwargs))
```

---

### 5. Data Loader (data_loader.py)

**Purpose**: Load and cache HuggingFace datasets.

**Features**:
- In-memory caching (5-minute TTL)
- Error handling for missing datasets
- Automatic retry logic
- Dataset validation

**Implementation**:
```python
from datasets import load_dataset
from functools import lru_cache
import time

class DataLoader:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def load_leaderboard(self, repo="kshitijthakkar/smoltrace-leaderboard"):
        """Load leaderboard with caching"""
        cache_key = f"leaderboard:{repo}"

        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data

        # Load fresh data
        ds = load_dataset(repo, split="train")
        df = pd.DataFrame(ds)

        # Cache
        self.cache[cache_key] = (time.time(), df)

        return df

    def load_results(self, repo):
        """Load results dataset for specific run"""
        ds = load_dataset(repo, split="train")
        return pd.DataFrame(ds)

    def load_traces(self, repo):
        """Load traces dataset for specific run"""
        ds = load_dataset(repo, split="train")
        return ds  # Keep as Dataset for filtering
```

---

## MCP Client Architecture

**Full details in**: [MCP_INTEGRATION.md](MCP_INTEGRATION_TRACEMIND_AI.md)

**Summary**:
- **Async Client**: `mcp_client/client.py` - async MCP protocol implementation
- **Sync Wrapper**: `mcp_client/sync_wrapper.py` - synchronous API for Gradio
- **Global Instance**: Initialized once in `app.py`, shared across all screens

**Usage Pattern**:
```python
# In app.py (initialization)
from mcp_client.sync_wrapper import get_sync_mcp_client
mcp_client = get_sync_mcp_client()
mcp_client.initialize()

# In screen (usage)
def some_event_handler(mcp_client):
    result = mcp_client.analyze_leaderboard(metric_focus="cost")
    return result
```

---

## Agent Framework Integration

**Full details in**: [MCP_INTEGRATION.md](MCP_INTEGRATION_TRACEMIND_AI.md)

**Framework**: smolagents (HuggingFace's agent framework)

**Key Features**:
- Autonomous tool discovery from MCP server
- Multi-step reasoning with tool chaining
- Context-aware responses
- Reasoning visualization (optional)

**Agent Setup**:
```python
from smolagents import ToolCallingAgent, MCPClient

agent = ToolCallingAgent(
    tools=[],  # Empty - tools loaded from MCP server
    model=HfApiModel("Qwen/Qwen2.5-Coder-32B-Instruct"),
    mcp_client=MCPClient(MCP_SERVER_URL),
    max_steps=10
)
```

---

## Data Flow

### Leaderboard Loading Flow

```
1. User clicks "Load Leaderboard"
   ↓
2. Gradio Event Handler (leaderboard.py)
   load_leaderboard()
   ↓
3. Data Loader (data_loader.py)
   ├─→ Check cache (5-min TTL)
   │   └─→ If cached: return cached data
   └─→ If not cached: load from HF Datasets
       └─→ load_dataset("kshitijthakkar/smoltrace-leaderboard")
   ↓
4. MCP Client (sync_wrapper.py)
   mcp_client.analyze_leaderboard(metric_focus="overall")
   ↓
5. MCP Server (TraceMind-mcp-server)
   ├─→ Load data
   ├─→ Call Gemini API
   └─→ Return AI analysis
   ↓
6. Render Components
   ├─→ AI Insights (Markdown)
   └─→ Leaderboard Table (Custom HTML)
   ↓
7. Display to User
```

### Agent Chat Flow

```
1. User types message: "What are the top 3 models?"
   ↓
2. Gradio Event Handler (chat.py)
   agent_chat(message, history, show_reasoning)
   ↓
3. smolagents Agent
   agent.run(message)
   ├─→ Step 1: Plan approach
   │   └─→ "Need to get top models from leaderboard"
   ├─→ Step 2: Discover MCP tools
   │   └─→ Found: get_top_performers, analyze_leaderboard
   ├─→ Step 3: Call MCP tool
   │   └─→ get_top_performers(metric="success_rate", top_n=3)
   ├─→ Step 4: Parse result
   │   └─→ Extract model names, success rates, costs
   └─→ Step 5: Format response
       └─→ Generate markdown table with insights
   ↓
4. Return to user with full reasoning trace (if enabled)
```

### Job Submission Flow

```
1. User fills form → Clicks "Submit Evaluation"
   ↓
2. Gradio Event Handler (dashboard.py)
   submit_job(model, agent_type, hardware, infrastructure)
   ↓
3. Job Submission Module (utils/)
   if infrastructure == "HuggingFace Jobs":
       ├─→ hf_jobs_submission.py
       ├─→ Build job config (YAML)
       ├─→ Submit via HF Jobs API
       └─→ Return job_id
   elif infrastructure == "Modal":
       ├─→ modal_job_submission.py
       ├─→ Build Modal app config
       ├─→ Submit via Modal SDK
       └─→ Return job_id
   ↓
4. Store job_id in session state
   ↓
5. Redirect to Job Monitoring screen
   ↓
6. Auto-refresh status every 30s
```

---

## Authentication & Authorization

### HuggingFace OAuth

**Implementation**: `utils/auth.py`

**Flow**:
```
1. User visits TraceMind-AI
   ↓
2. Check OAuth token in session
   ├─→ If valid: proceed to app
   └─→ If invalid: show login screen
   ↓
3. User clicks "Sign in with HuggingFace"
   ↓
4. Redirect to HuggingFace OAuth page
   ├─→ User authorizes TraceMind-AI
   └─→ HF redirects back with token
   ↓
5. Store token in Gradio State (session)
   ↓
6. Use token for:
   ├─→ HF Datasets access
   ├─→ HF Jobs submission
   └─→ User identification
```

**Code**:
```python
# utils/auth.py
import gradio as gr

def auth_ui():
    """Create OAuth login UI"""
    gr.LoginButton(
        value="Sign in with HuggingFace",
        auth_provider="huggingface"
    )

# In app.py
with gr.Blocks() as app:
    if not DISABLE_OAUTH:
        auth_ui()
```

### API Key Storage

**Strategy**: Session-only storage (not server-side persistence)

**Implementation**:
```python
# In settings screen
def save_api_keys(gemini_key, hf_token):
    """Store keys in session state"""
    session_state = gr.State({
        "gemini_key": gemini_key,
        "hf_token": hf_token
    })

    # Override default clients with user keys
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token

    return "✅ API keys saved for this session"
```

**Security**:
- ✅ Keys stored only in browser memory
- ✅ Not saved to disk or database
- ✅ Forms use `api_name=False` (not exposed via API)
- ✅ HTTPS encryption

---

## Screen Navigation

### State Management

**Pattern**: Gradio State components for session data

```python
# In app.py
with gr.Blocks() as app:
    # Global state
    session_state = gr.State({
        "user": None,
        "current_run_id": None,
        "current_trace_id": None,
        "api_keys": {}
    })

    # Pass to all screens
    leaderboard_screen(session_state)
    chat_screen(session_state)
```

### Navigation Between Screens

**Pattern**: Click event triggers tab switch + state update

```python
# In leaderboard screen
def row_click(run_id, session_state):
    """Navigate to run detail when row clicked"""
    session_state["current_run_id"] = run_id

    # Switch to trace detail tab (Tab index 4)
    return gr.Tabs.update(selected=4), session_state

table_component.select(
    fn=row_click,
    inputs=[gr.State(), session_state],
    outputs=[main_tabs, session_state]
)
```

---

## Job Submission Architecture

### HuggingFace Jobs Integration

**File**: `utils/hf_jobs_submission.py`

**Key Functions**:
```python
def submit_hf_job(model, agent_type, hardware, api_keys):
    """Submit evaluation job to HuggingFace Jobs"""

    # 1. Build job config (YAML)
    job_config = {
        "name": f"SMOLTRACE Eval - {model}",
        "hardware": hardware,  # cpu-basic, t4-small, a10g-small, a100-large, h200
        "environment": {
            "MODEL": model,
            "AGENT_TYPE": agent_type,
            "HF_TOKEN": api_keys["hf_token"],
            # ... other env vars
        },
        "command": [
            "pip install smoltrace[otel,gpu]",
            f"smoltrace-eval --model {model} --agent-type {agent_type} ..."
        ]
    }

    # 2. Submit via HF Jobs API
    response = requests.post(
        "https://huggingface.co/api/jobs",
        headers={"Authorization": f"Bearer {api_keys['hf_token']}"},
        json=job_config
    )

    # 3. Return job ID
    job_id = response.json()["id"]
    return job_id
```

### Modal Integration

**File**: `utils/modal_job_submission.py`

**Key Functions**:
```python
import modal

def submit_modal_job(model, agent_type, hardware, api_keys):
    """Submit evaluation job to Modal"""

    # 1. Create Modal app
    app = modal.App("smoltrace-eval")

    # 2. Define function with GPU
    @app.function(
        image=modal.Image.debian_slim().pip_install("smoltrace[otel,gpu]"),
        gpu=hardware,  # A10, A100-80GB, H200
        secrets=[
            modal.Secret.from_dict({
                "HF_TOKEN": api_keys["hf_token"],
                # ... other secrets
            })
        ]
    )
    def run_evaluation():
        import smoltrace
        # Run evaluation
        results = smoltrace.evaluate(model=model, agent_type=agent_type)
        return results

    # 3. Deploy and run
    with app.run():
        result = run_evaluation.remote()

    return result.job_id
```

---

## Deployment

### HuggingFace Spaces

**Platform**: HuggingFace Spaces
**SDK**: Gradio 5.49.1
**Hardware**: CPU Basic (upgradeable)
**URL**: https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind

### Configuration

**Space Metadata** (README.md header):
```yaml
---
title: TraceMind AI
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
short_description: AI agent evaluation with MCP-powered intelligence
license: agpl-3.0
pinned: true
tags:
  - mcp-in-action-track-enterprise
  - agent-evaluation
  - mcp-client
  - leaderboard
  - gradio
---
```

### Environment Variables

**Set in HF Spaces Secrets**:
```bash
# Required
GEMINI_API_KEY=your_gemini_key
HF_TOKEN=your_hf_token

# Optional
MCP_SERVER_URL=https://mcp-1st-birthday-tracemind-mcp-server.hf.space/gradio_api/mcp/sse
LEADERBOARD_REPO=kshitijthakkar/smoltrace-leaderboard
DISABLE_OAUTH=false  # Set to true for local development
```

---

## Performance Optimization

### 1. Data Caching

**Implementation**: `data_loader.py`
- In-memory cache with 5-minute TTL
- Reduces HF Datasets API calls
- Faster page loads

### 2. Async MCP Calls

**Pattern**: Use async for non-blocking I/O
```python
# Could be optimized to run in parallel
async def load_data_with_insights():
    leaderboard_task = load_dataset_async(...)
    insights_task = mcp_client.analyze_leaderboard_async(...)

    leaderboard, insights = await asyncio.gather(leaderboard_task, insights_task)
    return leaderboard, insights
```

### 3. Component Lazy Loading

**Strategy**: Load components only when tabs are activated
```python
with gr.Tab("Trace Detail", visible=False) as trace_tab:
    # Components created only when tab first shown
    @trace_tab.select
    def load_trace_components():
        return build_trace_visualization()
```

---

## Related Documentation

- [README.md](PROPOSED_README_TRACEMIND_AI.md) - Overview and quick start
- [USER_GUIDE.md](USER_GUIDE_TRACEMIND_AI.md) - Complete screen-by-screen guide
- [MCP_INTEGRATION.md](MCP_INTEGRATION_TRACEMIND_AI.md) - MCP client implementation
- [TraceMind MCP Server Architecture](ARCHITECTURE_MCP_SERVER.md) - Server-side architecture

---

**Last Updated**: November 21, 2025
**Version**: 1.0.0
**Track**: MCP in Action (Enterprise)
