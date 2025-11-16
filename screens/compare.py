"""
Compare Screen for TraceMind-AI
Side-by-side comparison of two evaluation runs
"""

import gradio as gr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any


def create_run_comparison_card(run_data: Dict[str, Any], label: str) -> str:
    """
    Create HTML card for a run in comparison view

    Args:
        run_data: Dict with run information
        label: "A" or "B"

    Returns:
        HTML string for the card
    """
    model = run_data.get('model', 'Unknown')
    success_rate = run_data.get('success_rate', 0)
    total_cost = run_data.get('total_cost_usd', 0)
    duration = run_data.get('total_duration_ms', 0) / 1000  # Convert to seconds
    tokens = run_data.get('total_tokens', 0)
    co2 = run_data.get('co2_emissions_g', 0)

    return f"""
    <div style="background: linear-gradient(135deg, {'#667eea' if label == 'A' else '#764ba2'} 0%, {'#764ba2' if label == 'A' else '#f093fb'} 100%);
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                color: white;">
        <h3 style="margin-top: 0;">Run {label}: {model}</h3>

        <div style="margin: 20px 0;">
            <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                <span>Success Rate:</span>
                <strong>{success_rate:.1f}%</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                <span>Total Cost:</span>
                <strong>${total_cost:.4f}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                <span>Duration:</span>
                <strong>{duration:.2f}s</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                <span>Tokens:</span>
                <strong>{tokens:,}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                <span>CO2:</span>
                <strong>{co2:.2f}g</strong>
            </div>
        </div>
    </div>
    """


def create_comparison_charts(run_a: Dict[str, Any], run_b: Dict[str, Any]) -> go.Figure:
    """
    Create comparison charts for two runs

    Args:
        run_a: First run data dict
        run_b: Second run data dict

    Returns:
        Plotly figure with comparison charts
    """
    try:
        # Extract metrics
        metrics = {
            'Success Rate (%)': [run_a.get('success_rate', 0), run_b.get('success_rate', 0)],
            'Cost ($)': [run_a.get('total_cost_usd', 0), run_b.get('total_cost_usd', 0)],
            'Duration (s)': [run_a.get('total_duration_ms', 0) / 1000, run_b.get('total_duration_ms', 0) / 1000],
            'Tokens': [run_a.get('total_tokens', 0), run_b.get('total_tokens', 0)],
            'CO2 (g)': [run_a.get('co2_emissions_g', 0), run_b.get('co2_emissions_g', 0)]
        }

        # Create subplots
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=list(metrics.keys()),
            specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}, {"type": "indicator"}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )

        model_a = run_a.get('model', 'Run A')
        model_b = run_b.get('model', 'Run B')

        # Add bar charts for each metric
        positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)]
        colors_a = ['#667eea', '#667eea', '#667eea', '#667eea', '#667eea']
        colors_b = ['#764ba2', '#764ba2', '#764ba2', '#764ba2', '#764ba2']

        for idx, (metric_name, values) in enumerate(metrics.items()):
            if idx < 5:  # First 5 metrics
                row, col = positions[idx]

                fig.add_trace(
                    go.Bar(
                        name=model_a,
                        x=[model_a],
                        y=[values[0]],
                        marker_color=colors_a[idx],
                        text=[f"{values[0]:.2f}"],
                        textposition='auto',
                        showlegend=(idx == 0)
                    ),
                    row=row, col=col
                )

                fig.add_trace(
                    go.Bar(
                        name=model_b,
                        x=[model_b],
                        y=[values[1]],
                        marker_color=colors_b[idx],
                        text=[f"{values[1]:.2f}"],
                        textposition='auto',
                        showlegend=(idx == 0)
                    ),
                    row=row, col=col
                )

        fig.update_layout(
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=80, b=50)
        )

        return fig
    except Exception as e:
        print(f"[ERROR] Creating comparison charts: {e}")
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating charts: {str(e)}", showarrow=False)
        return fig


def generate_winner_summary(run_a: Dict[str, Any], run_b: Dict[str, Any]) -> str:
    """
    Generate winner summary comparing two runs

    Args:
        run_a: First run data dict
        run_b: Second run data dict

    Returns:
        Markdown string with winner analysis
    """
    model_a = run_a.get('model', 'Run A')
    model_b = run_b.get('model', 'Run B')

    # Compare metrics
    winners = {
        'accuracy': model_a if run_a.get('success_rate', 0) > run_b.get('success_rate', 0) else model_b,
        'cost': model_a if run_a.get('total_cost_usd', 999) < run_b.get('total_cost_usd', 999) else model_b,
        'speed': model_a if run_a.get('total_duration_ms', 999999) < run_b.get('total_duration_ms', 999999) else model_b,
        'eco': model_a if run_a.get('co2_emissions_g', 999) < run_b.get('co2_emissions_g', 999) else model_b
    }

    # Count wins
    a_wins = sum(1 for w in winners.values() if w == model_a)
    b_wins = sum(1 for w in winners.values() if w == model_b)

    overall_winner = model_a if a_wins > b_wins else model_b if b_wins > a_wins else "Tie"

    return f"""
### Category Winners

| Category | Winner | Metric |
|----------|--------|--------|
| **Accuracy** | **{winners['accuracy']}** | {run_a.get('success_rate', 0):.1f}% vs {run_b.get('success_rate', 0):.1f}% |
| **Cost** | **{winners['cost']}** | ${run_a.get('total_cost_usd', 0):.4f} vs ${run_b.get('total_cost_usd', 0):.4f} |
| **Speed** | **{winners['speed']}** | {run_a.get('total_duration_ms', 0)/1000:.2f}s vs {run_b.get('total_duration_ms', 0)/1000:.2f}s |
| **Eco-Friendly** | **{winners['eco']}** | {run_a.get('co2_emissions_g', 0):.2f}g vs {run_b.get('co2_emissions_g', 0):.2f}g |

---

### Overall Winner: **{overall_winner}**

**{model_a}** wins {a_wins} categories
**{model_b}** wins {b_wins} categories

### Recommendation

{f"**{model_a}** is the better choice for most use cases" if a_wins > b_wins else
 f"**{model_b}** is the better choice for most use cases" if b_wins > a_wins else
 "Both runs are evenly matched - choose based on your specific priorities"}
"""


