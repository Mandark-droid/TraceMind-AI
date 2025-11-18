"""
Documentation Screen for TraceMind-AI
Comprehensive documentation for the TraceMind ecosystem
"""

import gradio as gr


def create_about_tab():
    """Create the About tab with ecosystem overview"""
    return gr.Markdown("""
# 🧠 TraceMind Ecosystem

<div align="center">
  <img src="https://raw.githubusercontent.com/Mandark-droid/TraceMind-AI/assets/TraceVerse_Logo.png" alt="TraceVerse Ecosystem" width="400"/>
  <br/>
  <br/>
  <img src="https://raw.githubusercontent.com/Mandark-droid/TraceMind-AI/assets/Logo.png" alt="TraceMind Logo" width="300"/>
</div>

<br/>

**The Complete AI Agent Evaluation Platform**

[![MCP's 1st Birthday Hackathon](https://img.shields.io/badge/MCP%27s%201st%20Birthday-Hackathon-blue)](https://github.com/modelcontextprotocol)
[![Track 2](https://img.shields.io/badge/Track-MCP%20in%20Action%20(Enterprise)-purple)](https://github.com/modelcontextprotocol/hackathon)
[![Powered by Gradio](https://img.shields.io/badge/Powered%20by-Gradio-orange)](https://gradio.app/)

> **🎯 Track 2 Submission**: MCP in Action (Enterprise)
> **📅 MCP's 1st Birthday Hackathon**: November 14-30, 2025

TraceMind is a comprehensive ecosystem for evaluating, monitoring, and optimizing AI agents. Built on open-source foundations and powered by the Model Context Protocol (MCP), TraceMind provides everything you need for production-grade agent evaluation.

---

## 📖 Table of Contents

- [Architecture Overview](#️-architecture-overview)
- [The Complete Flow](#-the-complete-flow)
- [Key Features](#-key-features)
- [Built for MCP's 1st Birthday Hackathon](#-built-for-mcps-1st-birthday-hackathon)
- [Quick Links](#-quick-links)
- [Documentation Navigation](#-documentation-navigation)
- [Getting Started](#-getting-started)
- [Contributing](#-contributing)
- [Acknowledgments](#-acknowledgments)

---

<details open>
<summary><h2>🏗️ Architecture Overview</h2></summary>

The TraceMind ecosystem consists of four integrated components:

```
┌─────────────────────────────────────────────────────────────┐
│                    TraceMind Ecosystem                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1️⃣ TraceVerde (genai_otel_instrument)                      │
│     └─ Automatic OpenTelemetry Instrumentation              │
│        └─ Zero-code tracing for LLM frameworks               │
│                                                               │
│  2️⃣ SMOLTRACE                                                │
│     └─ Lightweight Agent Evaluation Engine                   │
│        └─ Generates structured datasets                      │
│                                                               │
│  3️⃣ TraceMind-MCP-Server                                     │
│     └─ MCP Server (Track 1: Building MCP)                    │
│        └─ Provides intelligent analysis tools                │
│                                                               │
│  4️⃣ TraceMind-AI (This App!)                                 │
│     └─ Gradio UI (Track 2: MCP in Action)                    │
│        └─ Visualizes data + consumes MCP tools               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

</details>

---

<details open>
<summary><h2>🔄 The Complete Flow</h2></summary>

### 1. **Instrument Your Agents** (TraceVerde)
```python
import genai_otel

# Zero-code instrumentation
genai_otel.instrument()

# Your agent code runs normally, but now traced!
agent.run("What's the weather in Tokyo?")
```

### 2. **Evaluate with SMOLTRACE**
```bash
# Run comprehensive evaluation
smoltrace-eval \\
  --model openai/gpt-4 \\
  --agent-type both \\
  --enable-otel
```

### 3. **Analyze Results** (This UI)
- View leaderboard rankings
- Compare model performance
- Explore detailed traces
- Ask questions with MCP-powered chat

</details>

---

<details open>
<summary><h2>🎯 Key Features</h2></summary>

### For Developers
- ✅ **Zero-code Instrumentation**: Just import and go
- ✅ **Framework Agnostic**: Works with LiteLLM, Transformers, LangChain, CrewAI, etc.
- ✅ **Production Ready**: Lightweight, minimal overhead
- ✅ **Standards Compliant**: Uses OpenTelemetry conventions

### For Researchers
- ✅ **Comprehensive Metrics**: Token usage, costs, latency, GPU utilization
- ✅ **Reproducible Results**: Structured datasets on HuggingFace
- ✅ **Model Comparison**: Side-by-side analysis
- ✅ **Trace Visualization**: Step-by-step agent execution

### For Organizations
- ✅ **Cost Transparency**: Real-time cost tracking and estimation
- ✅ **Sustainability**: CO2 emissions monitoring (TraceVerde)
- ✅ **MCP Integration**: Connect to intelligent analysis tools
- ✅ **HuggingFace Native**: Seamless dataset integration

</details>

---

## 🏆 Built for MCP's 1st Birthday Hackathon

TraceMind demonstrates the complete MCP ecosystem:

**Track 1 (Building MCP)**: [TraceMind-mcp-server](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server)
- Provides MCP tools for leaderboard analysis, cost estimation, trace debugging

**Track 2 (MCP in Action)**: TraceMind-AI (this app!)
- Consumes MCP servers for autonomous agent chat and intelligent insights

---

## 🔗 Quick Links

| Component | Description | Links |
|-----------|-------------|-------|
| **TraceVerde** | OTEL Instrumentation | [GitHub](https://github.com/Mandark-droid/genai_otel_instrument) • [PyPI](https://pypi.org/project/genai-otel-instrument) |
| **SMOLTRACE** | Evaluation Engine | [GitHub](https://github.com/Mandark-droid/SMOLTRACE) • [PyPI](https://pypi.org/project/smoltrace/) |
| **MCP Server** | Building MCP (Track 1) | [HF Space](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server) |
| **TraceMind-AI** | MCP in Action (Track 2) | [HF Space](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind) |

---

## 📚 Documentation Navigation

Use the tabs above to explore detailed documentation for each component:

- **About**: This overview (you are here)
- **TraceVerde**: OpenTelemetry instrumentation for LLMs
- **SmolTrace**: Agent evaluation engine
- **TraceMind-MCP-Server**: MCP server implementation details

---

<details open>
<summary><h2>💡 Getting Started</h2></summary>

### Quick Start (5 minutes)
```bash
# 1. Install TraceVerde for instrumentation
pip install genai-otel-instrument

# 2. Install SMOLTRACE for evaluation
pip install smoltrace

# 3. Run your first evaluation
smoltrace-eval --model openai/gpt-4 --agent-type tool

# 4. View results in TraceMind-AI (this UI!)
```

### Learn More
- Read component-specific docs in the tabs above
- Try the **Agent Chat** for interactive queries
- Explore the **Leaderboard** to see real evaluation data
- Check the **Trace Detail** screen for deep inspection

</details>

---

## 🤝 Contributing

All components are open source under AGPL-3.0:
- Report issues on GitHub
- Submit pull requests
- Share your evaluation results
- Join the community discussions

---

## 👏 Acknowledgments

Built with ❤️ for **MCP's 1st Birthday Hackathon** by **Kshitij Thakkar**

Special thanks to:
- **Anthropic** - For the Model Context Protocol
- **Gradio Team** - For Gradio 6 with MCP integration
- **HuggingFace** - For Spaces and dataset infrastructure
- **Google** - For Gemini API access
- **OpenTelemetry** - For standardized observability

---

*Last Updated: November 2025*
""")


