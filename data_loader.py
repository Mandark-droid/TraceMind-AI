"""
Data Loader for MockTraceMind
Supports loading from both JSON files and HuggingFace datasets
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
import pandas as pd
from datasets import load_dataset
from huggingface_hub import HfApi
import gradio as gr


DataSource = Literal["json", "huggingface", "both"]


class DataLoader:
    """
    Unified data loader for TraceMind

    Supports:
    - Local JSON files
    - HuggingFace datasets
    - Automatic fallback between sources
    - Caching for performance
    """

    def __init__(
        self,
        data_source: DataSource = "both",
        json_data_path: Optional[str] = None,
        leaderboard_dataset: Optional[str] = None,
        hf_token: Optional[str] = None,
        use_streaming: bool = False
    ):
        self.data_source = data_source
        self.json_data_path = Path(json_data_path or os.getenv("JSON_DATA_PATH", "./sample_data"))
        self.leaderboard_dataset = leaderboard_dataset or os.getenv("LEADERBOARD_DATASET", "kshitijthakkar/smoltrace-leaderboard")
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.use_streaming = use_streaming

        # Cache
        self._cache: Dict[str, Any] = {}
        self.hf_api = HfApi(token=self.hf_token) if self.hf_token else None

    def load_leaderboard(self) -> pd.DataFrame:
        """
        Load leaderboard dataset

        Returns:
            DataFrame with leaderboard data
        """
        cache_key = "leaderboard"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try HuggingFace first
        if self.data_source in ["huggingface", "both"]:
            try:
                df = self._load_leaderboard_from_hf()
                self._cache[cache_key] = df
                return df
            except Exception as e:
                print(f"Failed to load from HuggingFace: {e}")
                if self.data_source == "huggingface":
                    raise

        # Fallback to JSON
        if self.data_source in ["json", "both"]:
            try:
                df = self._load_leaderboard_from_json()
                self._cache[cache_key] = df
                return df
            except Exception as e:
                print(f"Failed to load from JSON: {e}")
                raise

        raise ValueError("No valid data source available")

    def _load_leaderboard_from_hf(self) -> pd.DataFrame:
        """Load leaderboard from HuggingFace dataset with optional streaming"""
        try:
            if self.use_streaming:
                print("[INFO] Loading leaderboard with streaming...")
                # Load with streaming for faster initial response
                ds = load_dataset(
                    self.leaderboard_dataset,
                    split="train",
                    token=self.hf_token,
                    streaming=True
                )
                # Convert streamed data to list of dicts, then to DataFrame
                data = list(ds)
                df = pd.DataFrame(data)
                print(f"[OK] Streamed leaderboard from HuggingFace: {len(df)} rows")
            else:
                # Traditional full download
                ds = load_dataset(self.leaderboard_dataset, split="train", token=self.hf_token)
                df = ds.to_pandas()
                print(f"[OK] Loaded leaderboard from HuggingFace: {len(df)} rows")
            return df
        except Exception as e:
            print(f"[ERROR] Loading from HuggingFace: {e}")
            raise

    def _load_leaderboard_from_json(self) -> pd.DataFrame:
        """Load leaderboard from local JSON file"""
        json_path = self.json_data_path / "leaderboard.json"

        if not json_path.exists():
            raise FileNotFoundError(f"Leaderboard JSON not found: {json_path}")

        with open(json_path, "r") as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        print(f"[OK] Loaded leaderboard from JSON: {len(df)} rows")
        return df

    def load_results(self, results_dataset: str) -> pd.DataFrame:
        """
        Load results dataset for a specific run

        Args:
            results_dataset: Dataset reference (e.g., "user/agent-results-gpt4")

        Returns:
            DataFrame with test case results
        """
        cache_key = f"results_{results_dataset}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try HuggingFace first
        if self.data_source in ["huggingface", "both"]:
            try:
                df = self._load_results_from_hf(results_dataset)
                self._cache[cache_key] = df
                return df
            except Exception as e:
                print(f"Failed to load results from HuggingFace: {e}")
                if self.data_source == "huggingface":
                    raise

        # Fallback to JSON
        if self.data_source in ["json", "both"]:
            try:
                df = self._load_results_from_json(results_dataset)
                self._cache[cache_key] = df
                return df
            except Exception as e:
                print(f"Failed to load results from JSON: {e}")
                raise

        raise ValueError("No valid data source available")

    def _load_results_from_hf(self, dataset_id: str) -> pd.DataFrame:
        """Load results from HuggingFace dataset with optional streaming"""
        if self.use_streaming:
            print(f"[INFO] Streaming results from {dataset_id}...")
            ds = load_dataset(dataset_id, split="train", token=self.hf_token, streaming=True)
            data = list(ds)
            df = pd.DataFrame(data)
            print(f"[OK] Streamed results from HuggingFace: {len(df)} rows")
        else:
            ds = load_dataset(dataset_id, split="train", token=self.hf_token)
            df = ds.to_pandas()
            print(f"[OK] Loaded results from HuggingFace: {len(df)} rows")
        return df

    def _load_results_from_json(self, dataset_id: str) -> pd.DataFrame:
        """Load results from local JSON file"""
        # Extract filename from dataset ID (e.g., "user/agent-results-gpt4" -> "results_gpt4.json")
        filename = dataset_id.split("/")[-1].replace("agent-", "") + ".json"
        json_path = self.json_data_path / filename

        if not json_path.exists():
            raise FileNotFoundError(f"Results JSON not found: {json_path}")

        with open(json_path, "r") as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        print(f"[OK] Loaded results from JSON: {len(df)} rows")
        return df

    def load_traces(self, traces_dataset: str) -> List[Dict[str, Any]]:
        """
        Load traces dataset for a specific run

        Args:
            traces_dataset: Dataset reference (e.g., "user/agent-traces-gpt4")

        Returns:
            List of trace objects (OpenTelemetry format)
        """
        cache_key = f"traces_{traces_dataset}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try HuggingFace first
        if self.data_source in ["huggingface", "both"]:
            try:
                traces = self._load_traces_from_hf(traces_dataset)
                self._cache[cache_key] = traces
                return traces
            except Exception as e:
                print(f"Failed to load traces from HuggingFace: {e}")
                if self.data_source == "huggingface":
                    raise

        # Fallback to JSON
        if self.data_source in ["json", "both"]:
            try:
                traces = self._load_traces_from_json(traces_dataset)
                self._cache[cache_key] = traces
                return traces
            except Exception as e:
                print(f"Failed to load traces from JSON: {e}")
                raise

        raise ValueError("No valid data source available")

    def _load_traces_from_hf(self, dataset_id: str) -> List[Dict[str, Any]]:
        """Load traces from HuggingFace dataset with optional streaming"""
        if self.use_streaming:
            print(f"[INFO] Streaming traces from {dataset_id}...")
            ds = load_dataset(dataset_id, split="train", token=self.hf_token, streaming=True)
            traces = list(ds)
            print(f"[OK] Streamed traces from HuggingFace: {len(traces)} traces")
        else:
            ds = load_dataset(dataset_id, split="train", token=self.hf_token)
            traces = ds.to_pandas().to_dict("records")
            print(f"[OK] Loaded traces from HuggingFace: {len(traces)} traces")
        return traces

    def _load_traces_from_json(self, dataset_id: str) -> List[Dict[str, Any]]:
        """Load traces from local JSON file"""
        filename = dataset_id.split("/")[-1].replace("agent-", "") + ".json"
        json_path = self.json_data_path / filename

        if not json_path.exists():
            raise FileNotFoundError(f"Traces JSON not found: {json_path}")

        with open(json_path, "r") as f:
            data = json.load(f)

        print(f"[OK] Loaded traces from JSON: {len(data)} traces")
        return data

    def load_metrics(self, metrics_dataset: str) -> pd.DataFrame:
        """
        Load metrics dataset for a specific run (GPU metrics)

        Args:
            metrics_dataset: Dataset reference (e.g., "user/agent-metrics-gpt4")

        Returns:
            DataFrame with GPU metrics in flat format (columns: timestamp, gpu_utilization_percent, etc.)
        """
        cache_key = f"metrics_{metrics_dataset}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try HuggingFace first
        if self.data_source in ["huggingface", "both"]:
            try:
                metrics = self._load_metrics_from_hf(metrics_dataset)
                self._cache[cache_key] = metrics
                return metrics
            except Exception as e:
                print(f"Failed to load metrics from HuggingFace: {e}")
                if self.data_source == "huggingface":
                    raise

        # Fallback to JSON
        if self.data_source in ["json", "both"]:
            try:
                metrics = self._load_metrics_from_json(metrics_dataset)
                self._cache[cache_key] = metrics
                return metrics
            except Exception as e:
                print(f"Failed to load metrics from JSON: {e}")
                # Metrics might not exist for API models, don't raise
                print("⚠️ No metrics available (expected for API models)")
                return pd.DataFrame()

        return pd.DataFrame()

    def _load_metrics_from_hf(self, dataset_id: str) -> pd.DataFrame:
        """Load metrics from HuggingFace dataset (flat format) with optional streaming"""
        if self.use_streaming:
            print(f"[INFO] Streaming metrics from {dataset_id}...")
            ds = load_dataset(dataset_id, split="train", token=self.hf_token, streaming=True)
            data = list(ds)
            df = pd.DataFrame(data)
            print(f"[OK] Streamed metrics from HuggingFace: {len(df)} rows")
        else:
            ds = load_dataset(dataset_id, split="train", token=self.hf_token)
            df = ds.to_pandas()
            print(f"[OK] Loaded metrics from HuggingFace: {len(df)} rows")

        # Convert timestamp strings to datetime if needed
        if 'timestamp' in df.columns and not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        if not df.empty:
            print(f"   Columns: {list(df.columns)}")
        return df

    def _load_metrics_from_json(self, dataset_id: str) -> pd.DataFrame:
        """Load metrics from local JSON file"""
        filename = dataset_id.split("/")[-1].replace("agent-", "") + ".json"
        json_path = self.json_data_path / filename

        if not json_path.exists():
            # Metrics might not exist for API models
            return pd.DataFrame()

        with open(json_path, "r") as f:
            data = json.load(f)

        # Check if it's OpenTelemetry format (nested) or flat format
        if isinstance(data, dict) and 'resourceMetrics' in data:
            # Legacy OpenTelemetry format - convert to flat format
            df = self._convert_otel_to_flat(data)
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame()

        # Convert timestamp strings to datetime if needed
        if 'timestamp' in df.columns and not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        print(f"[OK] Loaded metrics from JSON: {len(df)} rows")
        return df

    def _convert_otel_to_flat(self, otel_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert OpenTelemetry resourceMetrics format to flat DataFrame"""
        rows = []

        for resource_metric in otel_data.get('resourceMetrics', []):
            for scope_metric in resource_metric.get('scopeMetrics', []):
                for metric in scope_metric.get('metrics', []):
                    metric_name = metric.get('name', '')

                    # Handle gauge metrics
                    if 'gauge' in metric:
                        for data_point in metric['gauge'].get('dataPoints', []):
                            row = self._extract_data_point(metric_name, data_point, metric.get('unit', ''))
                            if row:
                                rows.append(row)

                    # Handle sum metrics (like CO2)
                    elif 'sum' in metric:
                        for data_point in metric['sum'].get('dataPoints', []):
                            row = self._extract_data_point(metric_name, data_point, metric.get('unit', ''))
                            if row:
                                rows.append(row)

        return pd.DataFrame(rows)

    def _extract_data_point(self, metric_name: str, data_point: Dict, unit: str) -> Optional[Dict[str, Any]]:
        """Extract a single data point from OpenTelemetry format to flat row"""
        # Get GPU attributes
        gpu_id = None
        gpu_name = None
        for attr in data_point.get('attributes', []):
            if attr.get('key') == 'gpu_id':
                gpu_id = attr.get('value', {}).get('stringValue', '')
            elif attr.get('key') == 'gpu_name':
                gpu_name = attr.get('value', {}).get('stringValue', '')

        # Get value
        value = None
        if 'asInt' in data_point and data_point['asInt'] is not None:
            value = int(data_point['asInt'])
        elif 'asDouble' in data_point and data_point['asDouble'] is not None:
            value = float(data_point['asDouble'])

        # Get timestamp
        timestamp_nano = data_point.get('timeUnixNano', '')
        if timestamp_nano:
            timestamp_sec = int(timestamp_nano) / 1e9
            timestamp = pd.to_datetime(timestamp_sec, unit='s')
        else:
            timestamp = None

        # Map metric names to column names
        metric_col_map = {
            'gen_ai.gpu.utilization': 'gpu_utilization_percent',
            'gen_ai.gpu.memory.used': 'gpu_memory_used_mib',
            'gen_ai.gpu.temperature': 'gpu_temperature_celsius',
            'gen_ai.gpu.power': 'gpu_power_watts',
            'gen_ai.co2.emissions': 'co2_emissions_gco2e'
        }

        return {
            'timestamp': timestamp,
            'timestamp_unix_nano': timestamp_nano,
            'gpu_id': gpu_id,
            'gpu_name': gpu_name,
            'metric_name': metric_name,
            'value': value,
            'unit': unit
        }

    def get_trace_by_id(self, traces_dataset: str, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific trace by ID

        Args:
            traces_dataset: Dataset reference
            trace_id: Trace ID to find

        Returns:
            Trace object or None if not found
        """
        traces = self.load_traces(traces_dataset)

        for trace in traces:
            if trace.get("trace_id") == trace_id or trace.get("traceId") == trace_id:
                # Ensure spans is a proper list (not numpy array or pandas Series)
                if "spans" in trace:
                    spans = trace["spans"]
                    if hasattr(spans, 'tolist'):
                        trace["spans"] = spans.tolist()
                    elif not isinstance(spans, list):
                        trace["spans"] = list(spans) if spans is not None else []

                return trace

        return None

    def clear_cache(self) -> None:
        """Clear the internal cache"""
        self._cache.clear()
        print("[OK] Cache cleared")

    def refresh_leaderboard(self) -> pd.DataFrame:
        """Refresh leaderboard data (clear cache and reload)"""
        if "leaderboard" in self._cache:
            del self._cache["leaderboard"]
        return self.load_leaderboard()


def create_data_loader_from_env() -> DataLoader:
    """
    Create DataLoader instance from environment variables

    Returns:
        Configured DataLoader instance
    """
    data_source = os.getenv("DATA_SOURCE", "both")
    use_streaming = os.getenv("USE_STREAMING", "false").lower() == "true"

    return DataLoader(
        data_source=data_source,
        json_data_path=os.getenv("JSON_DATA_PATH"),
        leaderboard_dataset=os.getenv("LEADERBOARD_DATASET"),
        hf_token=os.getenv("HF_TOKEN"),
        use_streaming=use_streaming
    )
