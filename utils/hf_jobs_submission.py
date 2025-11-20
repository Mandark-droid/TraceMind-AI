"""
HuggingFace Jobs Submission Module

Handles submission of SMOLTRACE evaluation jobs to HuggingFace Jobs platform.
Uses the official HuggingFace Jobs API: `huggingface_hub.run_job()`
"""

import os
import uuid
from typing import Dict, Optional, List


def submit_hf_job(
    model: str,
    provider: str,
    agent_type: str,
    hardware: str,
    dataset_name: str,
    split: str = "train",
    difficulty: str = "all",
    parallel_workers: int = 1,
    hf_token: Optional[str] = None,
    hf_inference_provider: Optional[str] = None,
    search_provider: str = "duckduckgo",
    enable_tools: Optional[List[str]] = None,
    output_format: str = "hub",
    output_dir: Optional[str] = None,
    enable_otel: bool = True,
    enable_gpu_metrics: bool = True,
    private: bool = False,
    debug: bool = False,
    quiet: bool = False,
    run_id: Optional[str] = None,
    timeout: str = "1h"
) -> Dict:
    """
    Submit an evaluation job to HuggingFace Jobs using the run_job API

    Args:
        model: Model identifier (e.g., "openai/gpt-4")
        provider: Provider type ("litellm", "inference", "transformers")
        agent_type: Agent type ("tool", "code", "both")
        hardware: Hardware type (e.g., "auto", "cpu-basic", "t4-small", "a10g-small")
        dataset_name: HuggingFace dataset for evaluation
        split: Dataset split to use
        difficulty: Difficulty filter
        parallel_workers: Number of parallel workers
        hf_token: HuggingFace token
        hf_inference_provider: HF Inference provider
        search_provider: Search provider for agents
        enable_tools: List of tools to enable
        output_format: Output format ("hub" or "json")
        output_dir: Output directory for JSON format
        enable_otel: Enable OpenTelemetry tracing
        enable_gpu_metrics: Enable GPU metrics collection
        private: Make datasets private
        debug: Enable debug mode
        quiet: Enable quiet mode
        run_id: Optional run ID (auto-generated if not provided)
        timeout: Job timeout (default: "1h")

    Returns:
        dict: Job submission result with job_id, status, and details
    """
    try:
        from huggingface_hub import run_job
    except ImportError:
        return {
            "success": False,
            "error": "huggingface_hub package not installed or outdated. Install with: pip install -U huggingface_hub",
            "job_id": None
        }

    # Validate HF token
    token = hf_token or os.environ.get("HF_TOKEN")
    if not token:
        return {
            "success": False,
            "error": "HuggingFace token not configured. Please set HF_TOKEN in Settings.",
            "job_id": None
        }

    # Generate job ID
    job_id = run_id if run_id else f"job_{uuid.uuid4().hex[:8]}"

    # Map hardware to HF Jobs flavor
    if hardware == "auto":
        flavor = _auto_select_hf_hardware(provider, model)
    else:
        flavor = hardware

    # Determine if this is a GPU job
    is_gpu_job = flavor not in ["cpu-basic", "cpu-upgrade"]

    # Select appropriate Docker image
    if is_gpu_job:
        # GPU jobs use PyTorch with CUDA
        image = "pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel"
        pip_packages = "smoltrace ddgs smoltrace[gpu]"
    else:
        # CPU jobs use standard Python
        image = "python:3.12"
        pip_packages = "smoltrace ddgs"

    # Build secrets dictionary
    secrets = {
        "HF_TOKEN": token
    }

    # Add LLM provider API keys from environment
    llm_key_names = [
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
        "GEMINI_API_KEY", "COHERE_API_KEY", "MISTRAL_API_KEY",
        "TOGETHER_API_KEY", "GROQ_API_KEY", "REPLICATE_API_TOKEN",
        "ANYSCALE_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT",
        "LITELLM_API_KEY"
    ]

    for key_name in llm_key_names:
        value = os.environ.get(key_name)
        if value:
            secrets[key_name] = value

    # Build SMOLTRACE command
    cmd_parts = ["smoltrace-eval"]
    cmd_parts.append(f"--model {model}")
    cmd_parts.append(f"--provider {provider}")
    if hf_inference_provider:
        cmd_parts.append(f"--hf-inference-provider {hf_inference_provider}")
    cmd_parts.append(f"--search-provider {search_provider}")
    if enable_tools:
        cmd_parts.append(f"--enable-tools {','.join(enable_tools)}")
    cmd_parts.append(f"--agent-type {agent_type}")
    cmd_parts.append(f"--dataset-name {dataset_name}")
    cmd_parts.append(f"--split {split}")
    if difficulty != "all":
        cmd_parts.append(f"--difficulty {difficulty}")
    if parallel_workers > 1:
        cmd_parts.append(f"--parallel-workers {parallel_workers}")
    cmd_parts.append(f"--output-format {output_format}")
    if output_dir and output_format == "json":
        cmd_parts.append(f"--output-dir {output_dir}")
    if enable_otel:
        cmd_parts.append("--enable-otel")
    if not enable_gpu_metrics:
        cmd_parts.append("--disable-gpu-metrics")
    if private:
        cmd_parts.append("--private")
    if debug:
        cmd_parts.append("--debug")
    if quiet:
        cmd_parts.append("--quiet")
    cmd_parts.append(f"--run-id {job_id}")

    smoltrace_command = " ".join(cmd_parts)

    # Build full command with pip install
    full_command = f"pip install {pip_packages} && {smoltrace_command}"

    # Submit job using HuggingFace Jobs API
    try:
        job = run_job(
            image=image,
            command=["bash", "-c", full_command],
            secrets=secrets,
            flavor=flavor,
            timeout=timeout
        )

        return {
            "success": True,
            "job_id": job_id,
            "hf_job_id": job.job_id if hasattr(job, 'job_id') else str(job),
            "platform": "HuggingFace Jobs",
            "hardware": flavor,
            "image": image,
            "command": smoltrace_command,
            "status": "submitted",
            "message": f"Job successfully submitted to HuggingFace Jobs (flavor: {flavor})",
            "instructions": f"""
✅ Job submitted successfully!

**Job Details:**
- Flavor: {flavor}
- Image: {image}
- Timeout: {timeout}

**Monitor your job:**
- View job status: https://huggingface.co/jobs
- HF Job ID: {job.job_id if hasattr(job, 'job_id') else 'check dashboard'}

**What happens next:**
1. Job starts running on HuggingFace infrastructure
2. SMOLTRACE evaluates your model
3. Results are automatically pushed to HuggingFace datasets
4. They will appear in TraceMind leaderboard when complete
            """.strip()
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to submit job to HuggingFace: {str(e)}",
            "job_id": job_id,
            "command": smoltrace_command,
            "debug_info": {
                "image": image,
                "flavor": flavor,
                "timeout": timeout,
                "secrets_configured": list(secrets.keys())
            }
        }


