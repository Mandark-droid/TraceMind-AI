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
from utils.navigation import Navigator, Screen

# Initialize data loader
data_loader = create_data_loader_from_env()
navigator = Navigator()

# Pre-load and cache the leaderboard data before building UI
print("📥 Pre-loading leaderboard data from HuggingFace...")
leaderboard_df_cache = data_loader.load_leaderboard()
print(f"✅ Loaded {len(leaderboard_df_cache)} evaluation runs")

# Global state (already populated)
# leaderboard_df_cache is now set

# Additional global state for navigation
current_selected_run = None
current_selected_trace = None
current_drilldown_df = None  # Store currently displayed drilldown data


def load_leaderboard():
    """Load initial leaderboard data from cache"""
    global leaderboard_df_cache

    # Use pre-cached data (already loaded before UI build)
    df = leaderboard_df_cache.copy()

    html = generate_leaderboard_html(df)

    # Get filter choices
    models = ["All Models"] + sorted(df['model'].unique().tolist())

    return html, gr.update(choices=models), gr.update(choices=models)


def refresh_leaderboard():
    """Refresh leaderboard data from source (for reload button)"""
    global leaderboard_df_cache

    print("🔄 Refreshing leaderboard data...")
    df = data_loader.refresh_leaderboard()  # Clears cache and reloads
    leaderboard_df_cache = df.copy()
    print(f"✅ Refreshed {len(df)} evaluation runs")

    html = generate_leaderboard_html(df)
    models = ["All Models"] + sorted(df['model'].unique().tolist())

    return html, gr.update(choices=models), gr.update(choices=models)


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
    global current_drilldown_df

    try:
        df = data_loader.load_leaderboard()

        if df.empty:
            current_drilldown_df = pd.DataFrame()
            return pd.DataFrame()

        if agent_type != "All" and 'agent_type' in df.columns:
            df = df[df['agent_type'] == agent_type]
        if provider != "All" and 'provider' in df.columns:
            df = df[df['provider'] == provider]

        # IMPORTANT: Store the FULL dataframe in global state (with ALL columns)
        # This ensures the event handler has access to results_dataset, traces_dataset, etc.
        current_drilldown_df = df.copy()

        # Select only columns for DISPLAY
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

        # Return ONLY display columns for the UI table
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


