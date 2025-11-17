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

# 🧠 TraceMind-AI

<p align="center">
  <img src="https://raw.githubusercontent.com/Mandark-droid/TraceMind-AI/assets/Logo.png" alt="TraceMind-AI Logo" width="200"/>
</p>

**Agent Evaluation Platform with MCP-Powered Intelligence**

[![MCP's 1st Birthday Hackathon](https://img.shields.io/badge/MCP%27s%201st%20Birthday-Hackathon-blue)](https://github.com/modelcontextprotocol)
[![Track](https://img.shields.io/badge/Track-MCP%20in%20Action%20(Enterprise)-purple)](https://github.com/modelcontextprotocol/hackathon)
[![Powered by Gradio](https://img.shields.io/badge/Powered%20by-Gradio-orange)](https://gradio.app/)

> **🎯 Track 2 Submission**: MCP in Action (Enterprise)
> **📅 MCP's 1st Birthday Hackathon**: November 14-30, 2025

## Overview

TraceMind-AI is a comprehensive platform for evaluating AI agent performance across different models, providers, and configurations. It provides real-time insights, cost analysis, and detailed trace visualization powered by the Model Context Protocol (MCP).

### 🏗️ **Built on Open Source Foundation**

This platform is part of a complete agent evaluation ecosystem built on two foundational open-source projects:

**🔭 TraceVerde (genai_otel_instrument)** - Automatic OpenTelemetry Instrumentation
- **What**: Zero-code OTEL instrumentation for LLM frameworks (LiteLLM, Transformers, LangChain, etc.)
- **Why**: Captures every LLM call, tool usage, and agent step automatically
- **Links**: [GitHub](https://github.com/Mandark-droid/genai_otel_instrument) | [PyPI](https://pypi.org/project/genai-otel-instrument)

**📊 SMOLTRACE** - Agent Evaluation Engine
- **What**: Lightweight, production-ready evaluation framework with OTEL tracing built-in
- **Why**: Generates structured datasets (leaderboard, results, traces, metrics) displayed in this UI
- **Links**: [GitHub](https://github.com/Mandark-droid/SMOLTRACE) | [PyPI](https://pypi.org/project/smoltrace/)

**The Flow**: `TraceVerde` instruments your agents → `SMOLTRACE` evaluates them → `TraceMind-AI` visualizes results with MCP-powered intelligence

---

## Features

- **📊 Real-time Leaderboard**: Live evaluation data from HuggingFace datasets
- **🤖 Autonomous Agent Chat**: Interactive agent powered by smolagents with MCP tools (Track 2)
- **💬 MCP Integration**: AI-powered analysis using remote MCP servers
- **💰 Cost Estimation**: Calculate evaluation costs for different models and configurations
- **🔍 Trace Visualization**: Detailed OpenTelemetry trace analysis
- **📈 Performance Metrics**: GPU utilization, CO2 emissions, token usage tracking
- **🧠 Agent Reasoning**: View step-by-step agent planning and tool execution

## MCP Integration

TraceMind demonstrates enterprise MCP client usage by connecting to [TraceMind-mcp-server](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server) via the Model Context Protocol.

**MCP Tools Used:**
- `analyze_leaderboard` - AI-generated insights about evaluation trends
- `estimate_cost` - Cost estimation with hardware recommendations
- `debug_trace` - Interactive trace analysis and debugging
- `compare_runs` - Side-by-side run comparison
- `analyze_results` - Test case analysis with optimization recommendations

## Quick Start

### Prerequisites
- Python 3.10+
- HuggingFace account (for authentication)
- HuggingFace token (optional, for private datasets)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Mandark-droid/TraceMind-AI.git
cd TraceMind-AI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
python app.py
```

Visit http://localhost:7860

## Configuration

Create a `.env` file with the following variables:

```env
# HuggingFace Configuration
HF_TOKEN=your_token_here

# Agent Model Configuration (for Chat Screen - Track 2)
# Options: "hfapi" (default), "inference_client", "litellm"
AGENT_MODEL_TYPE=hfapi

# API Keys for different model types
# Required if AGENT_MODEL_TYPE=litellm
GEMINI_API_KEY=your_gemini_api_key_here

# MCP Server URL (note: /sse endpoint for smolagents integration)
MCP_SERVER_URL=https://mcp-1st-birthday-tracemind-mcp-server.hf.space/gradio_api/mcp/sse

# Dataset Configuration
LEADERBOARD_REPO=kshitijthakkar/smoltrace-leaderboard

# Development Mode (optional - disables OAuth for local testing)
DISABLE_OAUTH=true
```

### Agent Model Options

The Agent Chat screen supports three model configurations:

1. **`hfapi` (Default)**: Uses HuggingFace Inference API
   - Model: `Qwen/Qwen2.5-Coder-32B-Instruct`
   - Requires: `HF_TOKEN`
   - Best for: General use, free tier available

2. **`inference_client`**: Uses Nebius provider
   - Model: `deepseek-ai/DeepSeek-V3-0324`
   - Requires: `HF_TOKEN`
   - Best for: Advanced reasoning, faster inference

3. **`litellm`**: Uses Google Gemini
   - Model: `gemini/gemini-2.5-flash`
   - Requires: `GEMINI_API_KEY`
   - Best for: Gemini-specific features

## Data Sources

TraceMind-AI loads evaluation data from HuggingFace datasets:

- **Leaderboard**: Aggregate statistics for all evaluation runs
- **Results**: Individual test case results
- **Traces**: OpenTelemetry trace data
- **Metrics**: GPU metrics and performance data

## Architecture

### Project Structure

```
TraceMind-AI/
├── app.py                 # Main Gradio application
├── data_loader.py         # HuggingFace dataset integration
├── mcp_client/            # MCP client implementation
│   ├── client.py          # Async MCP client
│   └── sync_wrapper.py    # Synchronous wrapper
├── utils/                 # Utilities
│   ├── auth.py            # HuggingFace OAuth
│   └── navigation.py      # Screen navigation
├── screens/               # UI screens
├── components/            # Reusable components
└── styles/                # Custom CSS
```

### MCP Client Integration

TraceMind-AI uses the MCP Python SDK to connect to remote MCP servers:

```python
from mcp_client.sync_wrapper import get_sync_mcp_client

# Initialize MCP client
mcp_client = get_sync_mcp_client()
mcp_client.initialize()

# Call MCP tools
insights = mcp_client.analyze_leaderboard(
    metric_focus="overall",
    time_range="last_week",
    top_n=5
)
```

## Usage

### Viewing the Leaderboard

1. Log in with your HuggingFace account
2. Navigate to the "Leaderboard" tab
3. Click "Load Leaderboard" to fetch the latest data
4. View AI-powered insights generated by the MCP server

### Estimating Costs

1. Navigate to the "Cost Estimator" tab
2. Enter the model name (e.g., `openai/gpt-4`)
3. Select agent type and number of tests
4. Click "Estimate Cost" for AI-powered analysis

### Viewing Trace Details

1. Select an evaluation run from the leaderboard
2. Click on a specific test case
3. View detailed OpenTelemetry trace visualization
4. Ask questions about the trace using MCP-powered analysis

### Using the Agent Chat (Track 2)

1. Navigate to the "🤖 Agent Chat" tab
2. The autonomous agent will initialize with MCP tools from TraceMind MCP Server
3. Ask questions about agent evaluations:
   - "What are the top 3 performing models and their costs?"
   - "Estimate the cost of running 500 tests with DeepSeek-V3 on H200"
   - "Load the leaderboard and show me the last 5 run IDs"
4. Watch the agent plan, execute tools, and provide detailed answers
5. Enable "Show Agent Reasoning" to see step-by-step tool execution
6. Use Quick Action buttons for common queries

**Example Questions:**
- Analysis: "Analyze the current leaderboard and show me the top performing models with their costs"
- Cost Comparison: "Compare the costs of the top 3 models - which one offers the best value?"
- Recommendations: "Based on the leaderboard data, which model would you recommend for a production system?"

## Technology Stack

- **UI Framework**: Gradio 5.49.1
- **Agent Framework**: smolagents 1.22.0+ (Track 2)
- **MCP Protocol**: MCP integration via Gradio & smolagents MCPClient
- **Data**: HuggingFace Datasets API
- **Authentication**: HuggingFace OAuth
- **AI Models**:
  - Default: Qwen/Qwen2.5-Coder-32B-Instruct (HF Inference API)
  - Optional: DeepSeek-V3 (Nebius), Gemini 2.5 Flash
  - MCP Server: Google Gemini 2.5 Pro

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set development mode (optional - disables OAuth)
export DISABLE_OAUTH=true

# Run the app
python app.py
```

### Running on HuggingFace Spaces

This application is configured for deployment on HuggingFace Spaces using the Gradio SDK. The `app.py` file serves as the entry point.

## Documentation

For detailed implementation documentation, see:
- [Data Loader API](data_loader.py) - Dataset loading and caching
- [MCP Client API](mcp_client/client.py) - MCP protocol integration
- [Authentication](utils/auth.py) - HuggingFace OAuth integration

## Demo Video

[Link to demo video showing the application in action]

## Social Media

[Link to social media post about this project]

## License

AGPL-3.0 License

This project is licensed under the GNU Affero General Public License v3.0. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Built By

**Track**: MCP in Action (Enterprise)
**Author**: Kshitij Thakkar
**Powered by**: MCP Servers (TraceMind-mcp-server) + Gradio
**Built with**: Gradio 5.49.1 (MCP client integration)

---

## Acknowledgments

- **MCP Team** - For the Model Context Protocol specification
- **Gradio Team** - For Gradio 6 with MCP integration
- **HuggingFace** - For Spaces hosting and dataset infrastructure
- **Google** - For Gemini API access

## Links

- **Live Demo**: https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind
- **MCP Server**: https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server
- **GitHub**: https://github.com/Mandark-droid/TraceMind-AI
- **MCP Specification**: https://modelcontextprotocol.io

---

**MCP's 1st Birthday Hackathon Submission**
*Track: MCP in Action - Enterprise*
