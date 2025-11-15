"""
Generate sample metrics data in OpenTelemetry resourceMetrics format.
This simulates what SMOLTRACE would produce for GPU and API evaluation runs.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path


def generate_gpu_sample_metrics(
    run_id: str = "run_002_llama31",
    duration_seconds: int = 120,
    interval_seconds: int = 10
):
    """
    Generate sample GPU metrics data for a GPU model run.

    Args:
        run_id: Run identifier
        duration_seconds: Total duration of simulated run
        interval_seconds: Interval between data points

    Returns:
        Dict in OpenTelemetry resourceMetrics format
    """

    start_time = datetime.now()
    num_points = duration_seconds // interval_seconds

    # Generate time-series data points
    utilization_points = []
    memory_points = []
    temperature_points = []
    power_points = []
    co2_points = []

    cumulative_co2 = 0.0

    for i in range(num_points):
        timestamp = start_time + timedelta(seconds=i * interval_seconds)
        time_unix_nano = str(int(timestamp.timestamp() * 1e9))

        # Simulate realistic GPU metrics with some variation
        # Pattern: Higher utilization during inference, lower during idle
        utilization = 45 + (i % 5) * 10 + (i % 2) * 5  # 45-70%
        memory = 4096 + i * 100  # Gradually increasing memory usage
        temperature = 70 + (i % 6) * 2  # 70-80°C
        power = 250 + (i % 7) * 30  # 250-400W

        # Cumulative CO2 (monotonic increasing)
        # Rough estimate: power (W) * time (h) * carbon intensity (g/kWh)
        delta_co2 = (power / 1000.0) * (interval_seconds / 3600.0) * 400  # 400g/kWh assumed
        cumulative_co2 += delta_co2

        utilization_points.append({
            "attributes": [
                {"key": "gpu_id", "value": {"stringValue": "0"}},
                {"key": "gpu_name", "value": {"stringValue": "NVIDIA H200"}}
            ],
            "timeUnixNano": time_unix_nano,
            "asInt": str(utilization)
        })

        memory_points.append({
            "attributes": [
                {"key": "gpu_id", "value": {"stringValue": "0"}},
                {"key": "gpu_name", "value": {"stringValue": "NVIDIA H200"}}
            ],
            "timeUnixNano": time_unix_nano,
            "asDouble": float(memory)
        })

        temperature_points.append({
            "attributes": [
                {"key": "gpu_id", "value": {"stringValue": "0"}},
                {"key": "gpu_name", "value": {"stringValue": "NVIDIA H200"}}
            ],
            "timeUnixNano": time_unix_nano,
            "asInt": str(temperature)
        })

        power_points.append({
            "attributes": [
                {"key": "gpu_id", "value": {"stringValue": "0"}},
                {"key": "gpu_name", "value": {"stringValue": "NVIDIA H200"}}
            ],
            "timeUnixNano": time_unix_nano,
            "asDouble": float(power)
        })

        co2_points.append({
            "attributes": [
                {"key": "gpu_id", "value": {"stringValue": "0"}}
            ],
            "timeUnixNano": time_unix_nano,
            "asDouble": cumulative_co2
        })

    # Construct resourceMetrics structure (OpenTelemetry format)
    metrics_data = {
        "run_id": run_id,
        "resourceMetrics": [{
            "resource": {
                "attributes": [
                    {"key": "telemetry.sdk.language", "value": {"stringValue": "python"}},
                    {"key": "telemetry.sdk.name", "value": {"stringValue": "opentelemetry"}},
                    {"key": "telemetry.sdk.version", "value": {"stringValue": "1.37.0"}},
                    {"key": "service.name", "value": {"stringValue": "smoltrace-eval"}},
                    {"key": "run.id", "value": {"stringValue": run_id}}
                ]
            },
            "scopeMetrics": [{
                "scope": {"name": "genai.gpu", "version": None},
                "metrics": [
                    {
                        "name": "gen_ai.gpu.utilization",
                        "description": "GPU utilization percentage",
                        "unit": "%",
                        "gauge": {"dataPoints": utilization_points}
                    },
                    {
                        "name": "gen_ai.gpu.memory.used",
                        "description": "GPU memory used in MiB",
                        "unit": "MiB",
                        "gauge": {"dataPoints": memory_points}
                    },
                    {
                        "name": "gen_ai.gpu.temperature",
                        "description": "GPU temperature in Celsius",
                        "unit": "Cel",
                        "gauge": {"dataPoints": temperature_points}
                    },
                    {
                        "name": "gen_ai.gpu.power",
                        "description": "GPU power consumption in Watts",
                        "unit": "W",
                        "gauge": {"dataPoints": power_points}
                    },
                    {
                        "name": "gen_ai.co2.emissions",
                        "description": "Cumulative CO2 equivalent emissions in grams",
                        "unit": "gCO2e",
                        "sum": {
                            "dataPoints": co2_points,
                            "aggregationTemporality": 2,  # CUMULATIVE
                            "isMonotonic": True
                        }
                    }
                ]
            }]
        }]
    }

    return metrics_data


def generate_api_sample_metrics(run_id: str = "run_001_gpt4"):
    """
    Generate minimal sample metrics for an API model run (no GPU).

    Args:
        run_id: Run identifier

    Returns:
        Dict with empty resourceMetrics (API models don't have GPU)
    """
    return {
        "run_id": run_id,
        "resourceMetrics": []
    }


if __name__ == "__main__":
    # Create output directory
    output_dir = Path(__file__).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating sample metrics data...")

    # Generate GPU model metrics (Llama 3.1 on H200)
    gpu_metrics = generate_gpu_sample_metrics(
        run_id="run_002_llama31",
        duration_seconds=120,
        interval_seconds=10
    )

    output_file = output_dir / "metrics_llama31.json"
    with open(output_file, "w") as f:
        json.dump(gpu_metrics, f, indent=2)
    print(f"[OK] Generated GPU metrics: {output_file}")
    print(f"   - {len(gpu_metrics['resourceMetrics'][0]['scopeMetrics'][0]['metrics'])} metric types")
    print(f"   - {len(gpu_metrics['resourceMetrics'][0]['scopeMetrics'][0]['metrics'][0]['gauge']['dataPoints'])} data points per metric")

    # Generate API model metrics (GPT-4 - no GPU)
    api_metrics = generate_api_sample_metrics(run_id="run_001_gpt4")

    output_file = output_dir / "metrics_gpt4.json"
    with open(output_file, "w") as f:
        json.dump(api_metrics, f, indent=2)
    print(f"[OK] Generated API metrics: {output_file}")
    print(f"   - Empty resourceMetrics (API model has no GPU)")

    print("\n[SUCCESS] Sample metrics data generation complete!")
    print("\nYou can now test the visualization with:")
    print("  python gpu_metrics_with_time_series.py")