def create_traceverde_tab():
    """Create the TraceVerde documentation tab"""
    return gr.Markdown("""
# 🔭 TraceVerde (genai_otel_instrument)

<div align="center">
  <img src="https://raw.githubusercontent.com/Mandark-droid/genai_otel_instrument/main/.github/images/Logo.jpg" alt="TraceVerde Logo" width="400"/>
</div>

<br/>

[![PyPI version](https://badge.fury.io/py/genai-otel-instrument.svg)](https://badge.fury.io/py/genai-otel-instrument)
[![Python Versions](https://img.shields.io/pypi/pyversions/genai-otel-instrument.svg)](https://pypi.org/project/genai-otel-instrument/)
[![License](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Downloads](https://static.pepy.tech/badge/genai-otel-instrument)](https://pepy.tech/project/genai-otel-instrument)
[![Downloads/Month](https://static.pepy.tech/badge/genai-otel-instrument/month)](https://pepy.tech/project/genai-otel-instrument)

[![GitHub Stars](https://img.shields.io/github/stars/Mandark-droid/genai_otel_instrument?style=social)](https://github.com/Mandark-droid/genai_otel_instrument)
[![GitHub Forks](https://img.shields.io/github/forks/Mandark-droid/genai_otel_instrument?style=social)](https://github.com/Mandark-droid/genai_otel_instrument)
[![GitHub Issues](https://img.shields.io/github/issues/Mandark-droid/genai_otel_instrument)](https://github.com/Mandark-droid/genai_otel_instrument/issues)

[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-1.20%2B-blueviolet)](https://opentelemetry.io/)
[![Semantic Conventions](https://img.shields.io/badge/OTel%20Semconv-GenAI%20v1.28-orange)](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Automatic OpenTelemetry Instrumentation for LLM Applications**

---

## 📖 Table of Contents

- [What is TraceVerde?](#what-is-traceverde)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Supported Frameworks](#-supported-frameworks)
- [What Gets Captured?](#-what-gets-captured)
- [CO2 Emissions Tracking](#-co2-emissions-tracking)
- [Advanced Configuration](#-advanced-configuration)
- [Integration with SMOLTRACE](#-integration-with-smoltrace)
- [Use Cases](#-use-cases)
- [OpenTelemetry Standards](#-opentelemetry-standards)
- [Resources](#-resources)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)
- [Contributing](#-contributing)

---

## What is TraceVerde?

TraceVerde is a **zero-code** OpenTelemetry instrumentation library for GenAI applications. It automatically captures:

- 🔹 Every LLM call (token usage, cost, latency)
- 🔹 Tool executions and results
- 🔹 Agent reasoning steps
- 🔹 GPU metrics (utilization, memory, temperature)
- 🔹 CO2 emissions (via CodeCarbon integration)

All with **one import statement** - no code changes required!

---

## 📦 Installation

```bash
pip install genai-otel-instrument

# With GPU metrics support
pip install genai-otel-instrument[gpu]

# With CO2 emissions tracking
pip install genai-otel-instrument[carbon]

# All features
pip install genai-otel-instrument[all]
```

---

<details open>
<summary><h2>🚀 Quick Start</h2></summary>

### Basic Usage

**Option 1: Environment Variables (No code changes)**

```bash
export OTEL_SERVICE_NAME=my-llm-app
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
python your_app.py
```

**Option 2: One line of code**

```python
import genai_otel
genai_otel.instrument()

# Your existing code works unchanged
import openai
client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Traces are automatically captured and exported!
```

**Option 3: With OpenTelemetry Setup**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# 1. Setup OpenTelemetry (one-time setup)
trace.set_tracer_provider(TracerProvider())
span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

# 2. Instrument all LLM frameworks (one line!)
import genai_otel
genai_otel.instrument()

# 3. Use your LLM framework normally - it's now traced!
from litellm import completion

response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Traces are automatically captured and exported!
```

</details>

---

## 🎯 Supported Frameworks

TraceVerde automatically instruments:

| Framework | Status | Import Required |
|-----------|--------|-----------------|
| **LiteLLM** | ✅ Full Support | `from litellm import completion` |
| **Transformers** | ✅ Full Support | `from transformers import pipeline` |
| **LangChain** | ✅ Full Support | `from langchain import ...` |
| **CrewAI** | ✅ Full Support | `from crewai import Agent` |
| **smolagents** | ✅ Full Support | `from smolagents import ...` |
| **OpenAI SDK** | ✅ Full Support | `from openai import OpenAI` |

**No code changes needed** - just import and use as normal!

---

<details>
<summary><h2>📊 What Gets Captured?</h2></summary>

### LLM Spans

Every LLM call creates a span with:

```json
{
  "span_name": "LLM Call - Reasoning",
  "attributes": {
    "gen_ai.system": "openai",
    "gen_ai.request.model": "gpt-4",
    "gen_ai.operation.name": "chat",
    "gen_ai.usage.prompt_tokens": 78,
    "gen_ai.usage.completion_tokens": 156,
    "gen_ai.usage.total_tokens": 234,
    "gen_ai.usage.cost.total": 0.0012,
    "gen_ai.response.finish_reasons": ["stop"],
    "gen_ai.request.temperature": 0.7
  }
}
```

### Tool Spans

Tool executions are traced with:

```json
{
  "span_name": "Tool Call - get_weather",
  "attributes": {
    "tool.name": "get_weather",
    "tool.input": "{\\"location\\": \\"Tokyo\\"}",
    "tool.output": "{\\"temp\\": \\"18°C\\"}",
    "tool.latency_ms": 890
  }
}
```

### GPU Metrics

When enabled, captures real-time GPU data:

```json
{
  "metrics": [
    {
      "name": "gen_ai.gpu.utilization",
      "value": 67.5,
      "unit": "%",
      "timestamp": "2025-11-18T14:23:00Z"
    },
    {
      "name": "gen_ai.gpu.memory.used",
      "value": 512.34,
      "unit": "MiB"
    }
  ]
}
```

</details>

---

## 🌱 CO2 Emissions Tracking

TraceVerde integrates with CodeCarbon for sustainability monitoring:

```python
import genai_otel

# Enable CO2 tracking
genai_otel.instrument(enable_carbon_tracking=True)

# Your LLM calls now track carbon emissions!
```

**Captured Metrics:**
- 🌍 CO2 emissions (grams)
- ⚡ Energy consumed (kWh)
- 📍 Geographic region
- 💻 Hardware type (CPU/GPU)

---

## 🔧 Advanced Configuration

### Custom Exporters

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Export to Jaeger/Tempo/etc
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

import genai_otel
genai_otel.instrument()
```

### GPU Metrics

```python
# Enable GPU monitoring (requires pynvml)
import genai_otel
genai_otel.instrument(
    enable_gpu_metrics=True,
    gpu_poll_interval=1.0  # seconds
)
```

---

## 📈 Integration with SMOLTRACE

TraceVerde powers SMOLTRACE's evaluation capabilities:

```python
# SMOLTRACE automatically uses TraceVerde for instrumentation
from smoltrace import evaluate_agent

results = evaluate_agent(
    model="gpt-4",
    agent_type="tool",
    enable_otel=True  # Uses TraceVerde under the hood!
)
```

---

## 🎯 Use Cases

### 1. Development & Debugging
```python
# See exactly what your agent is doing
import genai_otel
genai_otel.instrument()

# Run your agent
agent.run("Complex task")

# View traces in console or Jaeger
```

### 2. Production Monitoring
```python
# Export to your observability platform
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

otlp_exporter = OTLPSpanExporter(endpoint="https://your-otel-collector")
# ... setup processor ...

import genai_otel
genai_otel.instrument()
```

### 3. Cost Analysis
```python
# Track costs across all LLM calls
import genai_otel
genai_otel.instrument()

# Analyze cost per user/session/feature
# All costs automatically captured in span attributes
```

### 4. Sustainability Reporting
```python
# Monitor environmental impact
import genai_otel
genai_otel.instrument(
    enable_carbon_tracking=True,
    enable_gpu_metrics=True
)

# Generate CO2 reports from trace data
```

---

## 📐 OpenTelemetry Standards

TraceVerde follows the **Gen AI Semantic Conventions**:
- ✅ Consistent attribute naming (`gen_ai.*`)
- ✅ Standard span structure
- ✅ Compatible with all OTEL collectors
- ✅ Works with Jaeger, Tempo, Datadog, New Relic, etc.

---

## 🔗 Resources

- **GitHub**: [github.com/Mandark-droid/genai_otel_instrument](https://github.com/Mandark-droid/genai_otel_instrument)
- **PyPI**: [pypi.org/project/genai-otel-instrument](https://pypi.org/project/genai-otel-instrument)
- **Examples**: [github.com/Mandark-droid/genai_otel_instrument/examples](https://github.com/Mandark-droid/genai_otel_instrument/tree/main/examples)
- **OpenTelemetry Docs**: [opentelemetry.io](https://opentelemetry.io)

---

## 🐛 Troubleshooting

### Common Issues

**Q: Traces not appearing?**
```python
# Make sure you setup a tracer provider first
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())
```

**Q: GPU metrics not working?**
```bash
# Install GPU support
pip install genai-otel-instrument[gpu]

# Verify NVIDIA drivers installed
nvidia-smi
```

**Q: How to configure different options?**
```python
# Use environment variables or pass options to instrument()
import genai_otel
genai_otel.instrument(enable_gpu_metrics=True)
```

---

## 📄 License

**AGPL-3.0** - Open source and free to use

---

## 🤝 Contributing

Contributions welcome!
- Report bugs on GitHub Issues
- Submit PRs for new framework support
- Share your use cases

---

*TraceVerde - Making AI agents observable, one trace at a time* 🔭
""")


