"""
Leaderboard HTML Table Generator
Creates styled HTML tables for the leaderboard view
"""

import pandas as pd
from typing import Optional
from .metric_displays import (
    get_rank_badge,
    get_success_rate_bar,
    get_gpu_utilization_bar,
    get_provider_badge,
    get_agent_type_badge,
    get_hardware_badge,
    format_cost,
    format_duration,
    get_tooltip_icon
)


def generate_leaderboard_html(
    df: pd.DataFrame,
    sort_by: str = "success_rate",
    ascending: bool = False
) -> str:
    """
    Generate styled HTML table for leaderboard

    Args:
        df: Leaderboard DataFrame
        sort_by: Column to sort by
        ascending: Sort order (False = descending)

    Returns:
        HTML string with complete styled table

    Expected DataFrame columns:
        - model (str): Model name
        - agent_type (str): tool, code, or both
        - provider (str): litellm or transformers
        - success_rate (float): 0-100
        - total_tests (int): Number of tests
        - avg_duration_ms (float): Average duration
        - total_cost_usd (float): Total cost
        - co2_emissions_g (float): CO2 emissions
        - gpu_utilization_avg (float, optional): GPU utilization %
        - submitted_by (str): Username
    """

    # Sort dataframe
    df_sorted = df.sort_values(by=sort_by, ascending=ascending).reset_index(drop=True)

    # Start HTML with embedded CSS
    html = """
    <style>
    /* Leaderboard Table Styles */
    .tm-leaderboard-container {
        background: #F8FAFC;  /* Light background for better readability */
        border-radius: 16px;
        overflow-x: auto;  /* Enable horizontal scrolling */
        overflow-y: visible;
        border: 1px solid rgba(203, 213, 225, 0.8);
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 100%;
    }

    /* Custom scrollbar styling */
    .tm-leaderboard-container::-webkit-scrollbar {
        height: 8px;
    }

    .tm-leaderboard-container::-webkit-scrollbar-track {
        background: #E2E8F0;
        border-radius: 4px;
    }

    .tm-leaderboard-container::-webkit-scrollbar-thumb {
        background: #94A3B8;
        border-radius: 4px;
    }

    .tm-leaderboard-container::-webkit-scrollbar-thumb:hover {
        background: #64748B;
    }

    .tm-leaderboard-table {
        width: 100%;
        min-width: 1650px;  /* Reduced from 1800px after combining columns */
        border-collapse: collapse;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: #FFFFFF;  /* White background */
        color: #0F172A;  /* Dark text for maximum contrast */
    }

    .tm-leaderboard-table thead {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);  /* Vibrant indigo gradient */
        position: sticky;
        top: 0;
        z-index: 10;
        backdrop-filter: blur(10px);
    }

    .tm-leaderboard-table th {
        padding: 16px 12px;
        text-align: left;
        font-weight: 600;
        color: #FFFFFF;  /* Pure white for headers - good contrast */
        border-bottom: 2px solid #4338CA;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        white-space: nowrap;
    }

    .tm-leaderboard-table td {
        padding: 14px 12px;
        border-bottom: 1px solid rgba(226, 232, 240, 0.8);
        color: #1E293B;  /* Dark text for cells */
        font-size: 14px;
        vertical-align: middle;
    }

    .tm-leaderboard-table tbody tr {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }

    .tm-leaderboard-table tbody tr:hover {
        background: rgba(99, 102, 241, 0.08) !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.15),
                    inset 0 0 15px rgba(99, 102, 241, 0.05);
        transform: scale(1.002);
    }

    .tm-leaderboard-table tbody tr:nth-child(even) {
        background: rgba(241, 245, 249, 0.6);  /* Light stripe */
    }

    .tm-model-name {
        font-weight: 600;
        color: #000000 !important;  /* Pure black - readable in all themes */
        font-size: 15px;
        transition: color 0.2s ease;
    }

    .tm-leaderboard-table tr:hover .tm-model-name {
        color: #4F46E5 !important;  /* Indigo on hover */
    }

    .tm-numeric-cell {
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 13px;
        text-align: center;
        color: #000000 !important;  /* Pure black for numbers */
    }

    .tm-badge-cell {
        text-align: center;
    }

    .tm-run-id {
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 12px;
        color: #000000 !important;  /* Pure black - readable in all themes */
        cursor: pointer;
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .tm-run-id:hover {
        color: #4F46E5 !important;  /* Indigo on hover */
        text-decoration: underline;
    }

    .tm-text-cell {
        color: #000000 !important;  /* Pure black for all text */
        font-size: 0.9em;
    }

    /* Responsive Design */
    @media (max-width: 1024px) {
        .tm-leaderboard-table th,
        .tm-leaderboard-table td {
            padding: 10px 8px;
            font-size: 12px;
        }

        /* Hide less important columns on smaller screens */
        .tm-hide-mobile {
            display: none !important;
        }
    }

    @media (max-width: 768px) {
        .tm-leaderboard-table th:nth-child(n+7),
        .tm-leaderboard-table td:nth-child(n+7) {
            display: none !important;
        }

        .tm-model-name {
            font-size: 13px;
        }
    }

    @media (max-width: 480px) {
        /* Ultra-compact: Show only rank, model, and success rate */
        .tm-leaderboard-table th:nth-child(n+4),
        .tm-leaderboard-table td:nth-child(n+4) {
            display: none !important;
        }

        .tm-leaderboard-table th:nth-child(3),
        .tm-leaderboard-table td:nth-child(3) {
            display: table-cell !important;
        }
    }
    </style>

    <div class="tm-leaderboard-container">
        <table class="tm-leaderboard-table">
            <thead>
                <tr>
                    <th style="width: 60px;">Rank</th>
                    <th style="width: 110px;" title="Click to view detailed run information">Run ID</th>
                    <th style="min-width: 160px;">Model</th>
                    <th style="width: 80px;">Type</th>
                    <th style="width: 90px;">Provider</th>
                    <th style="width: 85px;" title="Hardware used for evaluation: GPU or CPU">Hardware</th>
                    <th style="width: 150px;" title="Percentage of test cases that passed (0-100%). Higher is better.">
                        Success Rate
                    </th>
                    <th style="width: 140px;" class="tm-numeric-cell" title="Tests: Total / Pass / Fail">
                        Tests (P/F)
                    </th>
                    <th style="width: 70px;" class="tm-numeric-cell" title="Average number of steps per test case.">
                        Steps
                    </th>
                    <th style="width: 100px;" class="tm-numeric-cell" title="Average time per test case. Lower is better.">
                        Duration
                    </th>
                    <th style="width: 90px;" class="tm-numeric-cell" title="Total tokens used across all tests.">
                        Tokens
                    </th>
                    <th style="width: 90px;" class="tm-numeric-cell" title="Total API + power costs in USD. Lower is better.">
                        Cost
                    </th>
                    <th style="width: 80px;" class="tm-numeric-cell tm-hide-mobile" title="Carbon footprint in grams of CO2 equivalent.">
                        CO2
                    </th>
                    <th style="width: 100px;" class="tm-hide-mobile" title="Average GPU usage during evaluation (0-100%). Only for GPU jobs.">
                        GPU Util
                    </th>
                    <th style="width: 100px;" class="tm-numeric-cell tm-hide-mobile" title="GPU memory usage (avg/max in MiB). Only for GPU jobs.">
                        GPU Mem
                    </th>
                    <th style="width: 100px;" class="tm-numeric-cell tm-hide-mobile" title="GPU temperature (avg/max in Celsius). Only for GPU jobs.">
                        GPU Temp
                    </th>
                    <th style="width: 100px;" class="tm-numeric-cell tm-hide-mobile" title="Average GPU power consumption in Watts. Only for GPU jobs.">
                        GPU Power
                    </th>
                    <th style="width: 140px;" class="tm-hide-mobile">Timestamp</th>
                    <th style="width: 110px;" class="tm-hide-mobile">Submitted By</th>
                </tr>
            </thead>
            <tbody>
    """

    # Generate table rows
    for idx, row in df_sorted.iterrows():
        rank = idx + 1

        # Get values with safe defaults
        model = row.get('model', 'Unknown')
        agent_type = row.get('agent_type', 'unknown')
        provider = row.get('provider', 'unknown')
        success_rate = row.get('success_rate', 0.0)
        total_tests = row.get('total_tests', 0)
        successful_tests = row.get('successful_tests', 0)
        failed_tests = row.get('failed_tests', 0)
        avg_steps = row.get('avg_steps', 0.0)
        avg_duration_ms = row.get('avg_duration_ms', 0.0)
        total_tokens = row.get('total_tokens', 0)
        total_cost_usd = row.get('total_cost_usd', 0.0)
        co2_emissions_g = row.get('co2_emissions_g', 0.0)
        gpu_utilization_avg = row.get('gpu_utilization_avg', None)
        gpu_memory_avg_mib = row.get('gpu_memory_avg_mib', None)
        gpu_memory_max_mib = row.get('gpu_memory_max_mib', None)
        gpu_temperature_avg = row.get('gpu_temperature_avg', None)
        gpu_temperature_max = row.get('gpu_temperature_max', None)
        gpu_power_avg_w = row.get('gpu_power_avg_w', None)
        timestamp = row.get('timestamp', '')
        submitted_by = row.get('submitted_by', 'Unknown')

        # Check if GPU job
        has_gpu = pd.notna(gpu_utilization_avg) and gpu_utilization_avg > 0

        # Format GPU utilization
        if has_gpu:
            gpu_display = get_gpu_utilization_bar(gpu_utilization_avg)
        else:
            gpu_display = '<span style="color: #94A3B8; font-size: 0.85em;">N/A</span>'

        # Format CO2
        if pd.notna(co2_emissions_g) and co2_emissions_g > 0:
            co2_display = f'<span style="font-family: monospace; font-size: 0.9em; color: #334155;">{co2_emissions_g:.2f}g</span>'
        else:
            co2_display = '<span style="color: #94A3B8; font-size: 0.85em;">N/A</span>'

        # Format GPU Memory
        if pd.notna(gpu_memory_avg_mib) and pd.notna(gpu_memory_max_mib):
            gpu_mem_display = f'<span style="font-family: monospace; font-size: 0.85em; color: #334155;">{gpu_memory_avg_mib:.0f}/{gpu_memory_max_mib:.0f}</span>'
        else:
            gpu_mem_display = '<span style="color: #94A3B8; font-size: 0.85em;">N/A</span>'

        # Format GPU Temperature
        if pd.notna(gpu_temperature_avg) and pd.notna(gpu_temperature_max):
            gpu_temp_display = f'<span style="font-family: monospace; font-size: 0.85em; color: #334155;">{gpu_temperature_avg:.0f}/{gpu_temperature_max:.0f}°C</span>'
        else:
            gpu_temp_display = '<span style="color: #94A3B8; font-size: 0.85em;">N/A</span>'

        # Format GPU Power
        if pd.notna(gpu_power_avg_w):
            gpu_power_display = f'<span style="font-family: monospace; font-size: 0.85em; color: #334155;">{gpu_power_avg_w:.1f}W</span>'
        else:
            gpu_power_display = '<span style="color: #94A3B8; font-size: 0.85em;">N/A</span>'

        # Format timestamp
        from datetime import datetime
        if pd.notna(timestamp):
            try:
                # Handle both string and Timestamp objects
                if isinstance(timestamp, pd.Timestamp):
                    timestamp_display = timestamp.strftime('%Y-%m-%d %H:%M')
                else:
                    dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                    timestamp_display = dt.strftime('%Y-%m-%d %H:%M')
            except Exception as e:
                timestamp_display = str(timestamp)[:16] if timestamp else 'N/A'
        else:
            timestamp_display = 'N/A'

        # Format Run ID (show first 8 characters)
        run_id = row.get('run_id', 'N/A')
        run_id_short = run_id[:8] + '...' if len(run_id) > 8 else run_id

        # Get dataset references
        results_dataset = row.get('results_dataset', '')
        traces_dataset = row.get('traces_dataset', '')
        metrics_dataset = row.get('metrics_dataset', '')

        html += f"""
            <tr
                data-run-id="{run_id}"
                data-rank="{rank}"
                data-model="{model}"
                data-agent-type="{agent_type}"
                data-provider="{provider}"
                data-success-rate="{success_rate}"
                data-total-tests="{total_tests}"
                data-successful-tests="{successful_tests}"
                data-failed-tests="{failed_tests}"
                data-avg-steps="{avg_steps}"
                data-avg-duration-ms="{avg_duration_ms}"
                data-total-tokens="{total_tokens}"
                data-total-cost-usd="{total_cost_usd}"
                data-co2-emissions-g="{co2_emissions_g}"
                data-gpu-utilization-avg="{gpu_utilization_avg if pd.notna(gpu_utilization_avg) else 'None'}"
                data-gpu-memory-avg-mib="{gpu_memory_avg_mib if pd.notna(gpu_memory_avg_mib) else 'None'}"
                data-gpu-memory-max-mib="{gpu_memory_max_mib if pd.notna(gpu_memory_max_mib) else 'None'}"
                data-gpu-temperature-avg="{gpu_temperature_avg if pd.notna(gpu_temperature_avg) else 'None'}"
                data-gpu-temperature-max="{gpu_temperature_max if pd.notna(gpu_temperature_max) else 'None'}"
                data-gpu-power-avg-w="{gpu_power_avg_w if pd.notna(gpu_power_avg_w) else 'None'}"
                data-timestamp="{timestamp}"
                data-submitted-by="{submitted_by}"
                data-results-dataset="{results_dataset}"
                data-traces-dataset="{traces_dataset}"
                data-metrics-dataset="{metrics_dataset}"
                class="tm-clickable-row"
            >
                <td>{get_rank_badge(rank)}</td>
                <td class="tm-run-id" title="{run_id}">{run_id_short}</td>
                <td class="tm-model-name">{model}</td>
                <td class="tm-badge-cell">{get_agent_type_badge(agent_type)}</td>
                <td class="tm-badge-cell">{get_provider_badge(provider)}</td>
                <td class="tm-badge-cell">{get_hardware_badge(has_gpu)}</td>
                <td>{get_success_rate_bar(success_rate)}</td>
                <td class="tm-numeric-cell">
                    <strong>{total_tests}</strong>
                    <span style="color: #CBD5E1; margin: 0 4px;">/</span>
                    <span style="color: #10B981; font-weight: 600;">{successful_tests}</span>
                    <span style="color: #CBD5E1; margin: 0 4px;">/</span>
                    <span style="color: #EF4444; font-weight: 600;">{failed_tests}</span>
                </td>
                <td class="tm-numeric-cell">{avg_steps:.1f}</td>
                <td class="tm-numeric-cell">{format_duration(avg_duration_ms)}</td>
                <td class="tm-numeric-cell">{total_tokens:,}</td>
                <td class="tm-numeric-cell">{format_cost(total_cost_usd)}</td>
                <td class="tm-numeric-cell tm-hide-mobile">{co2_display}</td>
                <td class="tm-hide-mobile">{gpu_display}</td>
                <td class="tm-numeric-cell tm-hide-mobile">{gpu_mem_display}</td>
                <td class="tm-numeric-cell tm-hide-mobile">{gpu_temp_display}</td>
                <td class="tm-numeric-cell tm-hide-mobile">{gpu_power_display}</td>
                <td class="tm-hide-mobile tm-text-cell">{timestamp_display}</td>
                <td class="tm-hide-mobile tm-text-cell">
                    {submitted_by}
                </td>
            </tr>
        """

    html += """
            </tbody>
        </table>
    </div>
    """

    return html


