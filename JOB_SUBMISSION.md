# Job Submission Guide

This guide explains how to submit agent evaluation jobs to run on cloud infrastructure using TraceMind-AI.

## Table of Contents

- [Overview](#overview)
- [Infrastructure Options](#infrastructure-options)
  - [HuggingFace Jobs](#huggingface-jobs)
  - [Modal](#modal)
- [Prerequisites](#prerequisites)
- [Hardware Selection Guide](#hardware-selection-guide)
- [Submitting a Job](#submitting-a-job)
- [Cost Estimation](#cost-estimation)
- [Monitoring Jobs](#monitoring-jobs)
- [Understanding Job Results](#understanding-job-results)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Overview

TraceMind-AI allows you to submit SMOLTRACE evaluation jobs to two cloud platforms:

1. **HuggingFace Jobs** - Managed compute with GPU/CPU options
2. **Modal** - Serverless compute with pay-per-second billing

Both platforms:
- ✅ Run the same SMOLTRACE evaluation engine
- ✅ Push results automatically to HuggingFace datasets
- ✅ Appear in the TraceMind leaderboard when complete
- ✅ Collect OpenTelemetry traces and GPU metrics
- ✅ **Per-second billing** with no minimum duration

**Choose based on your needs**:
- **HuggingFace Jobs**: Best if you already have HF Pro subscription ($9/month)
- **Modal**: Best if you need H200/H100 GPUs or want to avoid subscriptions

**Pricing Sources**:
- [HuggingFace Jobs Documentation](https://huggingface.co/docs/huggingface_hub/main/en/guides/jobs)
- [HuggingFace Spaces GPU Pricing](https://huggingface.co/docs/hub/en/spaces-gpus)
- [Modal GPU Pricing](https://modal.com/pricing)

---

## Infrastructure Options

### HuggingFace Jobs

**What it is**: Managed compute platform from HuggingFace with dedicated GPU/CPU instances.

**Pricing Model**: Subscription-based ($9/month HF Pro) + **per-second** GPU charges

**Hardware Options** (pricing from [HF Spaces GPU pricing](https://huggingface.co/docs/hub/en/spaces-gpus)):
- `cpu-basic` - 2 vCPU, 16GB RAM (Free with Pro)
- `cpu-upgrade` - 8 vCPU, 32GB RAM (Free with Pro)
- `t4-small` - NVIDIA T4 16GB, 4 vCPU, 15GB RAM ($0.40/hr = $0.000111/sec)
- `t4-medium` - NVIDIA T4 16GB, 8 vCPU, 30GB RAM ($0.60/hr = $0.000167/sec)
- `l4x1` - NVIDIA L4 24GB, 8 vCPU, 30GB RAM ($0.80/hr = $0.000222/sec)
- `l4x4` - 4x NVIDIA L4 96GB total, 48 vCPU, 186GB RAM ($3.80/hr = $0.001056/sec)
- `a10g-small` - NVIDIA A10G 24GB ($1.00/hr = $0.000278/sec)
- `a10g-large` - NVIDIA A10G 24GB (more compute) ($1.50/hr = $0.000417/sec)
- `a10g-largex2` - 2x NVIDIA A10G 48GB total ($3.00/hr = $0.000833/sec)
- `a10g-largex4` - 4x NVIDIA A10G 96GB total ($5.00/hr = $0.001389/sec)
- `a100-large` - NVIDIA A100 80GB, 12 vCPU, 142GB RAM ($2.50/hr = $0.000694/sec)
- `v5e-1x1` - Google Cloud TPU v5e (pricing TBD)
- `v5e-2x2` - Google Cloud TPU v5e (pricing TBD)
- `v5e-2x4` - Google Cloud TPU v5e (pricing TBD)

*Note: Jobs billing is **per-second** with no minimum. You only pay for actual compute time used.*

**Pros**:
- Simple authentication (HuggingFace token)
- Integrated with HF ecosystem
- Job dashboard at https://huggingface.co/jobs
- Reliable infrastructure

**Cons**:
- Requires HF Pro subscription ($9/month)
- Slightly more expensive than Modal for most GPUs
- Limited hardware options compared to Modal (no H100/H200)

**When to use**:
- ✅ You already have HF Pro subscription
- ✅ You want simplicity and reliability
- ✅ You prefer HuggingFace ecosystem integration
- ✅ You prefer managed infrastructure

### Modal

**What it is**: Serverless compute platform with pay-per-second billing for CPU and GPU workloads.

**Pricing Model**: Pay-per-second usage (no subscription required)

**Hardware Options**:
- `cpu` - Physical core (2 vCPU equivalent) ($0.0000131/core/sec, min 0.125 cores)
- `gpu_t4` - NVIDIA T4 16GB ($0.000164/sec ~= $0.59/hr)
- `gpu_l4` - NVIDIA L4 24GB ($0.000222/sec ~= $0.80/hr)
- `gpu_a10` - NVIDIA A10G 24GB ($0.000306/sec ~= $1.10/hr)
- `gpu_l40s` - NVIDIA L40S 48GB ($0.000542/sec ~= $1.95/hr)
- `gpu_a100` - NVIDIA A100 40GB ($0.000583/sec ~= $2.10/hr)
- `gpu_a100_80gb` - NVIDIA A100 80GB ($0.000694/sec ~= $2.50/hr)
- `gpu_h100` - NVIDIA H100 80GB ($0.001097/sec ~= $3.95/hr)
- `gpu_h200` - NVIDIA H200 141GB ($0.001261/sec ~= $4.54/hr)
- `gpu_b200` - NVIDIA B200 192GB ($0.001736/sec ~= $6.25/hr)

**Pros**:
- Pay-per-second (no hourly minimums)
- Wide range of GPUs (including H200, H100)
- No subscription required
- Real-time logs and monitoring
- Fast cold starts

**Cons**:
- Requires Modal account setup
- Need to configure API tokens (MODAL_TOKEN_ID + MODAL_TOKEN_SECRET)
- Network egress charges apply
- Less integrated with HF ecosystem

**When to use**:
- ✅ You want to minimize costs (generally cheaper than HF Jobs)
- ✅ You need access to latest GPUs (H200, H100, B200)
- ✅ You prefer serverless architecture
- ✅ You don't have HF Pro subscription
- ✅ You want more GPU options and flexibility

---

## Prerequisites

### For Viewing Leaderboard (Free)

**Required**:
- HuggingFace account (free)
- HuggingFace token with **Read** permissions

**How to get**:
1. Go to https://huggingface.co/settings/tokens
2. Create new token with **Read** permission
3. Copy token (starts with `hf_...`)
4. Add to TraceMind Settings tab

### For Submitting Jobs to HuggingFace Jobs

**Required**:
1. **HuggingFace Pro** subscription ($9/month)
   - Sign up at https://huggingface.co/pricing
   - **Must add credit card** for GPU compute charges
2. HuggingFace token with **Read + Write + Run Jobs** permissions
3. LLM provider API keys (OpenAI, Anthropic, etc.) for API models

**How to setup**:
1. Subscribe to HF Pro: https://huggingface.co/pricing
2. Add credit card for compute charges
3. Create token with all permissions:
   - Go to https://huggingface.co/settings/tokens
   - Click "New token"
   - Select: **Read**, **Write**, **Run Jobs**
   - Copy token
4. Add API keys in TraceMind Settings:
   - HuggingFace Token
   - OpenAI API Key (if testing OpenAI models)
   - Anthropic API Key (if testing Claude models)
   - etc.

### For Submitting Jobs to Modal

**Required**:
1. Modal account (free to create, pay-per-use)
2. Modal API token (Token ID + Token Secret)
3. HuggingFace token with **Read + Write** permissions
4. LLM provider API keys (OpenAI, Anthropic, etc.) for API models

**How to setup**:
1. Create Modal account:
   - Go to https://modal.com
   - Sign up (GitHub or email)
2. Create API token:
   - Go to https://modal.com/settings/tokens
   - Click "Create token"
   - Copy **Token ID** (starts with `ak-...`)
   - Copy **Token Secret** (starts with `as-...`)
3. Add credentials in TraceMind Settings:
   - Modal Token ID
   - Modal Token Secret
   - HuggingFace Token (Read + Write)
   - LLM provider API keys

---

## Hardware Selection Guide

### Auto-Selection (Recommended)

Set hardware to **`auto`** to let TraceMind automatically select the optimal hardware based on:
- Model size (extracted from model name)
- Provider type (API vs local)
- Infrastructure (HF Jobs vs Modal)

**Auto-selection logic**:

**For API Models** (provider = `litellm` or `inference`):
- Always uses **CPU** (no GPU needed)
- HF Jobs: `cpu-basic`
- Modal: `cpu`

**For Local Models** (provider = `transformers`):

*Memory estimation for agentic workloads*:
- Model weights (FP16): ~2GB per 1B params
- KV cache for long contexts: ~1.5-2x model size
- Inference overhead: ~20-30% additional
- **Total: ~4-5GB per 1B params for safe execution**

**HuggingFace Jobs**:
| Model Size | Hardware | VRAM | Example Models |
|------------|----------|------|----------------|
| < 1B | `t4-small` | 16GB | Qwen-0.5B, Phi-3-mini |
| 1B - 5B | `t4-small` | 16GB | Llama-3.2-3B, Gemma-2B |
| 6B - 12B | `a10g-large` | 24GB | Llama-3.1-8B, Mistral-7B |
| 13B+ | `a100-large` | 80GB | Llama-3.1-70B, Qwen-14B |

**Modal**:
| Model Size | Hardware | VRAM | Example Models |
|------------|----------|------|----------------|
| < 1B | `gpu_t4` | 16GB | Qwen-0.5B, Phi-3-mini |
| 1B - 5B | `gpu_t4` | 16GB | Llama-3.2-3B, Gemma-2B |
| 6B - 12B | `gpu_l40s` | 48GB | Llama-3.1-8B, Mistral-7B |
| 13B - 24B | `gpu_a100_80gb` | 80GB | Llama-2-13B, Qwen-14B |
| 25B - 48B | `gpu_a100_80gb` | 80GB | Gemma-27B, Yi-34B |
| 49B+ | `gpu_h200` | 141GB | Llama-3.1-70B, Qwen-72B |

### Manual Selection

If you know your model's requirements, you can manually select hardware:

**CPU Jobs** (API models like GPT-4, Claude):
- HF Jobs: `cpu-basic` or `cpu-upgrade`
- Modal: `cpu`

**Small Models** (1B-5B params):
- HF Jobs: `t4-small` (16GB VRAM)
- Modal: `gpu_t4` (16GB VRAM)
- Examples: Llama-3.2-3B, Gemma-2B, Qwen-2.5-3B

**Medium Models** (6B-12B params):
- HF Jobs: `a10g-small` or `a10g-large` (24GB VRAM)
- Modal: `gpu_l40s` (48GB VRAM)
- Examples: Llama-3.1-8B, Mistral-7B, Qwen-2.5-7B

**Large Models** (13B-24B params):
- HF Jobs: `a100-large` (80GB VRAM)
- Modal: `gpu_a100_80gb` (80GB VRAM)
- Examples: Llama-2-13B, Qwen-14B, Mistral-22B

**Very Large Models** (25B+ params):
- HF Jobs: `a100-large` (80GB VRAM) - may need quantization
- Modal: `gpu_h200` (141GB VRAM) - recommended
- Examples: Llama-3.1-70B, Qwen-72B, Gemma-27B

**Cost vs Performance Trade-offs**:
- T4: Cheapest GPU, good for small models
- L4: Newer architecture, better performance than T4
- A10G: Good balance of cost/performance for medium models
- L40S: Best for 7B-12B models (Modal only)
- A100: Industry standard for large models
- H200: Latest GPU, massive VRAM (141GB), best for 70B+ models

---

## Submitting a Job

### Step 1: Navigate to New Evaluation Screen

1. Open TraceMind-AI
2. Click **▶️ New Evaluation** in the sidebar
3. You'll see a comprehensive configuration form

### Step 2: Configure Infrastructure

**Infrastructure Provider**:
- Choose `HuggingFace Jobs` or `Modal`

**Hardware**:
- Use `auto` (recommended) or select specific hardware
- See [Hardware Selection Guide](#hardware-selection-guide)

### Step 3: Configure Model

**Model**:
- Enter model ID (e.g., `openai/gpt-4`, `meta-llama/Llama-3.1-8B-Instruct`)
- Use HuggingFace format: `organization/model-name`

**Provider**:
- `litellm` - For API models (OpenAI, Anthropic, etc.)
- `inference` - For HuggingFace Inference API
- `transformers` - For local models loaded with transformers

**HF Inference Provider** (optional):
- Leave empty unless using HF Inference API
- Example: `openai-community/gpt2` for HF-hosted models

**HuggingFace Token** (optional):
- Leave empty if already configured in Settings
- Only needed for private models

### Step 4: Configure Agent

**Agent Type**:
- `tool` - Function calling agents only
- `code` - Code execution agents only
- `both` - Hybrid agents (recommended)

**Search Provider**:
- `duckduckgo` - Free, no API key required (recommended)
- `serper` - Requires Serper API key
- `brave` - Requires Brave Search API key

**Enable Optional Tools**:
- Select additional tools for the agent:
  - `google_search` - Google Search (requires API key)
  - `duckduckgo_search` - DuckDuckGo Search
  - `visit_webpage` - Web page scraping
  - `python_interpreter` - Python code execution
  - `wikipedia_search` - Wikipedia queries
  - `user_input` - User interaction (not recommended for batch eval)

### Step 5: Configure Test Dataset

**Dataset Name**:
- Default: `kshitijthakkar/smoltrace-tasks`
- Or use your own HuggingFace dataset
- Format: `username/dataset-name`

**Dataset Split**:
- Default: `train`
- Other options: `test`, `validation`

**Difficulty Filter**:
- `all` - All difficulty levels (recommended)
- `easy` - Easy tasks only
- `medium` - Medium tasks only
- `hard` - Hard tasks only

**Parallel Workers**:
- Default: `1` (sequential execution)
- Higher values (2-10) for faster execution
- ⚠️ Increases memory usage and API rate limits

### Step 6: Configure Output & Monitoring

**Output Format**:
- `hub` - Push to HuggingFace datasets (recommended)
- `json` - Save locally (requires output directory)

**Output Directory**:
- Only for `json` format
- Example: `./evaluation_results`

**Enable OpenTelemetry Tracing**:
- ✅ Recommended - Collects detailed execution traces
- Traces appear in TraceMind trace visualization

**Enable GPU Metrics**:
- ✅ Recommended for GPU jobs
- Collects GPU utilization, memory, temperature, CO2 emissions
- No effect on CPU jobs

**Private Datasets**:
- ☐ Make result datasets private on HuggingFace
- Default: Public datasets

**Debug Mode**:
- ☐ Enable verbose logging for troubleshooting
- Default: Off

**Quiet Mode**:
- ☐ Reduce output verbosity
- Default: Off

**Run ID** (optional):
- Auto-generated UUID if left empty
- Custom ID for tracking specific runs

**Job Timeout**:
- Default: `1h` (1 hour)
- Other examples: `30m`, `2h`, `3h`
- Job will be terminated if it exceeds timeout

### Step 7: Estimate Cost (Optional but Recommended)

1. Click **💰 Estimate Cost** button
2. Wait for AI-powered cost analysis
3. Review:
   - Estimated total cost
   - Estimated duration
   - Hardware selection (if auto)
   - Historical data (if available)

**Cost Estimation Sources**:
- **Historical Data**: Based on previous runs of the same model in leaderboard
- **MCP AI Analysis**: AI-powered estimation using Gemini 2.5 Flash (if no historical data)

### Step 8: Submit Job

1. Review all configurations
2. Click **🚀 Submit Evaluation** button
3. Wait for confirmation message
4. Copy job ID for tracking

**Confirmation message includes**:
- ✅ Job submission status
- Job ID and platform-specific ID
- Hardware selected
- Estimated duration
- Monitoring instructions

### Example: Submit HuggingFace Jobs Evaluation

```
Infrastructure: HuggingFace Jobs
Hardware: auto → a10g-large
Model: meta-llama/Llama-3.1-8B-Instruct
Provider: transformers
Agent Type: both
Dataset: kshitijthakkar/smoltrace-tasks
Output Format: hub

Click "Estimate Cost":
→ Estimated Cost: $1.25
→ Duration: 25 minutes
→ Hardware: a10g-large (auto-selected)

Click "Submit Evaluation":
→ ✅ Job submitted successfully!
→ HF Job ID: username/job_abc123
→ Monitor at: https://huggingface.co/jobs
```

### Example: Submit Modal Evaluation

```
Infrastructure: Modal
Hardware: auto → L40S
Model: meta-llama/Llama-3.1-8B-Instruct
Provider: transformers
Agent Type: both
Dataset: kshitijthakkar/smoltrace-tasks
Output Format: hub

Click "Estimate Cost":
→ Estimated Cost: $0.95
→ Duration: 20 minutes
→ Hardware: gpu_l40s (auto-selected)

Click "Submit Evaluation":
→ ✅ Job submitted successfully!
→ Modal Call ID: modal-job_xyz789
→ Monitor at: https://modal.com/apps
```

---

## Cost Estimation

### Understanding Cost Estimates

TraceMind provides AI-powered cost estimation before you submit jobs:

**Historical Data** (most accurate):
- Based on actual runs of the same model
- Shows average cost, duration from past evaluations
- Displays number of historical runs used

**MCP AI Analysis** (when no historical data):
- Powered by Google Gemini 2.5 Flash
- Analyzes model size, hardware, provider
- Estimates cost based on typical usage patterns
- Includes detailed breakdown and recommendations

### Cost Factors

**For HuggingFace Jobs**:
1. **Hardware per-second rate** (see [Infrastructure Options](#huggingface-jobs))
2. **Evaluation duration** (actual runtime only, billed per-second)
3. **LLM API costs** (if using API models like GPT-4)
4. **HF Pro subscription** ($9/month required)

**For Modal**:
1. **Hardware per-second rate** (no minimums)
2. **Evaluation duration** (actual runtime only)
3. **Network egress** (data transfer out)
4. **LLM API costs** (if using API models)

### Cost Optimization Tips

**Use Auto Hardware Selection**:
- Automatically picks cheapest hardware for your model
- Avoids over-provisioning (e.g., H200 for 3B model)

**Choose Right Infrastructure**:
- **If you have HF Pro**: Use HF Jobs (already paying subscription)
- **If you don't have HF Pro**: Use Modal (no subscription required)
- **For latest GPUs (H200/H100)**: Use Modal (HF Jobs doesn't offer these)

**Optimize Model Selection**:
- Smaller models (3B-7B) are 10x cheaper than large models (70B)
- API models (GPT-4-mini) often cheaper than local 70B models

**Reduce Test Count**:
- Use difficulty filter (`easy` only) for quick validation
- Test with small dataset first, then scale up

**Parallel Workers**:
- Keep at 1 for sequential execution (cheapest)
- Increase only if time is critical (increases API costs)

**Example Cost Comparison**:
| Model | Hardware | Infrastructure | Duration | HF Jobs Cost | Modal Cost |
|-------|----------|----------------|----------|--------------|------------|
| GPT-4 (API) | CPU | Either | 5 min | Free* | ~$0.00* |
| Llama-3.1-8B | A10G-large | HF Jobs | 25 min | $0.63** | N/A |
| Llama-3.1-8B | L40S | Modal | 20 min | N/A | $0.65** |
| Llama-3.1-70B | A100-80GB | Both | 45 min | $1.74** | $1.56** |
| Llama-3.1-70B | H200 | Modal only | 35 min | N/A | $2.65** |

\* Plus LLM API costs (OpenAI/Anthropic/etc. - not included)
\** Per-second billing, actual runtime only (no minimums)

---

## Monitoring Jobs

### HuggingFace Jobs

**Via HuggingFace Dashboard**:
1. Go to https://huggingface.co/jobs
2. Find your job in the list
3. Click to view details and logs

**Via TraceMind Job Monitoring Tab**:
1. Click **📈 Job Monitoring** in sidebar
2. See all your submitted jobs
3. Real-time status updates
4. Click job to view logs

**Job Statuses**:
- `pending` - Waiting for resources
- `running` - Currently executing
- `completed` - Finished successfully
- `failed` - Error occurred (check logs)
- `cancelled` - Manually stopped

### Modal

**Via Modal Dashboard**:
1. Go to https://modal.com/apps
2. Find your app: `smoltrace-eval-{job_id}`
3. Click to view real-time logs and metrics

**Via TraceMind Job Monitoring Tab**:
1. Click **📈 Job Monitoring** in sidebar
2. See all your submitted jobs
3. Modal jobs show as `submitted` (check Modal dashboard for details)

### Viewing Job Logs

**HuggingFace Jobs**:
```
1. Go to Job Monitoring tab
2. Click on your job
3. Click "View Logs" button
4. See real-time output from SMOLTRACE
```

**Modal**:
```
1. Go to https://modal.com/apps
2. Find your app
3. Click "Logs" tab
4. See streaming output in real-time
```

### Expected Job Duration

**API Models** (litellm provider):
- CPU job: 2-5 minutes for 100 tests
- No model download required
- Depends on API rate limits

**Local Models** (transformers provider):
- Model download: 5-15 minutes (one-time per job)
  - 3B model: ~6GB download
  - 8B model: ~16GB download
  - 70B model: ~140GB download
- Evaluation: 10-30 minutes for 100 tests
- Total: 15-45 minutes typical

**Progress Indicators**:
1. ⏳ Job queued (0-2 minutes)
2. 🔄 Downloading model (5-15 minutes for first run)
3. 🧪 Running evaluation (10-30 minutes)
4. 📤 Uploading results to HuggingFace (1-2 minutes)
5. ✅ Complete

---

## Understanding Job Results

### Where Results Are Stored

**HuggingFace Datasets** (if output_format = "hub"):

SMOLTRACE creates 4 datasets for each evaluation:

1. **Leaderboard Dataset**: `huggingface/smolagents-leaderboard`
   - Aggregate statistics for the run
   - Appears in TraceMind Leaderboard tab
   - Public, shared across all users

2. **Results Dataset**: `{your_username}/agent-results-{model}-{timestamp}`
   - Individual test case results
   - Success/failure, execution time, tokens, cost
   - Links to traces dataset

3. **Traces Dataset**: `{your_username}/agent-traces-{model}-{timestamp}`
   - OpenTelemetry traces (if enable_otel = True)
   - Detailed execution steps, LLM calls, tool usage
   - Viewable in TraceMind Trace Visualization

4. **Metrics Dataset**: `{your_username}/agent-metrics-{model}-{timestamp}`
   - GPU metrics (if enable_gpu_metrics = True)
   - GPU utilization, memory, temperature, CO2 emissions
   - Time-series data for each test

**Local JSON Files** (if output_format = "json"):
- Saved to `output_dir` on the job machine
- Not automatically uploaded to HuggingFace
- Useful for local testing

### Viewing Results in TraceMind

**Step 1: Refresh Leaderboard**
1. Go to **📊 Leaderboard** tab
2. Click **Load Leaderboard** button
3. Your new run appears in the table

**Step 2: View Run Details**
1. Click on your run in the leaderboard
2. See detailed test results:
   - Individual test cases
   - Success/failure breakdown
   - Execution times
   - Token usage
   - Costs

**Step 3: Visualize Traces** (if enable_otel = True)
1. From run details, click on a test case
2. Click **View Trace** button
3. See OpenTelemetry waterfall diagram
4. Analyze:
   - LLM calls and durations
   - Tool executions
   - Reasoning steps
   - GPU metrics overlay (if GPU job)

**Step 4: Ask Questions About Results**
1. Go to **🤖 Agent Chat** tab
2. Ask questions like:
   - "Analyze my latest evaluation run"
   - "Why did test case 5 fail?"
   - "Compare my run with the top model"
   - "What was the cost breakdown?"

### Interpreting Results

**Key Metrics**:

| Metric | Description | Good Value |
|--------|-------------|------------|
| **Success Rate** | % of tests passed | >90% excellent, >70% good |
| **Avg Duration** | Time per test case | <5s good, <10s acceptable |
| **Total Cost** | Cost for all tests | Varies by model |
| **Tokens Used** | Total tokens consumed | Lower is better |
| **CO2 Emissions** | Carbon footprint | Lower is better |
| **GPU Utilization** | GPU usage % | >60% efficient |

**Common Patterns**:

**High accuracy, low cost**:
- ✅ Excellent model for production
- Examples: GPT-4-mini, Claude-3-Haiku, Gemini-1.5-Flash

**High accuracy, high cost**:
- ✅ Best for quality-critical tasks
- Examples: GPT-4, Claude-3.5-Sonnet, Gemini-1.5-Pro

**Low accuracy, low cost**:
- ⚠️ May need prompt optimization or better model
- Examples: Small local models (<3B params)

**Low accuracy, high cost**:
- ❌ Poor choice, investigate or switch models
- May indicate configuration issues

---

## Troubleshooting

### Job Submission Failures

**Error: "HuggingFace token not configured"**
- **Cause**: Missing or invalid HF token
- **Fix**:
  1. Go to Settings tab
  2. Add HF token with "Read + Write + Run Jobs" permissions
  3. Click "Save API Keys"

**Error: "HuggingFace Pro subscription required"**
- **Cause**: HF Jobs requires Pro subscription
- **Fix**:
  1. Subscribe at https://huggingface.co/pricing ($9/month)
  2. Add credit card for GPU charges
  3. Try again

**Error: "Modal credentials not configured"**
- **Cause**: Missing Modal API tokens
- **Fix**:
  1. Go to https://modal.com/settings/tokens
  2. Create new token
  3. Copy Token ID and Token Secret
  4. Add to Settings tab
  5. Try again

**Error: "Modal package not installed"**
- **Cause**: Modal SDK missing (should not happen in hosted Space)
- **Fix**: Contact support or run locally with `pip install modal`

### Job Execution Failures

**Job stuck in "Pending" status**
- **Cause**: High demand for GPU resources
- **Fix**:
  - Wait 5-10 minutes
  - Try different hardware (e.g., T4 instead of A100)
  - Try different infrastructure (Modal vs HF Jobs)

**Job fails with "Out of Memory"**
- **Cause**: Model too large for selected hardware
- **Fix**:
  - Use larger GPU (A100-80GB or H200)
  - Or use `auto` hardware selection
  - Or reduce `parallel_workers` to 1

**Job fails with "Model not found"**
- **Cause**: Invalid model ID or private model
- **Fix**:
  - Check model ID format: `organization/model-name`
  - For private models, add HF token with access
  - Verify model exists on HuggingFace Hub

**Job fails with "API key not set"**
- **Cause**: Missing LLM provider API key
- **Fix**:
  1. Go to Settings tab
  2. Add API key for your provider (OpenAI, Anthropic, etc.)
  3. Submit job again

**Job fails with "Rate limit exceeded"**
- **Cause**: Too many API requests
- **Fix**:
  - Reduce `parallel_workers` to 1
  - Use different model with higher rate limits
  - Wait and retry later

**Modal job fails with "Authentication failed"**
- **Cause**: Invalid Modal tokens
- **Fix**:
  1. Go to https://modal.com/settings/tokens
  2. Create new token (old one may be expired)
  3. Update tokens in Settings tab

### Results Not Appearing

**Results not in leaderboard after job completes**
- **Cause**: Dataset upload failed or not configured
- **Fix**:
  - Check job logs for errors
  - Verify `output_format` was set to "hub"
  - Verify HF token has "Write" permission
  - Manually refresh leaderboard (click "Load Leaderboard")

**Traces not appearing**
- **Cause**: OpenTelemetry not enabled
- **Fix**:
  - Re-run evaluation with `enable_otel = True`
  - Check traces dataset exists on your HF profile

**GPU metrics not showing**
- **Cause**: GPU metrics not enabled or CPU job
- **Fix**:
  - Re-run with `enable_gpu_metrics = True`
  - Verify job used GPU hardware (not CPU)
  - Check metrics dataset exists

---

## Advanced Configuration

### Custom Test Datasets

**Create your own test dataset**:

1. Use **🔬 Synthetic Data Generator** tab:
   - Configure domain and tools
   - Generate custom tasks
   - Push to HuggingFace Hub

2. Use generated dataset in evaluation:
   - Set `dataset_name` to your dataset: `{username}/dataset-name`
   - Configure agent with matching tools

**Dataset Format Requirements**:
```python
{
    "task_id": "task_001",
    "prompt": "What's the weather in Tokyo?",
    "expected_tool": "get_weather",
    "difficulty": "easy",
    "category": "tool_usage"
}
```

### Environment Variables

**LLM Provider API Keys** (in Settings):
- `OPENAI_API_KEY` - OpenAI API
- `ANTHROPIC_API_KEY` - Anthropic API
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` - Google Gemini API
- `COHERE_API_KEY` - Cohere API
- `MISTRAL_API_KEY` - Mistral API
- `TOGETHER_API_KEY` - Together AI API
- `GROQ_API_KEY` - Groq API
- `REPLICATE_API_TOKEN` - Replicate API
- `ANYSCALE_API_KEY` - Anyscale API

**Infrastructure Credentials**:
- `HF_TOKEN` - HuggingFace token
- `MODAL_TOKEN_ID` - Modal token ID
- `MODAL_TOKEN_SECRET` - Modal token secret

### Parallel Execution

**Use `parallel_workers` to speed up evaluation**:

- `1` - Sequential execution (default, safest)
- `2-4` - Moderate parallelism (2-4x faster)
- `5-10` - High parallelism (5-10x faster, risky)

**Trade-offs**:
- ✅ **Faster**: Linear speedup with workers
- ⚠️ **Higher cost**: More API calls per minute
- ⚠️ **Rate limits**: May hit provider rate limits
- ⚠️ **Memory**: Increases GPU memory usage

**Recommendations**:
- API models: Keep at 1 (avoid rate limits)
- Local models: Can use 2-4 if GPU has enough VRAM
- Production runs: Use 1 for reliability

### Private Datasets

**Make results private**:

1. Set `private = True` in job configuration
2. Results will be private on your HuggingFace profile
3. Only you can view in leaderboard (if using private leaderboard dataset)

**Use cases**:
- Proprietary models
- Confidential evaluation data
- Internal benchmarking

---

## Quick Reference

### Job Submission Checklist

Before submitting a job, verify:

- [ ] Infrastructure selected (HF Jobs or Modal)
- [ ] Hardware configured (auto or manual)
- [ ] Model ID is correct
- [ ] Provider matches model type
- [ ] API keys configured in Settings
- [ ] Dataset name is valid
- [ ] Output format is "hub" for TraceMind integration
- [ ] OpenTelemetry tracing enabled (if you want traces)
- [ ] GPU metrics enabled (if using GPU)
- [ ] Cost estimate reviewed
- [ ] Timeout is sufficient for your model size

### Common Model Configurations

**OpenAI GPT-4**:
```
Model: openai/gpt-4
Provider: litellm
Hardware: auto → cpu-basic
Infrastructure: Either (HF Jobs or Modal)
Estimated Cost: API costs only
```

**Anthropic Claude-3.5-Sonnet**:
```
Model: anthropic/claude-3.5-sonnet
Provider: litellm
Hardware: auto → cpu-basic
Infrastructure: Either (HF Jobs or Modal)
Estimated Cost: API costs only
```

**Meta Llama-3.1-8B**:
```
Model: meta-llama/Llama-3.1-8B-Instruct
Provider: transformers
Hardware: auto → a10g-large (HF) or gpu_l40s (Modal)
Infrastructure: Modal (cheaper for short jobs)
Estimated Cost: $0.75-1.50
```

**Meta Llama-3.1-70B**:
```
Model: meta-llama/Llama-3.1-70B-Instruct
Provider: transformers
Hardware: auto → a100-large (HF) or gpu_h200 (Modal)
Infrastructure: Modal (if available), else HF Jobs
Estimated Cost: $3.00-8.00
```

**Qwen-2.5-Coder-32B**:
```
Model: Qwen/Qwen2.5-Coder-32B-Instruct
Provider: transformers
Hardware: auto → a100-large (HF) or gpu_a100_80gb (Modal)
Infrastructure: Either
Estimated Cost: $2.00-4.00
```

---

## Next Steps

After submitting your first job:

1. **Monitor progress** in Job Monitoring tab
2. **View results** in Leaderboard when complete
3. **Analyze traces** in Trace Visualization
4. **Ask questions** in Agent Chat about your results
5. **Compare** with other models using Compare feature
6. **Optimize** model selection based on cost/accuracy trade-offs
7. **Generate** custom test datasets for your domain
8. **Share** your results with the community

For more help:
- [USER_GUIDE.md](USER_GUIDE.md) - Complete screen-by-screen walkthrough
- [MCP_INTEGRATION.md](MCP_INTEGRATION.md) - MCP client architecture details
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture overview
- GitHub Issues: [TraceMind-AI/issues](https://github.com/Mandark-droid/TraceMind-AI/issues)