def create_smoltrace_tab():
    """Create the SMOLTRACE documentation tab"""
    return gr.Markdown("""
# 📊 SMOLTRACE

**Lightweight Agent Evaluation Engine with Built-in OpenTelemetry Tracing**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://github.com/Mandark-droid/SMOLTRACE/blob/main/LICENSE)
[![PyPI version](https://badge.fury.io/py/smoltrace.svg)](https://badge.fury.io/py/smoltrace)
[![Downloads](https://static.pepy.tech/badge/smoltrace)](https://pepy.tech/project/smoltrace)
[![Downloads/Month](https://static.pepy.tech/badge/smoltrace/month)](https://pepy.tech/project/smoltrace)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Tests](https://img.shields.io/github/actions/workflow/status/Mandark-droid/SMOLTRACE/test.yml?branch=main&label=tests)](https://github.com/Mandark-droid/SMOLTRACE/actions?query=workflow%3Atest)
[![Docs](https://img.shields.io/badge/docs-stable-blue.svg)](https://huggingface.co/docs/smoltrace/en/index)

---

## 📖 Table of Contents

- [What is SMOLTRACE?](#what-is-smoltrace)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Evaluation Types](#-evaluation-types)
- [What Gets Generated?](#-what-gets-generated)
- [Configuration Options](#-configuration-options)
- [Integration with HuggingFace Jobs](#️-integration-with-huggingface-jobs)
- [Integration with TraceMind-AI](#-integration-with-tracemind-ai)
- [Best Practices](#-best-practices)
- [Cost Estimation](#-cost-estimation)
- [Architecture](#-architecture)
- [Resources](#-resources)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)
- [Contributing](#-contributing)

---

## What is SMOLTRACE?

SMOLTRACE is a **production-ready** evaluation framework for AI agents that:

- ✅ Evaluates agents across tool usage, code execution, and both
- ✅ Supports both API models (via LiteLLM) and local models (via Transformers)
- ✅ Automatically captures OpenTelemetry traces using TraceVerde
- ✅ Generates structured datasets for HuggingFace
- ✅ Tracks costs, GPU metrics, and CO2 emissions

**Goal**: Become HuggingFace's standard agent evaluation platform

---

## 📦 Installation

```bash
# Basic installation
pip install smoltrace

# With OpenTelemetry support
pip install smoltrace[otel]

# With GPU metrics
pip install smoltrace[otel,gpu]

# Everything
pip install smoltrace[all]
```

---

<details open>
<summary><h2>🚀 Quick Start</h2></summary>

### Command Line

```bash
# Evaluate GPT-4 as a tool agent
smoltrace-eval \\
  --model openai/gpt-4 \\
  --provider litellm \\
  --agent-type tool \\
  --enable-otel

# Evaluate local Llama model
smoltrace-eval \\
  --model meta-llama/Llama-3.1-8B \\
  --provider transformers \\
  --agent-type both \\
  --enable-otel \\
  --enable-gpu-metrics
```

### Python API

```python
from smoltrace import evaluate_agent

# Run evaluation
results = evaluate_agent(
    model="openai/gpt-4",
    provider="litellm",
    agent_type="tool",
    enable_otel=True,
    num_tests=100
)

# Access results
print(f"Success Rate: {results.success_rate}%")
print(f"Total Cost: ${results.total_cost}")
print(f"Avg Duration: {results.avg_duration_ms}ms")

# Upload to HuggingFace
results.upload_to_hf(
    results_repo="username/agent-results-gpt4",
    traces_repo="username/agent-traces-gpt4",
    leaderboard_repo="username/agent-leaderboard"
)
```

</details>

---

## 🎯 Evaluation Types

### 1. Tool Agent
Tests ability to use external tools:
```bash
smoltrace-eval --model gpt-4 --agent-type tool
```

**Example Task**: "What's the weather in Tokyo?"
- Agent must call `get_weather` tool
- Verify correct tool selection
- Check response quality

### 2. Code Agent
Tests code generation and execution:
```bash
smoltrace-eval --model gpt-4 --agent-type code
```

**Example Task**: "Calculate the sum of first 10 prime numbers"
- Agent must generate Python code
- Execute code safely
- Return correct result

### 3. Both (Combined)
Tests comprehensive agent capabilities:
```bash
smoltrace-eval --model gpt-4 --agent-type both
```

**Tests both tool usage AND code generation**

---

<details>
<summary><h2>📊 What Gets Generated?</h2></summary>

SMOLTRACE creates **4 structured datasets** on HuggingFace:

### 1. Leaderboard Dataset
Aggregate statistics for all evaluation runs:

```python
{
    "run_id": "uuid",
    "model": "openai/gpt-4",
    "agent_type": "tool",
    "provider": "litellm",

    # Performance
    "success_rate": 95.8,
    "total_tests": 100,
    "avg_duration_ms": 3200.0,

    # Cost & Resources
    "total_tokens": 15000,
    "total_cost_usd": 0.05,
    "co2_emissions_g": 0.22,
    "gpu_utilization_avg": 67.5,

    # Dataset References
    "results_dataset": "username/agent-results-gpt4",
    "traces_dataset": "username/agent-traces-gpt4",
    "metrics_dataset": "username/agent-metrics-gpt4",

    # Metadata
    "timestamp": "2025-11-18T14:23:00Z",
    "submitted_by": "username"
}
```

### 2. Results Dataset
Individual test case results:

```python
{
    "run_id": "uuid",
    "task_id": "task_001",
    "test_index": 0,

    # Test Case
    "prompt": "What's the weather in Tokyo?",
    "expected_tool": "get_weather",

    # Result
    "success": true,
    "response": "The weather in Tokyo is 18°C and clear.",
    "tool_called": "get_weather",

    # Metrics
    "execution_time_ms": 2450.0,
    "total_tokens": 234,
    "cost_usd": 0.0012,

    # Trace Reference
    "trace_id": "trace_abc123"
}
```

### 3. Traces Dataset
Full OpenTelemetry traces:

```python
{
    "trace_id": "trace_abc123",
    "run_id": "uuid",
    "spans": [
        {
            "spanId": "span_001",
            "name": "Agent Execution",
            "startTime": "2025-11-18T14:23:01.000Z",
            "endTime": "2025-11-18T14:23:03.450Z",
            "attributes": {
                "agent.type": "tool",
                "gen_ai.system": "openai",
                "gen_ai.request.model": "gpt-4"
            }
        },
        # ... more spans ...
    ]
}
```

### 4. Metrics Dataset
GPU metrics and performance data:

```python
{
    "run_id": "uuid",
    "trace_id": "trace_abc123",
    "metrics": [
        {
            "name": "gen_ai.gpu.utilization",
            "value": 67.5,
            "unit": "%",
            "timestamp": "2025-11-18T14:23:01.000Z"
        },
        {
            "name": "gen_ai.co2.emissions",
            "value": 0.22,
            "unit": "gCO2e"
        }
    ]
}
```

</details>

---

## 🔧 Configuration Options

### Model Selection

```bash
# API Models (via LiteLLM)
--model openai/gpt-4
--model anthropic/claude-3-5-sonnet
--model google/gemini-pro

# Local Models (via Transformers)
--model meta-llama/Llama-3.1-8B
--model mistralai/Mistral-7B-v0.1
```

### Provider Selection

```bash
--provider litellm      # For API models
--provider transformers # For local models
```

### Hardware Selection

```bash
# Automatic (default)
# API models → CPU
# Local models → GPU if available

# Manual override
--hardware cpu
--hardware gpu_a10
--hardware gpu_h200
```

### OpenTelemetry Options

```bash
--enable-otel              # Enable tracing
--enable-gpu-metrics       # Capture GPU data
--enable-carbon-tracking   # Track CO2 emissions
```

---

## 🏗️ Integration with HuggingFace Jobs

SMOLTRACE works seamlessly with HuggingFace Jobs:

```yaml
# job.yaml
name: SMOLTRACE Evaluation
hardware: gpu-h200
environment:
  MODEL: meta-llama/Llama-3.1-8B
  HF_TOKEN: ${{ secrets.HF_TOKEN }}
command: |
  pip install smoltrace[otel,gpu]
  smoltrace-eval \\
    --model $MODEL \\
    --provider transformers \\
    --agent-type both \\
    --enable-otel \\
    --enable-gpu-metrics \\
    --results-repo ${{ username }}/agent-results \\
    --leaderboard-repo huggingface/smolagents-leaderboard
```

**Benefits:**
- 💰 **H200 GPUs**: 2x faster evaluation
- 📊 **Automatic Upload**: Results → HuggingFace datasets
- 🔄 **Reproducible**: Same environment every time

---

## 📈 Integration with TraceMind-AI

SMOLTRACE datasets power the TraceMind-AI interface:

```
SMOLTRACE Evaluation
         ↓
    4 Datasets Created
         ↓
┌────────┴────────┐
│                 │
│  TraceMind-AI   │  ← You are here!
│  (Gradio UI)    │
│                 │
└─────────────────┘
```

**What TraceMind-AI Shows:**
- 📊 **Leaderboard**: All evaluation runs
- 🔍 **Run Detail**: Individual test cases
- 🕵️ **Trace Detail**: OpenTelemetry visualization
- 🤖 **Agent Chat**: MCP-powered analysis

---

## 🎯 Best Practices

### 1. Start Small
```bash
# Test with 10 runs first
smoltrace-eval --model gpt-4 --num-tests 10

# Scale up after validation
smoltrace-eval --model gpt-4 --num-tests 1000
```

### 2. Use Appropriate Hardware
```bash
# API models → CPU (no GPU needed)
smoltrace-eval --model openai/gpt-4 --hardware cpu

# Local models → GPU (faster)
smoltrace-eval --model meta-llama/Llama-3.1-8B --hardware gpu_h200
```

### 3. Enable Full Observability
```bash
# Capture everything
smoltrace-eval \\
  --model your-model \\
  --enable-otel \\
  --enable-gpu-metrics \\
  --enable-carbon-tracking
```

### 4. Organize Your Datasets
```bash
# Use descriptive repo names
--results-repo username/results-gpt4-tool-20251118
--traces-repo username/traces-gpt4-tool-20251118
--leaderboard-repo username/agent-leaderboard
```

---

## 🔍 Cost Estimation

Before running evaluations, estimate costs:

```python
from smoltrace import estimate_cost

# API model
api_cost = estimate_cost(
    model="openai/gpt-4",
    num_tests=1000,
    agent_type="tool"
)
print(f"Estimated cost: ${api_cost.total_cost}")

# GPU job
gpu_cost = estimate_cost(
    model="meta-llama/Llama-3.1-8B",
    num_tests=1000,
    hardware="gpu_h200"
)
print(f"Estimated cost: ${gpu_cost.total_cost}")
print(f"Estimated time: {gpu_cost.duration_minutes} minutes")
```

---

## 📐 Architecture

```
┌─────────────────────────────────────────┐
│         SMOLTRACE Core                   │
├─────────────────────────────────────────┤
│                                          │
│  ┌──────────────┐   ┌──────────────┐   │
│  │   LiteLLM    │   │ Transformers │   │
│  │   Provider   │   │   Provider   │   │
│  └──────┬───────┘   └──────┬───────┘   │
│         │                   │            │
│         └────────┬──────────┘            │
│                  ↓                        │
│         ┌──────────────┐                 │
│         │  TraceVerde  │                 │
│         │     (OTEL)   │                 │
│         └──────┬───────┘                 │
│                ↓                          │
│         ┌──────────────┐                 │
│         │   Dataset    │                 │
│         │   Generator  │                 │
│         └──────┬───────┘                 │
│                ↓                          │
│    ┌───────────────────────┐            │
│    │  HuggingFace Upload   │            │
│    └───────────────────────┘            │
│                                          │
└─────────────────────────────────────────┘
```

---

## 🔗 Resources

- **GitHub**: [github.com/Mandark-droid/SMOLTRACE](https://github.com/Mandark-droid/SMOLTRACE)
- **PyPI**: [pypi.org/project/smoltrace](https://pypi.org/project/smoltrace/)
- **Documentation**: [SMOLTRACE README](https://github.com/Mandark-droid/SMOLTRACE#readme)

---

## 🐛 Troubleshooting

### Common Issues

**Q: Evaluation is slow?**
```bash
# Use GPU for local models
--hardware gpu_h200

# Or reduce test count
--num-tests 10
```

**Q: Traces not captured?**
```bash
# Make sure OTEL is enabled
--enable-otel
```

**Q: Upload to HF failing?**
```bash
# Check HF token
export HF_TOKEN=your_token_here

# Verify repo exists or allow auto-create
```

---

## 📄 License

**AGPL-3.0** - Open source and free to use

---

## 🤝 Contributing

We welcome contributions!
- Add new agent types
- Support more frameworks
- Improve evaluation metrics
- Optimize performance

---

*SMOLTRACE - Lightweight evaluation for heavyweight results* 📊
""")