def _auto_select_hf_hardware(provider: str, model: str) -> str:
    """
    Automatically select HuggingFace Jobs hardware based on model and provider

    Args:
        provider: Provider type
        model: Model identifier

    Returns:
        str: HF Jobs flavor
    """
    # API models only need CPU
    if provider in ["litellm", "inference"]:
        return "cpu-basic"

    # Local models need GPU - select based on model size
    model_lower = model.lower()

    if "70b" in model_lower or "65b" in model_lower:
        # Large models need high-end GPU
        return "a100-large"
    elif "13b" in model_lower or "34b" in model_lower:
        # Medium models work on A10
        return "a10g-large"
    elif "7b" in model_lower or "8b" in model_lower or "4b" in model_lower:
        # Small models efficient on T4 or A10
        return "t4-small"  # More cost-effective for small models
    else:
        # Default to T4 for unknown sizes
        return "t4-small"


def check_job_status(job_id: str, hf_token: Optional[str] = None) -> Dict:
    """
    Check the status of a HuggingFace Job

    Args:
        job_id: Job ID to check
        hf_token: HuggingFace token (optional, uses env if not provided)

    Returns:
        dict: Job status information
    """
    # Placeholder for when HF Jobs API becomes available
    return {
        "job_id": job_id,
        "status": "unknown",
        "message": "HuggingFace Jobs status API not yet available programmatically"
    }