def create_compare_ui():
    """
    Create the compare screen UI components

    Returns:
        Tuple of (screen_column, component_dict)
    """
    components = {}

    with gr.Column(visible=False) as compare_screen:
        gr.Markdown("# Compare Runs")
        gr.Markdown("*Side-by-side comparison of two evaluation runs*")

        with gr.Row():
            components['back_to_leaderboard_btn'] = gr.Button(
                "Back to Leaderboard",
                variant="secondary",
                size="sm"
            )

        gr.Markdown("## Select Runs to Compare")
        with gr.Row():
            with gr.Column():
                components['compare_run_a_dropdown'] = gr.Dropdown(
                    label="Run A",
                    choices=[],
                    interactive=True
                )
            with gr.Column():
                components['compare_run_b_dropdown'] = gr.Dropdown(
                    label="Run B",
                    choices=[],
                    interactive=True
                )

        components['compare_button'] = gr.Button(
            "Compare Selected Runs",
            variant="primary",
            size="lg"
        )

        # Comparison results
        with gr.Column(visible=False) as comparison_output:
            gr.Markdown("## Comparison Results")

            with gr.Tabs():
                with gr.TabItem("Side-by-Side"):
                    # Side-by-side metrics
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Run A")
                            components['run_a_card'] = gr.HTML()
                        with gr.Column():
                            gr.Markdown("### Run B")
                            components['run_b_card'] = gr.HTML()

                    # Comparison charts
                    gr.Markdown("## Metric Comparisons")
                    components['comparison_charts'] = gr.Plot(
                        label="Comparison Charts",
                        show_label=False
                    )

                    # Winner summary
                    gr.Markdown("## Winner Summary")
                    components['winner_summary'] = gr.Markdown()

                with gr.TabItem("Radar Comparison"):
                    gr.Markdown("""
                    ### Multi-Dimensional Comparison

                    Compare runs across **6 normalized dimensions**:
                    - **Success Rate**: Percentage of successful test cases
                    - **Speed**: Execution time (faster is better)
                    - **Cost Efficiency**: Dollar cost per test (cheaper is better)
                    - **Token Efficiency**: Success per 1000 tokens
                    - **CO2 Efficiency**: Environmental impact (lower is better)
                    - **GPU Utilization**: Resource usage (if applicable)
                    """)
                    components['radar_comparison_chart'] = gr.Plot(
                        label="Multi-Dimensional Radar Chart",
                        show_label=False
                    )

        components['comparison_output'] = comparison_output

    return compare_screen, components


def on_compare_runs(run_a_id: str, run_b_id: str, leaderboard_df, components: Dict):
    """
    Handle comparison of two runs

    Args:
        run_a_id: ID of first run
        run_b_id: ID of second run
        leaderboard_df: Full leaderboard dataframe
        components: Dictionary of Gradio components

    Returns:
        Dictionary of component updates
    """
    try:
        if not run_a_id or not run_b_id:
            gr.Warning("Please select two runs to compare")
            return {
                components['comparison_output']: gr.update(visible=False)
            }

        if run_a_id == run_b_id:
            gr.Warning("Please select two different runs")
            return {
                components['comparison_output']: gr.update(visible=False)
            }

        if leaderboard_df is None or leaderboard_df.empty:
            gr.Warning("Leaderboard data not loaded")
            return {
                components['comparison_output']: gr.update(visible=False)
            }

        # Find the runs in the dataframe
        run_a = leaderboard_df[leaderboard_df['run_id'] == run_a_id].iloc[0].to_dict()
        run_b = leaderboard_df[leaderboard_df['run_id'] == run_b_id].iloc[0].to_dict()

        # Create comparison visualizations
        card_a = create_run_comparison_card(run_a, "A")
        card_b = create_run_comparison_card(run_b, "B")
        charts = create_comparison_charts(run_a, run_b)
        summary = generate_winner_summary(run_a, run_b)

        # Create radar chart for multi-dimensional comparison
        from components.analytics_charts import create_comparison_radar
        radar_chart = create_comparison_radar([run_a, run_b])

        return {
            components['comparison_output']: gr.update(visible=True),
            components['run_a_card']: gr.update(value=card_a),
            components['run_b_card']: gr.update(value=card_b),
            components['comparison_charts']: gr.update(value=charts),
            components['winner_summary']: gr.update(value=summary),
            components['radar_comparison_chart']: gr.update(value=radar_chart)
        }

    except Exception as e:
        print(f"[ERROR] Comparing runs: {e}")
        import traceback
        traceback.print_exc()
        gr.Warning(f"Error comparing runs: {str(e)}")
        return {
            components['comparison_output']: gr.update(visible=False)
        }
