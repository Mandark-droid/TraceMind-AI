"""
Synchronous wrapper for MCP Client
Provides sync interface for Gradio event handlers
"""

import asyncio
from typing import Optional, Dict, Any, List
from .client import MCPClient


class SyncMCPClient:
    """Synchronous wrapper for MCPClient to use in Gradio event handlers"""

    def __init__(self, server_url: Optional[str] = None):
        self.client = MCPClient(server_url)
        self._loop = None

    def _get_or_create_event_loop(self):
        """Get or create an event loop for async operations"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop

    def _run_async(self, coro):
        """Run an async coroutine and return the result"""
        loop = self._get_or_create_event_loop()
        return loop.run_until_complete(coro)

    def initialize(self):
        """Initialize connection to MCP server (sync)"""
        return self._run_async(self.client.initialize())

    def analyze_leaderboard(
        self,
        leaderboard_repo: str = "kshitijthakkar/smoltrace-leaderboard",
        metric_focus: str = "overall",
        time_range: str = "last_week",
        top_n: int = 5,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """Analyze leaderboard (sync wrapper)"""
        return self._run_async(
            self.client.analyze_leaderboard(
                leaderboard_repo, metric_focus, time_range, top_n, hf_token, gemini_api_key
            )
        )

    def debug_trace(
        self,
        trace_data: Dict[str, Any],
        question: str,
        metrics_data: Optional[Dict[str, Any]] = None,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """Debug trace (sync wrapper)"""
        return self._run_async(
            self.client.debug_trace(trace_data, question, metrics_data, hf_token, gemini_api_key)
        )

    def estimate_cost(
        self,
        model: str,
        agent_type: str = "both",
        num_tests: int = 100,
        hardware: Optional[str] = None,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """Estimate cost (sync wrapper)"""
        return self._run_async(
            self.client.estimate_cost(model, agent_type, num_tests, hardware, hf_token, gemini_api_key)
        )

    def compare_runs(
        self,
        run_data_list: List[Dict[str, Any]],
        focus_metrics: Optional[List[str]] = None,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """Compare runs (sync wrapper)"""
        return self._run_async(
            self.client.compare_runs(run_data_list, focus_metrics, hf_token, gemini_api_key)
        )

    def analyze_results(
        self,
        results_data: List[Dict[str, Any]],
        analysis_focus: str = "optimization",
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """Analyze results (sync wrapper)"""
        return self._run_async(
            self.client.analyze_results(results_data, analysis_focus, hf_token, gemini_api_key)
        )

    def get_dataset_info(
        self,
        dataset_repo: str,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """Get dataset info (sync wrapper)"""
        return self._run_async(
            self.client.get_dataset_info(dataset_repo, hf_token, gemini_api_key)
        )

    def close(self):
        """Close the MCP client (sync wrapper)"""
        return self._run_async(self.client.close())


# Global instance
_sync_mcp_client: Optional[SyncMCPClient] = None


def get_sync_mcp_client() -> SyncMCPClient:
    """Get or create the global synchronous MCP client"""
    global _sync_mcp_client
    if _sync_mcp_client is None:
        _sync_mcp_client = SyncMCPClient()
    return _sync_mcp_client
