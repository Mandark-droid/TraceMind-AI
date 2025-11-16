"""
Dashboard Screen for TraceMind-AI
Displays aggregate statistics and recent evaluation runs
"""

import gradio as gr
import pandas as pd


def calculate_aggregate_stats(leaderboard_df):
    """Calculate aggregate statistics for dashboard"""
    if leaderboard_df.empty:
        return {
            'total_runs': 0,
            'avg_accuracy': 0.0,
            'avg_latency': 0.0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'avg_cost': 0.0,
            'total_co2': 0.0
        }

    return {
        'total_runs': len(leaderboard_df),
        'avg_accuracy': leaderboard_df['success_rate'].mean() if 'success_rate' in leaderboard_df.columns else 0.0,
        'avg_latency': leaderboard_df['avg_duration_ms'].mean() / 1000 if 'avg_duration_ms' in leaderboard_df.columns else 0.0,
        'total_tokens': int(leaderboard_df['total_tokens'].sum()) if 'total_tokens' in leaderboard_df.columns else 0,
        'total_cost': leaderboard_df['total_cost_usd'].sum() if 'total_cost_usd' in leaderboard_df.columns else 0.0,
        'avg_cost': leaderboard_df['total_cost_usd'].mean() if 'total_cost_usd' in leaderboard_df.columns else 0.0,
        'total_co2': leaderboard_df['co2_emissions_g'].sum() if 'co2_emissions_g' in leaderboard_df.columns else 0.0
    }


def generate_stats_card(title, value, emoji, gradient_colors, description):
    """
    Generate HTML for a single statistics card

    Args:
        title: Card title
        value: Main value to display
        emoji: Emoji icon
        gradient_colors: Tuple of (start_color, end_color) for gradient
        description: Description text
    """
    return f"""
    <div style="background: linear-gradient(135deg, {gradient_colors[0]} 0%, {gradient_colors[1]} 100%);
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                color: white;
                min-height: 150px;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 3em; font-weight: bold; margin: 10px 0;">{value}</div>
                <div style="font-size: 1.1em; opacity: 0.9;">{emoji} {title}</div>
            </div>
        </div>
        <div style="margin-top: 15px; font-size: 0.9em; opacity: 0.8;">
            <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px;">
                {description}
            </span>
        </div>
    </div>
    """


def create_dashboard_cards(stats):
    """
    Create all dashboard stat cards from stats dictionary

    Args:
        stats: Dictionary with aggregate statistics

    Returns:
        Dictionary of card HTML strings
    """
    cards = {}

    # Card 1: Total Runs
    cards['total_runs'] = generate_stats_card(
        title="Total Runs",
        value=stats['total_runs'],
        emoji="🚀",
        gradient_colors=("#667eea", "#764ba2"),
        description="All evaluations"
    )

    # Card 2: Avg Accuracy
    cards['avg_accuracy'] = generate_stats_card(
        title="Avg Accuracy",
        value=f"{stats['avg_accuracy']:.1f}%",
        emoji="🎯",
        gradient_colors=("#f093fb", "#f5576c"),
        description="Success rate"
    )

    # Card 3: Avg Latency
    cards['avg_latency'] = generate_stats_card(
        title="Avg Latency",
        value=f"{stats['avg_latency']:.2f}s",
        emoji="⚡",
        gradient_colors=("#4facfe", "#00f2fe"),
        description="Response time"
    )

    # Card 4: Total Tokens
    cards['total_tokens'] = generate_stats_card(
        title="Total Tokens",
        value=f"{stats['total_tokens']:,}",
        emoji="💬",
        gradient_colors=("#43e97b", "#38f9d7"),
        description="Across all runs"
    )

    # Card 5: Total Cost
    cards['total_cost'] = generate_stats_card(
        title="Total Cost",
        value=f"${stats['total_cost']:.4f}",
        emoji="💰",
        gradient_colors=("#fa709a", "#fee140"),
        description="All evaluations"
    )

    # Card 6: Total CO2
    cards['total_co2'] = generate_stats_card(
        title="Total CO2",
        value=f"{stats['total_co2']:.2f}g",
        emoji="🌱",
        gradient_colors=("#30cfd0", "#330867"),
        description="Carbon emissions"
    )

    return cards