def on_html_table_row_click(row_index_str):
    """Handle row click from HTML table via JavaScript (hidden textbox bridge)"""
    global current_selected_run, leaderboard_df_cache

    print(f"[DEBUG] on_html_table_row_click called with: '{row_index_str}'")

    try:
        # Parse row index from string
        if not row_index_str or row_index_str == "" or row_index_str.strip() == "":
            print("[DEBUG] Empty row index, ignoring")
            return {
                leaderboard_screen: gr.update(),
                run_detail_screen: gr.update(),
                run_metadata_html: gr.update(),
                test_cases_table: gr.update(),
                selected_row_index: gr.update(value="")  # Clear textbox
            }

        selected_idx = int(row_index_str)
        print(f"[DEBUG] Parsed row index: {selected_idx}")

        # Get the full run data from cache
        if leaderboard_df_cache is None or leaderboard_df_cache.empty:
            print("[ERROR] Leaderboard cache is empty")
            gr.Warning("Leaderboard data not loaded")
            return {
                leaderboard_screen: gr.update(),
                run_detail_screen: gr.update(),
                run_metadata_html: gr.update(),
                test_cases_table: gr.update(),
                selected_row_index: gr.update(value="")  # Clear textbox
            }

        if selected_idx < 0 or selected_idx >= len(leaderboard_df_cache):
            print(f"[ERROR] Invalid row index: {selected_idx}, cache size: {len(leaderboard_df_cache)}")
            gr.Warning(f"Invalid row index: {selected_idx}")
            return {
                leaderboard_screen: gr.update(),
                run_detail_screen: gr.update(),
                run_metadata_html: gr.update(),
                test_cases_table: gr.update(),
                selected_row_index: gr.update(value="")  # Clear textbox
            }

        run_data = leaderboard_df_cache.iloc[selected_idx].to_dict()

        # Set global
        current_selected_run = run_data

        print(f"[DEBUG] Selected run from HTML table: {run_data.get('model', 'Unknown')} (row {selected_idx})")

        # Load results for this run
        results_dataset = run_data.get('results_dataset')
        if not results_dataset:
            gr.Warning("No results dataset found for this run")
            return {
                leaderboard_screen: gr.update(visible=True),
                run_detail_screen: gr.update(visible=False),
                run_metadata_html: gr.update(value="<h3>No results dataset found</h3>"),
                test_cases_table: gr.update(value=pd.DataFrame()),
                selected_row_index: gr.update(value="")
            }

        results_df = data_loader.load_results(results_dataset)

        # Create metadata HTML
        metadata_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
            <h2 style="margin: 0 0 10px 0;">📊 Run Detail: {run_data.get('model', 'Unknown')}</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 15px;">
                <div>
                    <strong>Agent Type:</strong> {run_data.get('agent_type', 'N/A')}<br>
                    <strong>Provider:</strong> {run_data.get('provider', 'N/A')}<br>
                    <strong>Success Rate:</strong> {run_data.get('success_rate', 0):.1f}%
                </div>
                <div>
                    <strong>Total Tests:</strong> {run_data.get('total_tests', 0)}<br>
                    <strong>Successful:</strong> {run_data.get('successful_tests', 0)}<br>
                    <strong>Failed:</strong> {run_data.get('failed_tests', 0)}
                </div>
                <div>
                    <strong>Total Cost:</strong> ${run_data.get('total_cost_usd', 0):.4f}<br>
                    <strong>Avg Duration:</strong> {run_data.get('avg_duration_ms', 0):.0f}ms<br>
                    <strong>Submitted By:</strong> {run_data.get('submitted_by', 'Unknown')}
                </div>
            </div>
        </div>
        """

        # Format results for display
        display_df = results_df.copy()

        # Select and format columns if they exist
        display_columns = []
        if 'task_id' in display_df.columns:
            display_columns.append('task_id')
        if 'success' in display_df.columns:
            display_df['success'] = display_df['success'].apply(lambda x: "✅" if x else "❌")
            display_columns.append('success')
        if 'tool_called' in display_df.columns:
            display_columns.append('tool_called')
        if 'execution_time_ms' in display_df.columns:
            display_df['execution_time_ms'] = display_df['execution_time_ms'].apply(lambda x: f"{x:.0f}ms")
            display_columns.append('execution_time_ms')
        if 'total_tokens' in display_df.columns:
            display_columns.append('total_tokens')
        if 'cost_usd' in display_df.columns:
            display_df['cost_usd'] = display_df['cost_usd'].apply(lambda x: f"${x:.4f}")
            display_columns.append('cost_usd')
        if 'trace_id' in display_df.columns:
            display_columns.append('trace_id')

        if display_columns:
            display_df = display_df[display_columns]

        print(f"[DEBUG] Successfully loaded run detail for: {run_data.get('model', 'Unknown')}")

        return {
            # Hide leaderboard, show run detail
            leaderboard_screen: gr.update(visible=False),
            run_detail_screen: gr.update(visible=True),
            run_metadata_html: gr.update(value=metadata_html),
            test_cases_table: gr.update(value=display_df),
            selected_row_index: gr.update(value="")  # Clear textbox
        }

    except Exception as e:
        print(f"[ERROR] Handling HTML table row click: {e}")
        import traceback
        traceback.print_exc()
        gr.Warning(f"Error loading run details: {str(e)}")
        return {
            leaderboard_screen: gr.update(visible=True),  # Stay on leaderboard
            run_detail_screen: gr.update(visible=False),
            run_metadata_html: gr.update(),
            test_cases_table: gr.update(),
            selected_row_index: gr.update(value="")  # Clear textbox
        }


def load_run_detail(run_id):
    """Load run detail data including results dataset"""
    global current_selected_run, leaderboard_df_cache

    try:
        # Find run in cache
        df = leaderboard_df_cache
        run_data = df[df['run_id'] == run_id].iloc[0].to_dict()
        current_selected_run = run_data

        # Load results dataset
        results_dataset = run_data.get('results_dataset')
        if not results_dataset:
            return pd.DataFrame(), f"# Error\n\nNo results dataset found for this run", ""

        results_df = data_loader.load_results(results_dataset)

        # Create metadata HTML
        metadata_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
            <h2 style="margin: 0 0 10px 0;">📊 Run Detail: {run_data.get('model', 'Unknown')}</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 15px;">
                <div>
                    <strong>Agent Type:</strong> {run_data.get('agent_type', 'N/A')}<br>
                    <strong>Provider:</strong> {run_data.get('provider', 'N/A')}<br>
                    <strong>Success Rate:</strong> {run_data.get('success_rate', 0):.1f}%
                </div>
                <div>
                    <strong>Total Tests:</strong> {run_data.get('total_tests', 0)}<br>
                    <strong>Successful:</strong> {run_data.get('successful_tests', 0)}<br>
                    <strong>Failed:</strong> {run_data.get('failed_tests', 0)}
                </div>
                <div>
                    <strong>Total Cost:</strong> ${run_data.get('total_cost_usd', 0):.4f}<br>
                    <strong>Avg Duration:</strong> {run_data.get('avg_duration_ms', 0):.0f}ms<br>
                    <strong>Submitted By:</strong> {run_data.get('submitted_by', 'Unknown')}
                </div>
            </div>
        </div>
        """

        # Format results for display
        display_df = results_df.copy()

        # Select and format columns if they exist
        display_columns = []
        if 'task_id' in display_df.columns:
            display_columns.append('task_id')
        if 'success' in display_df.columns:
            display_df['success'] = display_df['success'].apply(lambda x: "✅" if x else "❌")
            display_columns.append('success')
        if 'tool_called' in display_df.columns:
            display_columns.append('tool_called')
        if 'execution_time_ms' in display_df.columns:
            display_df['execution_time_ms'] = display_df['execution_time_ms'].apply(lambda x: f"{x:.0f}ms")
            display_columns.append('execution_time_ms')
        if 'total_tokens' in display_df.columns:
            display_columns.append('total_tokens')
        if 'cost_usd' in display_df.columns:
            display_df['cost_usd'] = display_df['cost_usd'].apply(lambda x: f"${x:.4f}")
            display_columns.append('cost_usd')
        if 'trace_id' in display_df.columns:
            display_columns.append('trace_id')

        if display_columns:
            display_df = display_df[display_columns]

        return display_df, metadata_html, run_data.get('run_id', '')

    except Exception as e:
        print(f"[ERROR] load_run_detail: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(), f"# Error\n\nError loading run detail: {str(e)}", ""



# Screen 3 (Run Detail) event handlers
def on_drilldown_select(evt: gr.SelectData, df):
    """Handle row selection from DrillDown table - EXACT COPY from MockTraceMind"""
    global current_selected_run, current_drilldown_df

    try:
        # Get selected run - use currently displayed dataframe (filtered/sorted)
        selected_idx = evt.index[0]

        # Get the full run data from the displayed dataframe
        # This ensures we get the correct row even after filtering/sorting
        if current_drilldown_df is not None and not current_drilldown_df.empty:
            if selected_idx < len(current_drilldown_df):
                run_data = current_drilldown_df.iloc[selected_idx].to_dict()
            else:
                gr.Warning(f"Invalid row selection: index {selected_idx} out of bounds")
                return {}
        else:
            gr.Warning("Leaderboard data not available")
            return {}

        # IMPORTANT: Set global FIRST before any operations that might fail
        current_selected_run = run_data

        print(f"[DEBUG] Selected run: {run_data.get('model', 'Unknown')} (run_id: {run_data.get('run_id', 'N/A')[:8]}...)")

        # Load results for this run
        results_dataset = run_data.get('results_dataset')
        if not results_dataset:
            gr.Warning("No results dataset found for this run")
            return {
                leaderboard_screen: gr.update(visible=True),
                run_detail_screen: gr.update(visible=False),
                run_metadata_html: gr.update(value="<h3>No results dataset found</h3>"),
                test_cases_table: gr.update(value=pd.DataFrame())
            }

        results_df = data_loader.load_results(results_dataset)

        # Create metadata HTML
        metadata_html = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
            <h2 style="margin: 0 0 10px 0;">📊 Run Detail: {run_data.get('model', 'Unknown')}</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 15px;">
                <div>
                    <strong>Agent Type:</strong> {run_data.get('agent_type', 'N/A')}<br>
                    <strong>Provider:</strong> {run_data.get('provider', 'N/A')}<br>
                    <strong>Success Rate:</strong> {run_data.get('success_rate', 0):.1f}%
                </div>
                <div>
                    <strong>Total Tests:</strong> {run_data.get('total_tests', 0)}<br>
                    <strong>Successful:</strong> {run_data.get('successful_tests', 0)}<br>
                    <strong>Failed:</strong> {run_data.get('failed_tests', 0)}
                </div>
                <div>
                    <strong>Total Cost:</strong> ${run_data.get('total_cost_usd', 0):.4f}<br>
                    <strong>Avg Duration:</strong> {run_data.get('avg_duration_ms', 0):.0f}ms<br>
                    <strong>Submitted By:</strong> {run_data.get('submitted_by', 'Unknown')}
                </div>
            </div>
        </div>
        """

        # Format results for display
        display_df = results_df.copy()

        # Select and format columns if they exist
        display_columns = []
        if 'task_id' in display_df.columns:
            display_columns.append('task_id')
        if 'success' in display_df.columns:
            display_df['success'] = display_df['success'].apply(lambda x: "✅" if x else "❌")
            display_columns.append('success')
        if 'tool_called' in display_df.columns:
            display_columns.append('tool_called')
        if 'execution_time_ms' in display_df.columns:
            display_df['execution_time_ms'] = display_df['execution_time_ms'].apply(lambda x: f"{x:.0f}ms")
            display_columns.append('execution_time_ms')
        if 'total_tokens' in display_df.columns:
            display_columns.append('total_tokens')
        if 'cost_usd' in display_df.columns:
            display_df['cost_usd'] = display_df['cost_usd'].apply(lambda x: f"${x:.4f}")
            display_columns.append('cost_usd')
        if 'trace_id' in display_df.columns:
            display_columns.append('trace_id')

        if display_columns:
            display_df = display_df[display_columns]

        print(f"[DEBUG] Successfully loaded run detail for: {run_data.get('model', 'Unknown')}")

        return {
            # Hide leaderboard, show run detail
            leaderboard_screen: gr.update(visible=False),
            run_detail_screen: gr.update(visible=True),
            run_metadata_html: gr.update(value=metadata_html),
            test_cases_table: gr.update(value=display_df)
        }

    except Exception as e:
        print(f"[ERROR] Loading run details: {e}")
        import traceback
        traceback.print_exc()
        gr.Warning(f"Error loading run details: {e}")

        # Return updates for all output components to avoid Gradio error
        return {
            leaderboard_screen: gr.update(visible=True),  # Stay on leaderboard
            run_detail_screen: gr.update(visible=False),
            run_metadata_html: gr.update(value="<h3>Error loading run detail</h3>"),
            test_cases_table: gr.update(value=pd.DataFrame())
        }



def go_back_to_leaderboard():
    """Navigate back to leaderboard screen"""
    return {
        leaderboard_screen: gr.update(visible=True),
        run_detail_screen: gr.update(visible=False)
    }


# Build Gradio app
# Theme configuration (like MockTraceMind)
theme = gr.themes.Base(
    primary_hue="indigo",
    secondary_hue="purple",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
).set(
    body_background_fill="*neutral_50",
    body_background_fill_dark="*neutral_900",
    button_primary_background_fill="*primary_500",
    button_primary_background_fill_hover="*primary_600",
    button_primary_text_color="white",
)

with gr.Blocks(title="TraceMind-AI", theme=theme) as app:

    # Top Banner
    gr.HTML("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h1 style="color: white !important; margin: 0; font-size: 2.5em; font-weight: bold;">
            🧠 TraceMind
        </h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 1.2em;">
            Agent Evaluation Platform
        </p>
        <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0; font-size: 0.9em;">
            Powered by Gradio 6 🚀 | HuggingFace Jobs | MCP Integration
        </p>
    </div>
    """)

    # Main app container (wraps Sidebar + all screens like MockTraceMind)
    with gr.Column() as main_app_container:

        
        # Sidebar Navigation
        with gr.Sidebar():
            gr.Markdown("## 🧠 TraceMind")
            gr.Markdown("*Navigation & Controls*")
    
            gr.Markdown("---")
    
            # Navigation section
            gr.Markdown("### 🧭 Navigation")
    
            # Navigation buttons
            leaderboard_nav_btn = gr.Button("🏆 Leaderboard", variant="primary", size="lg")
            compare_nav_btn = gr.Button("⚖️ Compare", variant="secondary", size="lg")
            docs_nav_btn = gr.Button("📚 Documentation", variant="secondary", size="lg")
    
            gr.Markdown("---")
    
            # Data Controls
            gr.Markdown("### 🔄 Data Controls")
            refresh_leaderboard_btn = gr.Button("🔄 Refresh Data", variant="secondary", size="sm")
            gr.Markdown("*Reload leaderboard from HuggingFace*")
    
            gr.Markdown("---")
    
            # Filters section
            gr.Markdown("### 🔍 Global Filters")
    
            sidebar_model_filter = gr.Dropdown(
                choices=["All Models"],
                value="All Models",
                label="Model",
                info="Filter evaluations by AI model"
            )
    
            sidebar_agent_type_filter = gr.Radio(
                choices=["All", "tool", "code", "both"],
                value="All",
                label="Agent Type",
                info="Tool: Function calling | Code: Code execution | Both: Hybrid"
            )
    
        # Main content area
        # Screen 1: Main Leaderboard
        with gr.Column(visible=True) as leaderboard_screen:
            gr.Markdown("## 🏆 Agent Evaluation Leaderboard")
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
    
        # Screen 3: Run Detail
        with gr.Column(visible=False) as run_detail_screen:
            # Navigation
            with gr.Row():
                back_to_leaderboard_btn = gr.Button("⬅️ Back to Leaderboard", variant="secondary", size="sm")
    
            # Run metadata display
            run_metadata_html = gr.HTML()
    
            # Test cases table
            gr.Markdown("## 📋 Test Cases")
            test_cases_table = gr.Dataframe(
                headers=["Task ID", "Status", "Tool", "Duration", "Tokens", "Cost", "Trace ID"],
                interactive=False,
                wrap=True
            )
    
        # Event handlers
        app.load(
        fn=load_leaderboard,
        outputs=[leaderboard_by_model, model_filter, sidebar_model_filter]
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

        # Refresh button handler
        refresh_leaderboard_btn.click(
        fn=refresh_leaderboard,
        outputs=[leaderboard_by_model, model_filter, sidebar_model_filter]
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

        # Sidebar filter handlers
        def apply_sidebar_model_filter(model, sort_by_col):
            """Apply sidebar model filter to leaderboard"""
            return apply_filters(model, "All", sort_by_col), gr.update(value=model)

        sidebar_model_filter.change(
        fn=apply_sidebar_model_filter,
        inputs=[sidebar_model_filter, sort_by],
        outputs=[leaderboard_by_model, model_filter]
        )

        def apply_sidebar_agent_type_filter(agent_type):
            """Apply sidebar agent type filter to drilldown"""
            return load_drilldown(agent_type, "All"), gr.update(value=agent_type)

        sidebar_agent_type_filter.change(
        fn=apply_sidebar_agent_type_filter,
        inputs=[sidebar_agent_type_filter],
        outputs=[leaderboard_table, drilldown_agent_type]
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


        leaderboard_table.select(
        fn=on_drilldown_select,
        inputs=[leaderboard_table],  # Pass dataframe to handler (like MockTraceMind)
        outputs=[leaderboard_screen, run_detail_screen, run_metadata_html, test_cases_table]
        )

        back_to_leaderboard_btn.click(
        fn=go_back_to_leaderboard,
        inputs=[],
        outputs=[leaderboard_screen, run_detail_screen]
        )

        # HTML table row click handler (JavaScript bridge via hidden textbox)
        selected_row_index.change(
        fn=on_html_table_row_click,
        inputs=[selected_row_index],
        outputs=[leaderboard_screen, run_detail_screen, run_metadata_html, test_cases_table, selected_row_index]
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
