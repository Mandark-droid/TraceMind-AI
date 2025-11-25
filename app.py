"""
TraceMind-AI - Agent Evaluation Platform
Enterprise-grade AI agent evaluation with MCP integration

Built on Open Source Foundation:
    🔭 TraceVerde (genai_otel_instrument) - Automatic OpenTelemetry instrumentation
       for LLM frameworks (LiteLLM, Transformers, LangChain, etc.)
       GitHub: https://github.com/Mandark-droid/genai_otel_instrument
       PyPI: https://pypi.org/project/genai-otel-instrument

    📊 SMOLTRACE - Agent evaluation engine with OTEL tracing built-in
       Generates structured datasets (leaderboard, results, traces, metrics)
       GitHub: https://github.com/Mandark-droid/SMOLTRACE
       PyPI: https://pypi.org/project/smoltrace/

    The Flow: TraceVerde instruments → SMOLTRACE evaluates → TraceMind-AI visualizes
              with MCP-powered intelligence

Track 2 Submission: MCP in Action - Enterprise Category
https://huggingface.co/MCP-1st-Birthday
"""

import os
import pandas as pd
import gradio as gr
from gradio_htmlplus import HTMLPlus
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
from components.report_cards import generate_leaderboard_summary_card, generate_run_report_card, download_card_as_png_js
from screens.trace_detail import (
    create_span_visualization,
    create_span_table,
    create_gpu_metrics_dashboard,
    create_gpu_summary_cards
)
from screens.dashboard import (
    create_dashboard_ui,
    update_dashboard_data
)
from screens.compare import (
    create_compare_ui,
    on_compare_runs
)
from screens.chat import (
    create_chat_ui,
    on_send_message,
    on_clear_chat,
    on_quick_action
)
from screens.documentation import create_documentation_screen
from screens.settings import create_settings_screen
from screens.job_monitoring import create_job_monitoring_screen
from screens.mcp_helpers import (
    call_analyze_leaderboard_sync,
    call_debug_trace_sync,
    call_compare_runs_sync,
    call_analyze_results_sync
)
from utils.navigation import Navigator, Screen


# Helper function for AI insights header
def get_gemini_header() -> str:
    """
    Returns HTML header showing Gemini attribution for AI-generated insights
    """
    return """<div style="font-family: sans-serif; font-size: 0.8rem; color: #6B7280; border-bottom: 1px solid #E5E7EB; padding-bottom: 8px; margin-bottom: 8px;">
    Analyzed by <strong style="color: #111827;">Gemini-2.5-flash</strong>
    <br><span style="font-size: 0.7rem;">Provider: Gemini <img src='https://upload.wikimedia.org/wikipedia/commons/d/d9/Google_Gemini_logo_2025.svg' alt='logo' width='220' style='vertical-align: middle;'></span>
</div>

"""


# Trace Detail handlers and helpers

def create_span_details_table(spans):
    """
    Create table view of span details

    Args:
        spans: List of span dictionaries

    Returns:
        DataFrame with span details
    """
    try:
        if not spans:
            return pd.DataFrame(columns=["Span Name", "Kind", "Duration (ms)", "Tokens", "Cost (USD)", "Status"])

        rows = []
        for span in spans:
            name = span.get('name', 'Unknown')
            kind = span.get('kind', 'INTERNAL')

            # Get attributes
            attributes = span.get('attributes', {})
            if isinstance(attributes, dict) and 'openinference.span.kind' in attributes:
                kind = attributes.get('openinference.span.kind', kind)

            # Calculate duration
            start = span.get('startTime') or span.get('startTimeUnixNano', 0)
            end = span.get('endTime') or span.get('endTimeUnixNano', 0)
            duration = (end - start) / 1000000 if start and end else 0  # Convert to ms

            status = span.get('status', {}).get('code', 'OK') if isinstance(span.get('status'), dict) else 'OK'

            # Extract tokens and cost information
            tokens_str = "-"
            cost_str = "-"

            if isinstance(attributes, dict):
                # Check for token usage
                prompt_tokens = attributes.get('gen_ai.usage.prompt_tokens') or attributes.get('llm.token_count.prompt')
                completion_tokens = attributes.get('gen_ai.usage.completion_tokens') or attributes.get('llm.token_count.completion')
                total_tokens = attributes.get('llm.usage.total_tokens')

                # Build tokens string
                if prompt_tokens is not None and completion_tokens is not None:
                    total = int(prompt_tokens) + int(completion_tokens)
                    tokens_str = f"{total} ({int(prompt_tokens)}+{int(completion_tokens)})"
                elif total_tokens is not None:
                    tokens_str = str(int(total_tokens))

                # Check for cost
                cost = attributes.get('gen_ai.usage.cost.total') or attributes.get('llm.usage.cost')
                if cost is not None:
                    cost_str = f"${float(cost):.6f}"

            rows.append({
                "Span Name": name,
                "Kind": kind,
                "Duration (ms)": round(duration, 2),
                "Tokens": tokens_str,
                "Cost (USD)": cost_str,
                "Status": status
            })

        return pd.DataFrame(rows)

    except Exception as e:
        print(f"[ERROR] create_span_details_table: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=["Span Name", "Kind", "Duration (ms)", "Tokens", "Cost (USD)", "Status"])


def create_trace_metadata_html(trace_data: dict) -> str:
    """Create HTML for trace metadata display"""
    trace_id = trace_data.get('trace_id', 'Unknown')
    spans = trace_data.get('spans', [])
    if hasattr(spans, 'tolist'):
        spans = spans.tolist()
    elif not isinstance(spans, list):
        spans = list(spans) if spans is not None else []

    metadata_html = f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0 0 10px 0;">Trace Information</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div>
                <strong>Trace ID:</strong> {trace_id}<br>
                <strong>Total Spans:</strong> {len(spans)}
            </div>
        </div>
    </div>
    """
    return metadata_html


def on_test_case_select(evt: gr.SelectData, df):
    """Handle test case selection in run detail - navigate to trace detail"""
    global current_selected_run, current_selected_trace, _current_trace_info

    print(f"[DEBUG] on_test_case_select called with index: {evt.index}")

    # Helper function to return empty updates for all 8 outputs
    def return_error():
        return (
            gr.update(),  # run_detail_screen
            gr.update(),  # trace_detail_screen
            gr.update(),  # trace_title
            gr.update(),  # trace_metadata_html
            gr.update(),  # trace_thought_graph
            gr.update(),  # span_visualization
            gr.update(),  # span_details_table
            gr.update()   # span_details_json
        )

    # Check if we have a selected run
    if current_selected_run is None:
        print("[ERROR] No run selected - current_selected_run is None")
        gr.Warning("Please select a run from the leaderboard first")
        return return_error()

    try:
        # Get selected test case
        selected_idx = evt.index[0]
        if df is None or df.empty or selected_idx >= len(df):
            gr.Warning("Invalid test case selection")
            return return_error()

        test_case = df.iloc[selected_idx].to_dict()
        trace_id = test_case.get('trace_id')

        print(f"[DEBUG] Selected test case: {test_case.get('task_id', 'Unknown')} (trace_id: {trace_id})")

        # Load trace data
        traces_dataset = current_selected_run.get('traces_dataset')
        if not traces_dataset:
            gr.Warning("No traces dataset found in current run")
            return return_error()

        # Update global trace info for MCP debug_trace tool
        _current_trace_info["trace_id"] = trace_id
        _current_trace_info["traces_repo"] = traces_dataset
        print(f"[MCP] Updated trace info for debug_trace: trace_id={trace_id}, traces_repo={traces_dataset}")

        trace_data = data_loader.get_trace_by_id(traces_dataset, trace_id)

        if not trace_data:
            gr.Warning(f"Trace not found: {trace_id}")
            return return_error()

        current_selected_trace = trace_data

        # Get spans and ensure it's a list
        spans = trace_data.get('spans', [])
        if hasattr(spans, 'tolist'):
            spans = spans.tolist()
        elif not isinstance(spans, list):
            spans = list(spans) if spans is not None else []

        print(f"[DEBUG] Loaded trace with {len(spans)} spans")

        # Create visualizations
        span_viz_plot = create_span_visualization(spans, trace_id)
        # Process spans for JSON display (create_span_table returns gr.JSON component, we need the data)
        simplified_spans = []
        for span in spans:
            # Helper to get timestamp
            def get_timestamp(s, field_name):
                variations = [field_name, field_name.lower(), field_name.replace('Time', 'TimeUnixNano')]
                for var in variations:
                    if var in s:
                        value = s[var]
                        return int(value) if isinstance(value, str) else value
                return 0

            start_time = get_timestamp(span, 'startTime')
            end_time = get_timestamp(span, 'endTime')
            duration_ms = (end_time - start_time) / 1000000 if (end_time and start_time) else 0

            span_id = span.get('spanId') or span.get('span_id') or 'N/A'
            parent_id = span.get('parentSpanId') or span.get('parent_span_id') or 'root'

            simplified_spans.append({
                "Span ID": span_id,
                "Parent": parent_id,
                "Name": span.get('name', 'N/A'),
                "Kind": span.get('kind', 'N/A'),
                "Duration (ms)": round(duration_ms, 2),
                "Attributes": span.get('attributes', {}),
                "Status": span.get('status', {}).get('code', 'UNKNOWN')
            })

        span_details_data = simplified_spans

        # Create thought graph
        from components.thought_graph import create_thought_graph as create_network_graph
        thought_graph_plot = create_network_graph(spans, trace_id)

        # Create span details table
        span_table_df = create_span_details_table(spans)

        # Return dictionary with visibility updates and data
        return {
            run_detail_screen: gr.update(visible=False),
            trace_detail_screen: gr.update(visible=True),
            trace_title: gr.update(value=f"# 🔍 Trace Detail: {trace_id}"),
            trace_metadata_html: gr.update(value=create_trace_metadata_html(trace_data)),
            trace_thought_graph: gr.update(value=thought_graph_plot),
            span_visualization: gr.update(value=span_viz_plot),
            span_details_table: gr.update(value=span_table_df),
            span_details_json: gr.update(value=span_details_data)
        }

    except Exception as e:
        print(f"[ERROR] on_test_case_select failed: {e}")
        import traceback
        traceback.print_exc()
        gr.Warning(f"Error loading trace: {e}")
        return return_error()



def create_performance_charts(results_df):
    """
    Create performance analysis charts for the Performance tab

    Args:
        results_df: DataFrame with test results

    Returns:
        Plotly figure with performance metrics
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    try:
        if results_df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No performance data available", showarrow=False)
            return fig

        # Create 2x2 subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Response Time per Test",
                "Token Usage per Test",
                "Cost per Test",
                "Success vs Failure"
            ),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "pie"}]]
        )

        # 1. Response Time per Test (Bar)
        if 'execution_time_ms' in results_df.columns:
            test_indices = list(range(len(results_df)))
            fig.add_trace(
                go.Bar(
                    x=test_indices,
                    y=results_df['execution_time_ms'],
                    marker_color='#3498DB',
                    name='Response Time',
                    showlegend=False
                ),
                row=1, col=1
            )
            fig.update_xaxes(title_text="Test Index", row=1, col=1)
            fig.update_yaxes(title_text="Time (ms)", row=1, col=1)

        # 2. Token Usage per Test (Bar)
        if 'total_tokens' in results_df.columns:
            test_indices = list(range(len(results_df)))
            fig.add_trace(
                go.Bar(
                    x=test_indices,
                    y=results_df['total_tokens'],
                    marker_color='#9B59B6',
                    name='Tokens',
                    showlegend=False
                ),
                row=1, col=2
            )
            fig.update_xaxes(title_text="Test Index", row=1, col=2)
            fig.update_yaxes(title_text="Tokens", row=1, col=2)

        # 3. Cost per Test (Bar)
        if 'cost_usd' in results_df.columns:
            test_indices = list(range(len(results_df)))
            fig.add_trace(
                go.Bar(
                    x=test_indices,
                    y=results_df['cost_usd'],
                    marker_color='#E67E22',
                    name='Cost',
                    showlegend=False
                ),
                row=2, col=1
            )
            fig.update_xaxes(title_text="Test Index", row=2, col=1)
            fig.update_yaxes(title_text="Cost (USD)", row=2, col=1)

        # 4. Success vs Failure (Pie)
        if 'success' in results_df.columns:
            # Convert to boolean if needed
            success_series = results_df['success']
            if success_series.dtype == object:
                success_series = success_series == "✅"

            success_count = int(success_series.sum())
            failure_count = len(results_df) - success_count

            fig.add_trace(
                go.Pie(
                    labels=['Success', 'Failure'],
                    values=[success_count, failure_count],
                    marker_colors=['#2ECC71', '#E74C3C'],
                    showlegend=True
                ),
                row=2, col=2
            )

        # Update layout
        fig.update_layout(
            height=700,
            showlegend=False,
            title_text="Performance Analysis Dashboard",
            title_x=0.5
        )

        return fig

    except Exception as e:
        print(f"[ERROR] create_performance_charts: {e}")
        import traceback
        traceback.print_exc()
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating charts: {str(e)}", showarrow=False)
        return fig



def go_back_to_run_detail():
    """Navigate from trace detail back to run detail"""
    return {
        run_detail_screen: gr.update(visible=True),
        trace_detail_screen: gr.update(visible=False)
    }


# Initialize data loader
data_loader = create_data_loader_from_env()
navigator = Navigator()

# Pre-load and cache the leaderboard data before building UI
print("Pre-loading leaderboard data from HuggingFace...")
leaderboard_df_cache = data_loader.load_leaderboard()
print(f"Loaded {len(leaderboard_df_cache)} evaluation runs")

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
    providers = ["All"] + sorted(df['provider'].unique().tolist())

    return html, gr.update(choices=models), gr.update(choices=models), gr.update(choices=providers)


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


def apply_leaderboard_filters(agent_type, provider, sort_by_col, sort_order):
    """Apply filters and sorting to styled HTML leaderboard"""
    global leaderboard_df_cache, model_filter

    df = leaderboard_df_cache.copy() if leaderboard_df_cache is not None else data_loader.load_leaderboard()

    # Apply model filter from sidebar
    selected_model = model_filter.value if hasattr(model_filter, 'value') else "All Models"
    if selected_model != "All Models":
        df = df[df['model'] == selected_model]

    # Apply agent type filter
    if agent_type != "All":
        df = df[df['agent_type'] == agent_type]

    # Apply provider filter
    if provider != "All":
        df = df[df['provider'] == provider]

    # Sort
    ascending = (sort_order == "Ascending")
    df = df.sort_values(by=sort_by_col, ascending=ascending)

    html = generate_leaderboard_html(df, sort_by_col, ascending)
    return html


def apply_drilldown_filters(agent_type, provider, sort_by_col, sort_order):
    """Apply filters and sorting to drilldown table"""
    global leaderboard_df_cache

    df = leaderboard_df_cache.copy() if leaderboard_df_cache is not None else data_loader.load_leaderboard()

    # Apply model filter from sidebar
    selected_model = model_filter.value if hasattr(model_filter, 'value') else "All Models"
    if selected_model != "All Models":
        df = df[df['model'] == selected_model]

    # Apply agent type filter
    if agent_type != "All":
        df = df[df['agent_type'] == agent_type]

    # Apply provider filter
    if provider != "All":
        df = df[df['provider'] == provider]

    # Sort
    ascending = (sort_order == "Ascending")
    df = df.sort_values(by=sort_by_col, ascending=ascending).reset_index(drop=True)

    # Prepare simplified dataframe for display
    display_df = df[[
        'run_id', 'model', 'agent_type', 'provider', 'success_rate',
        'total_tests', 'avg_duration_ms', 'total_cost_usd', 'submitted_by'
    ]].copy()
    display_df.columns = ['Run ID', 'Model', 'Agent Type', 'Provider', 'Success Rate', 'Tests', 'Duration (ms)', 'Cost (USD)', 'Submitted By']

    return gr.update(value=display_df)