def prepare_recent_runs_data(leaderboard_df, n=5):
    """
    Prepare data for recent runs table

    Args:
        leaderboard_df: Leaderboard dataframe
        n: Number of recent runs to show

    Returns:
        List of lists for Gradio DataFrame
    """
    recent_runs_data = []

    if not leaderboard_df.empty:
        # Convert timestamp to datetime to avoid type errors during sorting
        if 'timestamp' in leaderboard_df.columns:
            leaderboard_df['timestamp'] = pd.to_datetime(leaderboard_df['timestamp'], errors='coerce')
            recent_df = leaderboard_df.sort_values('timestamp', ascending=False).head(n)
        else:
            recent_df = leaderboard_df.head(n)

        for _, row in recent_df.iterrows():
            # Format duration
            duration_ms = row.get('avg_duration_ms', 0)
            if duration_ms >= 1000:
                duration_str = f"{duration_ms/1000:.2f}s"
            else:
                duration_str = f"{duration_ms:.0f}ms"

            recent_runs_data.append([
                row.get('model', 'N/A'),
                f"{row.get('success_rate', 0):.1f}%",
                f"${row.get('total_cost_usd', 0):.4f}",
                duration_str,
                row.get('timestamp', 'N/A')
            ])

    return recent_runs_data


def create_dashboard_ui():
    """
    Create the dashboard screen UI components

    Returns:
        Tuple of (screen_column, component_dict)
    """
    components = {}

    with gr.Column(visible=True) as dashboard_screen:
        gr.Markdown("## 📊 Dashboard")
        gr.Markdown("*Overview of agent evaluation metrics*")

        # Stats cards in draggable grid layout
        with gr.Row():
            # Card 1: Total Runs
            with gr.Draggable():
                components['total_runs_card'] = gr.HTML(
                    generate_stats_card(
                        "Total Runs", "0", "🚀",
                        ("#667eea", "#764ba2"),
                        "All evaluations"
                    )
                )

            # Card 2: Avg Accuracy
            with gr.Draggable():
                components['avg_accuracy_card'] = gr.HTML(
                    generate_stats_card(
                        "Avg Accuracy", "0%", "🎯",
                        ("#f093fb", "#f5576c"),
                        "Success rate"
                    )
                )

        with gr.Row():
            # Card 3: Avg Latency
            with gr.Draggable():
                components['avg_latency_card'] = gr.HTML(
                    generate_stats_card(
                        "Avg Latency", "0.0s", "⚡",
                        ("#4facfe", "#00f2fe"),
                        "Response time"
                    )
                )

            # Card 4: Total Tokens
            with gr.Draggable():
                components['total_tokens_card'] = gr.HTML(
                    generate_stats_card(
                        "Total Tokens", "0", "💬",
                        ("#43e97b", "#38f9d7"),
                        "Across all runs"
                    )
                )

        with gr.Row():
            # Card 5: Total Cost
            with gr.Draggable():
                components['total_cost_card'] = gr.HTML(
                    generate_stats_card(
                        "Total Cost", "$0.00", "💰",
                        ("#fa709a", "#fee140"),
                        "All evaluations"
                    )
                )

            # Card 6: Total CO2
            with gr.Draggable():
                components['total_co2_card'] = gr.HTML(
                    generate_stats_card(
                        "Total CO2", "0g", "🌱",
                        ("#30cfd0", "#330867"),
                        "Carbon emissions"
                    )
                )

        gr.Markdown("---")

        # Recent Runs Preview
        gr.Markdown("### 📋 Recent Evaluations")
        components['recent_runs_table'] = gr.Dataframe(
            headers=["Model", "Success Rate", "Cost", "Duration", "Timestamp"],
            interactive=False,
            wrap=True,
            row_count=5,
            label="Latest 5 runs"
        )

    return dashboard_screen, components


def update_dashboard_data(leaderboard_df, components):
    """
    Update dashboard stats cards and recent runs table

    Args:
        leaderboard_df: Leaderboard dataframe
        components: Dictionary of Gradio components

    Returns:
        Dictionary of component updates
    """
    stats = calculate_aggregate_stats(leaderboard_df)
    cards = create_dashboard_cards(stats)
    recent_runs_data = prepare_recent_runs_data(leaderboard_df)

    return {
        components['total_runs_card']: gr.update(value=cards['total_runs']),
        components['avg_accuracy_card']: gr.update(value=cards['avg_accuracy']),
        components['avg_latency_card']: gr.update(value=cards['avg_latency']),
        components['total_tokens_card']: gr.update(value=cards['total_tokens']),
        components['total_cost_card']: gr.update(value=cards['total_cost']),
        components['total_co2_card']: gr.update(value=cards['total_co2']),
        components['recent_runs_table']: gr.update(value=recent_runs_data)
    }
