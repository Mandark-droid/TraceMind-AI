"""
TraceMind-AI - Agent Evaluation Platform
Enterprise-grade AI agent evaluation with MCP integration
"""

import os
import pandas as pd
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
from components.report_cards import generate_leaderboard_summary_card

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
    try:
        df = data_loader.load_leaderboard()

        if df.empty:
            return pd.DataFrame()

        if agent_type != "All" and 'agent_type' in df.columns:
            df = df[df['agent_type'] == agent_type]
        if provider != "All" and 'provider' in df.columns:
            df = df[df['provider'] == provider]

        # Select only columns that exist
        desired_columns = [
            'run_id', 'model', 'agent_type', 'provider',
            'success_rate', 'total_tests', 'avg_duration_ms', 'total_cost_usd'
        ]

        # Filter to only existing columns
        available_columns = [col for col in desired_columns if col in df.columns]

        if not available_columns:
            # If no desired columns exist, return empty dataframe
            return pd.DataFrame()

        display_df = df[available_columns].copy()

        return display_df
    except Exception as e:
        print(f"[ERROR] load_drilldown: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


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


def generate_card(top_n):
    """Generate summary card HTML"""
    df = data_loader.load_leaderboard()
    html = generate_leaderboard_summary_card(df, top_n)
    return html


def generate_insights():
    """Generate AI insights summary"""
    try:
        df = data_loader.load_leaderboard()

        if df.empty or 'success_rate' not in df.columns:
            return "## 📊 Leaderboard Summary\n\nNo data available for insights."

        top_model = df.loc[df['success_rate'].idxmax()]
        most_cost_effective = df.loc[(df['success_rate'] / (df['total_cost_usd'] + 0.0001)).idxmax()]
        fastest = df.loc[df['avg_duration_ms'].idxmin()]

        insights = f"""
## 📊 Leaderboard Summary

**Total Runs:** {len(df)}

**Top Performers:**
- 🥇 **Best Accuracy:** {top_model['model']} ({top_model['success_rate']:.1f}%)
- 💰 **Most Cost-Effective:** {most_cost_effective['model']} ({most_cost_effective['success_rate']:.1f}% @ ${most_cost_effective['total_cost_usd']:.4f})
- ⚡ **Fastest:** {fastest['model']} ({fastest['avg_duration_ms']:.0f}ms avg)

**Key Trends:**
- Average Success Rate: {df['success_rate'].mean():.1f}%
- Average Cost: ${df['total_cost_usd'].mean():.4f}
- Average Duration: {df['avg_duration_ms'].mean():.0f}ms

---

*Note: AI-powered insights will be available via MCP integration in the full version.*
        """

        return insights
    except Exception as e:
        print(f"[ERROR] generate_insights: {e}")
        import traceback
        traceback.print_exc()
        return f"## 📊 Leaderboard Summary\n\nError generating insights: {str(e)}"


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

            with gr.TabItem("📥 Summary Card"):
                top_n_slider = gr.Slider(1, 5, 3, step=1, label="Top N Models")
                generate_card_btn = gr.Button("🎨 Generate Card")
                card_preview = gr.HTML()

            with gr.TabItem("🤖 AI Insights"):
                regenerate_btn = gr.Button("🔄 Regenerate")
                mcp_insights = gr.Markdown("*Loading insights...*")

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

    # Load drilldown data on page load
    app.load(
        fn=load_drilldown,
        inputs=[drilldown_agent_type, drilldown_provider],
        outputs=[leaderboard_table]
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

    generate_card_btn.click(
        fn=generate_card,
        inputs=[top_n_slider],
        outputs=[card_preview]
    )

    app.load(
        fn=generate_insights,
        outputs=[mcp_insights]
    )

    regenerate_btn.click(
        fn=generate_insights,
        outputs=[mcp_insights]
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
