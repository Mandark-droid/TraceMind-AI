"""
MCP Client for connecting to TraceMind-mcp-server
Uses MCP protocol over HTTP to call remote MCP tools
"""

import os
import asyncio
from typing import Optional, Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
import aiohttp


class MCPClient:
    """Client for interacting with TraceMind MCP Server"""

    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize MCP Client

        Args:
            server_url: URL of the TraceMind-mcp-server endpoint
                       If None, uses MCP_SERVER_URL from environment
        """
        self.server_url = server_url or os.getenv(
            'MCP_SERVER_URL',
            'https://mcp-1st-birthday-tracemind-mcp-server.hf.space/gradio_api/mcp/'
        )
        self.session: Optional[ClientSession] = None
        self._initialized = False
        self._sse_context = None
        self._session_context = None

    async def initialize(self):
        """Initialize connection to MCP server"""
        if self._initialized:
            return

        try:
            # Connect to SSE endpoint and keep it open
            self._sse_context = sse_client(self.server_url)
            read, write = await self._sse_context.__aenter__()

            # Create session and keep it open
            self._session_context = ClientSession(read, write)
            self.session = await self._session_context.__aenter__()
            await self.session.initialize()
            self._initialized = True

            # List available tools for verification
            tools_result = await self.session.list_tools()
            print(f"✅ Connected to TraceMind MCP Server at {self.server_url}")
            print(f"📊 Available tools: {len(tools_result.tools)}")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            # Clean up on error
            await self._cleanup_connections()
            raise

    async def _ensure_connected(self):
        """Ensure the connection is active, reconnect if needed"""
        if not self._initialized or self.session is None:
            print("🔄 Reconnecting to MCP server...")
            await self._cleanup_connections()
            await self.initialize()

    async def _call_tool_with_retry(self, tool_name: str, arguments: dict, max_retries: int = 2):
        """Call MCP tool with automatic retry on connection errors"""
        for attempt in range(max_retries):
            try:
                await self._ensure_connected()
                result = await self.session.call_tool(tool_name, arguments=arguments)
                return result
            except Exception as e:
                error_str = str(e)
                if "ClosedResourceError" in error_str or "closed" in error_str.lower():
                    if attempt < max_retries - 1:
                        print(f"⚠️ Connection lost, retrying... (attempt {attempt + 1}/{max_retries})")
                        await self._cleanup_connections()
                        continue
                raise

    async def analyze_leaderboard(
        self,
        leaderboard_repo: str = "kshitijthakkar/smoltrace-leaderboard",
        metric_focus: str = "overall",
        time_range: str = "last_week",
        top_n: int = 5,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """
        Call the analyze_leaderboard tool on MCP server

        Args:
            leaderboard_repo: HuggingFace dataset repo for leaderboard
            metric_focus: Focus metric (overall, accuracy, cost, latency, co2)
            time_range: Time range filter (last_week, last_month, all_time)
            top_n: Number of top models to highlight
            hf_token: HuggingFace API token (optional if public dataset)
            gemini_api_key: Google Gemini API key (optional, server may have it)

        Returns:
            AI-generated analysis of the leaderboard
        """
        try:
            # Build arguments
            args = {
                "leaderboard_repo": leaderboard_repo,
                "metric_focus": metric_focus,
                "time_range": time_range,
                "top_n": top_n
            }

            # Add optional tokens if provided
            if hf_token:
                args["hf_token"] = hf_token
            if gemini_api_key:
                args["gemini_api_key"] = gemini_api_key

            # Call MCP tool with retry
            result = await self._call_tool_with_retry("analyze_leaderboard", args)

            # Extract text from result
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No analysis generated"

        except Exception as e:
            return f"❌ Error calling analyze_leaderboard: {str(e)}"

    async def debug_trace(
        self,
        trace_data: Dict[str, Any],
        question: str,
        metrics_data: Optional[Dict[str, Any]] = None,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """
        Call the debug_trace tool on MCP server

        Args:
            trace_data: OpenTelemetry trace data (dict with spans)
            question: User question about the trace
            metrics_data: Optional GPU metrics data
            hf_token: HuggingFace API token
            gemini_api_key: Google Gemini API key

        Returns:
            AI-generated answer to the trace question
        """
        try:
            args = {
                "trace_data": trace_data,
                "question": question
            }

            if metrics_data:
                args["metrics_data"] = metrics_data
            if hf_token:
                args["hf_token"] = hf_token
            if gemini_api_key:
                args["gemini_api_key"] = gemini_api_key

            result = await self._call_tool_with_retry("debug_trace", args)

            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No answer generated"

        except Exception as e:
            return f"❌ Error calling debug_trace: {str(e)}"

    async def estimate_cost(
        self,
        model: str,
        agent_type: str = "both",
        num_tests: int = 100,
        hardware: Optional[str] = None,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """
        Call the estimate_cost tool on MCP server

        Args:
            model: Model name (e.g., 'openai/gpt-4', 'meta-llama/Llama-3.1-8B')
            agent_type: Agent type (tool, code, both)
            num_tests: Number of tests to run
            hardware: Hardware type (cpu, gpu_a10, gpu_h200)
            hf_token: HuggingFace API token
            gemini_api_key: Google Gemini API key

        Returns:
            Cost estimation with breakdown
        """
        try:
            args = {
                "model": model,
                "agent_type": agent_type,
                "num_tests": num_tests
            }

            if hardware:
                args["hardware"] = hardware
            if hf_token:
                args["hf_token"] = hf_token
            if gemini_api_key:
                args["gemini_api_key"] = gemini_api_key

            result = await self._call_tool_with_retry("estimate_cost", args)

            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No estimation generated"

        except Exception as e:
            return f"❌ Error calling estimate_cost: {str(e)}"

    async def compare_runs(
        self,
        run_data_list: List[Dict[str, Any]],
        focus_metrics: Optional[List[str]] = None,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """
        Call the compare_runs tool on MCP server

        Args:
            run_data_list: List of run data dicts from leaderboard
            focus_metrics: List of metrics to focus on
            hf_token: HuggingFace API token
            gemini_api_key: Google Gemini API key

        Returns:
            AI-generated comparison analysis
        """
        try:
            args = {
                "run_data_list": run_data_list
            }

            if focus_metrics:
                args["focus_metrics"] = focus_metrics
            if hf_token:
                args["hf_token"] = hf_token
            if gemini_api_key:
                args["gemini_api_key"] = gemini_api_key

            result = await self._call_tool_with_retry("compare_runs", args)

            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No comparison generated"

        except Exception as e:
            return f"❌ Error calling compare_runs: {str(e)}"

    async def analyze_results(
        self,
        results_data: List[Dict[str, Any]],
        analysis_focus: str = "optimization",
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """
        Call the analyze_results tool on MCP server

        Args:
            results_data: List of test case results
            analysis_focus: Focus area (optimization, failures, performance, cost)
            hf_token: HuggingFace API token
            gemini_api_key: Google Gemini API key

        Returns:
            AI-generated results analysis with recommendations
        """
        try:
            args = {
                "results_data": results_data,
                "analysis_focus": analysis_focus
            }

            if hf_token:
                args["hf_token"] = hf_token
            if gemini_api_key:
                args["gemini_api_key"] = gemini_api_key

            result = await self._call_tool_with_retry("analyze_results", args)

            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No analysis generated"

        except Exception as e:
            return f"❌ Error calling analyze_results: {str(e)}"

    async def get_dataset_info(
        self,
        dataset_repo: str,
        hf_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """
        Call the get_dataset tool on MCP server (resource)

        Args:
            dataset_repo: HuggingFace dataset repo
            hf_token: HuggingFace API token
            gemini_api_key: Google Gemini API key

        Returns:
            Dataset information and structure
        """
        try:
            args = {
                "dataset_repo": dataset_repo
            }

            if hf_token:
                args["hf_token"] = hf_token
            if gemini_api_key:
                args["gemini_api_key"] = gemini_api_key

            result = await self._call_tool_with_retry("get_dataset", args)

            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No dataset info generated"

        except Exception as e:
            return f"❌ Error calling get_dataset: {str(e)}"

    async def _cleanup_connections(self):
        """Internal helper to clean up connections"""
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                print(f"⚠️ Error closing session context: {e}")
            self._session_context = None
            self.session = None

        if self._sse_context:
            try:
                await self._sse_context.__aexit__(None, None, None)
            except Exception as e:
                print(f"⚠️ Error closing SSE context: {e}")
            self._sse_context = None

        self._initialized = False

    async def close(self):
        """Close the MCP client session"""
        await self._cleanup_connections()


# Singleton instance for use across the app
_mcp_client_instance: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create the global MCP client instance"""
    global _mcp_client_instance
    if _mcp_client_instance is None:
        _mcp_client_instance = MCPClient()
    return _mcp_client_instance
