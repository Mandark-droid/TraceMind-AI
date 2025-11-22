"""
Modal Job Submission Module

Handles submission of SMOLTRACE evaluation jobs to Modal's serverless compute platform.
"""

import os
import sys
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

        # Detect current Python version dynamically (must match for serialized=True)
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        # Define Modal function with appropriate base image
        # Note: Must match local Python version when using serialized=True
        if modal_gpu:
            # Use GPU-optimized image with CUDA for GPU jobs (using latest stable CUDA)
            image = modal.Image.from_registry(
                "nvidia/cuda:12.6.0-cudnn-devel-ubuntu22.04",
                add_python=python_version  # Dynamically match current environment
            ).pip_install([
                "smoltrace",
                "ddgs",  # DuckDuckGo search
                "litellm",
                "transformers",
                "torch",
                "accelerate",  # Required for GPU device_map
                "bitsandbytes",  # For quantization support
                "sentencepiece",  # For some tokenizers
                "protobuf",  # For some models
                "hf_transfer",  # Fast HuggingFace downloads
                "nvidia-ml-py"  # GPU metrics collection
            ]).env({
                # Enable fast downloads and verbose logging
                "HF_HUB_ENABLE_HF_TRANSFER": "1",
                "TRANSFORMERS_VERBOSITY": "info",
                "HF_HUB_VERBOSITY": "info"
            })
        else:
            # Use lightweight image for CPU jobs
            image = modal.Image.debian_slim(python_version=python_version).pip_install([
                "smoltrace",
                "ddgs",  # DuckDuckGo search
                "litellm"
            ])

        @app.function(
            image=image,
            gpu=modal_gpu if modal_gpu else None,
            secrets=[
                modal.Secret.from_dict(env_vars)
            ],
            timeout=3600,  # 1 hour timeout
            serialized=True  # Required for functions defined in local scope
        )
        def run_evaluation(command_to_run: str):
            """Run SMOLTRACE evaluation on Modal"""
            import subprocess
            import sys
            import os

            print("=" * 80)
            print(f"Starting SMOLTRACE evaluation on Modal")
            print(f"Command: {command_to_run}")
            print(f"Python version: {sys.version}")

            # Show GPU info if available
            try:
                import torch
                if torch.cuda.is_available():
                    print(f"GPU: {torch.cuda.get_device_name(0)}")
                    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            except:
                pass

            print("=" * 80)
            print("\nNote: Model download may take several minutes for large models (14B = ~28GB)")
            print("Downloading and initializing model...\n")

            try:
                # Run with live output instead of capture_output so we can see progress
                result = subprocess.run(
                    command_to_run,
                    shell=True,
                    capture_output=False,  # Stream output in real-time
                    text=True
                )

                # Since we're not capturing, create a success message
                print("\n" + "=" * 80)
                print("EVALUATION COMPLETED")
                print(f"Return code: {result.returncode}")
                print("=" * 80)

                return {
                    "returncode": result.returncode,
                    "stdout": "Check Modal logs for full output (streaming mode)",
                    "stderr": ""
                }
            except Exception as e:
                error_msg = f"Error running evaluation: {str(e)}"
                print("\n" + "=" * 80)
                print("EVALUATION FAILED")
                print(error_msg)
                print("=" * 80)
                import traceback
                traceback.print_exc()
                return {
                    "returncode": -1,
                    "stdout": "",
                    "stderr": error_msg
                }

        # Submit the job using Modal's remote() in a background thread
        # Note: spawn() doesn't work well with dynamically created apps
        # remote() ensures the job actually executes, threading keeps UI responsive
        import threading

        # Store result in a shared dict since we're using threading
        result_container = {"modal_call_id": None, "started": False}

        def run_job_on_modal():
            """Run the Modal job in background thread"""
            try:
                with app.run():
                    # Use remote() instead of spawn() for dynamic apps
                    # This ensures the function actually executes
                    function_call = run_evaluation.remote(command)
                    result_container["started"] = True
                    print(f"Modal job completed with return code: {function_call.get('returncode', 'unknown')}")
            except Exception as e:
                print(f"Error running Modal job: {e}")
                result_container["error"] = str(e)

        # Start the job in a background thread so we don't block the UI
        job_thread = threading.Thread(target=run_job_on_modal, daemon=True)
        job_thread.start()

        # Give Modal a moment to start the job and capture any immediate errors
        import time
        time.sleep(2)

        # Use job_id as the tracking ID since remote() doesn't give us a call_id
        modal_call_id = f"modal-{job_id}"

        return {
            "success": True,
            "job_id": job_id,
            "modal_call_id": modal_call_id,  # Modal's internal function call ID
            "platform": "Modal",
            "hardware": modal_gpu or "CPU",
            "command": command,
            "status": "submitted",
            "message": f"Job successfully submitted to Modal (hardware: {modal_gpu or 'CPU'})",
            "instructions": f"""
✅ Job submitted successfully!

**Job Details:**
- Run ID: {job_id}
- Modal Call ID: {modal_call_id}
- Hardware: {modal_gpu or "CPU"}
- Platform: Modal (serverless compute)

**What happens next:**
1. Job starts running on Modal infrastructure
2. For GPU jobs: Model downloads first (14B models = ~28GB, can take 10-15 min)
3. SMOLTRACE evaluates your model
4. Results are automatically pushed to HuggingFace datasets
5. They will appear in TraceMind leaderboard when complete

**Monitoring**: Check Modal dashboard for real-time logs and progress:
https://modal.com/apps

**Expected Duration**:
- CPU jobs (API models): 2-5 minutes
- GPU jobs (local models): 15-30 minutes (includes model download)

**Cost**: Modal charges per-second usage. Estimated cost: $0.01-1.00 depending on model size and hardware.
            """.strip()
        }

    except Exception as e:
        error_msg = str(e)

        # Check for common Modal errors
        if "MODAL_TOKEN_ID" in error_msg or "authentication" in error_msg.lower():
            return {
                "success": False,
                "error": "Modal authentication failed. Please verify your MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in Settings.",
                "job_id": job_id,
                "troubleshooting": """
**Steps to fix:**
1. Go to https://modal.com/settings/tokens
2. Create a new token
3. Copy Token ID (starts with 'ak-') and Token Secret (starts with 'as-')
4. Add them to Settings in TraceMind
5. Try again
                """
            }
        else:
            return {
                "success": False,
                "error": f"Failed to submit Modal job: {error_msg}",
                "job_id": job_id,
                "command": command
            }


