"""
TraceMind-AI - Agent Evaluation Platform
Enterprise-grade AI agent evaluation with MCP integration
"""

import os
import gradio as gr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import data loader and components
from data_loader import create_data_loader_from_env
from components.leaderboard_table import generate_leaderboard_html
from components.analytics_charts import (
    create_trends_plot,
    create_performance_heatmap,
    create_speed_accuracy_scatter,
    create_cost_efficiency_scatter
)

# Initialize data loader
data_loader = create_data_loader_from_env()

# Global state
leaderboard_df_cache = None


def load_leaderboard():
    """Load initial leaderboard data"""
    global leaderboard_df_cache

    df = data_loader.load_leaderboard()
    leaderboard_df_cache = df.copy()

    html = generate_leaderboard_html(df)

    # Get filter choices
    models = ["All Models"] + sorted(df['model'].unique().tolist())

    return html, gr.update(choices=models)


def apply_filters(model, provider, sort_by_col):
    """Apply filters and sorting to leaderboard"""
    global leaderboard_df_cache

    df = leaderboard_df_cache.copy() if leaderboard_df_cache is not None else data_loader.load_leaderboard()

    # Apply filters
    if model != "All Models":
        df = df[df['model'] == model]
    if provider != "All":
        df = df[df['provider'] == provider]

    # Sort
    df = df.sort_values(by=sort_by_col, ascending=False)

    html = generate_leaderboard_html(df, sort_by_col)
    return html


def load_drilldown(agent_type, provider):
    """Load drilldown data with filters"""
    df = data_loader.load_leaderboard()

    if agent_type != "All":
        df = df[df['agent_type'] == agent_type]
    if provider != "All":
        df = df[df['provider'] == provider]

    # Format for dataframe
    display_df = df[[
        'run_id', 'model', 'agent_type', 'provider',
        'success_rate', 'total_tests', 'avg_duration_ms', 'total_cost_usd'
    ]].copy()

    return display_df


def load_trends():
    """Load trends visualization"""
    df = data_loader.load_leaderboard()
    fig = create_trends_plot(df)
    return fig


def update_analytics(viz_type):
    """Update analytics chart based on visualization type"""
    df = data_loader.load_leaderboard()

    if "Heatmap" in viz_type:
        return create_performance_heatmap(df)
    elif "Speed" in viz_type:
        return create_speed_accuracy_scatter(df)
    else:
        return create_cost_efficiency_scatter(df)


# Build Gradio app
with gr.Blocks(title="TraceMind-AI") as app:
    gr.Markdown("# 🧠 TraceMind-AI")

    # Navigation (placeholder)
    with gr.Row():
        nav_title = gr.Markdown("## 🏆 Agent Evaluation Leaderboard")

    # Screen 1: Main Leaderboard
    with gr.Column(visible=True) as leaderboard_screen:
        with gr.Tabs():
            with gr.TabItem("🏆 Leaderboard"):
                # Filters
                with gr.Row():
                    model_filter = gr.Dropdown(
                        choices=["All Models"],
                        value="All Models",
                        label="Filter by Model"
                    )
                    provider_filter = gr.Dropdown(
                        choices=["All", "litellm", "transformers"],
                        value="All",
                        label="Provider"
                    )
                    sort_by = gr.Dropdown(
                        choices=["success_rate", "total_cost_usd", "avg_duration_ms"],
                        value="success_rate",
                        label="Sort By"
                    )

                apply_filters_btn = gr.Button("🔍 Apply Filters")

                # HTML table
                leaderboard_by_model = gr.HTML()

            with gr.TabItem("📋 DrillDown"):
                with gr.Row():
                    drilldown_agent_type = gr.Radio(
                        choices=["All", "tool", "code", "both"],
                        value="All",
                        label="Agent Type"
                    )
                    drilldown_provider = gr.Dropdown(
                        choices=["All", "litellm", "transformers"],
                        value="All",
                        label="Provider"
                    )

                apply_drilldown_btn = gr.Button("🔍 Apply")

                leaderboard_table = gr.Dataframe(
                    headers=["Run ID", "Model", "Agent Type", "Provider", "Success Rate", "Tests", "Duration", "Cost"],
                    interactive=False
                )

            with gr.TabItem("📈 Trends"):
                trends_plot = gr.Plot()

            with gr.TabItem("📊 Analytics"):
                viz_type = gr.Radio(
                    choices=["🔥 Performance Heatmap", "⚡ Speed vs Accuracy", "💰 Cost Efficiency"],
                    value="🔥 Performance Heatmap",
                    label="Select Visualization"
                )
                analytics_chart = gr.Plot()

        # Hidden textbox for row selection (JavaScript bridge)
        selected_row_index = gr.Textbox(visible=False, elem_id="selected_row_index")

    # Event handlers
    app.load(
        fn=load_leaderboard,
        outputs=[leaderboard_by_model, model_filter]
    )

    app.load(
        fn=load_trends,
        outputs=[trends_plot]
    )

    apply_filters_btn.click(
        fn=apply_filters,
        inputs=[model_filter, provider_filter, sort_by],
        outputs=[leaderboard_by_model]
    )

    apply_drilldown_btn.click(
        fn=load_drilldown,
        inputs=[drilldown_agent_type, drilldown_provider],
        outputs=[leaderboard_table]
    )

    viz_type.change(
        fn=update_analytics,
        inputs=[viz_type],
        outputs=[analytics_chart]
    )

    app.load(
        fn=update_analytics,
        inputs=[viz_type],
        outputs=[analytics_chart]
    )


if __name__ == "__main__":
    print("🚀 Starting TraceMind-AI...")
    print(f"📊 Data Source: {os.getenv('DATA_SOURCE', 'both')}")
    print(f"📁 JSON Path: {os.getenv('JSON_DATA_PATH', './sample_data')}")

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
