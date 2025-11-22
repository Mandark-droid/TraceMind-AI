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

    # Build full command with pip upgrade + install
    # IMPORTANT: Upgrade pip first to avoid dependency resolution issues
    # (older pip in conda struggles with fief-client[cli] backtracking)
    # Set PYTHONIOENCODING to UTF-8 to handle unicode output properly
    full_command = f"export PYTHONIOENCODING=utf-8 && pip install --upgrade pip && pip install {pip_packages} && {smoltrace_command}"

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
    Automatically select HuggingFace Jobs hardware based on model and provider.

    Memory estimation for agentic workloads:
    - Model weights (FP16): ~2GB per 1B params
    - KV cache for long contexts: ~1.5-2x model size for agentic tasks
    - Inference overhead: ~20-30% additional
    - Total: ~4-5GB per 1B params for safe agentic execution

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
    # Conservative allocation for agentic tasks (model weights + KV cache + inference overhead)
    # Memory estimation: ~4-5GB per 1B params for safe agentic execution
    model_lower = model.lower()

    # Extract model size using regex to capture the number before 'b'
    import re
    size_match = re.search(r'(\d+\.?\d*)b', model_lower)

    if size_match:
        model_size = float(size_match.group(1))

        # Complete coverage from 0.5B to 100B+ with no gaps
        # HF Jobs has limited GPU options: t4-small, a10g-large, a100-large
        if model_size >= 13:
            # 13B-100B+: A100 large (e.g., 13B, 14B, 27B, 30B, 48B, 70B)
            return "a100-large"
        elif model_size >= 6:
            # 6B-12B: A10G large (e.g., 6B, 7B, 8B, 9B, 10B, 11B, 12B)
            return "a10g-large"
        elif model_size >= 1:
            # 1B-5B: T4 small (e.g., 1B, 2B, 3B, 4B, 5B)
            return "t4-small"
        else:
            # < 1B: T4 small
            return "t4-small"
    else:
        # No size detected in model name - default to A100 (safe for agentic workloads)
        return "a100-large"


def check_job_status(hf_job_id: str, hf_token: Optional[str] = None) -> Dict:
    """
    Check the status of a HuggingFace Job using the Jobs API

    Args:
        hf_job_id: HF Job ID (format: username/job_hash or just job_hash)
        hf_token: HuggingFace token (optional, uses env if not provided)

    Returns:
        dict: Job status information
    """
    try:
        from huggingface_hub import HfApi
    except ImportError:
        return {
            "success": False,
            "error": "huggingface_hub package not installed",
            "job_id": hf_job_id
        }

    token = hf_token or os.environ.get("HF_TOKEN")
    if not token:
        return {
            "success": False,
            "error": "HuggingFace token not configured",
            "job_id": hf_job_id
        }

    try:
        api = HfApi(token=token)

        # Parse job_id and namespace (username)
        # Format can be "username/job_hash" or just "job_hash"
        if "/" in hf_job_id:
            namespace, job_id_only = hf_job_id.split("/", 1)
            job_info = api.inspect_job(job_id=job_id_only, namespace=namespace)
        else:
            job_info = api.inspect_job(job_id=hf_job_id)

        # Extract status stage from JobStatus object
        if hasattr(job_info, 'status') and hasattr(job_info.status, 'stage'):
            status = job_info.status.stage
        else:
            status = str(job_info.status) if hasattr(job_info, 'status') else "unknown"

        return {
            "success": True,
            "job_id": hf_job_id,
            "status": status,
            "created_at": str(job_info.created_at) if hasattr(job_info, 'created_at') else None,
            "flavor": job_info.flavor if hasattr(job_info, 'flavor') else None,
            "url": job_info.url if hasattr(job_info, 'url') else None,
            "info": str(job_info)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch job status: {str(e)}",
            "job_id": hf_job_id
        }


def get_job_logs(hf_job_id: str, hf_token: Optional[str] = None) -> Dict:
    """
    Retrieve logs from a HuggingFace Job

    Args:
        hf_job_id: HF Job ID (format: username/job_hash or just job_hash)
        hf_token: HuggingFace token (optional, uses env if not provided)

    Returns:
        dict: Job logs information
    """
    try:
        from huggingface_hub import HfApi
    except ImportError:
        return {
            "success": False,
            "error": "huggingface_hub package not installed",
            "job_id": hf_job_id
        }

    token = hf_token or os.environ.get("HF_TOKEN")
    if not token:
        return {
            "success": False,
            "error": "HuggingFace token not configured",
            "job_id": hf_job_id
        }

    try:
        api = HfApi(token=token)

        # Parse job_id and namespace (username)
        # Format can be "username/job_hash" or just "job_hash"
        if "/" in hf_job_id:
            namespace, job_id_only = hf_job_id.split("/", 1)
            logs_iterable = api.fetch_job_logs(job_id=job_id_only, namespace=namespace)
        else:
            logs_iterable = api.fetch_job_logs(job_id=hf_job_id)

        # Convert iterable to string
        logs = "\n".join(logs_iterable)

        return {
            "success": True,
            "job_id": hf_job_id,
            "logs": logs
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch job logs: {str(e)}",
            "job_id": hf_job_id,
            "logs": ""
        }


def list_user_jobs(hf_token: Optional[str] = None, limit: int = 10) -> Dict:
    """
    List recent jobs for the authenticated user

    Args:
        hf_token: HuggingFace token (optional, uses env if not provided)
        limit: Maximum number of jobs to return (applied after fetching)

    Returns:
        dict: List of user's jobs
    """
    try:
        from huggingface_hub import HfApi
    except ImportError:
        return {
            "success": False,
            "error": "huggingface_hub package not installed"
        }

    token = hf_token or os.environ.get("HF_TOKEN")
    if not token:
        return {
            "success": False,
            "error": "HuggingFace token not configured"
        }

    try:
        api = HfApi(token=token)
        # List user's jobs (no limit parameter in API, so we fetch all and slice)
        all_jobs = api.list_jobs()

        # Limit the results
        jobs_to_display = all_jobs[:limit] if limit > 0 else all_jobs

        job_list = []
        for job in jobs_to_display:
            # Extract owner name from JobOwner object
            owner_name = job.owner.name if hasattr(job, 'owner') and hasattr(job.owner, 'name') else None

            # Build job_id in the format: owner/id
            if owner_name and hasattr(job, 'id'):
                job_id = f"{owner_name}/{job.id}"
            elif hasattr(job, 'id'):
                job_id = job.id
            else:
                job_id = "unknown"

            # Extract status stage from JobStatus object
            if hasattr(job, 'status') and hasattr(job.status, 'stage'):
                status = job.status.stage
            else:
                status = str(job.status) if hasattr(job, 'status') else "unknown"

            job_list.append({
                "job_id": job_id,
                "status": status,
                "created_at": str(job.created_at) if hasattr(job, 'created_at') else None
            })

        return {
            "success": True,
            "jobs": job_list,
            "count": len(job_list)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list jobs: {str(e)}",
            "jobs": []
        }
