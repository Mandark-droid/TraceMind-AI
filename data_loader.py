"""
Data Loader for TraceMind-AI
Loads real data from HuggingFace datasets (not mock data)
"""

import os
from typing import Optional, Dict, Any, List
import pandas as pd
from datasets import load_dataset
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TraceMindDataLoader:
    """Loads evaluation data from HuggingFace datasets"""

    def __init__(
        self,
        leaderboard_repo: Optional[str] = None,
        hf_token: Optional[str] = None
    ):
        """
        Initialize data loader

        Args:
            leaderboard_repo: HuggingFace dataset repo for leaderboard
            hf_token: HuggingFace API token for private datasets
        """
        self.leaderboard_repo = leaderboard_repo or os.getenv(
            'LEADERBOARD_REPO',
            'kshitijthakkar/smoltrace-leaderboard'
        )
        self.hf_token = hf_token or os.getenv('HF_TOKEN')

        # Cache for loaded datasets
        self._leaderboard_df: Optional[pd.DataFrame] = None
        self._results_cache: Dict[str, pd.DataFrame] = {}
        self._traces_cache: Dict[str, List[Dict]] = {}
        self._metrics_cache: Dict[str, Dict] = {}

    def load_leaderboard(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load leaderboard dataset from HuggingFace

        Args:
            force_refresh: Force reload from HF (ignore cache)

        Returns:
            DataFrame with leaderboard data
        """
        if self._leaderboard_df is not None and not force_refresh:
            return self._leaderboard_df

        try:
            print(f"📊 Loading leaderboard from {self.leaderboard_repo}...")

            # Load dataset from HuggingFace
            dataset = load_dataset(
                self.leaderboard_repo,
                split='train',
                token=self.hf_token
            )

            # Convert to DataFrame
            self._leaderboard_df = pd.DataFrame(dataset)

            print(f"✅ Loaded {len(self._leaderboard_df)} evaluation runs")
            return self._leaderboard_df

        except Exception as e:
            print(f"❌ Error loading leaderboard: {e}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'run_id', 'model', 'agent_type', 'provider',
                'success_rate', 'total_tests', 'successful_tests', 'failed_tests',
                'avg_steps', 'avg_duration_ms', 'total_duration_ms',
                'total_tokens', 'avg_tokens_per_test', 'total_cost_usd', 'avg_cost_per_test_usd',
                'co2_emissions_g', 'gpu_utilization_avg', 'gpu_memory_max_mib',
                'results_dataset', 'traces_dataset', 'metrics_dataset',
                'timestamp', 'submitted_by', 'hf_job_id', 'job_type',
                'dataset_used', 'smoltrace_version'
            ])

    def load_results(self, results_repo: str, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load results dataset for a specific run

        Args:
            results_repo: HuggingFace dataset repo for results (e.g., 'user/agent-results-gpt4')
            force_refresh: Force reload from HF

        Returns:
            DataFrame with test case results
        """
        if results_repo in self._results_cache and not force_refresh:
            return self._results_cache[results_repo]

        try:
            print(f"📊 Loading results from {results_repo}...")

            dataset = load_dataset(
                results_repo,
                split='train',
                token=self.hf_token
            )

            df = pd.DataFrame(dataset)
            self._results_cache[results_repo] = df

            print(f"✅ Loaded {len(df)} test cases")
            return df

        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return pd.DataFrame(columns=[
                'run_id', 'task_id', 'test_index',
                'prompt', 'expected_tool', 'difficulty', 'category',
                'success', 'response', 'tool_called', 'tool_correct',
                'expected_keywords', 'keywords_matched',
                'execution_time_ms', 'total_tokens', 'prompt_tokens', 'completion_tokens', 'cost_usd',
                'trace_id', 'start_time', 'end_time', 'start_time_unix_nano', 'end_time_unix_nano',
                'error', 'error_type'
            ])

    def load_traces(self, traces_repo: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Load traces dataset for a specific run

        Args:
            traces_repo: HuggingFace dataset repo for traces
            force_refresh: Force reload from HF

        Returns:
            List of trace dictionaries (OpenTelemetry format)
        """
        if traces_repo in self._traces_cache and not force_refresh:
            return self._traces_cache[traces_repo]

        try:
            print(f"🔍 Loading traces from {traces_repo}...")

            dataset = load_dataset(
                traces_repo,
                split='train',
                token=self.hf_token
            )

            # Convert to list of dicts
            traces = [dict(item) for item in dataset]
            self._traces_cache[traces_repo] = traces

            print(f"✅ Loaded {len(traces)} traces")
            return traces

        except Exception as e:
            print(f"❌ Error loading traces: {e}")
            return []

    def load_metrics(self, metrics_repo: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Load GPU metrics dataset for a specific run

        Args:
            metrics_repo: HuggingFace dataset repo for metrics
            force_refresh: Force reload from HF

        Returns:
            Metrics data (OpenTelemetry metrics format)
        """
        if metrics_repo in self._metrics_cache and not force_refresh:
            return self._metrics_cache[metrics_repo]

        try:
            print(f"📈 Loading metrics from {metrics_repo}...")

            dataset = load_dataset(
                metrics_repo,
                split='train',
                token=self.hf_token
            )

            # Assume metrics dataset has one row with all metrics
            if len(dataset) > 0:
                metrics = dict(dataset[0])
                self._metrics_cache[metrics_repo] = metrics
                print(f"✅ Loaded metrics data")
                return metrics
            else:
                print(f"⚠️ No metrics data found")
                return {}

        except Exception as e:
            print(f"❌ Error loading metrics: {e}")
            return {}

    def get_run_by_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific run from the leaderboard by run_id

        Args:
            run_id: Run ID to fetch

        Returns:
            Run data as dict, or None if not found
        """
        leaderboard_df = self.load_leaderboard()

        run_rows = leaderboard_df[leaderboard_df['run_id'] == run_id]

        if len(run_rows) > 0:
            return run_rows.iloc[0].to_dict()
        else:
            return None

    def get_trace_by_id(self, traces_repo: str, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific trace by trace_id

        Args:
            traces_repo: HuggingFace dataset repo for traces
            trace_id: Trace ID to fetch

        Returns:
            Trace data as dict, or None if not found
        """
        traces = self.load_traces(traces_repo)

        for trace in traces:
            if trace.get('trace_id') == trace_id or trace.get('traceId') == trace_id:
                return trace

        return None

    def clear_cache(self):
        """Clear all cached data"""
        self._leaderboard_df = None
        self._results_cache.clear()
        self._traces_cache.clear()
        self._metrics_cache.clear()
        print("🧹 Cache cleared")


def create_data_loader_from_env() -> TraceMindDataLoader:
    """
    Create a data loader using environment variables

    Returns:
        TraceMindDataLoader instance
    """
    return TraceMindDataLoader(
        leaderboard_repo=os.getenv('LEADERBOARD_REPO'),
        hf_token=os.getenv('HF_TOKEN')
    )