def apply_sidebar_filters(selected_model, selected_agent_type):
    """Apply sidebar filters to leaderboard (DrillDown tab removed)"""
    global leaderboard_df_cache

    df = leaderboard_df_cache.copy() if leaderboard_df_cache is not None else data_loader.load_leaderboard()

    # Apply model filter
    if selected_model != "All Models":
        df = df[df['model'] == selected_model]

    # Apply agent type filter
    if selected_agent_type != "All":
        df = df[df['agent_type'] == selected_agent_type]

    # For HTML leaderboard
    sorted_df = df.sort_values(by='success_rate', ascending=False).reset_index(drop=True)
    html = generate_leaderboard_html(sorted_df, 'success_rate', False)

    # Update trends
    trends_fig = create_trends_plot(df)

    # Update compare dropdowns
    compare_choices = []
    for _, row in df.iterrows():
        label = f"{row.get('model', 'Unknown')} - {row.get('timestamp', 'N/A')}"
        # Use composite key: run_id|timestamp to ensure uniqueness
        value = f"{row.get('run_id', '')}|{row.get('timestamp', '')}"
        if value:
            compare_choices.append((label, value))

    return {
        leaderboard_by_model: gr.update(value=html),
        # leaderboard_table removed (DrillDown tab is commented out)
        trends_plot: gr.update(value=trends_fig),
        compare_components['compare_run_a_dropdown']: gr.update(choices=compare_choices),
        compare_components['compare_run_b_dropdown']: gr.update(choices=compare_choices)
    }


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


def get_chart_explanation(viz_type):
    """Get explanation text for the selected chart type"""
    explanations = {
        "🔥 Performance Heatmap": """
#### 🔥 Performance Heatmap

**What it shows:** All models compared across all metrics in one view

**How to read it:**
- 🟢 **Green cells** = Better performance (higher is better)
- 🟡 **Yellow cells** = Average performance
- 🔴 **Red cells** = Worse performance (needs improvement)

**Metrics displayed:**
- Success Rate (%), Avg Duration (ms), Total Cost ($)
- CO2 Emissions (g), GPU Utilization (%), Total Tokens

**Use it to:** Quickly identify which models excel in which areas
        """,

        "⚡ Speed vs Accuracy": """
#### ⚡ Speed vs Accuracy Trade-off

**What it shows:** The relationship between model speed and accuracy

**How to read it:**
- **X-axis** = Average Duration (log scale) - left is faster
- **Y-axis** = Success Rate (%) - higher is better
- **Bubble size** = Total Cost - larger bubbles are more expensive
- **Color** = Agent Type (tool/code/both)

**Sweet spot:** Top-left quadrant = ⭐ **Fast & Accurate** models

**Quadrant lines:**
- Median lines split the chart into 4 zones
- Models above/left of medians are better than average

**Use it to:** Find models that balance speed and accuracy for your needs
        """,

        "💰 Cost Efficiency": """
#### 💰 Cost-Performance Efficiency

**What it shows:** Best value-for-money models

**How to read it:**
- **X-axis** = Total Cost (log scale) - left is cheaper
- **Y-axis** = Success Rate (%) - higher is better
- **Bubble size** = Duration - smaller bubbles are faster
- **Color** = Provider (blue=API, green=GPU/local)
- **⭐ Stars** = Top 3 most efficient models

**Cost bands:**
- 🟢 **Budget** = < $0.01 per run
- 🟡 **Mid-Range** = $0.01 - $0.10 per run
- 🟠 **Premium** = > $0.10 per run

**Efficiency metric:** Success Rate ÷ Cost (higher is better)

**Use it to:** Maximize ROI by finding models with best success-to-cost ratio
        """
    }

    return explanations.get(viz_type, explanations["🔥 Performance Heatmap"])


def update_analytics(viz_type):
    """Update analytics chart and explanation based on visualization type"""
    df = data_loader.load_leaderboard()

    # Get chart
    if "Heatmap" in viz_type:
        chart = create_performance_heatmap(df)
    elif "Speed" in viz_type:
        chart = create_speed_accuracy_scatter(df)
    else:
        chart = create_cost_efficiency_scatter(df)

    # Get explanation
    explanation = get_chart_explanation(viz_type)

    return chart, explanation


def generate_card(top_n):
    """Generate summary card HTML"""
    df = data_loader.load_leaderboard()

    if df is None or df.empty:
        return "<p>No data available</p>", gr.update(visible=False)

    html = generate_leaderboard_summary_card(df, top_n)
    return html, gr.update(visible=True)


def generate_insights():
    """Generate AI insights summary using MCP server"""
    try:
        # Load leaderboard to check if data exists
        df = data_loader.load_leaderboard()

        if df is None or df.empty:
            return "## 📊 AI Insights\n\nNo leaderboard data available. Please refresh the data."

        # Call MCP server's analyze_leaderboard tool
        print("[MCP] Calling analyze_leaderboard MCP tool...")
        insights = call_analyze_leaderboard_sync(
            leaderboard_repo="kshitijthakkar/smoltrace-leaderboard",
            metric_focus="overall",
            time_range="last_week",
            top_n=5
        )

        return get_gemini_header() + insights

    except Exception as e:
        print(f"[ERROR] generate_insights: {e}")
        import traceback
        traceback.print_exc()
        return f"## 📊 AI Insights\n\n❌ **Error generating insights**: {str(e)}\n\nPlease check:\n- MCP server is running\n- Network connectivity\n- Leaderboard dataset is accessible"


# Global variable to store current trace info for debug_trace MCP tool
_current_trace_info = {"trace_id": None, "traces_repo": None}


