"""
Analytics Charts Component
Interactive visualizations for leaderboard analytics
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


def create_performance_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Create an interactive heatmap of models × metrics

    Args:
        df: Leaderboard DataFrame with metrics

    Returns:
        Plotly figure with heatmap visualization
    """

    if df.empty:
        return _create_empty_figure("No data available for heatmap")

    # Select metrics to display
    metrics = [
        'success_rate',
        'avg_duration_ms',
        'total_cost_usd',
        'co2_emissions_g',
        'gpu_utilization_avg',
        'total_tokens'
    ]

    # Filter to only available metrics
    available_metrics = [m for m in metrics if m in df.columns]

    if not available_metrics:
        return _create_empty_figure("No metrics available for analysis")

    # Aggregate by model (in case of multiple runs)
    model_stats = df.groupby('model')[available_metrics].mean()

    # Prepare data matrix (rows=metrics, columns=models)
    heatmap_data = []
    heatmap_text = []
    metric_labels = []

    for metric in available_metrics:
        values = model_stats[metric].values

        # Normalize to 0-1 scale
        # For metrics where lower is better (duration, cost, co2), invert the scale
        if metric in ['avg_duration_ms', 'total_cost_usd', 'co2_emissions_g']:
            # Invert: lower is better (green)
            max_val = values.max()
            if max_val > 0:
                normalized = 1 - (values / max_val)
            else:
                normalized = np.zeros_like(values)
        else:
            # Higher is better (green)
            max_val = values.max()
            if max_val > 0:
                normalized = values / max_val
            else:
                normalized = np.zeros_like(values)

        heatmap_data.append(normalized)

        # Create hover text with actual values
        if metric == 'success_rate':
            text_row = [f"{v:.1f}%" for v in values]
        elif metric == 'avg_duration_ms':
            text_row = [f"{v:.0f}ms" for v in values]
        elif metric in ['total_cost_usd']:
            text_row = [f"${v:.4f}" for v in values]
        elif metric == 'co2_emissions_g':
            text_row = [f"{v:.2f}g" for v in values]
        elif metric == 'gpu_utilization_avg':
            text_row = [f"{v:.1f}%" if pd.notna(v) else "N/A" for v in values]
        else:
            text_row = [f"{v:.0f}" for v in values]

        heatmap_text.append(text_row)

        # Create readable metric labels
        label = metric.replace('_', ' ').replace('avg', 'Avg').replace('usd', 'USD').title()
        metric_labels.append(label)

    # Get model names
    models = model_stats.index.tolist()

    # Shorten model names if too long
    model_labels = [m.split('/')[-1] if '/' in m else m for m in models]
    model_labels = [m[:20] + '...' if len(m) > 20 else m for m in model_labels]

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=model_labels,
        y=metric_labels,
        text=heatmap_text,
        texttemplate='%{text}',
        textfont={"size": 10},
        colorscale='RdYlGn',  # Red (bad) → Yellow → Green (good)
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>Model: %{x}<br>Value: %{text}<br>Score: %{z:.2f}<extra></extra>',
        colorbar=dict(
            title=dict(
                text="Performance<br>Score",
                side="right"
            ),
            tickmode="linear",
            tick0=0,
            dtick=0.25
        )
    ))

    fig.update_layout(
        title={
            'text': '🔥 Model Performance Heatmap',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title='Model',
        yaxis_title='Metric',
        height=500,
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        xaxis=dict(tickangle=-45),
        margin=dict(l=150, r=100, t=100, b=150),
    )

    return fig


def create_speed_accuracy_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Speed vs Accuracy trade-off scatter plot

    Args:
        df: Leaderboard DataFrame

    Returns:
        Plotly figure with scatter plot
    """

    if df.empty:
        return _create_empty_figure("No data available for scatter plot")

    # Check required columns
    required_cols = ['model', 'success_rate', 'avg_duration_ms']
    if not all(col in df.columns for col in required_cols):
        return _create_empty_figure(f"Missing required columns: {required_cols}")

    # Aggregate by model
    model_stats = df.groupby('model').agg({
        'success_rate': 'mean',
        'avg_duration_ms': 'mean',
        'total_cost_usd': 'mean' if 'total_cost_usd' in df.columns else 'size',
        'agent_type': 'first' if 'agent_type' in df.columns else 'size'
    }).reset_index()

    # Create figure
    fig = go.Figure()

    # Get unique agent types
    agent_types = model_stats['agent_type'].unique() if 'agent_type' in model_stats.columns else ['all']

    # Color scheme
    colors = {
        'tool': '#E67E22',      # Orange
        'code': '#3498DB',      # Blue
        'both': '#9B59B6',      # Purple
        'all': '#1ABC9C',       # Teal
        'unknown': '#95A5A6'    # Gray
    }

    for agent_type in agent_types:
        if agent_type == 'all':
            subset = model_stats
        else:
            subset = model_stats[model_stats['agent_type'] == agent_type]

        # Prepare hover text
        hover_texts = []
        for _, row in subset.iterrows():
            model_name = row['model'].split('/')[-1] if '/' in row['model'] else row['model']
            hover = f"<b>{model_name}</b><br>"
            hover += f"Success Rate: {row['success_rate']:.1f}%<br>"
            hover += f"Avg Duration: {row['avg_duration_ms']:.0f}ms<br>"
            if 'total_cost_usd' in row and pd.notna(row['total_cost_usd']):
                hover += f"Cost: ${row['total_cost_usd']:.4f}"
            hover_texts.append(hover)

        # Bubble size based on cost (if available)
        if 'total_cost_usd' in subset.columns:
            sizes = subset['total_cost_usd'] * 5000  # Scale up for visibility
            sizes = sizes.clip(lower=10, upper=100)  # Reasonable range
        else:
            sizes = 30  # Default size

        fig.add_trace(go.Scatter(
            x=subset['avg_duration_ms'],
            y=subset['success_rate'],
            mode='markers+text',
            name=str(agent_type).title(),
            marker=dict(
                size=sizes,
                color=colors.get(str(agent_type).lower(), colors['unknown']),
                opacity=0.7,
                line=dict(width=2, color='white')
            ),
            text=[m.split('/')[-1][:15] for m in subset['model']],
            textposition='top center',
            textfont=dict(size=9),
            hovertext=hover_texts,
            hoverinfo='text'
        ))

    # Add quadrant lines (median split)
    if len(model_stats) > 1:
        median_speed = model_stats['avg_duration_ms'].median()
        median_accuracy = model_stats['success_rate'].median()

        fig.add_hline(
            y=median_accuracy,
            line_dash="dash",
            line_color="gray",
            opacity=0.4,
            annotation_text=f"Median Accuracy: {median_accuracy:.1f}%",
            annotation_position="right"
        )
        fig.add_vline(
            x=median_speed,
            line_dash="dash",
            line_color="gray",
            opacity=0.4,
            annotation_text=f"Median Speed: {median_speed:.0f}ms",
            annotation_position="top"
        )

        # Add zone annotations
        max_accuracy = model_stats['success_rate'].max()
        min_speed = model_stats['avg_duration_ms'].min()

        fig.add_annotation(
            x=min_speed + (median_speed - min_speed) * 0.5,
            y=max_accuracy * 0.98,
            text="⭐ Fast & Accurate",
            showarrow=False,
            font=dict(size=14, color='green', family='Arial Black'),
            bgcolor='rgba(144, 238, 144, 0.2)',
            borderpad=5
        )

    fig.update_layout(
        title={
            'text': '⚡ Speed vs Accuracy Trade-off',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title='Average Duration (ms)',
        yaxis_title='Success Rate (%)',
        xaxis_type='log',  # Log scale for duration
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='#f8f9fa',
        showlegend=True,
        legend=dict(
            title=dict(text='Agent Type'),
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        hovermode='closest'
    )

    # Add grid for better readability
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


def create_cost_efficiency_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Cost-Performance Efficiency scatter plot

    Args:
        df: Leaderboard DataFrame

    Returns:
        Plotly figure with cost efficiency scatter
    """

    if df.empty:
        return _create_empty_figure("No data available for cost analysis")

    # Check required columns
    if 'success_rate' not in df.columns or 'total_cost_usd' not in df.columns:
        return _create_empty_figure("Missing required columns: success_rate, total_cost_usd")

    # Aggregate by model
    agg_dict = {
        'success_rate': 'mean',
        'total_cost_usd': 'mean',
        'avg_duration_ms': 'mean' if 'avg_duration_ms' in df.columns else 'size',
        'provider': 'first' if 'provider' in df.columns else 'size'
    }

    model_stats = df.groupby('model').agg(agg_dict).reset_index()

    # Handle zero costs for log scale visualization
    # Replace zero costs with a small epsilon value (0.00001)
    # This allows log scale to work properly while keeping all models visible
    EPSILON = 0.00001
    model_stats['total_cost_usd_display'] = model_stats['total_cost_usd'].apply(
        lambda x: max(x, EPSILON)
    )

    # Calculate efficiency metric: success_rate / cost
    model_stats['efficiency'] = model_stats['success_rate'] / (model_stats['total_cost_usd'] + 0.0001)  # Avoid division by zero

    # Create figure
    fig = go.Figure()

    # Get unique providers
    providers = model_stats['provider'].unique() if 'provider' in model_stats.columns else ['all']

    # Color scheme
    provider_colors = {
        'litellm': '#3498DB',      # Blue (API)
        'transformers': '#2ECC71', # Green (GPU/local)
        'all': '#9B59B6',          # Purple
        'unknown': '#95A5A6'       # Gray
    }

    for provider in providers:
        if provider == 'all':
            subset = model_stats
        else:
            subset = model_stats[model_stats['provider'] == provider]

        # Prepare hover text
        hover_texts = []
        for _, row in subset.iterrows():
            model_name = row['model'].split('/')[-1] if '/' in row['model'] else row['model']
            hover = f"<b>{model_name}</b><br>"
            hover += f"Success Rate: {row['success_rate']:.1f}%<br>"
            # Show actual cost (even if zero) in hover text
            if row['total_cost_usd'] == 0:
                hover += f"Total Cost: $0.0000 (No cost data)<br>"
            else:
                hover += f"Total Cost: ${row['total_cost_usd']:.4f}<br>"
            hover += f"Efficiency: {row['efficiency']:.0f} (points/$)<br>"
            if 'avg_duration_ms' in row and pd.notna(row['avg_duration_ms']):
                hover += f"Duration: {row['avg_duration_ms']:.0f}ms"
            hover_texts.append(hover)

        # Bubble size based on duration (if available)
        if 'avg_duration_ms' in subset.columns:
            # Invert: smaller duration = smaller bubble
            sizes = subset['avg_duration_ms'] / 100  # Scale down
            sizes = sizes.clip(lower=10, upper=80)  # Reasonable range
        else:
            sizes = 30  # Default size

        fig.add_trace(go.Scatter(
            x=subset['total_cost_usd_display'],  # Use adjusted cost for log scale
            y=subset['success_rate'],
            mode='markers+text',
            name=str(provider).title(),
            marker=dict(
                size=sizes,
                color=provider_colors.get(str(provider).lower(), provider_colors['unknown']),
                opacity=0.7,
                line=dict(width=2, color='white')
            ),
            text=[m.split('/')[-1][:15] for m in subset['model']],
            textposition='top center',
            textfont=dict(size=9),
            hovertext=hover_texts,
            hoverinfo='text'
        ))

    # Add cost bands
    if len(model_stats) > 0:
        max_cost = model_stats['total_cost_usd'].max()

        # Budget band: < $0.01
        if max_cost > 0.01:
            fig.add_vrect(
                x0=0, x1=0.01,
                fillcolor="lightgreen", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="Budget", annotation_position="top left"
            )

        # Mid band: $0.01-$0.10
        if max_cost > 0.10:
            fig.add_vrect(
                x0=0.01, x1=0.10,
                fillcolor="yellow", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="Mid-Range", annotation_position="top left"
            )

        # Premium band: > $0.10
        if max_cost > 0.10:
            fig.add_vrect(
                x0=0.10, x1=max_cost * 1.1,
                fillcolor="orange", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="Premium", annotation_position="top left"
            )

    # Highlight top 3 most efficient models
    top_efficient = model_stats.nlargest(3, 'efficiency')
    for _, row in top_efficient.iterrows():
        fig.add_annotation(
            x=row['total_cost_usd_display'],  # Use adjusted cost for positioning
            y=row['success_rate'],
            text="⭐",
            showarrow=False,
            font=dict(size=20)
        )

    fig.update_layout(
        title={
            'text': '💰 Cost-Performance Efficiency',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title='Total Cost (USD)',
        yaxis_title='Success Rate (%)',
        xaxis_type='log',  # Log scale for cost
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='#f8f9fa',
        showlegend=True,
        legend=dict(
            title=dict(text='Provider'),
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        hovermode='closest'
    )

    # Add grid for better readability
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


def _create_empty_figure(message: str) -> go.Figure:
    """
    Create an empty figure with a message

    Args:
        message: Message to display

    Returns:
        Plotly figure with annotation
    """
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=16, color='gray')
    )

    fig.update_layout(
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='#f8f9fa',
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
    )

    return fig


def create_comparison_radar(runs: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a multi-dimensional radar chart comparing 2-3 runs

    Args:
        runs: List of run data dictionaries (2-3 models)

    Returns:
        Plotly figure with radar chart comparison
    """

    if not runs or len(runs) < 2:
        return _create_empty_figure("Please select at least 2 runs to compare")

    if len(runs) > 3:
        runs = runs[:3]  # Limit to 3 runs for readability

    # Define dimensions for radar chart
    dimensions = []
    dimension_names = []

    # Helper function to normalize values (0-1 scale)
    def normalize(values, invert=False):
        """Normalize values to 0-1, optionally inverting (lower is better)"""
        values = np.array(values, dtype=float)
        min_val, max_val = np.nanmin(values), np.nanmax(values)
        if max_val == min_val:
            return [0.5] * len(values)
        normalized = (values - min_val) / (max_val - min_val)
        if invert:
            normalized = 1 - normalized
        return normalized.tolist()

    # Extract metrics from all runs
    success_rates = [run.get('success_rate', 0) / 100 for run in runs]  # Already 0-1
    durations = [run.get('avg_duration_ms', 0) for run in runs]
    costs = [run.get('total_cost_usd', 0) for run in runs]
    tokens = [run.get('total_tokens', 0) for run in runs]
    co2 = [run.get('co2_emissions_g', 0) for run in runs]
    gpu_util = [run.get('gpu_utilization_avg', None) for run in runs]

    # Calculate Token Efficiency (success per 1000 tokens)
    # Use max() to avoid division by zero
    token_efficiency = [
        (run.get('success_rate', 0) / 100) / max((run.get('total_tokens', 0) / 1000), 0.001)
        for run in runs
    ]

    # Build dimensions (normalized 0-1)
    dimensions.append(success_rates)  # Already 0-1
    dimension_names.append('Success Rate')

    dimensions.append(normalize(durations, invert=True))  # Faster is better
    dimension_names.append('Speed')

    dimensions.append(normalize(costs, invert=True))  # Cheaper is better
    dimension_names.append('Cost Efficiency')

    dimensions.append(normalize(token_efficiency))  # Higher is better
    dimension_names.append('Token Efficiency')

    dimensions.append(normalize(co2, invert=True))  # Lower CO2 is better
    dimension_names.append('CO2 Efficiency')

    # Add GPU Utilization if available
    if any(g is not None for g in gpu_util):
        gpu_values = [g / 100 if g is not None else 0 for g in gpu_util]  # Normalize to 0-1
        dimensions.append(gpu_values)
        dimension_names.append('GPU Utilization')

    # Create radar chart
    fig = go.Figure()

    colors = ['#667eea', '#f093fb', '#43e97b']  # Purple, Pink, Green

    for idx, run in enumerate(runs):
        model_name = run.get('model', f'Run {idx+1}')
        if '/' in model_name:
            model_name = model_name.split('/')[-1]  # Show only model name, not provider

        # Extract values for this run across all dimensions
        values = [dim[idx] for dim in dimensions]

        # Close the radar chart by repeating first value
        values_closed = values + [values[0]]
        theta_closed = dimension_names + [dimension_names[0]]

        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=theta_closed,
            name=model_name,
            fill='toself',
            fillcolor=colors[idx],
            opacity=0.3,
            line=dict(color=colors[idx], width=2),
            marker=dict(size=8, color=colors[idx]),
            hovertemplate='<b>%{theta}</b><br>' +
                         'Score: %{r:.2f}<br>' +
                         f'<b>{model_name}</b>' +
                         '<extra></extra>'
        ))

    fig.update_layout(
        polar=dict(
            bgcolor='#f8f9fa',
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                showticklabels=True,
                ticks='',
                gridcolor='rgba(100, 100, 100, 0.2)',
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                gridcolor='rgba(100, 100, 100, 0.2)',
                linecolor='rgba(100, 100, 100, 0.4)',
                tickfont=dict(size=12, color='#0f172a')
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#ccc',
            borderwidth=1
        ),
        title=dict(
            text='Multi-Dimensional Model Comparison',
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#0f172a', family='Inter, sans-serif')
        ),
        height=600,
        paper_bgcolor='white',
        font=dict(family='Inter, sans-serif')
    )

    return fig


def create_trends_plot(df: pd.DataFrame) -> go.Figure:
    """
    Create trends visualization over time with enhanced GPU metrics

    Args:
        df: Leaderboard DataFrame with timestamp or evaluation_date column

    Returns:
        Plotly figure showing trends
    """
    from plotly.subplots import make_subplots

    try:
        # Use evaluation_date or timestamp depending on what's available
        date_col = 'evaluation_date' if 'evaluation_date' in df.columns else 'timestamp'

        if df.empty or date_col not in df.columns:
            fig = go.Figure()
            fig.add_annotation(text="No trend data available", showarrow=False)
            return fig

        # Convert date column to datetime to avoid type errors
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        # Sort by date column
        df_sorted = df.sort_values(date_col)

        # Check which GPU metrics are available
        has_gpu_util = 'gpu_utilization_avg' in df.columns and df_sorted['gpu_utilization_avg'].notna().any()
        has_gpu_memory = 'gpu_memory_avg_mib' in df.columns and df_sorted['gpu_memory_avg_mib'].notna().any()
        has_gpu_temp = 'gpu_temperature_avg' in df.columns and df_sorted['gpu_temperature_avg'].notna().any()
        has_power_cost = 'power_cost_total_usd' in df.columns and df_sorted['power_cost_total_usd'].notna().any()

        # Determine number of subplots based on available data
        num_plots = 2  # Always show success rate and cost
        if has_gpu_util:
            num_plots += 1
        if has_gpu_memory:
            num_plots += 1
        if has_gpu_temp:
            num_plots += 1
        if has_power_cost:
            num_plots += 1

        # Create subplots
        subplot_titles = ["Success Rate Over Time", "Cost Over Time"]
        if has_gpu_util:
            subplot_titles.append("GPU Utilization Over Time")
        if has_gpu_memory:
            subplot_titles.append("GPU Memory Usage Over Time")
        if has_gpu_temp:
            subplot_titles.append("GPU Temperature Over Time")
        if has_power_cost:
            subplot_titles.append("Power Cost Over Time")

        fig = make_subplots(
            rows=num_plots, cols=1,
            subplot_titles=subplot_titles,
            vertical_spacing=0.08
        )

        current_row = 1

        # Success rate trend
        fig.add_trace(
            go.Scatter(
                x=df_sorted[date_col],
                y=df_sorted['success_rate'],
                mode='lines+markers',
                name='Success Rate',
                line=dict(color='#3498DB', width=2),
                marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>Success Rate: %{y:.1f}%<extra></extra>'
            ),
            row=current_row, col=1
        )
        fig.update_yaxes(title_text="Success Rate (%)", row=current_row, col=1)
        current_row += 1

        # Cost trend
        fig.add_trace(
            go.Scatter(
                x=df_sorted[date_col],
                y=df_sorted['total_cost_usd'],
                mode='lines+markers',
                name='Cost (USD)',
                line=dict(color='#E67E22', width=2),
                marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>Cost: $%{y:.4f}<extra></extra>'
            ),
            row=current_row, col=1
        )
        fig.update_yaxes(title_text="Cost (USD)", row=current_row, col=1)
        current_row += 1

        # GPU Utilization trend (if available)
        if has_gpu_util:
            gpu_data = df_sorted[df_sorted['gpu_utilization_avg'].notna()]
            fig.add_trace(
                go.Scatter(
                    x=gpu_data[date_col],
                    y=gpu_data['gpu_utilization_avg'],
                    mode='lines+markers',
                    name='GPU Utilization',
                    line=dict(color='#9B59B6', width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>%{x}</b><br>GPU Util: %{y:.1f}%<extra></extra>'
                ),
                row=current_row, col=1
            )
            fig.update_yaxes(title_text="GPU Utilization (%)", row=current_row, col=1)
            current_row += 1

        # GPU Memory trend (if available)
        if has_gpu_memory:
            gpu_memory_data = df_sorted[df_sorted['gpu_memory_avg_mib'].notna()]
            fig.add_trace(
                go.Scatter(
                    x=gpu_memory_data[date_col],
                    y=gpu_memory_data['gpu_memory_avg_mib'],
                    mode='lines+markers',
                    name='GPU Memory',
                    line=dict(color='#1ABC9C', width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>%{x}</b><br>GPU Memory: %{y:.0f} MiB<extra></extra>'
                ),
                row=current_row, col=1
            )
            fig.update_yaxes(title_text="GPU Memory (MiB)", row=current_row, col=1)
            current_row += 1

        # GPU Temperature trend (if available)
        if has_gpu_temp:
            gpu_temp_data = df_sorted[df_sorted['gpu_temperature_avg'].notna()]
            fig.add_trace(
                go.Scatter(
                    x=gpu_temp_data[date_col],
                    y=gpu_temp_data['gpu_temperature_avg'],
                    mode='lines+markers',
                    name='GPU Temperature',
                    line=dict(color='#E74C3C', width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>%{x}</b><br>GPU Temp: %{y:.1f}°C<extra></extra>'
                ),
                row=current_row, col=1
            )
            fig.update_yaxes(title_text="GPU Temperature (°C)", row=current_row, col=1)
            current_row += 1

        # Power Cost trend (if available)
        if has_power_cost:
            power_cost_data = df_sorted[df_sorted['power_cost_total_usd'].notna()]
            fig.add_trace(
                go.Scatter(
                    x=power_cost_data[date_col],
                    y=power_cost_data['power_cost_total_usd'],
                    mode='lines+markers',
                    name='Power Cost',
                    line=dict(color='#F39C12', width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>%{x}</b><br>Power Cost: $%{y:.4f}<extra></extra>'
                ),
                row=current_row, col=1
            )
            fig.update_yaxes(title_text="Power Cost (USD)", row=current_row, col=1)

        fig.update_xaxes(title_text="Date", row=num_plots, col=1)

        # Calculate dynamic height based on number of plots
        plot_height = max(400, num_plots * 200)

        fig.update_layout(
            height=plot_height,
            showlegend=False,
            margin=dict(l=50, r=50, t=50, b=50)
        )

        return fig
    except Exception as e:
        print(f"[ERROR] Creating trends plot: {e}")
        import traceback
        traceback.print_exc()
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating trends: {str(e)}", showarrow=False)
        return fig
