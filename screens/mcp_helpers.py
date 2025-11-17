"""
MCP Helper Functions for TraceMind-AI Screens
Provides simplified interfaces to call MCP server tools from various screens
"""

import os
from gradio_client import Client
from typing import Optional, Dict, Any
import json


# MCP Server URL (from environment or default)
MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "https://mcp-1st-birthday-tracemind-mcp-server.hf.space/"
)

# Cache the client to avoid recreating it every time
_mcp_client_cache = None


def get_mcp_client() -> Client:
    """
    Get Gradio client for MCP server (cached)

    Returns:
        gradio_client.Client instance
    """
    global _mcp_client_cache

    # Return cached client if available
    if _mcp_client_cache is not None:
        return _mcp_client_cache

    # Create new client with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"[MCP] Connecting to MCP server (attempt {attempt + 1}/{max_retries})...")
            client = Client(MCP_SERVER_URL)
            _mcp_client_cache = client
            print(f"[MCP] Successfully connected to MCP server")
            return client
        except Exception as e:
            print(f"[MCP] Connection attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            import time
            time.sleep(1)  # Wait 1 second before retry

    return Client(MCP_SERVER_URL)


async def call_analyze_leaderboard(
    leaderboard_repo: str = "kshitijthakkar/smoltrace-leaderboard",
    metric_focus: str = "overall",
    time_range: str = "last_week",
    top_n: int = 5
) -> str:
    """
    Call the analyze_leaderboard MCP tool

    Args:
        leaderboard_repo: HuggingFace dataset repository
        metric_focus: Focus area - "overall", "accuracy", "cost", "latency", or "co2"
        time_range: Time range - "last_week", "last_month", or "all_time"
        top_n: Number of top models to highlight (3-10)

    Returns:
        Markdown-formatted analysis from Gemini
    """
    try:
        client = get_mcp_client()
        result = client.predict(
            repo=leaderboard_repo,
            metric=metric_focus,
            time_range=time_range,
            top_n=top_n,
            api_name="/run_analyze_leaderboard"
        )
        return result
    except Exception as e:
        return f"❌ **Error calling analyze_leaderboard**: {str(e)}\n\nPlease check:\n- MCP server is running\n- Network connectivity\n- API parameters are correct"


async def call_debug_trace(
    trace_id: str,
    traces_repo: str,
    question: str = "Analyze this trace and explain what happened"
) -> str:
    """
    Call the debug_trace MCP tool

    Args:
        trace_id: Unique identifier for the trace
        traces_repo: HuggingFace dataset repository with trace data
        question: Specific question about the trace

    Returns:
        Markdown-formatted debug analysis from Gemini
    """
    try:
        client = get_mcp_client()
        result = client.predict(
            trace_id_val=trace_id,
            traces_repo_val=traces_repo,
            question_val=question,
            api_name="/run_debug_trace"
        )
        return result
    except Exception as e:
        return f"❌ **Error calling debug_trace**: {str(e)}\n\nPlease check:\n- Trace ID exists in dataset\n- Traces repository is accessible\n- MCP server is running"


async def call_compare_runs(
    run_id_1: str,
    run_id_2: str,
    leaderboard_repo: str = "kshitijthakkar/smoltrace-leaderboard",
    comparison_focus: str = "comprehensive"
) -> str:
    """
    Call the compare_runs MCP tool

    Args:
        run_id_1: First run ID from leaderboard
        run_id_2: Second run ID to compare against
        leaderboard_repo: HuggingFace dataset repository
        comparison_focus: Focus area - "comprehensive", "cost", "performance", or "eco_friendly"

    Returns:
        Markdown-formatted comparison analysis from Gemini
    """
    try:
        client = get_mcp_client()
        result = client.predict(
            run_id_1=run_id_1,
            run_id_2=run_id_2,
            focus=comparison_focus,
            repo=leaderboard_repo,
            api_name="/run_compare_runs"
        )
        return result
    except Exception as e:
        return f"❌ **Error calling compare_runs**: {str(e)}\n\nPlease check:\n- Both run IDs exist in leaderboard\n- MCP server is running\n- Network connectivity"


async def call_analyze_results(
    results_repo: str,
    focus_area: str = "overall",
    max_rows: int = 100
) -> str:
    """
    Call the analyze_results MCP tool

    Args:
        results_repo: HuggingFace dataset repository with results data
        focus_area: Focus area - "overall", "failures", "performance", or "tools"
        max_rows: Maximum number of test cases to analyze

    Returns:
        Markdown-formatted results analysis from Gemini
    """
    try:
        client = get_mcp_client()
        result = client.predict(
            repo=results_repo,
            focus=focus_area,
            max_rows=max_rows,
            api_name="/run_analyze_results"
        )
        return result
    except Exception as e:
        return f"❌ **Error calling analyze_results**: {str(e)}\n\nPlease check:\n- Results repository exists and is accessible\n- MCP server is running\n- Network connectivity"


def call_analyze_leaderboard_sync(
    leaderboard_repo: str = "kshitijthakkar/smoltrace-leaderboard",
    metric_focus: str = "overall",
    time_range: str = "last_week",
    top_n: int = 5
) -> str:
    """
    Synchronous version of call_analyze_leaderboard for Gradio event handlers

    Args:
        leaderboard_repo: HuggingFace dataset repository
        metric_focus: Focus area - "overall", "accuracy", "cost", "latency", or "co2"
        time_range: Time range - "last_week", "last_month", or "all_time"
        top_n: Number of top models to highlight (3-10)

    Returns:
        Markdown-formatted analysis from Gemini
    """
    try:
        client = get_mcp_client()
        result = client.predict(
            repo=leaderboard_repo,
            metric=metric_focus,
            time_range=time_range,
            top_n=top_n,
            api_name="/run_analyze_leaderboard"
        )
        return result
    except Exception as e:
        return f"❌ **Error calling analyze_leaderboard**: {str(e)}\n\nPlease check:\n- MCP server is running at {MCP_SERVER_URL}\n- Network connectivity\n- API parameters are correct"


def call_debug_trace_sync(
    trace_id: str,
    traces_repo: str,
    question: str = "Analyze this trace and explain what happened"
) -> str:
    """
    Synchronous version of call_debug_trace for Gradio event handlers
    """
    try:
        client = get_mcp_client()
        result = client.predict(
            trace_id_val=trace_id,
            traces_repo_val=traces_repo,
            question_val=question,
            api_name="/run_debug_trace"
        )
        return result
    except Exception as e:
        return f"❌ **Error calling debug_trace**: {str(e)}"


def call_compare_runs_sync(
    run_id_1: str,
    run_id_2: str,
    leaderboard_repo: str = "kshitijthakkar/smoltrace-leaderboard",
    comparison_focus: str = "comprehensive"
) -> str:
    """
    Synchronous version of call_compare_runs for Gradio event handlers
    """
    try:
        print(f"[MCP] Calling compare_runs with run_id_1={run_id_1}, run_id_2={run_id_2}")
        client = get_mcp_client()
        print(f"[MCP] Client obtained, calling predict...")
        result = client.predict(
            run_id_1=run_id_1,
            run_id_2=run_id_2,
            focus=comparison_focus,
            repo=leaderboard_repo,
            api_name="/run_compare_runs"
        )
        print(f"[MCP] Predict completed, result length: {len(result) if isinstance(result, str) else 'N/A'}")
        return result
    except Exception as e:
        error_msg = str(e)
        print(f"[MCP ERROR] compare_runs failed: {error_msg}")
        import traceback
        traceback.print_exc()

        # Provide helpful error message
        if "Could not fetch config" in error_msg or "SSE" in error_msg:
            return f"❌ **MCP Server Connection Error**\n\nCould not connect to the MCP server at:\n`{MCP_SERVER_URL}`\n\n**Possible causes:**\n- The HuggingFace Space may be sleeping (first request can take 30-60 seconds)\n- Network connectivity issues\n- Server is rebuilding after recent changes\n\n**Try:**\n1. Wait a moment and try again\n2. Visit {MCP_SERVER_URL} in your browser to wake up the space\n3. Contact support if the issue persists\n\n**Technical details:** {error_msg}"
        return f"❌ **Error calling compare_runs**: {error_msg}"


def call_analyze_results_sync(
    results_repo: str,
    focus_area: str = "overall",
    max_rows: int = 100
) -> str:
    """
    Synchronous version of call_analyze_results for Gradio event handlers
    """
    try:
        client = get_mcp_client()
        result = client.predict(
            repo=results_repo,
            focus=focus_area,
            max_rows=max_rows,
            api_name="/run_analyze_results"
        )
        return result
    except Exception as e:
        return f"❌ **Error calling analyze_results**: {str(e)}"
