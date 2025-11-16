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
from utils.navigation import Navigator, Screen



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
    global current_selected_run, current_selected_trace

    print(f"[DEBUG] on_test_case_select called with index: {evt.index}")

    # Check if we have a selected run
    if current_selected_run is None:
        print("[ERROR] No run selected - current_selected_run is None")
        gr.Warning("Please select a run from the leaderboard first")
        return {}

    try:
        # Get selected test case
        selected_idx = evt.index[0]
        if df is None or df.empty or selected_idx >= len(df):
            gr.Warning("Invalid test case selection")
            return {}

        test_case = df.iloc[selected_idx].to_dict()
        trace_id = test_case.get('trace_id')

        print(f"[DEBUG] Selected test case: {test_case.get('task_id', 'Unknown')} (trace_id: {trace_id})")

        # Load trace data
        traces_dataset = current_selected_run.get('traces_dataset')
        if not traces_dataset:
            gr.Warning("No traces dataset found in current run")
            return {}

        trace_data = data_loader.get_trace_by_id(traces_dataset, trace_id)

        if not trace_data:
            gr.Warning(f"Trace not found: {trace_id}")
            return {}

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

        # Load GPU metrics (if available)
        gpu_summary_html = "<div style='padding: 20px; text-align: center;'>⚠️ No GPU metrics available (expected for API models)</div>"
        gpu_plot = None
        gpu_json_data = {}

        try:
            if 'metrics_dataset' in current_selected_run and current_selected_run['metrics_dataset']:
                metrics_dataset = current_selected_run['metrics_dataset']
                gpu_metrics_data = data_loader.load_metrics(metrics_dataset)

                if gpu_metrics_data is not None and not gpu_metrics_data.empty:
                    gpu_plot = create_gpu_metrics_dashboard(gpu_metrics_data)
                    gpu_summary_html = create_gpu_summary_cards(gpu_metrics_data)
                    gpu_json_data = gpu_metrics_data.to_dict('records')
        except Exception as e:
            print(f"[WARNING] Could not load GPU metrics: {e}")

        # Return dictionary with visibility updates and data
        return {
            run_detail_screen: gr.update(visible=False),
            trace_detail_screen: gr.update(visible=True),
            trace_title: gr.update(value=f"# 🔍 Trace Detail: {trace_id}"),
            trace_metadata_html: gr.update(value=create_trace_metadata_html(trace_data)),
            trace_thought_graph: gr.update(value=thought_graph_plot),
            span_visualization: gr.update(value=span_viz_plot),
            span_details_table: gr.update(value=span_table_df),
            span_details_json: gr.update(value=span_details_data),
            gpu_summary_cards_html: gr.update(value=gpu_summary_html),
            gpu_metrics_plot: gr.update(value=gpu_plot),
            gpu_metrics_json: gr.update(value=gpu_json_data)
        }

    except Exception as e:
        print(f"[ERROR] on_test_case_select failed: {e}")
        import traceback
        traceback.print_exc()
        gr.Warning(f"Error loading trace: {e}")
        return {}



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
                "Response Time Distribution",
                "Token Usage per Test",
                "Cost per Test",
                "Success vs Failure"
            ),
            specs=[[{"type": "histogram"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "pie"}]]
        )

        # 1. Response Time Distribution (Histogram)
        if 'execution_time_ms' in results_df.columns:
            fig.add_trace(
                go.Histogram(
                    x=results_df['execution_time_ms'],
                    nbinsx=20,
                    marker_color='#3498DB',
                    name='Response Time',
                    showlegend=False
                ),
                row=1, col=1
            )
            fig.update_xaxes(title_text="Time (ms)", row=1, col=1)
            fig.update_yaxes(title_text="Count", row=1, col=1)

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
    """Apply sidebar filters to both leaderboard tabs"""
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

    # For drilldown table
    display_df = df[[
        'run_id', 'model', 'agent_type', 'provider', 'success_rate',
        'total_tests', 'avg_duration_ms', 'total_cost_usd', 'submitted_by'
    ]].copy()
    display_df.columns = ['Run ID', 'Model', 'Agent Type', 'Provider', 'Success Rate', 'Tests', 'Duration (ms)', 'Cost (USD)', 'Submitted By']

    # Update trends
    trends_fig = create_trends_plot(df)

    # Update compare dropdowns
    compare_choices = []
    for _, row in df.iterrows():
        label = f"{row.get('model', 'Unknown')} - {row.get('timestamp', 'N/A')}"
        value = row.get('run_id', '')
        if value:
            compare_choices.append((label, value))

    return {
        leaderboard_by_model: gr.update(value=html),
        leaderboard_table: gr.update(value=display_df),
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

        # Generate performance chart
        perf_chart = create_performance_charts(results_df)

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

        # Generate performance chart
        perf_chart = create_performance_charts(results_df)

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
            performance_charts: gr.update(value=perf_chart)
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
            compare_nav_btn = gr.Button("⚖️ Compare", variant="secondary", size="lg")
            docs_nav_btn = gr.Button("📚 Documentation", variant="secondary", size="lg")
    
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
                                label="Sort By"
                            )
                        with gr.Column(scale=1):
                            sort_order = gr.Radio(
                                choices=["Descending", "Ascending"],
                                value="Descending",
                                label="Sort Order"
                            )

                    with gr.Row():
                        apply_filters_btn = gr.Button("🔍 Apply Filters", variant="primary", size="sm")

                    # Styled HTML leaderboard
                    leaderboard_by_model = gr.HTML(label="Styled Leaderboard")
    
                with gr.TabItem("📋 DrillDown"):
                    gr.Markdown("*Click any row to view detailed run information*")

                    # Inline filters for drilldown table
                    with gr.Row():
                        with gr.Column(scale=1):
                            drilldown_agent_type_filter = gr.Radio(
                                choices=["All", "tool", "code", "both"],
                                value="All",
                                label="Agent Type",
                                info="Filter by agent type"
                            )
                        with gr.Column(scale=1):
                            drilldown_provider_filter = gr.Dropdown(
                                choices=["All"],
                                value="All",
                                label="Provider",
                                info="Filter by provider"
                            )
                        with gr.Column(scale=1):
                            drilldown_sort_by_dropdown = gr.Dropdown(
                                choices=["success_rate", "total_cost_usd", "avg_duration_ms", "total_tokens"],
                                value="success_rate",
                                label="Sort By"
                            )
                        with gr.Column(scale=1):
                            drilldown_sort_order = gr.Radio(
                                choices=["Descending", "Ascending"],
                                value="Descending",
                                label="Sort Order"
                            )

                    with gr.Row():
                        apply_drilldown_filters_btn = gr.Button("🔍 Apply Filters", variant="primary", size="sm")

                    # Simple table controlled by inline filters
                    leaderboard_table = gr.Dataframe(
                        headers=["Run ID", "Model", "Agent Type", "Provider", "Success Rate", "Tests", "Duration (ms)", "Cost (USD)", "Submitted By"],
                        interactive=False,
                        wrap=True
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
    
        # Screen 3: Run Detail (Enhanced with Tabs)
        with gr.Column(visible=False) as run_detail_screen:
            # Navigation
            with gr.Row():
                back_to_leaderboard_btn = gr.Button("⬅️ Back to Leaderboard", variant="secondary", size="sm")

            run_detail_title = gr.Markdown("# 📊 Run Detail")

            with gr.Tabs():
                with gr.TabItem("📋 Overview"):
                    gr.Markdown("*Run metadata and summary*")
                    run_metadata_html = gr.HTML("")

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

                with gr.TabItem("🖥️ GPU Metrics"):
                    gr.Markdown("*Performance metrics for GPU-based models (not available for API models)*")
                    gpu_summary_cards_html = gr.HTML(label="GPU Summary", show_label=False)

                    with gr.Tabs():
                        with gr.TabItem("📈 Time Series Dashboard"):
                            gpu_metrics_plot = gr.Plot(label="GPU Metrics Over Time", show_label=False)

                        with gr.TabItem("📋 Raw Metrics Data"):
                            gpu_metrics_json = gr.JSON(label="GPU Metrics Data")

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
                    lines=2
                )
                trace_ask_btn = gr.Button("Ask", variant="primary")
                trace_answer = gr.Markdown("*Ask a question to get AI-powered insights*")

        # Screen 5: Compare Screen
        compare_screen, compare_components = create_compare_ui()

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
                dashboard_nav_btn: gr.update(variant="primary"),
                leaderboard_nav_btn: gr.update(variant="secondary"),
                compare_nav_btn: gr.update(variant="secondary"),
                docs_nav_btn: gr.update(variant="secondary"),
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
                dashboard_nav_btn: gr.update(variant="secondary"),
                leaderboard_nav_btn: gr.update(variant="primary"),
                compare_nav_btn: gr.update(variant="secondary"),
                docs_nav_btn: gr.update(variant="secondary"),
            }

        def navigate_to_compare():
            """Navigate to compare screen and populate dropdown choices"""
            try:
                leaderboard_df = data_loader.load_leaderboard()

                # Create run choices for dropdowns (model name with run_id)
                run_choices = []
                for _, row in leaderboard_df.iterrows():
                    label = f"{row.get('model', 'Unknown')} - {row.get('timestamp', 'N/A')}"
                    value = row.get('run_id', '')
                    if value:
                        run_choices.append((label, value))

                return {
                    dashboard_screen: gr.update(visible=False),
                    leaderboard_screen: gr.update(visible=False),
                    run_detail_screen: gr.update(visible=False),
                    trace_detail_screen: gr.update(visible=False),
                    compare_screen: gr.update(visible=True),
                    dashboard_nav_btn: gr.update(variant="secondary"),
                    leaderboard_nav_btn: gr.update(variant="secondary"),
                    compare_nav_btn: gr.update(variant="primary"),
                    docs_nav_btn: gr.update(variant="secondary"),
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
                    dashboard_nav_btn: gr.update(variant="secondary"),
                    leaderboard_nav_btn: gr.update(variant="secondary"),
                    compare_nav_btn: gr.update(variant="primary"),
                    docs_nav_btn: gr.update(variant="secondary"),
                }

        # Event handlers
        # Load dashboard on app start
        app.load(
            fn=navigate_to_dashboard,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen,
                dashboard_nav_btn, leaderboard_nav_btn, compare_nav_btn, docs_nav_btn
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

        # Load drilldown data on page load
        app.load(
        fn=load_drilldown,
        inputs=[drilldown_agent_type_filter, drilldown_provider_filter],
        outputs=[leaderboard_table]
        )

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

        # DrillDown tab inline filters
        apply_drilldown_filters_btn.click(
        fn=apply_drilldown_filters,
        inputs=[drilldown_agent_type_filter, drilldown_provider_filter, drilldown_sort_by_dropdown, drilldown_sort_order],
        outputs=[leaderboard_table]
        )

        # Sidebar filters (apply to all tabs)
        model_filter.change(
        fn=apply_sidebar_filters,
        inputs=[model_filter, sidebar_agent_type_filter],
        outputs=[leaderboard_by_model, leaderboard_table, trends_plot, compare_components['compare_run_a_dropdown'], compare_components['compare_run_b_dropdown']]
        )

        sidebar_agent_type_filter.change(
        fn=apply_sidebar_filters,
        inputs=[model_filter, sidebar_agent_type_filter],
        outputs=[leaderboard_by_model, leaderboard_table, trends_plot, compare_components['compare_run_a_dropdown'], compare_components['compare_run_b_dropdown']]
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

        # Wire up navigation buttons
        dashboard_nav_btn.click(
            fn=navigate_to_dashboard,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen,
                dashboard_nav_btn, leaderboard_nav_btn, compare_nav_btn, docs_nav_btn
            ] + list(dashboard_components.values())
        )

        leaderboard_nav_btn.click(
            fn=navigate_to_leaderboard,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen,
                dashboard_nav_btn, leaderboard_nav_btn, compare_nav_btn, docs_nav_btn
            ]
        )

        compare_nav_btn.click(
            fn=navigate_to_compare,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen,
                dashboard_nav_btn, leaderboard_nav_btn, compare_nav_btn, docs_nav_btn,
                compare_components['compare_run_a_dropdown'], compare_components['compare_run_b_dropdown']
            ]
        )

        # Compare button handler
        compare_components['compare_button'].click(
            fn=lambda run_a, run_b: on_compare_runs(run_a, run_b, leaderboard_df_cache, compare_components),
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
                compare_components['radar_comparison_chart']
            ]
        )

        # Back to leaderboard from compare
        compare_components['back_to_leaderboard_btn'].click(
            fn=navigate_to_leaderboard,
            outputs=[
                dashboard_screen, leaderboard_screen, run_detail_screen, trace_detail_screen, compare_screen,
                dashboard_nav_btn, leaderboard_nav_btn, compare_nav_btn, docs_nav_btn
            ]
        )

        leaderboard_table.select(
        fn=on_drilldown_select,
        inputs=[leaderboard_table],  # Pass dataframe to handler (like MockTraceMind)
        outputs=[leaderboard_screen, run_detail_screen, run_metadata_html, test_cases_table, performance_charts]
        )

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
                span_details_json,
                gpu_summary_cards_html,
                gpu_metrics_plot,
                gpu_metrics_json
            ]
        )

        back_to_run_detail_btn.click(
            fn=go_back_to_run_detail,
            outputs=[run_detail_screen, trace_detail_screen]
        )


        # HTML table row click handler (JavaScript bridge via hidden textbox)
        selected_row_index.change(
        fn=on_html_table_row_click,
        inputs=[selected_row_index],
        outputs=[leaderboard_screen, run_detail_screen, run_metadata_html, test_cases_table, selected_row_index]
        )


if __name__ == "__main__":
    print("Starting TraceMind-AI...")
    print(f"Data Source: {os.getenv('DATA_SOURCE', 'both')}")
    print(f"JSON Path: {os.getenv('JSON_DATA_PATH', './sample_data')}")

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
