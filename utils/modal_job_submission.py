"""
Modal Job Submission Module

Handles submission of SMOLTRACE evaluation jobs to Modal's serverless compute platform.
"""

import os
import uuid
from typing import Dict, Optional, List


def submit_modal_job(
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
    run_id: Optional[str] = None
) -> Dict:
    """
    Submit an evaluation job to Modal

    Args:
        model: Model identifier (e.g., "openai/gpt-4")
        provider: Provider type ("litellm", "inference", "transformers")
        agent_type: Agent type ("tool", "code", "both")
        hardware: Hardware type (e.g., "auto", "gpu_a10", "gpu_h200")
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

    Returns:
        dict: Job submission result with job_id, status, and details
    """
    try:
        import modal
    except ImportError:
        return {
            "success": False,
            "error": "Modal package not installed. Install with: pip install modal",
            "job_id": None
        }

    # Validate Modal credentials
    modal_token_id = os.environ.get("MODAL_TOKEN_ID")
    modal_token_secret = os.environ.get("MODAL_TOKEN_SECRET")

    if not modal_token_id or not modal_token_secret:
        return {
            "success": False,
            "error": "Modal credentials not configured. Please set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in Settings.",
            "job_id": None
        }

    # Generate job ID
    job_id = run_id if run_id else f"job_{uuid.uuid4().hex[:8]}"

    # Map hardware to Modal GPU types
    hardware_map = {
        "auto": _auto_select_modal_hardware(provider, model),
        "cpu": None,  # CPU only
        "gpu_t4": "T4",
        "gpu_l4": "L4",
        "gpu_a10": "A10G",
        "gpu_l40s": "L40S",
        "gpu_a100": "A100",
        "gpu_a100_80gb": "A100-80GB",
        "gpu_h100": "H100",
        "gpu_h200": "H200",
        "gpu_b200": "B200"
    }

    modal_gpu = hardware_map.get(hardware, "A10G")

    # Build environment variables
    env_vars = {
        "HF_TOKEN": hf_token or os.environ.get("HF_TOKEN", ""),
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
            env_vars[key_name] = value

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

    command = " ".join(cmd_parts)

    # Create Modal app dynamically
    try:
        app = modal.App(f"smoltrace-eval-{job_id}")

        # Define Modal function
        image = modal.Image.debian_slim().pip_install([
            "smoltrace[otel,gpu]",
            "litellm",
            "transformers",
            "torch"
        ])

        @app.function(
            image=image,
            gpu=modal_gpu if modal_gpu else None,
            secrets=[
                modal.Secret.from_dict(env_vars)
            ],
            timeout=3600  # 1 hour timeout
        )
        def run_evaluation():
            """Run SMOLTRACE evaluation on Modal"""
            import subprocess
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        # Submit the job
        # Note: Modal doesn't have a direct "submit and return" API like HF Jobs
        # For now, we'll return the command that should be run
        # In production, you'd use Modal's async API or spawn the function

        return {
            "success": True,
            "job_id": job_id,
            "platform": "Modal",
            "hardware": modal_gpu or "CPU",
            "command": command,
            "status": "pending",
            "message": "Modal job configured. Use Modal CLI to submit: modal run modal_job_submission.py",
            "note": "Direct Modal API submission requires async handling. For now, use the generated command with Modal CLI."
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create Modal job: {str(e)}",
            "job_id": job_id
        }


def _auto_select_modal_hardware(provider: str, model: str) -> Optional[str]:
    """
    Automatically select Modal hardware based on model and provider

    Args:
        provider: Provider type
        model: Model identifier

    Returns:
        str: Modal GPU type or None for CPU
    """
    # API models don't need GPU
    if provider in ["litellm", "inference"]:
        return None

    # Local models need GPU - select based on model size
    model_lower = model.lower()

    if "70b" in model_lower or "65b" in model_lower:
        return "A100-80GB"  # Large models need A100 80GB
    elif "13b" in model_lower or "34b" in model_lower:
        return "A10G"  # Medium models work well on A10G
    elif "7b" in model_lower or "8b" in model_lower:
        return "A10G"  # Small models efficient on A10G
    else:
        return "A10G"  # Default to A10G for unknown sizes
