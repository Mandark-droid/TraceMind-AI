# TraceMind-AI - MCP Integration Guide

This document explains how TraceMind-AI integrates with MCP servers to provide AI-powered agent evaluation.

## Table of Contents

- [Overview](#overview)
- [Dual MCP Integration](#dual-mcp-integration)
- [Architecture](#architecture)
- [MCP Client Implementation](#mcp-client-implementation)
- [Agent Framework Integration](#agent-framework-integration)
- [MCP Tools Usage](#mcp-tools-usage)
- [Development Guide](#development-guide)

---

## Overview

TraceMind-AI demonstrates **enterprise MCP client usage** as part of the **Track 2: MCP in Action** submission. It showcases two distinct patterns of MCP integration:

1. **Direct MCP Client**: Python-based client connecting to remote MCP server via SSE transport
2. **Autonomous Agent**: `smolagents`-based agent with access to MCP tools for multi-step reasoning

Both patterns consume the same MCP server ([TraceMind-mcp-server](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server)) to provide AI-powered analysis of agent evaluation data.

---

## Dual MCP Integration

### Pattern 1: Direct MCP Client Integration

**Where**: Leaderboard insights, cost estimation dialogs, trace debugging

**How it works**:
```python
# TraceMind-AI calls MCP server directly
mcp_client = get_sync_mcp_client()
insights = mcp_client.analyze_leaderboard(
    metric_focus="overall",
    time_range="last_week",
    top_n=5
)
# Display insights in UI
```

**Use cases**:
- Generate leaderboard insights when user clicks "Load Leaderboard"
- Estimate costs when user clicks "Estimate Cost" in New Evaluation form
- Debug traces when user asks questions in trace visualization

**Advantages**:
- Direct, fast execution
- Synchronous API (easy to integrate with Gradio)
- Predictable, structured responses

---

### Pattern 2: Autonomous Agent with MCP Tools

**Where**: Agent Chat tab

**How it works**:
```python
# smolagents agent discovers and uses MCP tools autonomously
from smolagents import ToolCallingAgent, MCPClient

# Agent initialized with MCP client
agent = ToolCallingAgent(
    tools=[],  # Tools loaded from MCP server
    model=model_client,
    mcp_client=MCPClient(mcp_server_url)
)

# User asks question
result = agent.run("What are the top 3 models and their costs?")

# Agent plans:
#   1. Call get_top_performers MCP tool
#   2. Extract costs from results
#   3. Format and present to user
```

**Use cases**:
- Answer complex questions requiring multi-step analysis
- Compare models across multiple dimensions
- Plan evaluation strategies with cost estimates
- Provide recommendations based on leaderboard data

**Advantages**:
- Natural language interface
- Multi-step reasoning
- Autonomous tool selection
- Context-aware responses

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│ TraceMind-AI (Gradio App) - Track 2                         │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ UI Layer (Gradio)                                       │ │
│ │  - Leaderboard tab                                      │ │
│ │  - Agent Chat tab                                       │ │
│ │  - New Evaluation tab                                   │ │
│ │  - Trace Visualization tab                              │ │
│ └────────────┬─────────────────────────────┬──────────────┘ │
│              ↓                             ↓                 │
│  ┌───────────────────────┐   ┌──────────────────────────┐  │
│  │ Direct MCP Client     │   │ Autonomous Agent         │  │
│  │ (sync_wrapper.py)     │   │ (smolagents)             │  │
│  │                       │   │                          │  │
│  │ - Synchronous API     │   │ - Multi-step reasoning   │  │
│  │ - Tool calling        │   │ - Tool discovery         │  │
│  │ - Error handling      │   │ - Context management     │  │
│  └───────────┬───────────┘   └─────────────┬────────────┘  │
│              └─────────────────┬─────────────┘               │
│                                ↓                             │
│                         MCP Protocol                         │
│                         (SSE Transport)                      │
└────────────────────────────────┬────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────┐
│ TraceMind MCP Server - Track 1                              │
│ https://huggingface.co/spaces/MCP-1st-Birthday/             │
│ TraceMind-mcp-server                                        │
│                                                               │
│ 11 AI-Powered Tools:                                        │
│  - analyze_leaderboard                                      │
│  - debug_trace                                              │
│  - estimate_cost                                            │
│  - compare_runs                                             │
│  - analyze_results                                          │
│  - get_top_performers                                       │
│  - get_leaderboard_summary                                  │
│  - get_dataset                                              │
│  - generate_synthetic_dataset                               │
│  - push_dataset_to_hub                                      │
│  - generate_prompt_template                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## MCP Client Implementation

### File Structure

```
TraceMind-AI/
├── mcp_client/
│   ├── __init__.py
│   ├── client.py              # Async MCP client
│   └── sync_wrapper.py        # Synchronous wrapper for Gradio
├── agent/
│   ├── __init__.py
│   └── smolagents_setup.py    # Agent with MCP integration
└── app.py                     # Main Gradio app
```

### Async MCP Client (`client.py`)

```python
from mcp import ClientSession, StdioServerParameters
import mcp.types as types

class TraceMindMCPClient:
    """Async MCP client for TraceMind MCP Server"""

    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        self.session = None

    async def connect(self):
        """Establish connection to MCP server via SSE"""
        # For HTTP-based MCP servers (HuggingFace Spaces)
        self.session = ClientSession(
            ServerParameters(
                url=self.mcp_server_url,
                transport="sse"
            )
        )
        await self.session.__aenter__()

        # List available tools
        tools_result = await self.session.list_tools()
        self.available_tools = {tool.name: tool for tool in tools_result.tools}

        print(f"Connected to MCP server. Available tools: {list(self.available_tools.keys())}")

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool with given arguments"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        if tool_name not in self.available_tools:
            raise ValueError(f"Tool '{tool_name}' not available. Available: {list(self.available_tools.keys())}")

        # Call the tool
        result = await self.session.call_tool(tool_name, arguments=arguments)

        # Extract text response
        if result.content and len(result.content) > 0:
            return result.content[0].text
        return ""

    async def analyze_leaderboard(self, **kwargs) -> str:
        """Wrapper for analyze_leaderboard tool"""
        return await self.call_tool("analyze_leaderboard", kwargs)

    async def estimate_cost(self, **kwargs) -> str:
        """Wrapper for estimate_cost tool"""
        return await self.call_tool("estimate_cost", kwargs)

    async def debug_trace(self, **kwargs) -> str:
        """Wrapper for debug_trace tool"""
        return await self.call_tool("debug_trace", kwargs)

    async def compare_runs(self, **kwargs) -> str:
        """Wrapper for compare_runs tool"""
        return await self.call_tool("compare_runs", kwargs)

    async def get_top_performers(self, **kwargs) -> str:
        """Wrapper for get_top_performers tool"""
        return await self.call_tool("get_top_performers", kwargs)

    async def disconnect(self):
        """Close MCP connection"""
        if self.session:
            await self.session.__aexit__(None, None, None)
```

### Synchronous Wrapper (`sync_wrapper.py`)

```python
import asyncio
from typing import Optional
from .client import TraceMindMCPClient

class SyncMCPClient:
    """Synchronous wrapper for async MCP client (Gradio-compatible)"""

    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        self.async_client = TraceMindMCPClient(mcp_server_url)
        self._connected = False

    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)

    def initialize(self):
        """Connect to MCP server"""
        if not self._connected:
            self._run_async(self.async_client.connect())
            self._connected = True

    def analyze_leaderboard(self, **kwargs) -> str:
        """Synchronous wrapper for analyze_leaderboard"""
        if not self._connected:
            self.initialize()
        return self._run_async(self.async_client.analyze_leaderboard(**kwargs))

    def estimate_cost(self, **kwargs) -> str:
        """Synchronous wrapper for estimate_cost"""
        if not self._connected:
            self.initialize()
        return self._run_async(self.async_client.estimate_cost(**kwargs))

    def debug_trace(self, **kwargs) -> str:
        """Synchronous wrapper for debug_trace"""
        if not self._connected:
            self.initialize()
        return self._run_async(self.async_client.debug_trace(**kwargs))

    # ... (similar wrappers for other tools)

# Global instance for use in Gradio app
_mcp_client: Optional[SyncMCPClient] = None

def get_sync_mcp_client() -> SyncMCPClient:
    """Get or create global sync MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        mcp_server_url = os.getenv(
            "MCP_SERVER_URL",
            "https://mcp-1st-birthday-tracemind-mcp-server.hf.space/gradio_api/mcp/sse"
        )
        _mcp_client = SyncMCPClient(mcp_server_url)
    return _mcp_client
```

### Usage in Gradio App

```python
# app.py
from mcp_client.sync_wrapper import get_sync_mcp_client

# Initialize MCP client
mcp_client = get_sync_mcp_client()
mcp_client.initialize()

# Use in Gradio event handlers
def load_leaderboard():
    """Load leaderboard and generate AI insights"""
    # Load dataset
    ds = load_dataset("kshitijthakkar/smoltrace-leaderboard")
    df = pd.DataFrame(ds)

    # Get AI insights from MCP server
    try:
        insights = mcp_client.analyze_leaderboard(
            metric_focus="overall",
            time_range="last_week",
            top_n=5
        )
    except Exception as e:
        insights = f"❌ Error generating insights: {str(e)}"

    return df, insights

# Gradio UI
with gr.Blocks() as app:
    with gr.Tab("📊 Leaderboard"):
        load_btn = gr.Button("Load Leaderboard")
        insights_md = gr.Markdown(label="AI Insights")
        leaderboard_table = gr.Dataframe()

        load_btn.click(
            fn=load_leaderboard,
            outputs=[leaderboard_table, insights_md]
        )
```

---

## Agent Framework Integration

### smolagents Setup

```python
# agent/smolagents_setup.py
from smolagents import ToolCallingAgent, MCPClient, HfApiModel
import os

def create_agent():
    """Create smolagents agent with MCP tool access"""

    # 1. Configure MCP client
    mcp_server_url = os.getenv(
        "MCP_SERVER_URL",
        "https://mcp-1st-birthday-tracemind-mcp-server.hf.space/gradio_api/mcp/sse"
    )

    mcp_client = MCPClient(mcp_server_url)

    # 2. Configure LLM
    model = HfApiModel(
        model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
        token=os.getenv("HF_TOKEN")
    )

    # 3. Create agent with MCP tools
    agent = ToolCallingAgent(
        tools=[],  # MCP tools loaded automatically
        model=model,
        mcp_client=mcp_client,
        max_steps=10,
        verbosity_level=1
    )

    return agent

def run_agent_query(agent: ToolCallingAgent, query: str, show_reasoning: bool = False):
    """Run agent query and return response"""
    try:
        # Set verbosity based on show_reasoning flag
        if show_reasoning:
            agent.verbosity_level = 2  # Show tool execution logs
        else:
            agent.verbosity_level = 0  # Only show final answer

        # Run agent
        result = agent.run(query)

        return result
    except Exception as e:
        return f"❌ Agent error: {str(e)}"
```

### Agent Chat UI

```python
# app.py
from agent.smolagents_setup import create_agent, run_agent_query

# Initialize agent (once at startup)
agent = create_agent()

def agent_chat(message: str, history: list, show_reasoning: bool):
    """Handle agent chat interaction"""
    # Run agent query
    response = run_agent_query(agent, message, show_reasoning)

    # Update chat history
    history.append((message, response))

    return history, ""

# Gradio UI
with gr.Blocks() as app:
    with gr.Tab("🤖 Agent Chat"):
        gr.Markdown("## Autonomous Agent with MCP Tools")
        gr.Markdown("Ask questions about agent evaluations. The agent has access to all MCP tools.")

        chatbot = gr.Chatbot(label="Agent Chat")
        msg = gr.Textbox(label="Your Question", placeholder="What are the top 3 models and their costs?")
        show_reasoning = gr.Checkbox(label="Show Agent Reasoning", value=False)

        # Quick action buttons
        with gr.Row():
            quick_top = gr.Button("Quick: Top Models")
            quick_cost = gr.Button("Quick: Cost Estimate")
            quick_load = gr.Button("Quick: Load Leaderboard")

        # Event handlers
        msg.submit(agent_chat, [msg, chatbot, show_reasoning], [chatbot, msg])

        quick_top.click(
            lambda h, sr: agent_chat(
                "What are the top 5 models by success rate with their costs?",
                h,
                sr
            ),
            [chatbot, show_reasoning],
            [chatbot, msg]
        )
```

---

## MCP Tools Usage

### Tools Used in TraceMind-AI

| Tool | Where Used | Purpose |
|------|-----------|---------|
| `analyze_leaderboard` | Leaderboard tab | Generate AI insights when user loads leaderboard |
| `estimate_cost` | New Evaluation tab | Predict costs before submitting evaluation |
| `debug_trace` | Trace Visualization | Answer questions about execution traces |
| `compare_runs` | Agent Chat | Compare two evaluation runs side-by-side |
| `analyze_results` | Agent Chat | Analyze detailed test results with optimization recommendations |
| `get_top_performers` | Agent Chat | Efficiently fetch top N models (90% token reduction) |
| `get_leaderboard_summary` | Agent Chat | Get high-level statistics (99% token reduction) |
| `get_dataset` | Agent Chat | Load SMOLTRACE datasets for detailed analysis |

### Example Tool Calls

**Example 1: Leaderboard Insights**
```python
# User clicks "Load Leaderboard" button
insights = mcp_client.analyze_leaderboard(
    leaderboard_repo="kshitijthakkar/smoltrace-leaderboard",
    metric_focus="overall",
    time_range="last_week",
    top_n=5
)

# Display in Gradio Markdown component
insights_md.value = insights
```

**Example 2: Cost Estimation**
```python
# User fills New Evaluation form and clicks "Estimate Cost"
estimate = mcp_client.estimate_cost(
    model="meta-llama/Llama-3.1-8B",
    agent_type="both",
    num_tests=100,
    hardware="auto"
)

# Display in dialog
gr.Info(estimate)
```

**Example 3: Agent Multi-Step Query**
```python
# User asks: "What are the top 3 models and how much do they cost?"

# Agent reasoning (internal):
#   Step 1: Need to get top models by success rate
#   → Call get_top_performers(metric="success_rate", top_n=3)
#
#   Step 2: Extract cost information from results
#   → Parse JSON response, get "total_cost_usd" field
#
#   Step 3: Format response for user
#   → Create markdown table with model names, success rates, costs

# Agent response:
"""
Here are the top 3 models by success rate:

1. **GPT-4**: 95.8% success rate, $0.05 per run
2. **Claude-3**: 94.1% success rate, $0.04 per run
3. **Llama-3.1-8B**: 93.4% success rate, $0.002 per run

GPT-4 leads in accuracy but is 25x more expensive than Llama-3.1.
For cost-sensitive workloads, Llama-3.1 offers the best value.
"""
```

---

## Development Guide

### Adding New MCP Tool Integration

1. **Add method to async client** (`client.py`):
```python
async def new_tool_name(self, **kwargs) -> str:
    """Wrapper for new_tool_name MCP tool"""
    return await self.call_tool("new_tool_name", kwargs)
```

2. **Add synchronous wrapper** (`sync_wrapper.py`):
```python
def new_tool_name(self, **kwargs) -> str:
    """Synchronous wrapper for new_tool_name"""
    if not self._connected:
        self.initialize()
    return self._run_async(self.async_client.new_tool_name(**kwargs))
```

3. **Use in Gradio app** (`app.py`):
```python
def handle_new_tool():
    result = mcp_client.new_tool_name(param1="value1", param2="value2")
    return result
```

**Note**: Agent automatically discovers new tools from MCP server, no code changes needed!

### Testing MCP Integration

**Test 1: Connection**
```python
python -c "from mcp_client.sync_wrapper import get_sync_mcp_client; client = get_sync_mcp_client(); client.initialize(); print('✅ MCP client connected')"
```

**Test 2: Tool Call**
```python
from mcp_client.sync_wrapper import get_sync_mcp_client

client = get_sync_mcp_client()
client.initialize()

result = client.analyze_leaderboard(
    metric_focus="cost",
    time_range="last_week",
    top_n=3
)

print(result)
```

**Test 3: Agent**
```python
from agent.smolagents_setup import create_agent, run_agent_query

agent = create_agent()
response = run_agent_query(agent, "What are the top 3 models?", show_reasoning=True)
print(response)
```

### Debugging MCP Issues

**Issue**: Connection timeout
- **Check**: MCP server is running at specified URL
- **Check**: Network connectivity to HuggingFace Spaces
- **Check**: SSE transport is enabled on server

**Issue**: Tool not found
- **Check**: MCP server has the tool implemented
- **Check**: Tool name matches exactly (case-sensitive)
- **Check**: Client initialized successfully (call `initialize()` first)

**Issue**: Agent not using MCP tools
- **Check**: MCPClient is properly configured in agent setup
- **Check**: Agent has `max_steps > 0` to allow tool usage
- **Check**: Query requires tool usage (not answerable from agent's knowledge alone)

---

## Performance Considerations

### Token Optimization

**Problem**: Loading full leaderboard dataset consumes excessive tokens
**Solution**: Use token-optimized MCP tools

```python
# ❌ BAD: Loads all 51 runs (50K+ tokens)
leaderboard = mcp_client.get_dataset("kshitijthakkar/smoltrace-leaderboard")

# ✅ GOOD: Returns only top 5 (5K tokens, 90% reduction)
top_performers = mcp_client.get_top_performers(top_n=5)

# ✅ BETTER: Returns summary stats (500 tokens, 99% reduction)
summary = mcp_client.get_leaderboard_summary()
```

### Caching

**Problem**: Repeated identical MCP calls waste time and credits
**Solution**: Implement client-side caching

```python
from functools import lru_cache
import time

@lru_cache(maxsize=32)
def cached_analyze_leaderboard(metric_focus: str, time_range: str, top_n: int, cache_key: int):
    """Cached MCP call with TTL via cache_key"""
    return mcp_client.analyze_leaderboard(
        metric_focus=metric_focus,
        time_range=time_range,
        top_n=top_n
    )

# Use with 5-minute cache TTL
cache_key = int(time.time() // 300)  # Changes every 5 minutes
insights = cached_analyze_leaderboard("overall", "last_week", 5, cache_key)
```

### Async Optimization

**Problem**: Sequential MCP calls block UI
**Solution**: Use async for parallel calls

```python
import asyncio

async def load_leaderboard_with_insights():
    """Load leaderboard and insights in parallel"""
    # Start both operations concurrently
    leaderboard_task = asyncio.create_task(load_dataset_async("kshitijthakkar/smoltrace-leaderboard"))
    insights_task = asyncio.create_task(mcp_client.analyze_leaderboard(metric_focus="overall"))

    # Wait for both to complete
    leaderboard, insights = await asyncio.gather(leaderboard_task, insights_task)

    return leaderboard, insights
```

---

## Security Considerations

### API Key Management

**DO**:
- Store API keys in environment variables or HF Spaces secrets
- Use session-only storage in Gradio (not server-side persistence)
- Rotate keys regularly

**DON'T**:
- Hardcode API keys in source code
- Expose keys in client-side JavaScript
- Log API keys in console or files

### MCP Server Trust

**Verify MCP server authenticity**:
- Use HTTPS URLs only
- Verify domain ownership (huggingface.co spaces)
- Review MCP server code before connecting (open source)

**Limit tool access**:
- Only connect to trusted MCP servers
- Review tool permissions before use
- Implement rate limiting for tool calls

---

## Related Documentation

- [USER_GUIDE.md](USER_GUIDE.md) - Complete UI walkthrough
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
- [TraceMind MCP Server Documentation](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server)

---

**Last Updated**: November 21, 2025