def generate_empty_state_html() -> str:
    """
    Generate HTML for empty leaderboard state

    Returns:
        HTML string for empty state
    """
    return """
    <div style="
        text-align: center;
        padding: 60px 20px;
        background: var(--tm-bg-card, #1E293B);
        border-radius: 16px;
        border: 2px dashed var(--tm-border-default, rgba(148, 163, 184, 0.2));
        margin: 20px 0;
    ">
        <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
        <h3 style="
            color: var(--tm-text-primary, #F1F5F9);
            margin: 0 0 12px 0;
            font-size: 1.5rem;
        ">
            No Evaluation Results Yet
        </h3>
        <p style="
            color: var(--tm-text-secondary, #94A3B8);
            margin: 0 0 24px 0;
            font-size: 1rem;
        ">
            Run your first evaluation to see results appear here.
        </p>
        <button style="
            padding: 12px 24px;
            background: var(--tm-primary, #4F46E5);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            font-size: 1rem;
        ">
            Start New Evaluation
        </button>
    </div>
    """


def generate_filter_summary_html(
    total_runs: int,
    filtered_runs: int,
    active_filters: dict
) -> str:
    """
    Generate summary of active filters

    Args:
        total_runs: Total number of runs
        filtered_runs: Number of runs after filtering
        active_filters: Dict of active filter values

    Returns:
        HTML string with filter summary
    """
    if filtered_runs == total_runs:
        return f"""
        <div style="
            padding: 12px 16px;
            background: var(--tm-bg-secondary, #334155);
            border-radius: 8px;
            margin-bottom: 16px;
            color: var(--tm-text-secondary, #94A3B8);
            font-size: 0.9em;
        ">
            Showing all <strong style="color: var(--tm-text-primary, #F1F5F9);">{total_runs}</strong> evaluation runs
        </div>
        """

    filter_chips = []
    for key, value in active_filters.items():
        if value and value != "All":
            filter_chips.append(f"""
                <span style="
                    display: inline-flex;
                    align-items: center;
                    padding: 4px 10px;
                    background: var(--tm-primary, #4F46E5);
                    color: white;
                    border-radius: 6px;
                    font-size: 0.85em;
                    margin-right: 8px;
                    font-weight: 500;
                ">
                    {key}: {value}
                </span>
            """)

    filters_html = "".join(filter_chips) if filter_chips else ""

    return f"""
    <div style="
        padding: 12px 16px;
        background: var(--tm-bg-secondary, #334155);
        border-radius: 8px;
        margin-bottom: 16px;
        color: var(--tm-text-secondary, #94A3B8);
        font-size: 0.9em;
    ">
        <div style="margin-bottom: 8px;">
            Showing <strong style="color: var(--tm-text-primary, #F1F5F9);">{filtered_runs}</strong> of
            <strong style="color: var(--tm-text-primary, #F1F5F9);">{total_runs}</strong> runs
        </div>
        {filters_html}
    </div>
    """