def create_mcp_server_tab():
    """Create the TraceMind-MCP-Server documentation tab"""
    return gr.Markdown("""
# 🔌 TraceMind-MCP-Server

<div align="center">
  <img src="https://raw.githubusercontent.com/Mandark-droid/TraceMind-mcp-server/assets/Logo.png" alt="TraceMind MCP Server Logo" width="300"/>
</div>

<br/>

**Building MCP: Intelligent Analysis Tools for Agent Evaluation**

[![MCP's 1st Birthday Hackathon](https://img.shields.io/badge/MCP%27s%201st%20Birthday-Hackathon-blue)](https://github.com/modelcontextprotocol)
[![Track 1](https://img.shields.io/badge/Track-Building%20MCP%20(Enterprise)-blue)](https://github.com/modelcontextprotocol/hackathon)
[![HF Space](https://img.shields.io/badge/HuggingFace-TraceMind--MCP--Server-yellow?logo=huggingface)](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server)
[![Google Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini%202.5%20Pro-orange)](https://ai.google.dev/)

> **🎯 Track 1 Submission**: Building MCP (Enterprise)
> **📅 MCP's 1st Birthday Hackathon**: November 14-30, 2025

---

## 📖 Table of Contents

- [What is TraceMind-MCP-Server?](#what-is-tracemind-mcp-server)
- [MCP Tools Provided](#️-mcp-tools-provided)
  - [analyze_leaderboard](#1-analyze_leaderboard)
  - [estimate_cost](#2-estimate_cost)
  - [debug_trace](#3-debug_trace)
  - [compare_runs](#4-compare_runs)
  - [analyze_results](#5-analyze_results)
- [Accessing the MCP Server](#-accessing-the-mcp-server)
- [Use Cases](#-use-cases)
- [Architecture](#️-architecture)
- [Configuration](#-configuration)
- [Dataset Requirements](#-dataset-requirements)
- [Learning Resources](#-learning-resources)
- [Troubleshooting](#-troubleshooting)
- [Links](#-links)
- [License](#-license)
- [Contributing](#-contributing)
- [MCP's 1st Birthday Hackathon](#-mcps-1st-birthday-hackathon)

---

## What is TraceMind-MCP-Server?

TraceMind-MCP-Server is a **Track 1 (Building MCP)** submission that provides MCP tools for intelligent agent evaluation analysis.

**Key Features:**
- 🤖 Powered by Google Gemini 2.5 Pro
- 🔌 Standards-compliant MCP implementation
- 📊 Analyzes HuggingFace evaluation datasets
- 💡 Provides actionable insights and recommendations
- 🌐 Accessible via SSE transport for Gradio integration

---

<details>
<summary><h2>🛠️ MCP Tools Provided</h2></summary>

### 1. `analyze_leaderboard`

**Purpose**: Generate AI-powered insights about evaluation leaderboard data

**Input Schema:**
```json
{
  "leaderboard_repo": "string",     // HF dataset (default: kshitijthakkar/smoltrace-leaderboard)
  "metric_focus": "string",         // "overall" | "accuracy" | "cost" | "latency" | "co2"
  "time_range": "string",           // "last_week" | "last_month" | "all_time"
  "top_n": "integer"                // Number of top models to highlight
}
```

**What It Does:**
1. Fetches leaderboard dataset from HuggingFace
2. Filters by time range
3. Analyzes trends based on metric focus
4. Uses Gemini to generate insights
5. Returns markdown-formatted analysis

**Example Output:**
```markdown
Based on 247 evaluations in the past week:

**Top Performers:**
- GPT-4 leads in accuracy at 95.8% but costs $0.05 per run
- Llama-3.1-8B offers best cost/performance at 93.4% accuracy for $0.002
- Qwen3-MoE is fastest at 1.7s average duration

**Trends:**
- API models dominate accuracy rankings
- GPU models are 10x more cost-effective
- H200 jobs show 2x faster execution vs A10

**Recommendations:**
- For production: Consider Llama-3.1-8B for cost-sensitive workloads
- For maximum accuracy: GPT-4 remains state-of-the-art
- For eco-friendly: Claude-3-Haiku has lowest CO2 emissions
```

---

### 2. `estimate_cost`

**Purpose**: Estimate evaluation costs with hardware recommendations

**Input Schema:**
```json
{
  "model": "string",                // Model name (e.g., "openai/gpt-4")
  "agent_type": "string",           // "tool" | "code" | "both"
  "num_tests": "integer",           // Number of test cases (default: 100)
  "hardware": "string"              // "cpu" | "gpu_a10" | "gpu_h200" (optional)
}
```

**What It Does:**
1. Determines if model is API or local
2. Calculates token usage estimates
3. Computes costs (API pricing or GPU time)
4. Estimates duration and CO2 emissions
5. Provides hardware recommendations

**Example Output:**
```markdown
## Cost Estimation: openai/gpt-4 (Tool Agent, 100 tests)

**Hardware**: CPU (API model)

**Cost Breakdown:**
- Total Tokens: ~15,000
- Prompt Tokens: ~5,000 ($0.03)
- Completion Tokens: ~10,000 ($0.06)
- **Total Cost: $0.09**

**Time Estimate:**
- Average per test: 3.2s
- Total duration: ~5.3 minutes

**CO2 Emissions:**
- Estimated: 0.45g CO2e

**Recommendations:**
- ✅ Good choice for accuracy-critical applications
- ⚠️ Consider Llama-3.1-8B for cost savings (10x cheaper)
- 💡 Use caching to reduce repeated API calls
```

---

### 3. `debug_trace`

**Purpose**: Answer questions about agent execution traces

**Input Schema:**
```json
{
  "trace_dataset": "string",        // HF dataset with OTEL traces
  "trace_id": "string",             // Specific trace to analyze
  "question": "string",             // Question about the trace
  "include_metrics": "boolean"      // Include GPU metrics (default: true)
}
```

**What It Does:**
1. Fetches trace data from HuggingFace
2. Parses OpenTelemetry spans
3. Analyzes execution flow
4. Uses Gemini to answer questions
5. Provides span-level details

**Example Output:**
```markdown
## Why was the tool called twice?

Based on trace analysis for `trace_abc123`:

**First Tool Call (span_003)**:
- Time: 14:23:19.000
- Tool: `search_web`
- Input: {"query": "latest AI news"}
- Result: 5 results returned
- Issue: Results were 2 days old

**Second Tool Call (span_005)**:
- Time: 14:23:21.200
- Tool: `search_web`
- Input: {"query": "latest AI news today"}
- Reasoning: LLM determined first results were outdated
- Duration: 1200ms

**Why Twice?**
The agent's reasoning chain shows it initially received outdated results.
The LLM then decided to refine the query with "today" keyword to get
more recent data.

**Performance Impact:**
- Added 2.09s to total execution
- Cost increase: +$0.0003
- This is normal for agents with iterative reasoning

**Recommendation:**
Consider adding date filters to initial tool calls to avoid retries.
```

---

### 4. `compare_runs`

**Purpose**: Side-by-side comparison of evaluation runs

**Input Schema:**
```json
{
  "leaderboard_repo": "string",     // HF leaderboard dataset
  "run_id_1": "string",             // First run ID
  "run_id_2": "string",             // Second run ID
  "comparison_focus": "string"      // "overall" | "cost" | "accuracy" | "speed"
}
```

**What It Does:**
1. Fetches data for both runs
2. Compares key metrics
3. Identifies strengths/weaknesses
4. Provides recommendations

**Example Output:**
```markdown
## Comparison: GPT-4 vs Llama-3.1-8B

| Metric | GPT-4 | Llama-3.1-8B | Winner |
|--------|-------|--------------|--------|
| Success Rate | 95.8% | 93.4% | GPT-4 (+2.4%) |
| Avg Duration | 3.2s | 2.1s | Llama (+34% faster) |
| Cost per Run | $0.05 | $0.002 | Llama (25x cheaper) |
| CO2 Emissions | 0.22g | 0.08g | Llama (64% less) |

**Analysis:**
- GPT-4 has slight accuracy edge but at significant cost premium
- Llama-3.1-8B offers excellent cost/performance ratio
- For 1000 runs: GPT-4 costs $50, Llama costs $2

**Recommendation:**
Use Llama-3.1-8B for production unless 95%+ accuracy is critical.
Consider hybrid approach: Llama for routine tasks, GPT-4 for complex ones.
```

---

### 5. `analyze_results`

**Purpose**: Deep dive into test case results

**Input Schema:**
```json
{
  "results_repo": "string",         // HF results dataset
  "run_id": "string",               // Run to analyze
  "focus": "string"                 // "failures" | "successes" | "all"
}
```

**What It Does:**
1. Loads results dataset
2. Filters by success/failure
3. Identifies patterns
4. Suggests optimizations

</details>

---

## 🌐 Accessing the MCP Server

### Via TraceMind-AI (This App!)

The **Agent Chat** screen uses TraceMind-MCP-Server automatically:

```python
# Happens automatically in the Chat screen
from mcp_client.sync_wrapper import get_sync_mcp_client

mcp = get_sync_mcp_client()
insights = mcp.analyze_leaderboard(
    metric_focus="overall",
    time_range="last_week"
)
```

### Via SSE Endpoint (for smolagents)

```python
from smolagents import MCPClient, ToolCallingAgent

# Connect to MCP server via SSE
mcp_client = MCPClient(
    "https://mcp-1st-birthday-tracemind-mcp-server.hf.space/gradio_api/mcp/sse"
)

# Create agent with MCP tools
agent = ToolCallingAgent(
    tools=[],
    model="hfapi",
    additional_authorized_imports=["requests", "pandas"]
)

# Tools automatically available!
agent.run("Analyze the leaderboard and show top 3 models")
```

### Via MCP SDK (for other clients)

```python
from mcp import ClientSession, StdioServerParameters

# For local development
session = ClientSession(
    StdioServerParameters(
        command="python",
        args=["-m", "mcp_tools"]
    )
)

# Call tools
result = await session.call_tool(
    "analyze_leaderboard",
    arguments={"metric_focus": "cost"}
)
```

---

## 🎯 Use Cases

### 1. Interactive Analysis (Agent Chat)
Ask natural language questions:
- "What are the top 3 models by accuracy?"
- "Compare GPT-4 and Claude-3 on cost"
- "Why is this agent slow?"

### 2. Automated Insights (Leaderboard)
Get AI summaries automatically:
- Weekly trend reports
- Cost optimization recommendations
- Performance alerts

### 3. Debugging (Trace Detail)
Understand agent behavior:
- "Why did the agent fail?"
- "Which tool took the longest?"
- "Why was the same tool called twice?"

### 4. Planning (Cost Estimator)
Before running evaluations:
- "How much will 1000 tests cost?"
- "Should I use A10 or H200?"
- "What's the CO2 impact?"

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│         TraceMind-MCP-Server (HF Space)              │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────┐        ┌──────────────────┐   │
│  │   Gradio App    │        │   MCP Protocol   │   │
│  │   (UI + SSE)    │◄──────►│   Handler        │   │
│  └─────────────────┘        └────────┬─────────┘   │
│                                       │              │
│                              ┌────────▼─────────┐   │
│                              │   Tool Router    │   │
│                              └────────┬─────────┘   │
│                                       │              │
│         ┌─────────────────────────────┼──────────┐  │
│         │                             │          │  │
│  ┌──────▼──────┐   ┌─────────▼───────▼──┐   ┌──▼──▼──┐
│  │ Leaderboard │   │  Cost Estimator   │   │ Trace  │
│  │  Analyzer   │   │                   │   │Debugger│
│  └─────────────┘   └───────────────────┘   └────────┘
│         │                     │                  │    │
│         └─────────────────────┴──────────────────┘    │
│                             │                          │
│                   ┌─────────▼──────────┐              │
│                   │  Gemini 2.5 Pro    │              │
│                   │  (Analysis Engine)  │              │
│                   └────────────────────┘              │
│                                                        │
└────────────────────────────────────────────────────────┘
                          │
                          │ MCP Protocol (SSE)
                          │
                          ▼
            ┌──────────────────────────┐
            │   TraceMind-AI (UI)      │
            │   Agent Chat Screen      │
            └──────────────────────────┘
```

---

## 🔧 Configuration

### Environment Variables

```env
# Google Gemini API (required)
GEMINI_API_KEY=your_api_key_here

# HuggingFace Token (for dataset access)
HF_TOKEN=your_token_here

# Default Leaderboard (optional)
DEFAULT_LEADERBOARD_REPO=kshitijthakkar/smoltrace-leaderboard
```

---

## 📊 Dataset Requirements

MCP tools expect datasets with specific schemas:

### Leaderboard Dataset
```python
{
    "run_id": "string",
    "model": "string",
    "success_rate": "float",
    "total_cost_usd": "float",
    "timestamp": "string",
    # ... other metrics
}
```

### Results Dataset
```python
{
    "run_id": "string",
    "task_id": "string",
    "success": "boolean",
    "trace_id": "string",
    # ... other fields
}
```

### Traces Dataset
```python
{
    "trace_id": "string",
    "spans": [
        {
            "spanId": "string",
            "name": "string",
            "attributes": {},
            # ... OTEL format
        }
    ]
}
```

---

## 🎓 Learning Resources

### MCP Documentation
- [Model Context Protocol Spec](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Gradio MCP Integration](https://www.gradio.app/guides/creating-a-custom-chatbot-with-blocks#model-context-protocol-mcp)

### Implementation Examples
- **This Server**: [HF Space Code](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server/tree/main)
- **Client Integration**: [TraceMind-AI mcp_client/](https://github.com/Mandark-droid/TraceMind-AI/tree/main/mcp_client)

---

## 🐛 Troubleshooting

### Common Issues

**Q: MCP tools not appearing?**
```bash
# Verify MCP_SERVER_URL is correct
echo $MCP_SERVER_URL

# Should be: https://mcp-1st-birthday-tracemind-mcp-server.hf.space/gradio_api/mcp/sse
```

**Q: "Failed to load dataset" error?**
```bash
# Check HF token
export HF_TOKEN=your_token_here

# Verify dataset exists
huggingface-cli repo info kshitijthakkar/smoltrace-leaderboard
```

**Q: Gemini API errors?**
```bash
# Verify API key
curl -H "Authorization: Bearer $GEMINI_API_KEY" \\
  https://generativelanguage.googleapis.com/v1beta/models

# Check rate limits (10 requests/minute on free tier)
```

---

## 🔗 Links

- **Live Server**: [HF Space](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server)
- **Source Code**: [GitHub](https://github.com/Mandark-droid/TraceMind-mcp-server)
- **Client (This App)**: [TraceMind-AI](https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind)
- **MCP Spec**: [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## 📄 License

**AGPL-3.0** - Open source and free to use

---

## 🤝 Contributing

Help improve TraceMind-MCP-Server:
- Add new MCP tools
- Improve analysis quality
- Optimize performance
- Add support for more datasets

---

## 🏆 MCP's 1st Birthday Hackathon

**Track 1 Submission: Building MCP (Enterprise)**

TraceMind-MCP-Server demonstrates:
- ✅ Standards-compliant MCP implementation
- ✅ SSE transport for Gradio integration
- ✅ Real-world use case (agent evaluation)
- ✅ Gemini 2.5 Pro integration
- ✅ Production-ready deployment on HF Spaces

**Used by**: TraceMind-AI (Track 2) for autonomous agent chat

---

*TraceMind-MCP-Server - Intelligent analysis, one tool at a time* 🔌
""")


