# TraceMind-AI - Complete User Guide

This guide provides a comprehensive walkthrough of all features and screens in TraceMind-AI.

## Table of Contents

- [Getting Started](#getting-started)
- [Screen-by-Screen Guide](#screen-by-screen-guide)
  - [📊 Leaderboard](#-leaderboard)
  - [🤖 Agent Chat](#-agent-chat)
  - [🚀 New Evaluation](#-new-evaluation)
  - [📈 Job Monitoring](#-job-monitoring)
  - [🔍 Trace Visualization](#-trace-visualization)
  - [🔬 Synthetic Data Generator](#-synthetic-data-generator)
  - [⚙️ Settings](#️-settings)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### First-Time Setup

1. **Visit** https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind
2. **Sign in** with your HuggingFace account (required for viewing)
3. **Configure API keys** (optional but recommended):
   - Go to **⚙️ Settings** tab
   - Enter Gemini API Key and HuggingFace Token
   - Click **"Save API Keys"**

### Navigation

TraceMind-AI is organized into tabs:
- **📊 Leaderboard**: View evaluation results with AI insights
- **🤖 Agent Chat**: Interactive autonomous agent powered by MCP tools
- **🚀 New Evaluation**: Submit evaluation jobs to HF Jobs or Modal
- **📈 Job Monitoring**: Track status of submitted jobs
- **🔍 Trace Visualization**: Deep-dive into agent execution traces
- **🔬 Synthetic Data Generator**: Create custom test datasets with AI
- **⚙️ Settings**: Configure API keys and preferences

---

## Screen-by-Screen Guide

### 📊 Leaderboard

**Purpose**: Browse all evaluation runs with AI-powered insights and detailed analysis.

#### Features

**Main Table**:
- View all evaluation runs from the SMOLTRACE leaderboard
- Sortable columns: Model, Success Rate, Cost, Duration, CO2 emissions
- Click any row to see detailed test results

**AI Insights Panel** (Top of screen):
- Automatically generated insights from MCP server
- Powered by Google Gemini 2.5 Flash
- Updates when you click "Load Leaderboard"
- Shows top performers, trends, and recommendations

**Filter & Sort Options**:
- Filter by agent type (tool, code, both)
- Filter by provider (litellm, transformers)
- Sort by any metric (success rate, cost, duration)

#### How to Use

1. **Load Data**:
   ```
   Click "Load Leaderboard" button
   → Fetches latest evaluation runs from HuggingFace
   → AI generates insights automatically
   ```

2. **Read AI Insights**:
   - Located at top of screen
   - Summary of evaluation trends
   - Top performing models
   - Cost/accuracy trade-offs
   - Actionable recommendations

3. **Explore Runs**:
   - Scroll through table
   - Sort by clicking column headers
   - Click on any run to see details

4. **View Details**:
   ```
   Click a row in the table
   → Opens detail view with:
      - All test cases (success/failure)
      - Execution times
      - Cost breakdown
      - Link to trace visualization
   ```

#### Example Workflow

```
Scenario: Find the most cost-effective model for production

1. Click "Load Leaderboard"
2. Read AI insights: "Llama-3.1-8B offers best cost/performance at $0.002/run"
3. Sort table by "Cost" (ascending)
4. Compare top 3 cheapest models
5. Click on Llama-3.1-8B run to see detailed results
6. Review success rate (93.4%) and test case breakdowns
7. Decision: Use Llama-3.1-8B for cost-sensitive workloads
```

#### Tips

- **Refresh regularly**: Click "Load Leaderboard" to see new evaluation results
- **Compare models**: Use the sort function to compare across different metrics
- **Trust the AI**: The insights panel provides strategic recommendations based on all data

---

### 🤖 Agent Chat

**Purpose**: Interactive autonomous agent that can answer questions about evaluations using MCP tools.

**🎯 Track 2 Feature**: This demonstrates MCP client usage with smolagents framework.

#### Features

**Autonomous Agent**:
- Built with `smolagents` framework
- Has access to all TraceMind MCP Server tools
- Plans and executes multi-step actions
- Provides detailed, data-driven answers

**MCP Tools Available to Agent**:
- `analyze_leaderboard` - Get AI insights about top performers
- `estimate_cost` - Calculate evaluation costs before running
- `debug_trace` - Analyze execution traces
- `compare_runs` - Compare two evaluation runs
- `get_top_performers` - Fetch top N models efficiently
- `get_leaderboard_summary` - Get high-level statistics
- `get_dataset` - Load SMOLTRACE datasets
- `analyze_results` - Analyze detailed test results

**Agent Reasoning Visibility**:
- Toggle **"Show Agent Reasoning"** to see:
  - Planning steps
  - Tool execution logs
  - Intermediate results
  - Final synthesis

**Quick Action Buttons**:
- **"Quick: Top Models"**: Get top 5 models with costs
- **"Quick: Cost Estimate"**: Estimate cost for a model
- **"Quick: Load Leaderboard"**: Fetch leaderboard summary

#### How to Use

1. **Start a Conversation**:
   ```
   Type your question in the chat box
   Example: "What are the top 3 performing models and how much do they cost?"

   Click "Send"
   → Agent plans approach
   → Executes MCP tools
   → Returns synthesized answer
   ```

2. **Watch Agent Work** (optional):
   ```
   Enable "Show Agent Reasoning" checkbox
   → See step-by-step execution:
      Step 1: Calling get_top_performers with metric=success_rate, top_n=3
      Step 2: Analyzing costs from results
      Step 3: Formatting response with recommendations
   ```

3. **Ask Follow-Up Questions**:
   ```
   You: "Which one is most cost-effective?"
   Agent: Uses previous context + MCP tools to answer
   ```

4. **Use Quick Actions**:
   ```
   Click "Quick: Top Models" button
   → Agent automatically executes query
   → Returns top 5 models with metrics
   ```

#### Example Conversations

**Example 1: Cost Comparison**
```
User: "Compare the costs of the top 3 models. Which one offers the best value?"

Agent:
Let me analyze the top 3 models by success rate:

[Calls: get_top_performers(metric="success_rate", top_n=3)]

Top 3 Models:
1. GPT-4: 95.8% success, $0.05/run
2. Claude-3: 94.1% success, $0.04/run
3. Llama-3.1-8B: 93.4% success, $0.002/run

[Calls: analyze_leaderboard(metric_focus="cost")]

Cost Analysis:
- GPT-4: Highest accuracy but 25x more expensive than Llama
- Claude-3: Good middle ground at $0.04/run
- Llama-3.1: Best value at $0.002/run with only 2.4% accuracy drop

Recommendation for "best value":
→ Llama-3.1-8B offers 93.4% accuracy at $0.002/run
→ For 1M runs: Saves $48,000/month vs GPT-4
→ Only 2.4% accuracy trade-off
```

**Example 2: Evaluation Planning**
```
User: "I want to evaluate DeepSeek-V3 with 100 tests. How much will it cost and which hardware should I use?"

Agent:
Let me estimate costs for DeepSeek-V3:

[Calls: estimate_cost(model="deepseek-ai/DeepSeek-V3", num_tests=100, hardware="auto")]

Cost Estimate:
- Model: deepseek-ai/DeepSeek-V3
- Tests: 100
- Recommended hardware: GPU A100 (70B+ parameters)

Breakdown:
- LLM inference cost: ~$0.01/test (self-hosted, no API fees)
- HF Jobs GPU cost: ~$3.00/hr for A100
- Estimated duration: 25 minutes
- Total compute cost: $1.25
- Total cost: $1.25 (100 tests)

Recommendation:
Use HuggingFace Jobs with A100 GPU. Total cost: $1.25 for 100 tests.
Alternative: Modal H200 for 2x faster inference at $2.50.
```

#### Tips

- **Be specific**: Ask clear, focused questions for better answers
- **Use context**: Agent remembers conversation history
- **Watch reasoning**: Enable to understand how agent uses MCP tools
- **Try quick actions**: Fast way to get common information

---

### 🚀 New Evaluation

**Purpose**: Submit evaluation jobs to HuggingFace Jobs or Modal for running SMOLTRACE evaluations.

**⚠️ Requires**: HuggingFace Pro account ($9/month) with credit card, or Modal account.

#### Features

**Model Selection**:
- Enter any model name (format: `provider/model-name`)
- Examples: `openai/gpt-4`, `meta-llama/Llama-3.1-8B`, `deepseek-ai/DeepSeek-V3`
- Auto-detects if API model or local model

**Infrastructure Choice**:
- **HuggingFace Jobs**: Managed compute (H200, A100, A10, T4, CPU)
- **Modal**: Serverless GPU compute (pay-per-second)

**Hardware Selection**:
- **Auto** (recommended): Automatically selects optimal hardware based on model size
- **Manual**: Choose specific GPU tier (A10, A100, H200) or CPU

**Cost Estimation**:
- Click **"💰 Estimate Cost"** before submitting
- Shows predicted:
  - LLM API costs (for API models)
  - Compute costs (for local models)
  - Duration estimate
  - CO2 emissions

**Agent Type**:
- **tool**: Test tool-calling capabilities
- **code**: Test code generation capabilities
- **both**: Test both (recommended)

#### How to Use

**Step 1: Configure Prerequisites** (One-time setup)

For **HuggingFace Jobs**:
```
1. Sign up for HF Pro: https://huggingface.co/pricing ($9/month)
2. Add credit card for compute charges
3. Create HF token with "Read + Write + Run Jobs" permissions
4. Go to Settings tab → Enter HF token → Save
```

For **Modal** (Alternative):
```
1. Sign up: https://modal.com (free tier available)
2. Generate API token: https://modal.com/settings/tokens
3. Go to Settings tab → Enter MODAL_TOKEN_ID + MODAL_TOKEN_SECRET → Save
```

For **API Models** (OpenAI, Anthropic, etc.):
```
1. Get API key from provider (e.g., https://platform.openai.com/api-keys)
2. Go to Settings tab → Enter provider API key → Save
```

**Step 2: Create Evaluation**

```
1. Enter model name:
   Example: "meta-llama/Llama-3.1-8B"

2. Select infrastructure:
   - HuggingFace Jobs (default)
   - Modal (alternative)

3. Choose agent type:
   - "both" (recommended)

4. Select hardware:
   - "auto" (recommended - smart selection)
   - Or choose manually: cpu-basic, t4-small, a10g-small, a100-large, h200

5. Set timeout (optional):
   - Default: 3600s (1 hour)
   - Range: 300s - 7200s

6. Click "💰 Estimate Cost":
   → Shows predicted cost and duration
   → Example: "$2.00, 20 minutes, 0.5g CO2"

7. Review estimate, then click "Submit Evaluation"
```

**Step 3: Monitor Job**

```
After submission:
→ Job ID displayed
→ Go to "📈 Job Monitoring" tab to track progress
→ Or visit HuggingFace Jobs dashboard: https://huggingface.co/jobs
```

**Step 4: View Results**

```
When job completes:
→ Results automatically uploaded to HuggingFace datasets
→ Appears in Leaderboard within 1-2 minutes
→ Click on your run to see detailed results
```

#### Hardware Selection Guide

**For API Models** (OpenAI, Anthropic, Google):
- Use: `cpu-basic` (HF Jobs) or CPU (Modal)
- Cost: ~$0.05/hr (HF), ~$0.0001/sec (Modal)
- Why: No GPU needed for API calls

**For Small Models** (4B-8B parameters):
- Use: `t4-small` (HF) or A10G (Modal)
- Cost: ~$0.60/hr (HF), ~$0.0006/sec (Modal)
- Examples: Llama-3.1-8B, Mistral-7B

**For Medium Models** (7B-13B parameters):
- Use: `a10g-small` (HF) or A10G (Modal)
- Cost: ~$1.10/hr (HF), ~$0.0006/sec (Modal)
- Examples: Qwen2.5-14B, Mixtral-8x7B

**For Large Models** (70B+ parameters):
- Use: `a100-large` (HF) or A100-80GB (Modal)
- Cost: ~$3.00/hr (HF), ~$0.0030/sec (Modal)
- Examples: Llama-3.1-70B, DeepSeek-V3

**For Fastest Inference**:
- Use: `h200` (HF or Modal)
- Cost: ~$5.00/hr (HF), ~$0.0050/sec (Modal)
- Best for: Time-sensitive evaluations, large batches

#### Example Workflows

**Workflow 1: Evaluate API Model (OpenAI GPT-4)**
```
1. Model: "openai/gpt-4"
2. Infrastructure: HuggingFace Jobs
3. Agent type: both
4. Hardware: auto (selects cpu-basic)
5. Estimate: $50.00 (mostly API costs), 45 min
6. Submit → Monitor → View in leaderboard
```

**Workflow 2: Evaluate Local Model (Llama-3.1-8B)**
```
1. Model: "meta-llama/Llama-3.1-8B"
2. Infrastructure: Modal (for pay-per-second billing)
3. Agent type: both
4. Hardware: auto (selects A10G)
5. Estimate: $0.20, 15 min
6. Submit → Monitor → View in leaderboard
```

#### Tips

- **Always estimate first**: Prevents surprise costs
- **Use "auto" hardware**: Smart selection based on model size
- **Start small**: Test with 10-20 tests before scaling to 100+
- **Monitor jobs**: Check Job Monitoring tab for status
- **Modal for experimentation**: Pay-per-second is cost-effective for testing

---

### 📈 Job Monitoring

**Purpose**: Track status of submitted evaluation jobs.

#### Features

**Job Status Display**:
- Job ID
- Current status (pending, running, completed, failed)
- Start time
- Duration
- Infrastructure (HF Jobs or Modal)

**Real-time Updates**:
- Auto-refreshes every 30 seconds
- Manual refresh button

**Job Actions**:
- View logs
- Cancel job (if still running)
- View results (if completed)

#### How to Use

```
1. Go to "📈 Job Monitoring" tab
2. See list of your submitted jobs
3. Click "Refresh" for latest status
4. When status = "completed":
   → Click "View Results"
   → Opens leaderboard filtered to your run
```

#### Job Statuses

- **Pending**: Job queued, waiting for resources
- **Running**: Evaluation in progress
- **Completed**: Evaluation finished successfully
- **Failed**: Evaluation encountered an error

#### Tips

- **Check logs** if job fails: Helps diagnose issues
- **Expected duration**:
  - API models: 2-5 minutes
  - Local models: 15-30 minutes (includes model download)

---

### 🔍 Trace Visualization

**Purpose**: Deep-dive into OpenTelemetry traces to understand agent execution.

**Access**: Click on any test case in a run's detail view

#### Features

**Waterfall Diagram**:
- Visual timeline of execution
- Spans show: LLM calls, tool executions, reasoning steps
- Duration bars (wider = slower)
- Parent-child relationships

**Span Details**:
- Span name (e.g., "LLM Call - Reasoning", "Tool Call - get_weather")
- Start/end times
- Duration
- Attributes (model, tokens, cost, tool inputs/outputs)
- Status (OK, ERROR)

**GPU Metrics Overlay** (for GPU jobs only):
- GPU utilization %
- Memory usage
- Temperature
- CO2 emissions

**MCP-Powered Q&A**:
- Ask questions about the trace
- Example: "Why was tool X called twice?"
- Agent uses `debug_trace` MCP tool to analyze

#### How to Use

```
1. From leaderboard → Click a run → Click a test case
2. View waterfall diagram:
   → Spans arranged chronologically
   → Parent spans (e.g., "Agent Execution")
   → Child spans (e.g., "LLM Call", "Tool Call")

3. Click any span:
   → See detailed attributes
   → Token counts, costs, inputs/outputs

4. Ask questions (MCP-powered):
   User: "Why did this test fail?"
   → Agent analyzes trace with debug_trace tool
   → Returns explanation with span references

5. Check GPU metrics (if available):
   → Graph shows utilization over time
   → Overlayed on execution timeline
```

#### Example Analysis

**Scenario: Understanding a slow execution**

```
1. Open trace for test_045 (duration: 8.5s)
2. Waterfall shows:
   - Span 1: LLM Call - Reasoning (1.2s) ✓
   - Span 2: Tool Call - search_web (6.5s) ⚠️ SLOW
   - Span 3: LLM Call - Final Response (0.8s) ✓

3. Click Span 2 (search_web):
   - Input: {"query": "weather in Tokyo"}
   - Output: 5 results
   - Duration: 6.5s (6x slower than typical)

4. Ask agent: "Why was the search_web call so slow?"
   → Agent analysis:
      "The search_web call took 6.5s due to network latency.
       Span attributes show API response time: 6.2s.
       This is an external dependency issue, not agent code.
       Recommendation: Implement timeout (5s) and fallback strategy."
```

#### Tips

- **Look for patterns**: Similar failures often have common spans
- **Use MCP Q&A**: Faster than manual trace analysis
- **Check GPU metrics**: Identify resource bottlenecks
- **Compare successful vs failed traces**: Spot differences

---

### 🔬 Synthetic Data Generator

**Purpose**: Generate custom synthetic test datasets for agent evaluation using AI, complete with domain-specific tasks and prompt templates.

#### Features

**AI-Powered Dataset Generation**:
- Generate 5-100 synthetic tasks using Google Gemini 2.5 Flash
- Customizable domain, tools, difficulty, and agent type
- Automatic batching for large datasets (parallel generation)
- SMOLTRACE-format output ready for evaluation

**Prompt Template Generation**:
- Customized YAML templates based on smolagents format
- Optimized for your specific domain and tools
- Included automatically in dataset card

**Push to HuggingFace Hub**:
- One-click upload to HuggingFace Hub
- Public or private repositories
- Auto-generated README with usage instructions
- Ready to use with SMOLTRACE evaluations

#### How to Use

**Step 1: Configure & Generate Dataset**

1. Navigate to **🔬 Synthetic Data Generator** tab

2. Configure generation parameters:
   - **Domain**: Topic/industry (e.g., "travel", "finance", "healthcare", "customer_support")
   - **Tools**: Comma-separated list of tool names (e.g., "get_weather,search_flights,book_hotel")
   - **Number of Tasks**: 5-100 tasks (slider)
   - **Difficulty Level**:
     - `balanced` (40% easy, 40% medium, 20% hard)
     - `easy_only` (100% easy tasks)
     - `medium_only` (100% medium tasks)
     - `hard_only` (100% hard tasks)
     - `progressive` (50% easy, 30% medium, 20% hard)
   - **Agent Type**:
     - `tool` (ToolCallingAgent only)
     - `code` (CodeAgent only)
     - `both` (50/50 mix)

3. Click **"🎲 Generate Synthetic Dataset"**

4. Wait for generation (30-120s depending on size):
   - Shows progress message
   - Automatic batching for >20 tasks
   - Parallel API calls for faster generation

**Step 2: Review Generated Content**

1. **Dataset Preview Tab**:
   - View all generated tasks in JSON format
   - Check task IDs, prompts, expected tools, difficulty
   - See dataset statistics:
     - Total tasks
     - Difficulty distribution
     - Agent type distribution
     - Tools coverage

2. **Prompt Template Tab**:
   - View customized YAML prompt template
   - Based on smolagents templates
   - Adapted for your domain and tools
   - Ready to use with ToolCallingAgent or CodeAgent

**Step 3: Push to HuggingFace Hub** (Optional)

1. Enter **Repository Name**:
   - Format: `username/smoltrace-{domain}-tasks`
   - Example: `alice/smoltrace-finance-tasks`
   - Auto-filled with your HF username after generation

2. Set **Visibility**:
   - ☐ Private Repository (unchecked = public)
   - ☑ Private Repository (checked = private)

3. Provide **HuggingFace Token** (optional):
   - Leave empty to use environment token (HF_TOKEN from Settings)
   - Or paste token from https://huggingface.co/settings/tokens
   - Requires write permissions

4. Click **"📤 Push to HuggingFace Hub"**

5. Wait for upload (5-30s):
   - Creates dataset repository
   - Uploads tasks
   - Generates README with:
     - Usage instructions
     - Prompt template
     - SMOLTRACE integration code
   - Returns dataset URL

#### Example Workflow

```
Scenario: Create finance evaluation dataset with 20 tasks

1. Configure:
   Domain: "finance"
   Tools: "get_stock_price,calculate_roi,get_market_news,send_alert"
   Number of Tasks: 20
   Difficulty: "balanced"
   Agent Type: "both"

2. Click "Generate"
   → AI generates 20 tasks:
      - 8 easy (single tool, straightforward)
      - 8 medium (multiple tools or complex logic)
      - 4 hard (complex reasoning, edge cases)
      - 10 for ToolCallingAgent
      - 10 for CodeAgent
   → Also generates customized prompt template

3. Review Dataset Preview:
   Task 1:
   {
     "id": "finance_stock_price_1",
     "prompt": "What is the current price of AAPL stock?",
     "expected_tool": "get_stock_price",
     "difficulty": "easy",
     "agent_type": "tool",
     "expected_keywords": ["AAPL", "price", "$"]
   }

   Task 15:
   {
     "id": "finance_complex_analysis_15",
     "prompt": "Calculate the ROI for investing $10,000 in AAPL last year and send an alert if ROI > 15%",
     "expected_tool": "calculate_roi",
     "expected_tool_calls": 2,
     "difficulty": "hard",
     "agent_type": "code",
     "expected_keywords": ["ROI", "15%", "alert"]
   }

4. Review Prompt Template:
   See customized YAML with:
   - Finance-specific system prompt
   - Tool descriptions for get_stock_price, calculate_roi, etc.
   - Response format guidelines

5. Push to Hub:
   Repository: "yourname/smoltrace-finance-tasks"
   Private: No (public)
   Token: (empty, using environment token)

   → Uploads to https://huggingface.co/datasets/yourname/smoltrace-finance-tasks
   → README includes usage instructions and prompt template

6. Use in evaluation:
   # Load your custom dataset
   dataset = load_dataset("yourname/smoltrace-finance-tasks")

   # Run SMOLTRACE evaluation
   smoltrace-eval --model openai/gpt-4 \
                  --dataset-name yourname/smoltrace-finance-tasks \
                  --agent-type both
```

#### Configuration Reference

**Difficulty Levels Explained**:

| Level | Characteristics | Example |
|-------|----------------|---------|
| **Easy** | Single tool call, straightforward input, clear expected output | "What's the weather in Tokyo?" → get_weather("Tokyo") |
| **Medium** | Multiple tool calls OR complex input parsing OR conditional logic | "Compare weather in Tokyo and London" → get_weather("Tokyo"), get_weather("London"), compare |
| **Hard** | Multiple tools, complex reasoning, edge cases, error handling | "Plan a trip with best weather, book flights if under $500, alert if unavailable" |

**Agent Types Explained**:

| Type | Description | Use Case |
|------|-------------|----------|
| **tool** | ToolCallingAgent - Declarative tool calling with structured outputs | API-based models that support function calling (GPT-4, Claude) |
| **code** | CodeAgent - Writes Python code to use tools programmatically | Models that excel at code generation (Qwen-Coder, DeepSeek-Coder) |
| **both** | 50/50 mix of tool and code agent tasks | Comprehensive evaluation across agent types |

#### Best Practices

**Domain Selection**:
- Be specific: "customer_support_saas" > "support"
- Match your use case: Use actual business domain
- Consider tools available: Domain should align with tools

**Tool Names**:
- Use descriptive names: "get_stock_price" > "fetch"
- Match actual tool implementations
- 3-8 tools is ideal (enough variety, not overwhelming)
- Include mix of data retrieval and action tools

**Number of Tasks**:
- 5-10 tasks: Quick testing, proof of concept
- 20-30 tasks: Solid evaluation dataset
- 50-100 tasks: Comprehensive benchmark

**Difficulty Distribution**:
- `balanced`: Best for general evaluation
- `progressive`: Good for learning/debugging
- `easy_only`: Quick sanity checks
- `hard_only`: Stress testing advanced capabilities

**Quality Assurance**:
- Always review generated tasks before pushing
- Check for domain relevance and variety
- Verify expected tools match your actual tools
- Ensure prompts are clear and executable

#### Troubleshooting

**Generation fails with "Invalid API key"**:
- Go to **⚙️ Settings**
- Configure Gemini API Key
- Get key from https://aistudio.google.com/apikey

**Generated tasks don't match domain**:
- Be more specific in domain description
- Try regenerating with adjusted parameters
- Review prompt template for domain alignment

**Push to Hub fails with "Authentication error"**:
- Verify HuggingFace token has write permissions
- Get token from https://huggingface.co/settings/tokens
- Check token in **⚙️ Settings** or provide directly

**Dataset generation is slow (>60s)**:
- Large requests (>20 tasks) are automatically batched
- Each batch takes 30-120s
- Example: 100 tasks = 5 batches × 60s = ~5 minutes
- This is normal for large datasets

**Tasks are too easy/hard**:
- Adjust difficulty distribution
- Regenerate with different settings
- Mix difficulty levels with `balanced` or `progressive`

#### Advanced Tips

**Iterative Refinement**:
1. Generate 10 tasks with `balanced` difficulty
2. Review quality and variety
3. If satisfied, generate 50-100 tasks with same settings
4. If not, adjust domain/tools and regenerate

**Dataset Versioning**:
- Use version suffixes: `username/smoltrace-finance-tasks-v2`
- Iterate on datasets as tools evolve
- Keep track of which version was used for evaluations

**Combining Datasets**:
- Generate multiple small datasets for different domains
- Use SMOLTRACE CLI to merge datasets
- Create comprehensive multi-domain benchmarks

**Custom Prompt Templates**:
- Generate prompt template separately
- Customize further based on your needs
- Use in agent initialization before evaluation
- Include in dataset card for reproducibility

---

### ⚙️ Settings

**Purpose**: Configure API keys, preferences, and authentication.

#### Features

**API Key Configuration**:
- Gemini API Key (for MCP server AI analysis)
- HuggingFace Token (for dataset access + job submission)
- Modal Token ID + Secret (for Modal job submission)
- LLM Provider Keys (OpenAI, Anthropic, etc.)

**Preferences**:
- Default infrastructure (HF Jobs vs Modal)
- Default hardware tier
- Auto-refresh intervals

**Security**:
- Keys stored in browser session only (not server)
- HTTPS encryption for all API calls
- Keys never logged or exposed

#### How to Use

**Configure Essential Keys**:
```
1. Go to "⚙️ Settings" tab

2. Enter Gemini API Key:
   - Get from: https://ai.google.dev/
   - Click "Get API Key" → Create project → Generate
   - Paste into field
   - Free tier: 1,500 requests/day

3. Enter HuggingFace Token:
   - Get from: https://huggingface.co/settings/tokens
   - Click "New token" → Name: "TraceMind"
   - Permissions:
     - Read (for viewing datasets)
     - Write (for uploading results)
     - Run Jobs (for evaluation submission)
   - Paste into field

4. Click "Save API Keys"
   → Keys stored in browser session
   → MCP server will use your keys
```

**Configure for Job Submission** (Optional):

For **HuggingFace Jobs**:
```
Already configured if you entered HF token above with "Run Jobs" permission.
```

For **Modal** (Alternative):
```
1. Sign up: https://modal.com
2. Get token: https://modal.com/settings/tokens
3. Copy MODAL_TOKEN_ID (starts with 'ak-')
4. Copy MODAL_TOKEN_SECRET (starts with 'as-')
5. Paste both into Settings → Save
```

For **API Model Providers**:
```
1. Get API key from provider:
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/settings/keys
   - Google: https://ai.google.dev/

2. Paste into corresponding field in Settings
3. Click "Save LLM Provider Keys"
```

#### Security Best Practices

- **Use environment variables**: For production, set keys via HF Spaces secrets
- **Rotate keys regularly**: Generate new tokens every 3-6 months
- **Minimal permissions**: Only grant "Run Jobs" if you need to submit evaluations
- **Monitor usage**: Check API provider dashboards for unexpected charges

---

## Common Workflows

### Workflow 1: Quick Model Comparison

```
Goal: Compare GPT-4 vs Llama-3.1-8B for production use

Steps:
1. Go to Leaderboard → Load Leaderboard
2. Read AI insights: "GPT-4 leads accuracy, Llama-3.1 best cost"
3. Sort by Success Rate → Note: GPT-4 (95.8%), Llama (93.4%)
4. Sort by Cost → Note: GPT-4 ($0.05), Llama ($0.002)
5. Go to Agent Chat → Ask: "Compare GPT-4 and Llama-3.1. Which should I use for 1M runs/month?"
   → Agent analyzes with MCP tools
   → Returns: "Llama saves $48K/month, only 2.4% accuracy drop"
6. Decision: Use Llama-3.1-8B for production
```

### Workflow 2: Evaluate Custom Model

```
Goal: Evaluate your fine-tuned model on SMOLTRACE benchmark

Steps:
1. Ensure model is on HuggingFace: username/my-finetuned-model
2. Go to Settings → Configure HF token (with Run Jobs permission)
3. Go to New Evaluation:
   - Model: "username/my-finetuned-model"
   - Infrastructure: HuggingFace Jobs
   - Agent type: both
   - Hardware: auto
4. Click "Estimate Cost" → Review: $1.50, 20 min
5. Click "Submit Evaluation"
6. Go to Job Monitoring → Wait for "Completed" (15-25 min)
7. Go to Leaderboard → Refresh → See your model in table
8. Click your run → Review detailed results
9. Compare vs other models using Agent Chat
```

### Workflow 3: Debug Failed Test

```
Goal: Understand why test_045 failed in your evaluation

Steps:
1. Go to Leaderboard → Find your run → Click to open details
2. Filter to failed tests only
3. Click test_045 → Opens trace visualization
4. Examine waterfall:
   - Span 1: LLM Call (OK)
   - Span 2: Tool Call - "unknown_tool" (ERROR)
   - No Span 3 (execution stopped)
5. Ask Agent: "Why did test_045 fail?"
   → Agent uses debug_trace MCP tool
   → Returns: "Tool 'unknown_tool' not found. Add to agent's tool list."
6. Fix: Update agent config to include missing tool
7. Re-run evaluation with fixed config
```

---

## Troubleshooting

### Leaderboard Issues

**Problem**: "Load Leaderboard" button doesn't work
- **Solution**: Check HuggingFace token in Settings (needs Read permission)
- **Solution**: Verify leaderboard dataset exists: https://huggingface.co/datasets/kshitijthakkar/smoltrace-leaderboard

**Problem**: AI insights not showing
- **Solution**: Check Gemini API key in Settings
- **Solution**: Wait 5-10 seconds for AI generation to complete

### Agent Chat Issues

**Problem**: Agent responds with "MCP server connection failed"
- **Solution**: Check MCP server status: https://huggingface.co/spaces/MCP-1st-Birthday/TraceMind-mcp-server
- **Solution**: Configure Gemini API key in both TraceMind-AI and MCP server Settings

**Problem**: Agent gives incorrect information
- **Solution**: Agent may be using stale data. Ask: "Load the latest leaderboard data"
- **Solution**: Verify question is clear and specific

### Evaluation Submission Issues

**Problem**: "Submit Evaluation" fails with auth error
- **Solution**: HF token needs "Run Jobs" permission
- **Solution**: Ensure HF Pro account is active ($9/month)
- **Solution**: Verify credit card is on file for compute charges

**Problem**: Job stuck in "Pending" status
- **Solution**: HuggingFace Jobs may have queue. Wait 5-10 minutes.
- **Solution**: Try Modal as alternative infrastructure

**Problem**: Job fails with "Out of Memory"
- **Solution**: Model too large for selected hardware
- **Solution**: Increase hardware tier (e.g., t4-small → a10g-small)
- **Solution**: Use auto hardware selection

### Trace Visualization Issues

**Problem**: Traces not loading
- **Solution**: Ensure evaluation completed successfully
- **Solution**: Check traces dataset exists on HuggingFace
- **Solution**: Verify HF token has Read permission

**Problem**: GPU metrics missing
- **Solution**: Only available for GPU jobs (not API models)
- **Solution**: Ensure evaluation was run with SMOLTRACE's GPU metrics enabled

---

## Getting Help

- **📧 GitHub Issues**: [TraceMind-AI/issues](https://github.com/Mandark-droid/TraceMind-AI/issues)
- **💬 HF Discord**: `#agents-mcp-hackathon-winter25`
- **📖 Documentation**: See [MCP_INTEGRATION.md](MCP_INTEGRATION.md) and [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Last Updated**: November 21, 2025