def ask_about_trace(question: str) -> str:
    """
    Call debug_trace MCP tool to answer questions about current trace

    Args:
        question: User's question about the trace

    Returns:
        AI-powered answer from MCP server
    """
    global _current_trace_info

    try:
        if not _current_trace_info["trace_id"] or not _current_trace_info["traces_repo"]:
            return "❌ **No trace selected**\n\nPlease navigate to a trace first by clicking on a test case from the Run Detail screen."

        if not question or question.strip() == "":
            return "❌ **Please enter a question**\n\nFor example:\n- Why was the tool called twice?\n- Which step took the most time?\n- Why did this test fail?"

        print(f"[MCP] Calling debug_trace MCP tool for trace_id: {_current_trace_info['trace_id']}")

        # Call MCP server's debug_trace tool
        answer = call_debug_trace_sync(
            trace_id=_current_trace_info["trace_id"],
            traces_repo=_current_trace_info["traces_repo"],
            question=question
        )

        return get_gemini_header() + answer

    except Exception as e:
        print(f"[ERROR] ask_about_trace: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ **Error asking about trace**: {str(e)}\n\nPlease check:\n- MCP server is running\n- Network connectivity\n- Trace data is accessible"


# Global variable to store current comparison for compare_runs MCP tool
_current_comparison = {"run_id_1": None, "run_id_2": None}


def handle_compare_runs(run_a_id: str, run_b_id: str, leaderboard_df, components):
    """
    Wrapper function to handle run comparison and update global state

    Args:
        run_a_id: ID of first run (composite key: run_id|timestamp)
        run_b_id: ID of second run (composite key: run_id|timestamp)
        leaderboard_df: Full leaderboard dataframe
        components: Dictionary of Gradio components

    Returns:
        Dictionary of component updates from on_compare_runs
    """
    global _current_comparison

    # Parse composite keys (run_id|timestamp) to extract just the run_id
    run_a_parts = run_a_id.split('|') if run_a_id else []
    run_b_parts = run_b_id.split('|') if run_b_id else []

    # Extract just the run_id portion for MCP server
    run_a_id_parsed = run_a_parts[0] if len(run_a_parts) >= 1 else run_a_id
    run_b_id_parsed = run_b_parts[0] if len(run_b_parts) >= 1 else run_b_id

    # Update global state for MCP compare_runs tool
    _current_comparison["run_id_1"] = run_a_id_parsed
    _current_comparison["run_id_2"] = run_b_id_parsed
    print(f"[MCP] Updated comparison state: {run_a_id_parsed} vs {run_b_id_parsed}")

    # Call the original compare function (with original composite keys)
    from screens.compare import on_compare_runs
    return on_compare_runs(run_a_id, run_b_id, leaderboard_df, components)


def generate_ai_comparison(comparison_focus: str) -> str:
    """
    Call compare_runs MCP tool to generate AI insights about run comparison

    Args:
        comparison_focus: Focus area - "comprehensive", "cost", "performance", or "eco_friendly"

    Returns:
        AI-powered comparison analysis from MCP server
    """
    global _current_comparison

    try:
        if not _current_comparison["run_id_1"] or not _current_comparison["run_id_2"]:
            return "❌ **No runs selected for comparison**\n\nPlease select two runs and click 'Compare Selected Runs' first."

        print(f"[MCP] Calling compare_runs MCP tool: {_current_comparison['run_id_1']} vs {_current_comparison['run_id_2']}")

        # Call MCP server's compare_runs tool
        insights = call_compare_runs_sync(
            run_id_1=_current_comparison["run_id_1"],
            run_id_2=_current_comparison["run_id_2"],
            leaderboard_repo="kshitijthakkar/smoltrace-leaderboard",
            comparison_focus=comparison_focus
        )

        return get_gemini_header() + insights

    except Exception as e:
        print(f"[ERROR] generate_ai_comparison: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ **Error generating AI comparison**: {str(e)}\n\nPlease check:\n- MCP server is running\n- Network connectivity\n- Leaderboard dataset is accessible"


# Global variable to store current run's results dataset for analyze_results MCP tool
_current_run_results_repo = None


def generate_run_ai_insights(focus_area: str, max_rows: int) -> str:
    """
    Call analyze_results MCP tool to generate AI insights about run results

    Args:
        focus_area: Focus area - "overall", "failures", "performance", or "tools"
        max_rows: Maximum number of test cases to analyze

    Returns:
        AI-powered results analysis from MCP server
    """
    global _current_run_results_repo

    try:
        if not _current_run_results_repo:
            return "❌ **No run selected**\n\nPlease navigate to a run detail first by clicking on a run from the Leaderboard screen."

        print(f"[MCP] Calling analyze_results MCP tool for: {_current_run_results_repo}")

        # Call MCP server's analyze_results tool
        insights = call_analyze_results_sync(
            results_repo=_current_run_results_repo,
            focus_area=focus_area,
            max_rows=max_rows
        )

        return get_gemini_header() + insights

    except Exception as e:
        print(f"[ERROR] generate_run_ai_insights: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ **Error generating run insights**: {str(e)}\n\nPlease check:\n- MCP server is running\n- Network connectivity\n- Results dataset is accessible"


def on_html_table_row_click(row_index_str):
    """Handle row click from HTML table via JavaScript (hidden textbox bridge)"""
    global current_selected_run, leaderboard_df_cache, _current_run_results_repo

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
                run_card_html: gr.update(),
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
                run_card_html: gr.update(),
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
                run_card_html: gr.update(),
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

        # Update global state for MCP analyze_results tool
        _current_run_results_repo = results_dataset
        print(f"[MCP] Updated results repo for analyze_results: {results_dataset}")

        results_df = data_loader.load_results(results_dataset)

        # Generate performance chart
        perf_chart = create_performance_charts(results_df)

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

        # Generate run report card HTML
        run_card_html_content = generate_run_report_card(run_data)

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

        # Load GPU metrics (if available)
        gpu_summary_html = "<div style='padding: 20px; text-align: center;'>⚠️ No GPU metrics available (expected for API models)</div>"
        gpu_plot = None
        gpu_json_data = {}

        try:
            if 'metrics_dataset' in run_data and run_data.get('metrics_dataset'):
                metrics_dataset = run_data['metrics_dataset']
                gpu_metrics_data = data_loader.load_metrics(metrics_dataset)

                if gpu_metrics_data is not None and not gpu_metrics_data.empty:
                    from screens.trace_detail import create_gpu_metrics_dashboard, create_gpu_summary_cards
                    gpu_plot = create_gpu_metrics_dashboard(gpu_metrics_data)
                    gpu_summary_html = create_gpu_summary_cards(gpu_metrics_data)
                    gpu_json_data = gpu_metrics_data.to_dict('records')
        except Exception as e:
            print(f"[WARNING] Could not load GPU metrics for run: {e}")

        print(f"[DEBUG] Successfully loaded run detail for: {run_data.get('model', 'Unknown')}")

        return {
            # Hide leaderboard, show run detail
            leaderboard_screen: gr.update(visible=False),
            run_detail_screen: gr.update(visible=True),
            run_metadata_html: gr.update(value=metadata_html),
            test_cases_table: gr.update(value=display_df),
            run_card_html: gr.update(value=run_card_html_content),
            performance_charts: gr.update(value=perf_chart),
            selected_row_index: gr.update(value=""),  # Clear textbox
            run_gpu_summary_cards_html: gr.update(value=gpu_summary_html),
            run_gpu_metrics_plot: gr.update(value=gpu_plot),
            run_gpu_metrics_json: gr.update(value=gpu_json_data)
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
            run_card_html: gr.update(),
            performance_charts: gr.update(),
            selected_row_index: gr.update(value=""),  # Clear textbox
            run_gpu_summary_cards_html: gr.update(),
            run_gpu_metrics_plot: gr.update(),
            run_gpu_metrics_json: gr.update()
        }


def load_run_detail(run_id):
    """Load run detail data including results dataset"""
    global current_selected_run, leaderboard_df_cache, _current_run_results_repo

    try:
        # Find run in cache
        df = leaderboard_df_cache
        run_data = df[df['run_id'] == run_id].iloc[0].to_dict()
        current_selected_run = run_data

        # Load results dataset
        results_dataset = run_data.get('results_dataset')
        if not results_dataset:
            return pd.DataFrame(), f"# Error\n\nNo results dataset found for this run", ""

        # Update global state for MCP analyze_results tool
        _current_run_results_repo = results_dataset
        print(f"[MCP] Updated results repo for analyze_results (load_run_detail): {results_dataset}")

        results_df = data_loader.load_results(results_dataset)

        # Generate performance chart
        perf_chart = create_performance_charts(results_df)

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

        # Generate run report card HTML
        run_card_html_content = generate_run_report_card(run_data)

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
    global current_selected_run, current_drilldown_df, _current_run_results_repo

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
                test_cases_table: gr.update(value=pd.DataFrame()),
                performance_charts: gr.update(),
                run_card_html: gr.update()
            }

        # Update global state for MCP analyze_results tool
        _current_run_results_repo = results_dataset
        print(f"[MCP] Updated results repo for analyze_results (on_drilldown_select): {results_dataset}")

        results_df = data_loader.load_results(results_dataset)

        # Generate performance chart
        perf_chart = create_performance_charts(results_df)

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

        # Generate run report card HTML
        run_card_html_content = generate_run_report_card(run_data)

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

        # Load GPU metrics (if available)
        gpu_summary_html = "<div style='padding: 20px; text-align: center;'>⚠️ No GPU metrics available (expected for API models)</div>"
        gpu_plot = None
        gpu_json_data = {}

        try:
            if 'metrics_dataset' in run_data and run_data.get('metrics_dataset'):
                metrics_dataset = run_data['metrics_dataset']
                gpu_metrics_data = data_loader.load_metrics(metrics_dataset)

                if gpu_metrics_data is not None and not gpu_metrics_data.empty:
                    from screens.trace_detail import create_gpu_metrics_dashboard, create_gpu_summary_cards
                    gpu_plot = create_gpu_metrics_dashboard(gpu_metrics_data)
                    gpu_summary_html = create_gpu_summary_cards(gpu_metrics_data)
                    gpu_json_data = gpu_metrics_data.to_dict('records')
        except Exception as e:
            print(f"[WARNING] Could not load GPU metrics for run: {e}")

        print(f"[DEBUG] Successfully loaded run detail for: {run_data.get('model', 'Unknown')}")

        return {
            # Hide leaderboard, show run detail
            leaderboard_screen: gr.update(visible=False),
            run_detail_screen: gr.update(visible=True),
            run_metadata_html: gr.update(value=metadata_html),
            test_cases_table: gr.update(value=display_df),
            performance_charts: gr.update(value=perf_chart),
            run_card_html: gr.update(value=run_card_html_content),
            run_gpu_summary_cards_html: gr.update(value=gpu_summary_html),
            run_gpu_metrics_plot: gr.update(value=gpu_plot),
            run_gpu_metrics_json: gr.update(value=gpu_json_data)
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
            test_cases_table: gr.update(value=pd.DataFrame()),
            performance_charts: gr.update(),
            run_card_html: gr.update(),
            run_gpu_summary_cards_html: gr.update(),
            run_gpu_metrics_plot: gr.update(),
            run_gpu_metrics_json: gr.update()
        }



def on_html_leaderboard_select(evt: gr.SelectData):
    """Handle row selection from HTMLPlus leaderboard (By Model tab)"""
    global current_selected_run, leaderboard_df_cache, _current_run_results_repo

    try:
        # HTMLPlus returns data attributes from the selected row
        # evt.index = CSS selector that was matched (e.g., "tr")
        # evt.value = dictionary of data-* attributes from the HTML element

        print(f"[DEBUG] HTMLPlus event triggered")
        print(f"[DEBUG] evt.index: {evt.index}")
        print(f"[DEBUG] evt.value type: {type(evt.value)}")
        print(f"[DEBUG] evt.value keys: {list(evt.value.keys()) if isinstance(evt.value, dict) else 'Not a dict'}")
        print(f"[DEBUG] evt.value: {evt.value}")

        if evt.index != "tr":
            gr.Warning("Invalid selection")
            return {
                leaderboard_screen: gr.update(visible=True),
                run_detail_screen: gr.update(visible=False),
                run_metadata_html: gr.update(value="<h3>Invalid selection</h3>"),
                test_cases_table: gr.update(value=pd.DataFrame()),
                performance_charts: gr.update(),
                run_card_html: gr.update(),
                run_gpu_summary_cards_html: gr.update(),
                run_gpu_metrics_plot: gr.update(),
                run_gpu_metrics_json: gr.update()
            }

        # Get the run_id from the data attributes
        # Note: HTML data-run-id becomes runId in JavaScript (camelCase conversion)
        row_data = evt.value
        run_id = row_data.get('runId')  # JavaScript converts data-run-id to runId

        if not run_id:
            gr.Warning("No run ID found in selection")
            print(f"[ERROR] No run_id found. Available keys: {list(row_data.keys())}")
            return {
                leaderboard_screen: gr.update(visible=True),
                run_detail_screen: gr.update(visible=False),
                run_metadata_html: gr.update(value="<h3>No run ID found</h3>"),
                test_cases_table: gr.update(value=pd.DataFrame()),
                performance_charts: gr.update(),
                run_card_html: gr.update(),
                run_gpu_summary_cards_html: gr.update(),
                run_gpu_metrics_plot: gr.update(),
                run_gpu_metrics_json: gr.update()
            }

        print(f"[DEBUG] HTMLPlus selected row with run_id: {run_id[:8]}...")

        # Find the full run data from the cached leaderboard dataframe using run_id
        if leaderboard_df_cache is not None and not leaderboard_df_cache.empty:
            matching_rows = leaderboard_df_cache[leaderboard_df_cache['run_id'] == run_id]
            if not matching_rows.empty:
                run_data = matching_rows.iloc[0].to_dict()
            else:
                gr.Warning(f"Run ID {run_id[:8]}... not found in leaderboard data")
                return {
                    leaderboard_screen: gr.update(visible=True),
                    run_detail_screen: gr.update(visible=False),
                    run_metadata_html: gr.update(value="<h3>Run not found</h3>"),
                    test_cases_table: gr.update(value=pd.DataFrame()),
                    performance_charts: gr.update(),
                    run_card_html: gr.update(),
                    run_gpu_summary_cards_html: gr.update(),
                    run_gpu_metrics_plot: gr.update(),
                    run_gpu_metrics_json: gr.update()
                }
        else:
            gr.Warning("Leaderboard data not available")
            return {
                leaderboard_screen: gr.update(visible=True),
                run_detail_screen: gr.update(visible=False),
                run_metadata_html: gr.update(value="<h3>Leaderboard data not available</h3>"),
                test_cases_table: gr.update(value=pd.DataFrame()),
                performance_charts: gr.update(),
                run_card_html: gr.update(),
                run_gpu_summary_cards_html: gr.update(),
                run_gpu_metrics_plot: gr.update(),
                run_gpu_metrics_json: gr.update()
            }

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
                test_cases_table: gr.update(value=pd.DataFrame()),
                performance_charts: gr.update(),
                run_card_html: gr.update(),
                run_gpu_summary_cards_html: gr.update(),
                run_gpu_metrics_plot: gr.update(),
                run_gpu_metrics_json: gr.update()
            }

        # Update global state for MCP analyze_results tool
        _current_run_results_repo = results_dataset
        print(f"[MCP] Updated results repo for analyze_results (on_html_leaderboard_select): {results_dataset}")

        results_df = data_loader.load_results(results_dataset)

        # Generate performance chart
        perf_chart = create_performance_charts(results_df)

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

        # Generate run report card HTML
        run_card_html_content = generate_run_report_card(run_data)

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

        # Load GPU metrics (if available)
        gpu_summary_html = "<div style='padding: 20px; text-align: center;'>⚠️ No GPU metrics available (expected for API models)</div>"
        gpu_plot = None
        gpu_json_data = {}

        try:
            if 'metrics_dataset' in run_data and run_data.get('metrics_dataset'):
                metrics_dataset = run_data['metrics_dataset']
                gpu_metrics_data = data_loader.load_metrics(metrics_dataset)

                if gpu_metrics_data is not None and not gpu_metrics_data.empty:
                    from screens.trace_detail import create_gpu_metrics_dashboard, create_gpu_summary_cards
                    gpu_plot = create_gpu_metrics_dashboard(gpu_metrics_data)
                    gpu_summary_html = create_gpu_summary_cards(gpu_metrics_data)
                    gpu_json_data = gpu_metrics_data.to_dict('records')
        except Exception as e:
            print(f"[WARNING] Could not load GPU metrics for run: {e}")

        print(f"[DEBUG] Successfully loaded run detail for: {run_data.get('model', 'Unknown')}")

        return {
            # Hide leaderboard, show run detail
            leaderboard_screen: gr.update(visible=False),
            run_detail_screen: gr.update(visible=True),
            run_metadata_html: gr.update(value=metadata_html),
            test_cases_table: gr.update(value=display_df),
            performance_charts: gr.update(value=perf_chart),
            run_card_html: gr.update(value=run_card_html_content),
            run_gpu_summary_cards_html: gr.update(value=gpu_summary_html),
            run_gpu_metrics_plot: gr.update(value=gpu_plot),
            run_gpu_metrics_json: gr.update(value=gpu_json_data)
        }

    except Exception as e:
        print(f"[ERROR] Loading run details from HTMLPlus: {e}")
        import traceback
        traceback.print_exc()
        gr.Warning(f"Error loading run details: {e}")

        # Return updates for all output components to avoid Gradio error
        return {
            leaderboard_screen: gr.update(visible=True),  # Stay on leaderboard
            run_detail_screen: gr.update(visible=False),
            run_metadata_html: gr.update(value="<h3>Error loading run detail</h3>"),
            test_cases_table: gr.update(value=pd.DataFrame()),
            performance_charts: gr.update(),
            run_card_html: gr.update(),
            run_gpu_summary_cards_html: gr.update(),
            run_gpu_metrics_plot: gr.update(),
            run_gpu_metrics_json: gr.update()
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
            Powered by Gradio 🚀 | HuggingFace Jobs | TraceVerde | SmolTrace | MCP | Gemini | Modal
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
            dashboard_nav_btn = gr.Button("📊 Dashboard", variant="primary", size="lg")
            leaderboard_nav_btn = gr.Button("🏆 Leaderboard", variant="secondary", size="lg")
            new_eval_nav_btn = gr.Button("▶️ New Evaluation", variant="secondary", size="lg")
            compare_nav_btn = gr.Button("⚖️ Compare", variant="secondary", size="lg")
            chat_nav_btn = gr.Button("🤖 Agent Chat", variant="secondary", size="lg")
            job_monitoring_nav_btn = gr.Button("🔍 Job Monitoring", variant="secondary", size="lg")
            synthetic_data_nav_btn = gr.Button("🔬 Synthetic Data", variant="secondary", size="lg")
            docs_nav_btn = gr.Button("📚 Documentation", variant="secondary", size="lg")
            settings_nav_btn = gr.Button("⚙️ Settings", variant="secondary", size="lg")

            gr.Markdown("---")
    
            # Data Controls
            gr.Markdown("### 🔄 Data Controls")
            refresh_leaderboard_btn = gr.Button("🔄 Refresh Data", variant="secondary", size="sm")
            gr.Markdown("*Reload leaderboard from HuggingFace*")
    
            gr.Markdown("---")
    
            # Filters section
            gr.Markdown("### 🔍 Filters")

            model_filter = gr.Dropdown(
                choices=["All Models"],
                value="All Models",
                label="Model",
                info="Filter evaluations by AI model. Select 'All Models' to see all runs."
            )

            sidebar_agent_type_filter = gr.Radio(
                choices=["All", "tool", "code", "both"],
                value="All",
                label="Agent Type",
                info="Tool: Function calling agents | Code: Code execution | Both: Hybrid agents"
            )

        # Main content area
        # Screen 0: Dashboard
        dashboard_screen, dashboard_components = create_dashboard_ui()

        # Screen 1: Main Leaderboard
        with gr.Column(visible=False) as leaderboard_screen:
            gr.Markdown("## 🏆 Agent Evaluation Leaderboard")
            with gr.Tabs():
                with gr.TabItem("🏆 Leaderboard"):
                    gr.Markdown("*Styled leaderboard with inline filters*")

                    # User Guide Accordion
                    with gr.Accordion("📖 How to Use the Leaderboard", open=False):
                        gr.Markdown("""
                        ### 🏆 Interactive Leaderboard View

                        **What is this tab?**
                        The main leaderboard displays all evaluation runs in a styled HTML table with color-coded performance indicators.

                        **How to use it:**
                        - 🎨 **Visual Design**: Gradient cards with model logos and performance metrics
                        - 🔍 **Filters**: Use agent type, provider, and sorting controls above
                        - 📊 **Sort Options**: Click "Sort By" to order by success rate, cost, duration, or tokens
                        - 👆 **Clickable Rows**: Click on any row to navigate to the detailed run view

                        **Performance Indicators:**
                        - 🟢 Green metrics = Excellent performance
                        - 🟡 Yellow metrics = Average performance
                        - 🔴 Red metrics = Needs improvement

                        **Navigation:**
                        - 🖱️ Click any leaderboard row to view detailed run results
                        - See test-by-test breakdown, cost analysis, and execution traces
                        - Use the sidebar filters to narrow down by model before drilling down

                        **Tips:**
                        - Use sidebar filters to narrow down by model
                        - Apply inline filters for more granular control
                        - Click any row to explore detailed results and traces
                        """)

                    # Inline filters for styled leaderboard
                    with gr.Row():
                        with gr.Column(scale=1):
                            agent_type_filter = gr.Radio(
                                choices=["All", "tool", "code", "both"],
                                value="All",
                                label="Agent Type",
                                info="Filter by agent type"
                            )
                        with gr.Column(scale=1):
                            provider_filter = gr.Dropdown(
                                choices=["All"],
                                value="All",
                                label="Provider",
                                info="Filter by provider"
                            )
                        with gr.Column(scale=1):
                            sort_by_dropdown = gr.Dropdown(
                                choices=["success_rate", "total_cost_usd", "avg_duration_ms", "total_tokens"],
                                value="success_rate",
                                label="Sort By",
                                info="Choose metric to sort the leaderboard by"
                            )
                        with gr.Column(scale=1):
                            sort_order = gr.Radio(
                                choices=["Descending", "Ascending"],
                                value="Descending",
                                label="Sort Order"
                            )

                    with gr.Row():
                        apply_filters_btn = gr.Button("🔍 Apply Filters", variant="primary", size="sm")

                    # Styled HTML leaderboard with clickable rows
                    leaderboard_by_model = HTMLPlus(
                        label="Styled Leaderboard",
                        value="<p>Loading leaderboard...</p>",
                        selectable_elements=["tr"]  # Make table rows clickable
                    )

                # COMMENTED OUT: DrillDown tab (replaced by clickable HTML table in By Model tab)
                # with gr.TabItem("📋 DrillDown"):
                #     gr.Markdown("*Click any row to view detailed run information*")

                #     # User Guide Accordion
                #     with gr.Accordion("📖 How to Use DrillDown", open=False):
                #         gr.Markdown("""
                #         ### 📋 Data Table View

                #         **What is this tab?**
                #         The DrillDown tab provides a raw, sortable table view of all evaluation runs with full details.

                #         **How to use it:**
                #         - 📊 **Table Format**: Clean, spreadsheet-like view of all runs
                #         - 🔍 **Filters**: Apply agent type, provider, and sorting controls
                #         - 📥 **Export Ready**: Easy to copy/paste data for reports
                #         - 👆 **Click Rows**: Click any row to navigate to detailed run view
                #         - 🔢 **All Metrics**: Shows run ID, model, success rate, cost, duration, and more

                #         **Columns Explained:**
                #         - **Run ID**: Unique identifier for each evaluation
                #         - **Model**: AI model that was evaluated
                #         - **Agent Type**: tool (function calling), code (code execution), or both
                #         - **Provider**: litellm (API models) or transformers (local models)
                #         - **Success Rate**: Percentage of test cases passed
                #         - **Tests**: Number of test cases executed
                #         - **Duration**: Average execution time in milliseconds
                #         - **Cost**: Total cost in USD for this run
                #         - **Submitted By**: HuggingFace username of evaluator

                #         **Tips:**
                #         - Use this for detailed data analysis
                #         - Combine with sidebar filters for focused views
                #         - Sort by any column to find best/worst performers
                #         """)

                #     # Inline filters for drilldown table
                #     with gr.Row():
                #         with gr.Column(scale=1):
                #             drilldown_agent_type_filter = gr.Radio(
                #                 choices=["All", "tool", "code", "both"],
                #                 value="All",
                #                 label="Agent Type",
                #                 info="Filter by agent type"
                #             )
                #         with gr.Column(scale=1):
                #             drilldown_provider_filter = gr.Dropdown(
                #                 choices=["All"],
                #                 value="All",
                #                 label="Provider",
                #                 info="Filter by provider"
                #             )
                #         with gr.Column(scale=1):
                #             drilldown_sort_by_dropdown = gr.Dropdown(
                #                 choices=["success_rate", "total_cost_usd", "avg_duration_ms", "total_tokens"],
                #                 value="success_rate",
                #                 label="Sort By"
                #             )
                #         with gr.Column(scale=1):
                #             drilldown_sort_order = gr.Radio(
                #                 choices=["Descending", "Ascending"],
                #                 value="Descending",
                #                 label="Sort Order"
                #             )

                #     with gr.Row():
                #         apply_drilldown_filters_btn = gr.Button("🔍 Apply Filters", variant="primary", size="sm")

                #     # Simple table controlled by inline filters
                #     leaderboard_table = gr.Dataframe(
                #         headers=["Run ID", "Model", "Agent Type", "Provider", "Success Rate", "Tests", "Duration (ms)", "Cost (USD)", "Submitted By"],
                #         interactive=False,
                #         wrap=True
                #     )

                with gr.TabItem("📈 Trends"):
                    # User Guide Accordion
                    with gr.Accordion("📖 How to Read Trends", open=False):
                        gr.Markdown("""
                        ### 📈 Temporal Performance Analysis

                        **What is this tab?**
                        The Trends tab visualizes how model performance evolves over time, helping you identify patterns and improvements.

                        **How to read it:**
                        - 📅 **X-axis**: Timeline showing when evaluations were run
                        - 📊 **Y-axis**: Performance metrics (success rate, cost, duration, etc.)
                        - 📈 **Line Charts**: Each line represents a different model
                        - 🎨 **Color Coding**: Different colors for different models
                        - 🔍 **Interactive**: Hover over points to see exact values

                        **What to look for:**
                        - **Upward trends** = Model improvements over time
                        - **Downward trends** = Performance degradation (needs investigation)
                        - **Flat lines** = Consistent performance
                        - **Spikes** = Anomalies or special test conditions
                        - **Gaps** = Periods without evaluations

                        **Use cases:**
                        - Track model version improvements
                        - Identify when performance degraded
                        - Compare model evolution over time
                        - Spot patterns in cost or latency changes
                        - Validate optimization efforts

                        **Tips:**
                        - Use sidebar filters to focus on specific models
                        - Look for correlation between cost and accuracy
                        - Identify best time periods for each model
                        """)

                    trends_plot = gr.Plot()
    
                with gr.TabItem("📊 Analytics"):
                    viz_type = gr.Radio(
                        choices=["🔥 Performance Heatmap", "⚡ Speed vs Accuracy", "💰 Cost Efficiency"],
                        value="🔥 Performance Heatmap",
                        label="Select Visualization",
                        info="Choose which analytics chart to display"
                    )
                    analytics_chart = gr.Plot(label="Interactive Chart", show_label=False)

                    # Explanation panel in accordion (dynamically updates based on chart selection)
                    with gr.Accordion("💡 How to Read This Chart", open=False):
                        viz_explanation = gr.Markdown("""
                        #### 🔥 Performance Heatmap

                        **What it shows:** All models compared across all metrics in one view

                        **How to read it:**
                        - 🟢 **Green cells** = Better performance (higher is better)
                        - 🟡 **Yellow cells** = Average performance
                        - 🔴 **Red cells** = Worse performance (needs improvement)

                        **Metrics displayed:**
                        - Success Rate (%), Avg Duration (ms), Total Cost ($)
                        - CO2 Emissions (g), GPU Utilization (%), Total Tokens

                        **Use it to:** Quickly identify which models excel in which areas
                        """, elem_id="viz-explanation")

                with gr.TabItem("📥 Summary Card"):
                    # User Guide Accordion
                    with gr.Accordion("📖 How to Create Summary Cards", open=False):
                        gr.Markdown("""
                        ### 📥 Downloadable Leaderboard Summary Card

                        **What is this tab?**
                        Generate professional, shareable summary cards with top performers and key statistics.
                        Perfect for presentations, reports, and sharing results with your team!

                        **How to use it:**
                        1. **Select Top N**: Use the slider to choose how many top models to include (1-5)
                        2. **Generate Preview**: Click "Generate Card Preview" to see the card
                        3. **Download**: Click "Download as PNG" to save as high-quality image
                        4. **Share**: Use the downloaded image in presentations, reports, or social media

                        **Card Features:**
                        - 🏆 **Medal Indicators**: Gold, silver, bronze for top 3 performers
                        - 📊 **Key Metrics**: Success rate, cost, duration, and tokens per model
                        - 📈 **Aggregate Stats**: Overall leaderboard statistics at a glance
                        - 🎨 **TraceMind Branding**: Professional design with logo
                        - 📥 **High Quality**: PNG format suitable for presentations

                        **Best Practices:**
                        - Use 3-5 models for balanced card density
                        - Include metric context in your presentations
                        - Update cards regularly to reflect latest results
                        - Combine with detailed reports for stakeholders

                        **Tips:**
                        - Cards are automatically sized for readability
                        - All current sidebar filters are applied
                        - Cards update dynamically as data changes
                        """)

                    with gr.Row():
                        with gr.Column(scale=1):
                            top_n_slider = gr.Slider(
                                minimum=1,
                                maximum=5,
                                value=3,
                                step=1,
                                label="Number of top models to show",
                                info="Select how many top performers to include in the card"
                            )

                            with gr.Row():
                                generate_card_btn = gr.Button("🎨 Generate Card Preview", variant="secondary", size="lg")
                                download_card_btn = gr.Button("📥 Download as PNG", variant="primary", size="lg", visible=False)

                        with gr.Column(scale=2):
                            card_preview = gr.HTML(label="Card Preview", value="<p style='text-align: center; color: #666; padding: 40px;'>Click 'Generate Card Preview' to see your summary card</p>")
    
                with gr.TabItem("🤖 AI Insights"):
                    # User Guide Accordion
                    with gr.Accordion("📖 About AI Insights", open=False):
                        gr.Markdown("""
                        ### 🤖 LLM-Powered Leaderboard Analysis

                        **What is this tab?**
                        AI Insights provides intelligent, natural language analysis of your leaderboard data using advanced language models.
                        Get instant insights, trends, and recommendations powered by AI.

                        **How it works:**
                        - 📊 **Automatic Analysis**: AI analyzes all leaderboard data automatically
                        - 🔄 **Streaming Responses**: Watch insights generate in real-time (Gradio 6)
                        - 🎯 **Smart Recommendations**: Get actionable advice for model selection
                        - 📈 **Trend Detection**: AI identifies patterns and anomalies
                        - 💡 **Context-Aware**: Insights adapt to current filters and data

                        **What insights you'll get:**
                        - **Top Performers**: Which models lead in accuracy, speed, cost
                        - **Trade-offs**: Cost vs accuracy, speed vs quality analysis
                        - **Recommendations**: Best model for different use cases
                        - **Trends**: Performance changes over time
                        - **Anomalies**: Unusual results that need attention
                        - **Optimization Tips**: How to improve evaluation strategies

                        **Powered by:**
                        - 🤖 **MCP Servers**: Model Context Protocol for intelligent data access
                        - 🧠 **Advanced LLMs**: Google Gemini 2.5 Flash for analysis
                        - 📡 **Real-time Streaming**: Gradio 6 for live response generation
                        - 🔗 **Context Integration**: Understands your full leaderboard context

                        **Tips:**
                        - Click "Regenerate" for updated insights after data changes
                        - Insights respect your sidebar and inline filters
                        - Use insights to guide model selection decisions
                        - Share AI insights in team discussions
                        """)

                    with gr.Row():
                        regenerate_btn = gr.Button("🔄 Regenerate Insights (Streaming)", size="sm", variant="secondary")
                        gr.Markdown("*Real-time AI analysis powered by Gradio 6 streaming*", elem_classes=["text-sm"])
                    mcp_insights = gr.Markdown("*Loading insights...*")
    
            # Hidden textbox for row selection (JavaScript bridge)
            selected_row_index = gr.Textbox(visible=False, elem_id="selected_row_index")
    
        # Screen 3: Run Detail (Enhanced with Tabs)
        with gr.Column(visible=False) as run_detail_screen:
            # Navigation
            with gr.Row():
                back_to_leaderboard_btn = gr.Button("⬅️ Back to Leaderboard", variant="secondary", size="sm")
                download_run_card_btn = gr.Button("📥 Download Run Report Card", variant="secondary", size="sm")

            run_detail_title = gr.Markdown("# 📊 Run Detail")

            with gr.Tabs():
                with gr.TabItem("📋 Overview"):
                    gr.Markdown("*Run metadata and summary*")
                    run_metadata_html = gr.HTML("")

                    gr.Markdown("### 📥 Downloadable Run Report Card")
                    run_card_html = gr.HTML(label="Run Report Card", elem_id="run-card-html")

                with gr.TabItem("✅ Test Cases"):
                    gr.Markdown("*Individual test case results*")
                    test_cases_table = gr.Dataframe(
                        headers=["Task ID", "Status", "Tool", "Duration", "Tokens", "Cost", "Trace ID"],
                        interactive=False,
                        wrap=True
                    )
                    gr.Markdown("*Click a test case to view detailed trace (including Thought Graph)*")

                with gr.TabItem("⚡ Performance"):
                    gr.Markdown("*Performance metrics and charts*")
                    performance_charts = gr.Plot(label="Performance Analysis", show_label=False)

                with gr.TabItem("🖥️ GPU Metrics"):
                    gr.Markdown("*Performance metrics for GPU-based models (not available for API models)*")
                    run_gpu_summary_cards_html = gr.HTML(label="GPU Summary", show_label=False)

                    with gr.Tabs():
                        with gr.TabItem("📈 Time Series Dashboard"):
                            run_gpu_metrics_plot = gr.Plot(label="GPU Metrics Over Time", show_label=False)

                        with gr.TabItem("📋 Raw Metrics Data"):
                            run_gpu_metrics_json = gr.JSON(label="GPU Metrics Data")

                with gr.TabItem("🤖 AI Insights"):
                    gr.Markdown("### AI-Powered Results Analysis")
                    gr.Markdown("*Get intelligent insights about test results and optimization recommendations using the MCP server*")

                    with gr.Row():
                        with gr.Column(scale=1):
                            run_analysis_focus = gr.Dropdown(
                                label="Analysis Focus",
                                choices=["comprehensive", "failures", "performance", "cost"],
                                value="comprehensive",
                                info="Choose what aspect to focus on in the AI analysis"
                            )
                            run_max_rows = gr.Slider(
                                label="Max Test Cases to Analyze",
                                minimum=10,
                                maximum=200,
                                value=100,
                                step=10,
                                info="Limit analysis to reduce processing time"
                            )
                        with gr.Column(scale=1):
                            generate_run_ai_insights_btn = gr.Button(
                                "🤖 Generate AI Insights",
                                variant="primary",
                                size="lg"
                            )

                    run_ai_insights = gr.Markdown(
                        "*Click 'Generate AI Insights' to get intelligent analysis powered by the MCP server*"
                    )

        # Screen 4: Trace Detail with Sub-tabs
        with gr.Column(visible=False) as trace_detail_screen:
            with gr.Row():
                back_to_run_detail_btn = gr.Button("⬅️ Back to Run Detail", variant="secondary", size="sm")

            trace_title = gr.Markdown("# 🔍 Trace Detail")
            trace_metadata_html = gr.HTML("")

            with gr.Tabs():
                with gr.TabItem("🧠 Thought Graph"):
                    gr.Markdown("""
                    ### Agent Reasoning Flow

                    This interactive network graph shows **how your agent thinks** - the logical flow of reasoning steps,
                    tool calls, and LLM interactions.

                    **How to read it:**
                    - 🟣 **Purple nodes** = LLM reasoning steps
                    - 🟠 **Orange nodes** = Tool calls
                    - 🔵 **Blue nodes** = Chains/Agents
                    - **Arrows** = Flow from one step to the next
                    - **Hover** = See tokens, costs, and timing details
                    """)
                    trace_thought_graph = gr.Plot(label="Thought Graph", show_label=False)

                with gr.TabItem("📊 Waterfall"):
                    gr.Markdown("*Interactive waterfall diagram showing span execution timeline*")
                    gr.Markdown("*Hover over spans for details. Drag to zoom, double-click to reset.*")
                    span_visualization = gr.Plot(label="Trace Waterfall", show_label=False)

                with gr.TabItem("📝 Span Details"):
                    gr.Markdown("*Detailed span information with token and cost data*")
                    span_details_table = gr.Dataframe(
                        headers=["Span Name", "Kind", "Duration (ms)", "Tokens", "Cost (USD)", "Status"],
                        interactive=False,
                        wrap=True,
                        label="Span Breakdown"
                    )

                with gr.TabItem("🔍 Raw Data"):
                    gr.Markdown("*Raw OpenTelemetry trace data (JSON)*")
                    span_details_json = gr.JSON()

            with gr.Accordion("🤖 Ask About This Trace", open=False):
                trace_question = gr.Textbox(
                    label="Question",
                    placeholder="e.g., Why was the tool called twice?",
                    lines=2,
                    info="Ask questions about agent execution, tool usage, or trace behavior"
                )
                trace_ask_btn = gr.Button("Ask", variant="primary")
                trace_answer = gr.Markdown("*Ask a question to get AI-powered insights*")

        # Screen 5: Compare Screen
        compare_screen, compare_components = create_compare_ui()

        # Screen 6: Agent Chat Screen
        chat_screen, chat_components = create_chat_ui()

        # Screen 7: Synthetic Data Generator
        with gr.Column(visible=False) as synthetic_data_screen:
            gr.Markdown("## 🔬 Synthetic Data Generator")

            # Help/README Accordion
            with gr.Accordion("📖 How to Use This Screen", open=False):
                gr.Markdown("""
                ### Generate Synthetic Evaluation Datasets

                This tool allows you to create custom synthetic evaluation datasets for testing AI agents.

                **Step-by-Step Process:**

                1. **Configure & Generate**:
                   - Select a **domain** (e.g., travel, finance, healthcare)
                   - Specify available **tools** (comma-separated)
                   - Choose **number of tasks** to generate
                   - Set **difficulty level** (easy/medium/hard/balanced)
                   - Select **agent type** (tool/code/both)
                   - Click "Generate" to create the dataset

                2. **Review Dataset**:
                   - Inspect the generated tasks in JSON format
                   - Check dataset statistics (task count, difficulty distribution, etc.)
                   - Verify the quality before pushing to Hub

                3. **Push to HuggingFace Hub** (Optional):
                   - Enter a **repository name** for your dataset
                   - Choose visibility (public/private)
                   - Provide your **HF token** OR leave empty to use environment token
                   - Click "Push" to upload the dataset

                **Note**: This screen uses the TraceMind MCP Server's synthetic data generation tools.
                """)

            gr.Markdown("---")

            # Store generated dataset and prompt template in component state
            generated_dataset_state = gr.State(None)
            generated_prompt_template_state = gr.State(None)

            # Step 1: Generate Dataset
            with gr.Group():
                gr.Markdown("### 📝 Step 1: Configure & Generate Dataset")

                with gr.Row():
                    with gr.Column(scale=1):
                        domain_input = gr.Textbox(
                            label="Domain",
                            placeholder="e.g., travel, finance, healthcare",
                            value="travel",
                            info="The domain/topic for the synthetic tasks"
                        )
                        tools_input = gr.Textbox(
                            label="Tools (comma-separated)",
                            placeholder="e.g., get_weather,search_flights,book_hotel",
                            value="get_weather,search_flights,book_hotel",
                            info="Available tools the agent can use"
                        )
                        num_tasks_input = gr.Slider(
                            label="Number of Tasks",
                            minimum=5,
                            maximum=100,
                            value=10,
                            step=5,
                            info="Total tasks to generate"
                        )

                    with gr.Column(scale=1):
                        difficulty_input = gr.Radio(
                            label="Difficulty Level",
                            choices=["easy", "medium", "hard", "balanced"],
                            value="balanced",
                            info="Task complexity level"
                        )
                        agent_type_input = gr.Radio(
                            label="Agent Type",
                            choices=["tool", "code", "both"],
                            value="both",
                            info="Type of agent to evaluate"
                        )

                generate_btn = gr.Button("🎲 Generate Synthetic Dataset", variant="primary", size="lg")
                generation_status = gr.Markdown("")

            # Step 2: Review Dataset
            with gr.Group():
                gr.Markdown("### 🔍 Step 2: Review Generated Dataset & Prompt Template")

                with gr.Tab("📊 Dataset Preview"):
                    dataset_preview = gr.JSON(
                        label="Generated Dataset",
                        visible=False
                    )

                    dataset_stats = gr.Markdown("", visible=False)

                with gr.Tab("📝 Prompt Template"):
                    gr.Markdown("""
                    **AI-Generated Prompt Template**

                    This customized prompt template is based on smolagents templates and adapted for your domain and tools.
                    It will be automatically included in your dataset card when you push to HuggingFace Hub.
                    """)

                    prompt_template_preview = gr.Code(
                        label="Customized Prompt Template (YAML)",
                        language="yaml",
                        visible=False
                    )

            # Step 3: Push to Hub
            with gr.Group():
                gr.Markdown("### 📤 Step 3: Push to HuggingFace Hub (Optional)")
                gr.Markdown("*Leave HF Token empty to use the environment token (if configured in your Space/deployment)*")

                with gr.Row():
                    repo_name_input = gr.Textbox(
                        label="Repository Name",
                        placeholder="e.g., username/smoltrace-travel-tasks",
                        info="Include username prefix (auto-filled after generation)",
                        scale=2
                    )
                    private_checkbox = gr.Checkbox(
                        label="Private Repository",
                        value=False,
                        info="Make dataset private",
                        scale=1
                    )

                hf_token_input = gr.Textbox(
                    label="HuggingFace Token (Optional)",
                    placeholder="Leave empty to use environment token (HF_TOKEN)",
                    type="password",
                    info="Get your token from https://huggingface.co/settings/tokens"
                )

                push_btn = gr.Button("📤 Push to HuggingFace Hub", variant="primary", size="lg", visible=False)
                push_status = gr.Markdown("")

        # ============================================================================
        # Screen 8: New Evaluation (Comprehensive Form)
        # ============================================================================
        with gr.Column(visible=False) as new_evaluation_screen:
            gr.Markdown("## ▶️ New Evaluation")
            gr.Markdown("*Configure and submit a new agent evaluation job*")

            with gr.Row():
                back_to_leaderboard_from_eval_btn = gr.Button("⬅️ Back to Leaderboard", variant="secondary", size="sm")

            gr.Markdown("---")

            # Section 1: Infrastructure Configuration
            with gr.Accordion("🏗️ Infrastructure Configuration", open=True):
                gr.Markdown("*Choose where and how to run the evaluation*")

                with gr.Row():
                    eval_infra_provider = gr.Dropdown(
                        choices=["HuggingFace Jobs", "Modal"],
                        value="HuggingFace Jobs",
                        label="Infrastructure Provider",
                        info="Select the platform to run the evaluation"
                    )

                    eval_hardware = gr.Dropdown(
                        choices=[
                            "auto",
                            "cpu-basic",
                            "cpu-upgrade",
                            "t4-small",
                            "t4-medium",
                            "l4x1",
                            "l4x4",
                            "a10g-small",
                            "a10g-large",
                            "a10g-largex2",
                            "a10g-largex4",
                            "a100-large",
                            "v5e-1x1",
                            "v5e-2x2",
                            "v5e-2x4"
                        ],
                        value="auto",
                        label="Hardware",
                        info="Auto: cpu-basic for API models, a10g-small for local models. HF Jobs pricing."
                    )

            # Section 2: Model Configuration
            with gr.Accordion("🤖 Model Configuration", open=True):
                gr.Markdown("*Configure the model and provider settings*")

                with gr.Row():
                    eval_model = gr.Textbox(
                        value="openai/gpt-4.1-nano",
                        label="Model",
                        info="Model ID (e.g., openai/gpt-4.1-nano, meta-llama/Llama-3.1-8B-Instruct)",
                        placeholder="openai/gpt-4.1-nano"
                    )

                    eval_provider = gr.Dropdown(
                        choices=["litellm", "inference", "transformers"],
                        value="litellm",
                        label="Provider",
                        info="Model inference provider (litellm/inference=API, transformers=local)"
                    )

                with gr.Row():
                    eval_hf_inference_provider = gr.Textbox(
                        label="HF Inference Provider",
                        info="For HuggingFace Inference API (optional)",
                        placeholder="Leave empty for default"
                    )

                    # Check if HF token is already configured in Settings
                    hf_token_configured = bool(os.environ.get("HF_TOKEN"))
                    hf_token_info = "✅ Already configured in Settings - leave empty to use saved token" if hf_token_configured else "Your HF token for private models (optional)"

                    eval_hf_token = gr.Textbox(
                        label="HuggingFace Token",
                        type="password",
                        info=hf_token_info,
                        placeholder="hf_... (leave empty if already set in Settings)"
                    )

            # Section 3: Agent Configuration
            with gr.Accordion("🤖 Agent Configuration", open=True):
                gr.Markdown("*Configure agent type and capabilities*")

                with gr.Row():
                    eval_agent_type = gr.Radio(
                        choices=["tool", "code", "both"],
                        value="both",
                        label="Agent Type",
                        info="Tool: Function calling | Code: Code execution | Both: Hybrid"
                    )

                    eval_search_provider = gr.Dropdown(
                        choices=["duckduckgo", "serper", "brave"],
                        value="duckduckgo",
                        label="Search Provider",
                        info="Web search provider for agents"
                    )

                with gr.Row():
                    eval_enable_tools = gr.CheckboxGroup(
                        choices=[
                            "google_search",
                            "duckduckgo_search",
                            "visit_webpage",
                            "python_interpreter",
                            "wikipedia_search",
                            "user_input"
                        ],
                        label="Enable Optional Tools",
                        info="Select additional tools to enable for the agent"
                    )

            # Section 4: Test Configuration
            with gr.Accordion("🧪 Test Configuration", open=True):
                gr.Markdown("*Configure test dataset and execution parameters*")

                with gr.Row():
                    eval_dataset_name = gr.Textbox(
                        value="kshitijthakkar/smoltrace-tasks",
                        label="Dataset Name",
                        info="HuggingFace dataset for evaluation tasks"
                    )

                    eval_split = gr.Textbox(
                        value="train",
                        label="Dataset Split",
                        info="Which split to use from the dataset"
                    )

                with gr.Row():
                    eval_difficulty = gr.Dropdown(
                        choices=["all", "easy", "medium", "hard"],
                        value="all",
                        label="Difficulty Filter",
                        info="Filter tests by difficulty level"
                    )

                    eval_parallel_workers = gr.Number(
                        value=1,
                        label="Parallel Workers",
                        info="Number of parallel workers for execution",
                        minimum=1,
                        maximum=10
                    )

            # Section 5: Output & Monitoring Configuration
            with gr.Accordion("📊 Output & Monitoring", open=True):
                gr.Markdown("*Configure output format and monitoring options*")

                with gr.Row():
                    eval_output_format = gr.Radio(
                        choices=["hub", "json"],
                        value="hub",
                        label="Output Format",
                        info="Hub: Push to HuggingFace | JSON: Save locally"
                    )

                    eval_output_dir = gr.Textbox(
                        label="Output Directory",
                        info="Directory for JSON output (if format=json)",
                        placeholder="./evaluation_results"
                    )

                with gr.Row():
                    eval_enable_otel = gr.Checkbox(
                        value=True,
                        label="Enable OpenTelemetry Tracing",
                        info="Collect detailed execution traces"
                    )

                    eval_enable_gpu_metrics = gr.Checkbox(
                        value=True,
                        label="Enable GPU Metrics",
                        info="Collect GPU utilization, memory, and CO2 emissions (GPU jobs only)"
                    )

                with gr.Row():
                    eval_private = gr.Checkbox(
                        value=False,
                        label="Private Datasets",
                        info="Make result datasets private on HuggingFace"
                    )

                    eval_debug = gr.Checkbox(
                        value=False,
                        label="Debug Mode",
                        info="Enable debug output for troubleshooting"
                    )

                    eval_quiet = gr.Checkbox(
                        value=False,
                        label="Quiet Mode",
                        info="Reduce verbosity of output"
                    )

                eval_run_id = gr.Textbox(
                    label="Run ID (Optional)",
                    info="Unique identifier for this run (auto-generated if empty)",
                    placeholder="UUID will be auto-generated"
                )

                with gr.Row():
                    eval_timeout = gr.Textbox(
                        value="1h",
                        label="Job Timeout",
                        info="Maximum job duration (e.g., '30m', '1h', '2h')",
                        placeholder="1h"
                    )

            gr.Markdown("---")

            # Cost Estimate Section
            with gr.Row():
                eval_estimate_btn = gr.Button("💰 Estimate Cost", variant="secondary", size="lg")

            eval_cost_estimate = gr.Markdown("*Click 'Estimate Cost' to get AI-powered cost analysis*")

            gr.Markdown("---")

            # Submit Section
            with gr.Row():
                eval_submit_btn = gr.Button("🚀 Submit Evaluation", variant="primary", size="lg")

            eval_success_message = gr.HTML(visible=False)

        # ============================================================================
        # Screen 9: Documentation
        # ============================================================================
        documentation_screen = create_documentation_screen()

        # ============================================================================
        # Screen 10: Settings
        # ============================================================================
        settings_screen = create_settings_screen()

        # ============================================================================
        # Screen 11: Job Monitoring
        # ============================================================================
        job_monitoring_screen = create_job_monitoring_screen()

        # ============================================================================
        # Evaluation Helper Functions
        # ============================================================================

        def estimate_job_cost_with_mcp_fallback(model, hardware, provider="litellm", infrastructure="HuggingFace Jobs"):
            """
            Estimate cost using historical leaderboard data first,
            then fall back to MCP server if model not found

            Args:
                model: Model name
                hardware: Hardware selection from UI
                provider: Provider type (litellm, transformers, etc.)
                infrastructure: Infrastructure provider (Modal, HuggingFace Jobs)
            """
            # Handle auto-selection for both infrastructure providers
            selected_hardware_display = None

            if hardware == "auto":
                if infrastructure == "Modal":
                    # Modal auto-selection
                    from utils.modal_job_submission import _auto_select_modal_hardware
                    modal_gpu = _auto_select_modal_hardware(provider, model)
                    selected_hardware_display = f"auto → **{modal_gpu or 'CPU'}** (Modal)"

                    # Map Modal GPU names to HF Jobs equivalent for cost estimation
                    modal_to_hf_map = {
                        None: "cpu-basic",  # CPU
                        "T4": "t4-small",
                        "L4": "l4x1",
                        "A10G": "a10g-small",
                        "L40S": "a10g-large",
                        "A100": "a100-large",
                        "A100-80GB": "a100-large",  # Use a100-large as proxy for cost
                        "H100": "a100-large",  # Use a100 as proxy
                        "H200": "a100-large",  # Use a100 as proxy
                    }
                    hardware = modal_to_hf_map.get(modal_gpu, "a10g-small")
                else:
                    # HuggingFace Jobs auto-selection
                    from utils.hf_jobs_submission import _auto_select_hf_hardware
                    hf_hardware = _auto_select_hf_hardware(provider, model)
                    selected_hardware_display = f"auto → **{hf_hardware}** (HF Jobs)"
                    hardware = hf_hardware

            try:
                # Try to get historical data from leaderboard
                df = data_loader.load_leaderboard()

                # Filter for this model
                model_runs = df[df['model'] == model]

                if len(model_runs) > 0:
                    # We have historical data - use it!
                    avg_cost = model_runs['total_cost_usd'].mean()
                    avg_duration = model_runs['avg_duration_ms'].mean()
                    has_cost_data = model_runs['total_cost_usd'].sum() > 0

                    result = {
                        'source': 'historical',
                        'total_cost_usd': f"{avg_cost:.4f}",
                        'estimated_duration_minutes': f"{(avg_duration / 1000 / 60):.1f}",
                        'historical_runs': len(model_runs),
                        'has_cost_data': has_cost_data
                    }
                    if selected_hardware_display:
                        result['hardware_display'] = selected_hardware_display
                    return result
                else:
                    # No historical data - use MCP tool
                    print(f"[INFO] No historical data for {model}, using MCP cost estimator")
                    try:
                        from gradio_client import Client
                        import re

                        mcp_client = Client("https://mcp-1st-birthday-tracemind-mcp-server.hf.space/")
                        result = mcp_client.predict(
                            model=model,
                            agent_type="both",
                            num_tests=100,
                            hardware=hardware,
                            api_name="/run_estimate_cost"
                        )

                        print(f"[INFO] MCP result type: {type(result)}")
                        print(f"[INFO] MCP result: {result[:200] if isinstance(result, str) else result}")

                        # MCP returns markdown text, not a dict
                        # Parse the markdown to extract cost and duration
                        if isinstance(result, str):
                            # Try to extract cost values from markdown
                            cost_match = re.search(r'\$(\d+\.?\d*)', result)
                            duration_match = re.search(r'(\d+\.?\d+)\s*(minutes?|hours?)', result, re.IGNORECASE)

                            extracted_cost = cost_match.group(1) if cost_match else 'See details below'
                            extracted_duration = duration_match.group(0) if duration_match else 'See details below'

                            # Return with markdown content
                            result_dict = {
                                'source': 'mcp',
                                'total_cost_usd': extracted_cost,
                                'estimated_duration_minutes': extracted_duration,
                                'historical_runs': 0,
                                'has_cost_data': True,
                                'markdown_details': result  # Include full markdown response
                            }
                            if selected_hardware_display:
                                result_dict['hardware_display'] = selected_hardware_display
                            return result_dict
                        else:
                            # Unexpected response type
                            result_dict = {
                                'source': 'mcp',
                                'total_cost_usd': 'N/A',
                                'estimated_duration_minutes': 'N/A',
                                'historical_runs': 0,
                                'has_cost_data': False,
                                'error': f'MCP returned unexpected type: {type(result)}'
                            }
                            if selected_hardware_display:
                                result_dict['hardware_display'] = selected_hardware_display
                            return result_dict
                    except Exception as mcp_error:
                        print(f"[ERROR] MCP cost estimation failed: {mcp_error}")
                        import traceback
                        traceback.print_exc()
                        # Return a result indicating MCP is unavailable
                        result_dict = {
                            'source': 'mcp',
                            'total_cost_usd': 'N/A',
                            'estimated_duration_minutes': 'N/A',
                            'historical_runs': 0,
                            'has_cost_data': False,
                            'error': str(mcp_error)
                        }
                        if selected_hardware_display:
                            result_dict['hardware_display'] = selected_hardware_display
                        return result_dict

            except Exception as e:
                print(f"[ERROR] Cost estimation failed (leaderboard load): {e}")
                return None

        def on_hardware_change(model, hardware, provider, infrastructure):
            """Update cost estimate when hardware selection changes"""
            cost_est = estimate_job_cost_with_mcp_fallback(model, hardware, provider, infrastructure)

            if cost_est is None:
                # Error occurred
                return f"""## ⚠️ Cost Estimation Failed

Unable to estimate cost for **{model}**.

Please check your model ID and try again, or proceed without cost estimation.
"""

            # Check if MCP returned an error
            if cost_est.get('error'):
                return f"""## ⚠️ MCP Cost Estimator Unavailable

No historical data available for **{model}**.

**Error**: {cost_est.get('error', 'Unknown error')}

💡 You can still proceed with the evaluation. Actual costs will be tracked and displayed after completion.
"""

            # Format based on source
            if cost_est['source'] == 'historical':
                source_label = f"📊 Historical Data ({cost_est['historical_runs']} past runs)"
                cost_display = f"${cost_est['total_cost_usd']}" if cost_est['has_cost_data'] else "N/A (cost tracking not enabled)"
                duration = cost_est['estimated_duration_minutes']

                # Use custom hardware display if available, otherwise show hardware as-is
                hardware_display = cost_est.get('hardware_display', hardware.upper())

                return f"""## 💰 Cost Estimate

**{source_label}**

| Metric | Value |
|--------|-------|
| **Model** | {model} |
| **Hardware** | {hardware_display} |
| **Estimated Cost** | {cost_display} |
| **Duration** | {duration} minutes |

---

*Based on {cost_est['historical_runs']} previous evaluation runs in the leaderboard.*
"""
            else:
                # MCP Cost Estimator - return the full markdown from MCP
                markdown_details = cost_est.get('markdown_details', '')

                # Add hardware selection note if applicable
                hardware_note = ""
                if cost_est.get('hardware_display'):
                    hardware_note = f"\n\n**Hardware**: {cost_est['hardware_display']}\n\n"

                # Add header to identify the source
                header = f"""## 💰 Cost Estimate - AI Analysis

**🤖 Powered by MCP Server + Gemini 2.5 Pro**

{get_gemini_header()}

*This estimate was generated by AI analysis since no historical data is available for this model.*
{hardware_note}
---

"""
                return header + markdown_details

        def on_submit_evaluation_comprehensive(
            # Infrastructure
            infra_provider, hardware,
            # Model Configuration
            model, provider, hf_inference_provider, hf_token,
            # Agent Configuration
            agent_type, search_provider, enable_tools,
            # Test Configuration
            dataset_name, split, difficulty, parallel_workers,
            # Output & Monitoring
            output_format, output_dir, enable_otel, enable_gpu_metrics, private, debug, quiet, run_id, timeout
        ):
            """Submit a new evaluation job with comprehensive configuration"""
            from utils.modal_job_submission import submit_modal_job
            from utils.hf_jobs_submission import submit_hf_job

            # Submit job based on infrastructure provider
            if infra_provider == "Modal":
                result = submit_modal_job(
                    model=model,
                    provider=provider,
                    agent_type=agent_type,
                    hardware=hardware,
                    dataset_name=dataset_name,
                    split=split,
                    difficulty=difficulty,
                    parallel_workers=parallel_workers,
                    hf_token=hf_token,
                    hf_inference_provider=hf_inference_provider,
                    search_provider=search_provider,
                    enable_tools=enable_tools,
                    output_format=output_format,
                    output_dir=output_dir,
                    enable_otel=enable_otel,
                    enable_gpu_metrics=enable_gpu_metrics,
                    private=private,
                    debug=debug,
                    quiet=quiet,
                    run_id=run_id
                )
            else:  # HuggingFace Jobs
                result = submit_hf_job(
                    model=model,
                    provider=provider,
                    agent_type=agent_type,
                    hardware=hardware,
                    dataset_name=dataset_name,
                    split=split,
                    difficulty=difficulty,
                    parallel_workers=parallel_workers,
                    hf_token=hf_token,
                    hf_inference_provider=hf_inference_provider,
                    search_provider=search_provider,
                    enable_tools=enable_tools,
                    output_format=output_format,
                    output_dir=output_dir,
                    enable_otel=enable_otel,
                    enable_gpu_metrics=enable_gpu_metrics,
                    private=private,
                    debug=debug,
                    quiet=quiet,
                    run_id=run_id,
                    timeout=timeout or "1h"
                )

            # Handle submission result
            if not result.get("success"):
                # Error occurred
                error_html = f"""
                <div style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
                            padding: 25px; border-radius: 10px; color: white; margin: 15px 0;">
                    <h2 style="margin-top: 0;">❌ Job Submission Failed</h2>
                    <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 5px;">Error</div>
                        <div style="font-size: 1.0em;">{result.get('error', 'Unknown error')}</div>
                    </div>
                </div>
                """
                return gr.update(value=error_html, visible=True)

            # Success - build success message
            job_id = result.get('job_id', 'unknown')
            hf_job_id = result.get('hf_job_id', job_id)  # Get actual HF job ID
            modal_call_id = result.get('modal_call_id', None)  # Get Modal call ID if available
            job_platform = result.get('platform', infra_provider)
            job_hardware = result.get('hardware', hardware)
            job_status = result.get('status', 'submitted')
            job_message = result.get('message', '')

            # Estimate cost
            cost_est = estimate_job_cost_with_mcp_fallback(model, hardware, provider, infra_provider)
            has_cost_estimate = cost_est is not None

            cost_info_html = ""
            if has_cost_estimate:
                source_label = "📊 Historical" if cost_est['source'] == 'historical' else "🤖 MCP Estimate"
                if cost_est.get('has_cost_data', False):
                    cost_info_html = f"""
                        <div>
                            <div style="font-size: 0.9em; opacity: 0.9;">Estimated Cost ({source_label})</div>
                            <div style="font-weight: bold;">${cost_est['total_cost_usd']}</div>
                        </div>
                    """
                else:
                    cost_info_html = """
                        <div>
                            <div style="font-size: 0.9em; opacity: 0.9;">Estimated Cost</div>
                            <div style="font-weight: bold;">N/A</div>
                        </div>
                    """
                duration_info = f"Estimated completion: {cost_est['estimated_duration_minutes']} minutes"
            else:
                cost_info_html = """
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Estimated Cost</div>
                        <div style="font-weight: bold;">N/A</div>
                    </div>
                """
                duration_info = "Estimated completion: Will be tracked in leaderboard once job completes"

            # Add job-specific details
            job_details_html = ""
            if result.get('job_yaml'):
                job_details_html += f"""
                <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.15); border-radius: 5px;">
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 10px;">📄 Job Configuration (job.yaml)</div>
                    <div style="font-family: monospace; font-size: 0.7em; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 3px; overflow-x: auto; max-height: 300px; overflow-y: auto;">
                        {result['job_yaml']}
                    </div>
                </div>
                """

            if result.get('command'):
                job_details_html += f"""
                <div style="margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.15); border-radius: 5px;">
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 10px;">📋 SMOLTRACE Command</div>
                    <div style="font-family: monospace; font-size: 0.75em; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 3px; overflow-x: auto;">
                        {result['command']}
                    </div>
                </div>
                """

            if result.get('instructions'):
                job_details_html += f"""
                <div style="margin-top: 15px; padding: 15px; background: rgba(255,200,100,0.2); border-radius: 5px; border-left: 4px solid rgba(255,255,255,0.5);">
                    <div style="font-size: 0.85em; white-space: pre-wrap;">{result['instructions']}</div>
                </div>
                """

            success_html = f"""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        padding: 25px; border-radius: 10px; color: white; margin: 15px 0;">
                <h2 style="margin-top: 0;">✅ Evaluation Job Configured!</h2>

                <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 5px;">Run ID (SMOLTRACE)</div>
                    <div style="font-family: monospace; font-size: 0.95em; font-weight: bold;">{job_id}</div>
                    {f'''
                    <div style="font-size: 0.9em; opacity: 0.9; margin-top: 10px; margin-bottom: 5px;">Modal Call ID</div>
                    <div style="font-family: monospace; font-size: 0.95em; font-weight: bold;">{modal_call_id}</div>
                    <div style="font-size: 0.8em; opacity: 0.8; margin-top: 8px;">View on Modal Dashboard: <a href="https://modal.com/apps" target="_blank" style="color: rgba(255,255,255,0.9);">https://modal.com/apps</a></div>
                    ''' if modal_call_id else f'''
                    <div style="font-size: 0.9em; opacity: 0.9; margin-top: 10px; margin-bottom: 5px;">HF Job ID</div>
                    <div style="font-family: monospace; font-size: 0.95em; font-weight: bold;">{hf_job_id}</div>
                    <div style="font-size: 0.8em; opacity: 0.8; margin-top: 8px;">Use this ID to monitor: <code style="background: rgba(0,0,0,0.2); padding: 2px 6px; border-radius: 3px;">hf jobs inspect {hf_job_id}</code></div>
                    '''}
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 15px;">
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Platform</div>
                        <div style="font-weight: bold;">{job_platform}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Model</div>
                        <div style="font-weight: bold;">{model}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Hardware</div>
                        <div style="font-weight: bold;">{job_hardware}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Agent Type</div>
                        <div style="font-weight: bold;">{agent_type}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Status</div>
                        <div style="font-weight: bold;">{job_status.upper()}</div>
                    </div>
                    {cost_info_html}
                </div>

                <div style="margin-top: 15px; padding: 10px; background: rgba(255,255,255,0.15); border-radius: 5px;">
                    <div style="font-size: 0.9em;">
                        ℹ️ {job_message}
                    </div>
                </div>

                {job_details_html}

                <div style="margin-top: 15px; padding: 10px; background: rgba(255,255,255,0.15); border-radius: 5px;">
                    <div style="font-size: 0.9em;">
                        ⏱️ {duration_info}
                    </div>
                </div>
            </div>
            """

            return gr.update(value=success_html, visible=True)

        def on_infra_provider_change(infra_provider):
            """Update hardware options based on infrastructure provider"""
            if infra_provider == "Modal":
                # Modal hardware options (per-second pricing)
                return gr.update(
                    choices=[
                        "auto",
                        "cpu",
                        "gpu_t4",
                        "gpu_l4",
                        "gpu_a10",
                        "gpu_l40s",
                        "gpu_a100",
                        "gpu_a100_80gb",
                        "gpu_h100",
                        "gpu_h200",
                        "gpu_b200"
                    ],
                    value="auto",
                    info="Auto: CPU for API models, A10 for local models. Modal per-second pricing."
                )
            else:  # HuggingFace Jobs
                # HuggingFace Jobs hardware options
                return gr.update(
                    choices=[
                        "auto",
                        "cpu-basic",
                        "cpu-upgrade",
                        "t4-small",
                        "t4-medium",
                        "l4x1",
                        "l4x4",
                        "a10g-small",
                        "a10g-large",
                        "a10g-largex2",
                        "a10g-largex4",
                        "a100-large",
                        "v5e-1x1",
                        "v5e-2x2",
                        "v5e-2x4"
                    ],
                    value="auto",
                    info="Auto: cpu-basic for API models, a10g-small for local models. HF Jobs pricing."
                )

        def on_provider_change(provider):
            """Auto-select hardware based on provider type"""
            # litellm and inference are for API models → CPU
            # transformers is for local models → GPU
            if provider in ["litellm", "inference"]:
                return gr.update(value="cpu-basic")
            elif provider == "transformers":
                return gr.update(value="a10g-small")
            else:
                return gr.update(value="auto")

        # Navigation handlers (define before use)
        def navigate_to_dashboard():
            """Navigate to dashboard screen and load dashboard data"""
            try:
                leaderboard_df = data_loader.load_leaderboard()
                dashboard_updates = update_dashboard_data(leaderboard_df, dashboard_components)
            except Exception as e:
                print(f"[ERROR] Loading dashboard data: {e}")
                dashboard_updates = {}

            # Combine navigation updates with dashboard data updates
            result = {
                dashboard_screen: gr.update(visible=True),
                leaderboard_screen: gr.update(visible=False),
                run_detail_screen: gr.update(visible=False),
                trace_detail_screen: gr.update(visible=False),
                compare_screen: gr.update(visible=False),
                chat_screen: gr.update(visible=False),
                synthetic_data_screen: gr.update(visible=False),
                new_evaluation_screen: gr.update(visible=False),
                documentation_screen: gr.update(visible=False),
                settings_screen: gr.update(visible=False),
                job_monitoring_screen: gr.update(visible=False),
                dashboard_nav_btn: gr.update(variant="primary"),
                leaderboard_nav_btn: gr.update(variant="secondary"),
                new_eval_nav_btn: gr.update(variant="secondary"),
                compare_nav_btn: gr.update(variant="secondary"),
                chat_nav_btn: gr.update(variant="secondary"),
                job_monitoring_nav_btn: gr.update(variant="secondary"),
                synthetic_data_nav_btn: gr.update(variant="secondary"),
                docs_nav_btn: gr.update(variant="secondary"),
                settings_nav_btn: gr.update(variant="secondary"),
            }
            result.update(dashboard_updates)
            return result

        def navigate_to_leaderboard():
            """Navigate to leaderboard screen"""
            return {
                dashboard_screen: gr.update(visible=False),
                leaderboard_screen: gr.update(visible=True),
                run_detail_screen: gr.update(visible=False),
                trace_detail_screen: gr.update(visible=False),
                compare_screen: gr.update(visible=False),
                chat_screen: gr.update(visible=False),
                synthetic_data_screen: gr.update(visible=False),
                new_evaluation_screen: gr.update(visible=False),
                documentation_screen: gr.update(visible=False),
                settings_screen: gr.update(visible=False),
                job_monitoring_screen: gr.update(visible=False),
                dashboard_nav_btn: gr.update(variant="secondary"),
                leaderboard_nav_btn: gr.update(variant="primary"),
                new_eval_nav_btn: gr.update(variant="secondary"),
                compare_nav_btn: gr.update(variant="secondary"),
                chat_nav_btn: gr.update(variant="secondary"),
                job_monitoring_nav_btn: gr.update(variant="secondary"),
                synthetic_data_nav_btn: gr.update(variant="secondary"),
                docs_nav_btn: gr.update(variant="secondary"),
                settings_nav_btn: gr.update(variant="secondary"),
            }

        def navigate_to_new_evaluation():
            """Navigate to new evaluation screen"""
            return {
                dashboard_screen: gr.update(visible=False),
                leaderboard_screen: gr.update(visible=False),
                run_detail_screen: gr.update(visible=False),
                trace_detail_screen: gr.update(visible=False),
                compare_screen: gr.update(visible=False),
                chat_screen: gr.update(visible=False),
                synthetic_data_screen: gr.update(visible=False),
                new_evaluation_screen: gr.update(visible=True),
                documentation_screen: gr.update(visible=False),
                settings_screen: gr.update(visible=False),
                job_monitoring_screen: gr.update(visible=False),
                dashboard_nav_btn: gr.update(variant="secondary"),
                leaderboard_nav_btn: gr.update(variant="secondary"),
                new_eval_nav_btn: gr.update(variant="primary"),
                compare_nav_btn: gr.update(variant="secondary"),
                chat_nav_btn: gr.update(variant="secondary"),
                job_monitoring_nav_btn: gr.update(variant="secondary"),
                synthetic_data_nav_btn: gr.update(variant="secondary"),
                docs_nav_btn: gr.update(variant="secondary"),
                settings_nav_btn: gr.update(variant="secondary"),
            }

        def navigate_to_compare():
            """Navigate to compare screen and populate dropdown choices"""
            try:
                leaderboard_df = data_loader.load_leaderboard()

                # Create run choices for dropdowns (model name with composite unique identifier)
                run_choices = []
                for _, row in leaderboard_df.iterrows():
                    label = f"{row.get('model', 'Unknown')} - {row.get('timestamp', 'N/A')}"
                    # Use composite key: run_id|timestamp to ensure uniqueness
                    value = f"{row.get('run_id', '')}|{row.get('timestamp', '')}"
                    if value:
                        run_choices.append((label, value))

                return {
                    dashboard_screen: gr.update(visible=False),
                    leaderboard_screen: gr.update(visible=False),
                    run_detail_screen: gr.update(visible=False),
                    trace_detail_screen: gr.update(visible=False),
                    compare_screen: gr.update(visible=True),
                    chat_screen: gr.update(visible=False),
                synthetic_data_screen: gr.update(visible=False),
                    new_evaluation_screen: gr.update(visible=False),
                    documentation_screen: gr.update(visible=False),
                settings_screen: gr.update(visible=False),
                    job_monitoring_screen: gr.update(visible=False),
                    dashboard_nav_btn: gr.update(variant="secondary"),
                    leaderboard_nav_btn: gr.update(variant="secondary"),
                    new_eval_nav_btn: gr.update(variant="secondary"),
                    compare_nav_btn: gr.update(variant="primary"),
                    chat_nav_btn: gr.update(variant="secondary"),
                job_monitoring_nav_btn: gr.update(variant="secondary"),
                synthetic_data_nav_btn: gr.update(variant="secondary"),
                    docs_nav_btn: gr.update(variant="secondary"),
                    settings_nav_btn: gr.update(variant="secondary"),
                    compare_components['compare_run_a_dropdown']: gr.update(choices=run_choices),
                    compare_components['compare_run_b_dropdown']: gr.update(choices=run_choices),
                }
            except Exception as e:
                print(f"[ERROR] Navigating to compare: {e}")
                return {
                    dashboard_screen: gr.update(visible=False),
                    leaderboard_screen: gr.update(visible=False),
                    run_detail_screen: gr.update(visible=False),
                    trace_detail_screen: gr.update(visible=False),
                    compare_screen: gr.update(visible=True),
                    chat_screen: gr.update(visible=False),
                synthetic_data_screen: gr.update(visible=False),
                    new_evaluation_screen: gr.update(visible=False),
                    documentation_screen: gr.update(visible=False),
                    settings_screen: gr.update(visible=False),
                    job_monitoring_screen: gr.update(visible=False),
                    dashboard_nav_btn: gr.update(variant="secondary"),
                    leaderboard_nav_btn: gr.update(variant="secondary"),
                    new_eval_nav_btn: gr.update(variant="secondary"),
                    compare_nav_btn: gr.update(variant="primary"),
                    chat_nav_btn: gr.update(variant="secondary"),
                job_monitoring_nav_btn: gr.update(variant="secondary"),
                synthetic_data_nav_btn: gr.update(variant="secondary"),
                    docs_nav_btn: gr.update(variant="secondary"),
                settings_nav_btn: gr.update(variant="secondary"),
                }

        def navigate_to_chat():
            """Navigate to chat screen"""
            return {
                dashboard_screen: gr.update(visible=False),
                leaderboard_screen: gr.update(visible=False),
                run_detail_screen: gr.update(visible=False),
                trace_detail_screen: gr.update(visible=False),
                compare_screen: gr.update(visible=False),
                chat_screen: gr.update(visible=True),
                synthetic_data_screen: gr.update(visible=False),
                new_evaluation_screen: gr.update(visible=False),
                documentation_screen: gr.update(visible=False),
                settings_screen: gr.update(visible=False),
                job_monitoring_screen: gr.update(visible=False),
                dashboard_nav_btn: gr.update(variant="secondary"),
                leaderboard_nav_btn: gr.update(variant="secondary"),
                new_eval_nav_btn: gr.update(variant="secondary"),
                compare_nav_btn: gr.update(variant="secondary"),
                chat_nav_btn: gr.update(variant="primary"),
                job_monitoring_nav_btn: gr.update(variant="secondary"),
                synthetic_data_nav_btn: gr.update(variant="secondary"),
                docs_nav_btn: gr.update(variant="secondary"),
                settings_nav_btn: gr.update(variant="secondary"),
            }

        def navigate_to_synthetic_data():
            """Navigate to synthetic data generator screen"""
            return {
                dashboard_screen: gr.update(visible=False),
                leaderboard_screen: gr.update(visible=False),
                run_detail_screen: gr.update(visible=False),
                trace_detail_screen: gr.update(visible=False),
                compare_screen: gr.update(visible=False),
                chat_screen: gr.update(visible=False),
                synthetic_data_screen: gr.update(visible=True),
                new_evaluation_screen: gr.update(visible=False),
                documentation_screen: gr.update(visible=False),
                settings_screen: gr.update(visible=False),
                job_monitoring_screen: gr.update(visible=False),
                dashboard_nav_btn: gr.update(variant="secondary"),
                leaderboard_nav_btn: gr.update(variant="secondary"),
                new_eval_nav_btn: gr.update(variant="secondary"),
                compare_nav_btn: gr.update(variant="secondary"),
                chat_nav_btn: gr.update(variant="secondary"),
                job_monitoring_nav_btn: gr.update(variant="secondary"),
                synthetic_data_nav_btn: gr.update(variant="primary"),
                docs_nav_btn: gr.update(variant="secondary"),
                settings_nav_btn: gr.update(variant="secondary"),
            }

        def navigate_to_documentation():
            """Navigate to documentation screen"""
            return {
                dashboard_screen: gr.update(visible=False),
                leaderboard_screen: gr.update(visible=False),
                run_detail_screen: gr.update(visible=False),
                trace_detail_screen: gr.update(visible=False),
                compare_screen: gr.update(visible=False),
                chat_screen: gr.update(visible=False),
                synthetic_data_screen: gr.update(visible=False),
                new_evaluation_screen: gr.update(visible=False),
                documentation_screen: gr.update(visible=True),
                settings_screen: gr.update(visible=False),
                job_monitoring_screen: gr.update(visible=False),
                dashboard_nav_btn: gr.update(variant="secondary"),
                leaderboard_nav_btn: gr.update(variant="secondary"),
                new_eval_nav_btn: gr.update(variant="secondary"),
                compare_nav_btn: gr.update(variant="secondary"),
                chat_nav_btn: gr.update(variant="secondary"),
                job_monitoring_nav_btn: gr.update(variant="secondary"),
                synthetic_data_nav_btn: gr.update(variant="secondary"),
                docs_nav_btn: gr.update(variant="primary"),
                settings_nav_btn: gr.update(variant="secondary"),
            }

        def navigate_to_settings():
            """Navigate to settings screen"""
            return {
                dashboard_screen: gr.update(visible=False),
                leaderboard_screen: gr.update(visible=False),
                run_detail_screen: gr.update(visible=False),
                trace_detail_screen: gr.update(visible=False),
                compare_screen: gr.update(visible=False),
                chat_screen: gr.update(visible=False),
                synthetic_data_screen: gr.update(visible=False),
                new_evaluation_screen: gr.update(visible=False),
                documentation_screen: gr.update(visible=False),
                settings_screen: gr.update(visible=True),
                job_monitoring_screen: gr.update(visible=False),
                dashboard_nav_btn: gr.update(variant="secondary"),
                leaderboard_nav_btn: gr.update(variant="secondary"),
                new_eval_nav_btn: gr.update(variant="secondary"),
                compare_nav_btn: gr.update(variant="secondary"),
                chat_nav_btn: gr.update(variant="secondary"),
                job_monitoring_nav_btn: gr.update(variant="secondary"),
                synthetic_data_nav_btn: gr.update(variant="secondary"),
                docs_nav_btn: gr.update(variant="secondary"),
                settings_nav_btn: gr.update(variant="primary"),
            }

        def navigate_to_job_monitoring():
            """Navigate to job monitoring screen"""
            return {
                dashboard_screen: gr.update(visible=False),
                leaderboard_screen: gr.update(visible=False),
                run_detail_screen: gr.update(visible=False),
                trace_detail_screen: gr.update(visible=False),
                compare_screen: gr.update(visible=False),
                chat_screen: gr.update(visible=False),
                synthetic_data_screen: gr.update(visible=False),
                new_evaluation_screen: gr.update(visible=False),
                documentation_screen: gr.update(visible=False),
                settings_screen: gr.update(visible=False),
                job_monitoring_screen: gr.update(visible=True),
                dashboard_nav_btn: gr.update(variant="secondary"),
                leaderboard_nav_btn: gr.update(variant="secondary"),
                new_eval_nav_btn: gr.update(variant="secondary"),
                compare_nav_btn: gr.update(variant="secondary"),
                chat_nav_btn: gr.update(variant="secondary"),
                job_monitoring_nav_btn: gr.update(variant="primary"),
                synthetic_data_nav_btn: gr.update(variant="secondary"),
                docs_nav_btn: gr.update(variant="secondary"),
                settings_nav_btn: gr.update(variant="secondary"),
            }

        # Synthetic Data Generator Callbacks
        def on_generate_synthetic_data(domain, tools, num_tasks, difficulty, agent_type):
            """Generate synthetic dataset AND prompt template using MCP server"""
            try:
                from gradio_client import Client
                import json

                # Connect to MCP server
                client = Client("https://mcp-1st-birthday-tracemind-mcp-server.hf.space/")

                # ===== STEP 1: Generate Dataset =====
                print(f"[INFO] Generating synthetic dataset for domain: {domain}")
                dataset_result = client.predict(
                    domain=domain,
                    tools=tools,
                    num_tasks=int(num_tasks),
                    difficulty=difficulty,
                    agent_type=agent_type,
                    api_name="/run_generate_synthetic"
                )

                # Parse the dataset result
                if isinstance(dataset_result, str):
                    try:
                        dataset = json.loads(dataset_result)
                    except:
                        dataset = {"raw_result": dataset_result}
                else:
                    dataset = dataset_result

                # ===== STEP 2: Generate Prompt Template(s) =====
                # When agent_type="both", generate templates for both tool and code agents
                agent_types_to_generate = ["tool", "code"] if agent_type == "both" else [agent_type]
                print(f"[INFO] Generating prompt template(s) for: {agent_types_to_generate}")

                prompt_templates = {}
                try:
                    for current_agent_type in agent_types_to_generate:
                        print(f"[INFO] Generating {current_agent_type} agent template for domain: {domain}")

                        template_result = client.predict(
                            domain=domain,
                            tools=tools,
                            agent_type=current_agent_type,
                            api_name="/run_generate_prompt_template"
                        )

                        # Parse the template result
                        if isinstance(template_result, dict):
                            prompt_template_data = template_result
                        elif isinstance(template_result, str):
                            try:
                                prompt_template_data = json.loads(template_result)
                            except:
                                prompt_template_data = {"error": "Failed to parse template response"}
                        else:
                            prompt_template_data = {"error": "Unexpected template response format"}

                        # Extract the YAML template
                        if "prompt_template" in prompt_template_data:
                            prompt_templates[current_agent_type] = prompt_template_data["prompt_template"]
                            print(f"[INFO] {current_agent_type} agent template generated successfully")
                        elif "error" in prompt_template_data:
                            prompt_templates[current_agent_type] = f"# Error generating template:\n# {prompt_template_data['error']}"
                            print(f"[WARNING] {current_agent_type} template generation error: {prompt_template_data['error']}")
                        else:
                            prompt_templates[current_agent_type] = "# Template format not recognized"
                            print(f"[WARNING] Unexpected template format for {current_agent_type}")

                    # Combine templates for display
                    if agent_type == "both":
                        prompt_template = f"""# ========================================
# TOOL AGENT TEMPLATE (ToolCallingAgent)
# ========================================

{prompt_templates.get('tool', '# Failed to generate tool agent template')}

# ========================================
# CODE AGENT TEMPLATE (CodeAgent)
# ========================================

{prompt_templates.get('code', '# Failed to generate code agent template')}
"""
                    else:
                        prompt_template = prompt_templates.get(agent_type, "# Template not generated")

                    # Store all templates in data for push_to_hub
                    prompt_template_data = {
                        "agent_type": agent_type,
                        "templates": prompt_templates,
                        "combined": prompt_template
                    }

                except Exception as template_error:
                    print(f"[WARNING] Failed to generate prompt template: {template_error}")
                    prompt_template = f"# Failed to generate template: {str(template_error)}"
                    prompt_template_data = {"error": str(template_error)}

                # Generate stats
                task_count = len(dataset.get('tasks', [])) if isinstance(dataset.get('tasks'), list) else 0

                # Generate suggested repository name with default username
                domain_clean = domain.lower().replace(' ', '-').replace('_', '-')
                default_username = "kshitijthakkar"  # Default username for env HF_TOKEN
                suggested_repo_name = f"{default_username}/smoltrace-{domain_clean}-tasks"

                stats_md = f"""
                ### ✅ Dataset & Prompt Template Generated Successfully!

                - **Total Tasks**: {task_count}
                - **Domain**: {dataset.get('domain', domain)}
                - **Difficulty**: {dataset.get('difficulty', difficulty)}
                - **Agent Type**: {dataset.get('agent_type', agent_type)}
                - **Tools Available**: {len(tools.split(','))}
                - **Prompt Template**: ✅ AI-customized for your domain

                Review both the dataset and prompt template in the tabs above, then push to HuggingFace Hub when ready.

                **Suggested repo name**: `{suggested_repo_name}`

                💡 **Tip**: The prompt template will be automatically included in your dataset card!
                """

                return {
                    generated_dataset_state: dataset,
                    generated_prompt_template_state: prompt_template_data,
                    dataset_preview: gr.update(value=dataset, visible=True),
                    dataset_stats: gr.update(value=stats_md, visible=True),
                    prompt_template_preview: gr.update(value=prompt_template, visible=True),
                    generation_status: "✅ Dataset & prompt template generated! Review in tabs above.",
                    push_btn: gr.update(visible=True),
                    repo_name_input: gr.update(value=suggested_repo_name)
                }

            except Exception as e:
                error_msg = f"❌ Error generating dataset: {str(e)}"
                print(f"[ERROR] Synthetic data generation failed: {e}")
                import traceback
                traceback.print_exc()

                return {
                    generated_dataset_state: None,
                    generated_prompt_template_state: None,
                    dataset_preview: gr.update(visible=False),
                    dataset_stats: gr.update(visible=False),
                    prompt_template_preview: gr.update(visible=False),
                    generation_status: error_msg,
                    push_btn: gr.update(visible=False),
                    repo_name_input: gr.update(value="")
                }

        def on_push_to_hub(dataset, prompt_template_data, repo_name, hf_token, private):
            """Push dataset AND prompt template to HuggingFace Hub"""
            try:
                from gradio_client import Client
                import os
                import json

                # Validate inputs
                if not dataset:
                    return "❌ No dataset to push. Please generate a dataset first."

                if not repo_name:
                    return "❌ Please provide a repository name."

                # Extract prompt template for pushing
                prompt_template_to_push = None
                if prompt_template_data and isinstance(prompt_template_data, dict):
                    if "combined" in prompt_template_data:
                        prompt_template_to_push = prompt_template_data["combined"]
                    elif "prompt_template" in prompt_template_data:
                        prompt_template_to_push = prompt_template_data["prompt_template"]

                print(f"[INFO] Prompt template will {'be included' if prompt_template_to_push else 'NOT be included'} in dataset card")

                # Determine which HF token to use (user-provided or environment)
                if hf_token and hf_token.strip():
                    # User provided a token
                    token_to_use = hf_token.strip()
                    token_source = "user-provided"
                    print(f"[INFO] Using user-provided HF token")
                else:
                    # Fall back to environment token
                    token_to_use = os.getenv("HF_TOKEN", "")
                    token_source = "environment (HF_TOKEN)"
                    print(f"[INFO] No user token provided, using environment HF_TOKEN")

                # Validate token exists
                if not token_to_use:
                    return "❌ No HuggingFace token available. Please either:\n- Provide your HF token in the field above, OR\n- Set HF_TOKEN environment variable"

                print(f"[INFO] Token source: {token_source}")
                print(f"[INFO] Token length: {len(token_to_use)} characters")

                # Connect to MCP server
                client = Client("https://mcp-1st-birthday-tracemind-mcp-server.hf.space/")

                # Extract tasks array from dataset (MCP server expects just the tasks array)
                if isinstance(dataset, dict):
                    # If dataset has a 'tasks' key, use that array
                    if 'tasks' in dataset:
                        tasks_to_push = dataset['tasks']
                        print(f"[INFO] Extracted {len(tasks_to_push)} tasks from dataset")
                    else:
                        # Otherwise, assume the entire dict is the tasks array
                        tasks_to_push = dataset
                        print(f"[INFO] Using entire dataset dict (no 'tasks' key found)")
                elif isinstance(dataset, list):
                    # If it's already a list, use it directly
                    tasks_to_push = dataset
                    print(f"[INFO] Dataset is already a list with {len(tasks_to_push)} items")
                else:
                    # Fallback: wrap in a list
                    tasks_to_push = [dataset]
                    print(f"[INFO] Wrapped dataset in list")

                # Validate tasks_to_push is a list
                if not isinstance(tasks_to_push, list):
                    return f"❌ Error: Expected tasks to be a list, got {type(tasks_to_push).__name__}"

                # Convert tasks array to JSON string
                dataset_json = json.dumps(tasks_to_push)
                print(f"[INFO] Sending {len(tasks_to_push)} tasks to MCP server")
                print(f"[INFO] Repo name: {repo_name}")
                print(f"[INFO] Private: {private}")
                print(f"[INFO] Passing HF token to MCP server (source: {token_source})")

                # Call the push dataset endpoint with the token and prompt template
                result = client.predict(
                    dataset_json=dataset_json,
                    repo_name=repo_name,
                    hf_token=token_to_use,  # Token from user input OR environment
                    private=private,
                    prompt_template=prompt_template_to_push if prompt_template_to_push else "",  # Include template if available
                    api_name="/run_push_dataset"
                )

                # Parse result
                print(f"[INFO] MCP server response: {result}")

                # Handle dict response with error
                if isinstance(result, dict):
                    if 'error' in result:
                        error_msg = result['error']
                        # Check if it's an authentication error
                        if 'authentication' in error_msg.lower() or 'unauthorized' in error_msg.lower() or 'token' in error_msg.lower():
                            return f"❌ Authentication Error: {error_msg}\n\n💡 Check that your HF token has write permissions for datasets."
                        return f"❌ Error from MCP server: {error_msg}"
                    elif 'success' in result or 'repo_url' in result:
                        repo_url = result.get('repo_url', f"https://huggingface.co/datasets/{repo_name}")
                        return f"""✅ Dataset successfully pushed to HuggingFace Hub!

**Repository**: [{repo_name}]({repo_url})

{result.get('message', 'Dataset uploaded successfully!')}
"""
                    else:
                        return f"✅ Push completed. Result: {result}"

                # Handle string response
                elif isinstance(result, str):
                    if "error" in result.lower():
                        return f"❌ Error: {result}"
                    elif "success" in result.lower() or "pushed" in result.lower():
                        return f"""✅ Dataset successfully pushed to HuggingFace Hub!

**Repository**: [{repo_name}](https://huggingface.co/datasets/{repo_name})

Result: {result}
"""
                    else:
                        return f"✅ Push completed. Result: {result}"
                else:
                    return f"✅ Push completed. Result: {result}"

            except Exception as e:
                error_msg = f"❌ Error pushing to Hub: {str(e)}"
                print(f"[ERROR] Push to Hub failed: {e}")
                import traceback
                traceback.print_exc()
                return error_msg

        # Event handlers
        # Load dashboard on app start
        app.load(
            fn=navigate_to_dashboard,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen,
                new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ] + list(dashboard_components.values())
        )

        app.load(
        fn=load_leaderboard,
        outputs=[leaderboard_by_model, model_filter, model_filter, provider_filter]
        )

        app.load(
        fn=load_trends,
        outputs=[trends_plot]
        )

        # COMMENTED OUT: Load drilldown data on page load (DrillDown tab removed)
        # app.load(
        # fn=load_drilldown,
        # inputs=[drilldown_agent_type_filter, drilldown_provider_filter],
        # outputs=[leaderboard_table]
        # )

        # Refresh button handler
        refresh_leaderboard_btn.click(
        fn=refresh_leaderboard,
        outputs=[leaderboard_by_model, model_filter, model_filter]
        )

        # Leaderboard tab inline filters
        apply_filters_btn.click(
        fn=apply_leaderboard_filters,
        inputs=[agent_type_filter, provider_filter, sort_by_dropdown, sort_order],
        outputs=[leaderboard_by_model]
        )

        # HTML Plus leaderboard row selection
        leaderboard_by_model.select(
        fn=on_html_leaderboard_select,
        inputs=None,  # HTMLPlus passes data via evt.value
        outputs=[
            leaderboard_screen,
            run_detail_screen,
            run_metadata_html,
            test_cases_table,
            performance_charts,
            run_card_html,
            run_gpu_summary_cards_html,
            run_gpu_metrics_plot,
            run_gpu_metrics_json
        ]
        )

        # COMMENTED OUT: DrillDown tab inline filters
        # apply_drilldown_filters_btn.click(
        # fn=apply_drilldown_filters,
        # inputs=[drilldown_agent_type_filter, drilldown_provider_filter, drilldown_sort_by_dropdown, drilldown_sort_order],
        # outputs=[leaderboard_table]
        # )

        # Sidebar filters (apply to remaining tabs - removed leaderboard_table)
        model_filter.change(
        fn=apply_sidebar_filters,
        inputs=[model_filter, sidebar_agent_type_filter],
        outputs=[leaderboard_by_model, trends_plot, compare_components['compare_run_a_dropdown'], compare_components['compare_run_b_dropdown']]
        )

        sidebar_agent_type_filter.change(
        fn=apply_sidebar_filters,
        inputs=[model_filter, sidebar_agent_type_filter],
        outputs=[leaderboard_by_model, trends_plot, compare_components['compare_run_a_dropdown'], compare_components['compare_run_b_dropdown']]
        )


        viz_type.change(
        fn=update_analytics,
        inputs=[viz_type],
        outputs=[analytics_chart, viz_explanation]
        )

        app.load(
        fn=update_analytics,
        inputs=[viz_type],
        outputs=[analytics_chart, viz_explanation]
        )

        generate_card_btn.click(
        fn=generate_card,
        inputs=[top_n_slider],
        outputs=[card_preview, download_card_btn]
        )

        # Download leaderboard summary card as PNG
        download_card_btn.click(
            fn=None,
            js=download_card_as_png_js("summary-card-html")
        )

        app.load(
        fn=generate_insights,
        outputs=[mcp_insights]
        )

        regenerate_btn.click(
        fn=generate_insights,
        outputs=[mcp_insights]
        )

        # Wire up navigation buttons
        dashboard_nav_btn.click(
            fn=navigate_to_dashboard,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen,
                new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ] + list(dashboard_components.values())
        )

        leaderboard_nav_btn.click(
            fn=navigate_to_leaderboard,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen, new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ]
        )

        new_eval_nav_btn.click(
            fn=navigate_to_new_evaluation,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen, new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ]
        )

        compare_nav_btn.click(
            fn=navigate_to_compare,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen,
                new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn,
                compare_components['compare_run_a_dropdown'], compare_components['compare_run_b_dropdown']
            ]
        )

        chat_nav_btn.click(
            fn=navigate_to_chat,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen,
                new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ]
        )
        synthetic_data_nav_btn.click(
            fn=navigate_to_synthetic_data,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen,
                new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ]
        )

        job_monitoring_nav_btn.click(
            fn=navigate_to_job_monitoring,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen,
                new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ]
        )

        docs_nav_btn.click(
            fn=navigate_to_documentation,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen,
                new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ]
        )

        settings_nav_btn.click(
            fn=navigate_to_settings,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen,
                new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ]
        )

        # Synthetic Data Generator event handlers
        generate_btn.click(
            fn=on_generate_synthetic_data,
            inputs=[domain_input, tools_input, num_tasks_input, difficulty_input, agent_type_input],
            outputs=[generated_dataset_state, generated_prompt_template_state, dataset_preview, dataset_stats, prompt_template_preview, generation_status, push_btn, repo_name_input]
        )

        push_btn.click(
            fn=on_push_to_hub,
            inputs=[generated_dataset_state, generated_prompt_template_state, repo_name_input, hf_token_input, private_checkbox],
            outputs=[push_status]
        )

        # New Evaluation screen event handlers
        back_to_leaderboard_from_eval_btn.click(
            fn=navigate_to_leaderboard,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen, new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ]
        )

        eval_estimate_btn.click(
            fn=on_hardware_change,
            inputs=[eval_model, eval_hardware, eval_provider, eval_infra_provider],
            outputs=[eval_cost_estimate]
        )

        # Update hardware options when infrastructure provider changes
        eval_infra_provider.change(
            fn=on_infra_provider_change,
            inputs=[eval_infra_provider],
            outputs=[eval_hardware]
        )

        # Auto-select hardware when provider changes
        eval_provider.change(
            fn=on_provider_change,
            inputs=[eval_provider],
            outputs=[eval_hardware]
        )

        eval_submit_btn.click(
            fn=on_submit_evaluation_comprehensive,
            inputs=[
                # Infrastructure
                eval_infra_provider, eval_hardware,
                # Model Configuration
                eval_model, eval_provider, eval_hf_inference_provider, eval_hf_token,
                # Agent Configuration
                eval_agent_type, eval_search_provider, eval_enable_tools,
                # Test Configuration
                eval_dataset_name, eval_split, eval_difficulty, eval_parallel_workers,
                # Output & Monitoring
                eval_output_format, eval_output_dir, eval_enable_otel, eval_enable_gpu_metrics, eval_private, eval_debug, eval_quiet, eval_run_id, eval_timeout
            ],
            outputs=[eval_success_message]
        )

        # Chat screen event handlers (with streaming and per-session agent state)
        chat_components['send_btn'].click(
            fn=on_send_message,
            inputs=[chat_components['message'], chat_components['chatbot'], chat_components['agent_state']],
            outputs=[chat_components['chatbot'], chat_components['message'], chat_components['agent_state']]
        )

        chat_components['message'].submit(
            fn=on_send_message,
            inputs=[chat_components['message'], chat_components['chatbot'], chat_components['agent_state']],
            outputs=[chat_components['chatbot'], chat_components['message'], chat_components['agent_state']]
        )

        chat_components['clear_btn'].click(
            fn=on_clear_chat,
            inputs=[chat_components['agent_state']],
            outputs=[chat_components['chatbot'], chat_components['agent_state']]
        )

        chat_components['quick_analyze'].click(
            fn=lambda: on_quick_action("analyze"),
            inputs=[],
            outputs=[chat_components['message']]
        )

        chat_components['quick_costs'].click(
            fn=lambda: on_quick_action("costs"),
            inputs=[],
            outputs=[chat_components['message']]
        )

        chat_components['quick_recommend'].click(
            fn=lambda: on_quick_action("recommend"),
            inputs=[],
            outputs=[chat_components['message']]
        )

        chat_components['quick_multi_tool'].click(
            fn=lambda: on_quick_action("multi_tool"),
            inputs=[],
            outputs=[chat_components['message']]
        )

        chat_components['quick_synthetic'].click(
            fn=lambda: on_quick_action("synthetic"),
            inputs=[],
            outputs=[chat_components['message']]
        )

        # Compare button handler
        compare_components['compare_button'].click(
            fn=lambda run_a, run_b: handle_compare_runs(run_a, run_b, leaderboard_df_cache, compare_components),
            inputs=[
                compare_components['compare_run_a_dropdown'],
                compare_components['compare_run_b_dropdown']
            ],
            outputs=[
                compare_components['comparison_output'],
                compare_components['run_a_card'],
                compare_components['run_b_card'],
                compare_components['comparison_charts'],
                compare_components['winner_summary'],
                compare_components['radar_comparison_chart'],
                compare_components['comparison_card_html']
            ]
        )

        # Wire up AI comparison insights button (MCP compare_runs tool)
        compare_components['generate_ai_comparison_btn'].click(
            fn=generate_ai_comparison,
            inputs=[compare_components['comparison_focus']],
            outputs=[compare_components['ai_comparison_insights']]
        )

        # Wire up run AI insights button (MCP analyze_results tool)
        generate_run_ai_insights_btn.click(
            fn=generate_run_ai_insights,
            inputs=[run_analysis_focus, run_max_rows],
            outputs=[run_ai_insights]
        )

        # Back to leaderboard from compare
        compare_components['back_to_leaderboard_btn'].click(
            fn=navigate_to_leaderboard,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen, chat_screen, synthetic_data_screen, new_evaluation_screen, documentation_screen, settings_screen, job_monitoring_screen,
                dashboard_nav_btn, leaderboard_nav_btn, new_eval_nav_btn, compare_nav_btn, chat_nav_btn, synthetic_data_nav_btn, job_monitoring_nav_btn, docs_nav_btn, settings_nav_btn
            ]
        )

        # Download comparison report card as PNG
        compare_components['download_comparison_card_btn'].click(
            fn=None,
            js=download_card_as_png_js(element_id="comparison-card-html")
        )

        # COMMENTED OUT: DrillDown table select event handler
        # leaderboard_table.select(
        # fn=on_drilldown_select,
        # inputs=[leaderboard_table],  # Pass dataframe to handler (like MockTraceMind)
        # outputs=[
        #     leaderboard_screen,
        #     run_detail_screen,
        #     run_metadata_html,
        #     test_cases_table,
        #     performance_charts,
        #     run_card_html,
        #     run_gpu_summary_cards_html,
        #     run_gpu_metrics_plot,
        #     run_gpu_metrics_json
        # ]
        # )

        back_to_leaderboard_btn.click(
        fn=go_back_to_leaderboard,
        inputs=[],
        outputs=[leaderboard_screen, run_detail_screen]
        )

        # Trace detail navigation
        test_cases_table.select(
            fn=on_test_case_select,
            inputs=[test_cases_table],
            outputs=[
                run_detail_screen,
                trace_detail_screen,
                trace_title,
                trace_metadata_html,
                trace_thought_graph,
                span_visualization,
                span_details_table,
                span_details_json
            ]
        )

        back_to_run_detail_btn.click(
            fn=go_back_to_run_detail,
            outputs=[run_detail_screen, trace_detail_screen]
        )

        # Wire up trace AI question button (MCP debug_trace tool)
        trace_ask_btn.click(
            fn=ask_about_trace,
            inputs=[trace_question],
            outputs=[trace_answer]
        )

        # HTML table row click handler (JavaScript bridge via hidden textbox)
        selected_row_index.change(
        fn=on_html_table_row_click,
        inputs=[selected_row_index],
        outputs=[
            leaderboard_screen,
            run_detail_screen,
            run_metadata_html,
            test_cases_table,
            run_card_html,
            performance_charts,
            selected_row_index,
            run_gpu_summary_cards_html,
            run_gpu_metrics_plot,
            run_gpu_metrics_json
        ]
        )

        # Download run report card as PNG
        download_run_card_btn.click(
            fn=None,
            js=download_card_as_png_js(element_id="run-card-html")
        )


if __name__ == "__main__":
    print("Starting TraceMind-AI...")
    print(f"Data Source: {os.getenv('DATA_SOURCE', 'both')}")
    print(f"JSON Path: {os.getenv('JSON_DATA_PATH', './sample_data')}")

    # Configure queue to handle up to 4 concurrent users
    app.queue(default_concurrency_limit=4, max_size=4)

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