def create_documentation_screen():
    """
    Create the complete documentation screen with tabs

    Returns:
        gr.Column: Gradio Column component for documentation (can be shown/hidden)
    """
    with gr.Column(visible=False) as documentation_interface:
        gr.Markdown("""
        # 📚 TraceMind Documentation

        Comprehensive documentation for the entire TraceMind ecosystem
        """)

        with gr.Tabs():
            with gr.Tab("📖 About"):
                create_about_tab()

            with gr.Tab("🔭 TraceVerde"):
                create_traceverde_tab()

            with gr.Tab("📊 SmolTrace"):
                create_smoltrace_tab()

            with gr.Tab("🔌 TraceMind-MCP-Server"):
                create_mcp_server_tab()

        gr.Markdown("""
        ---

        ### 💡 Quick Navigation

        - **Getting Started**: Start with the "About" tab for ecosystem overview
        - **Instrumentation**: See "TraceVerde" for adding observability to your agents
        - **Evaluation**: Check "SmolTrace" for running evaluations
        - **MCP Integration**: Explore "TraceMind-MCP-Server" for intelligent analysis

        ### 🔗 External Resources

        - [GitHub Organization](https://github.com/Mandark-droid)
        - [HuggingFace Spaces](https://huggingface.co/MCP-1st-Birthday)
        - [MCP Specification](https://modelcontextprotocol.io)

        *Built with ❤️ for MCP's 1st Birthday Hackathon*
        """)

    return documentation_interface


if __name__ == "__main__":
    # For standalone testing
    with gr.Blocks() as demo:
        doc_screen = create_documentation_screen()
        # Make it visible for standalone testing
        doc_screen.visible = True
    demo.launch()