def _auto_select_modal_hardware(provider: str, model: str) -> Optional[str]:
    """
    Automatically select Modal hardware based on model and provider.

    Memory estimation for agentic workloads:
    - Model weights (FP16): ~2GB per 1B params
    - KV cache for long contexts: ~1.5-2x model size for agentic tasks
    - Inference overhead: ~20-30% additional
    - Total: ~4-5GB per 1B params for safe agentic execution

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
    # Conservative allocation for agentic tasks (model weights + KV cache + inference overhead)
    # Memory estimation: ~4-5GB per 1B params for safe agentic execution
    model_lower = model.lower()

    # Extract model size using regex to capture the number before 'b'
    import re
    size_match = re.search(r'(\d+\.?\d*)b', model_lower)

    if size_match:
        model_size = float(size_match.group(1))

        # Complete coverage from 0.5B to 100B+ with no gaps
        if model_size >= 49:
            # 49B-100B+: H200 (140GB VRAM)
            return "H200"
        elif model_size >= 25:
            # 25B-48B: A100-80GB (e.g., Gemma-27B, Kimi-48B, 30B, 34B)
            return "A100-80GB"
        elif model_size >= 13:
            # 13B-24B: A100-80GB (e.g., 13B, 14B, 15B, 20B, 22B)
            return "A100-80GB"
        elif model_size >= 6:
            # 6B-12B: L40S 48GB (e.g., 6B, 7B, 8B, 9B, 10B, 11B, 12B)
            return "L40S"
        elif model_size >= 1:
            # 1B-5B: T4 16GB (e.g., 1B, 2B, 3B, 4B, 5B)
            return "T4"
        else:
            # < 1B: T4 16GB
            return "T4"
    else:
        # No size detected in model name - default to L40S (safe middle ground)
        return "L40S"
