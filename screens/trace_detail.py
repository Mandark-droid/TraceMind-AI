"""
Screen 4: Trace Detail View
Shows detailed OpenTelemetry trace visualization
"""

import gradio as gr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pandas as pd
from typing import Optional, Callable, Dict, Any, List
from components.thought_graph import create_thought_graph


def create_trace_detail_screen(
    trace_data: dict,
    on_back: Optional[Callable] = None,
    mcp_qa_enabled: bool = True
) -> gr.Blocks:
    """
    Create the trace detail screen UI

    Args:
        trace_data: OpenTelemetry trace data
        on_back: Callback for back button
        mcp_qa_enabled: Enable MCP Q&A tool

    Returns:
        Gradio Blocks for trace detail screen
    """

    with gr.Blocks() as trace_detail:
        with gr.Row():
            if on_back:
                back_btn = gr.Button("⬅️ Back to Run Detail", variant="secondary", size="sm")

        gr.Markdown(f"# 🔍 Trace Detail: {trace_data.get('trace_id', 'Unknown')}")

        # Safely extract spans
        spans = trace_data.get('spans', [])
        if hasattr(spans, 'tolist'):
            spans = spans.tolist()
        elif not isinstance(spans, list):
            spans = list(spans) if spans is not None else []

        # Trace metadata
        with gr.Row():
            gr.Markdown(f"""
            **Trace ID:** `{trace_data.get('trace_id', 'N/A')}`
            **Total Spans:** {len(spans)}
            """)

        # Tabs for different visualizations
        with gr.Tabs() as tabs:
            # Tab 1: Thought Graph (STAR FEATURE!)
            with gr.Tab("🧠 Thought Graph"):
                gr.Markdown("""
                ### Agent Reasoning Flow
                This graph visualizes how your agent thinks - showing the flow of reasoning steps,
                tool calls, and LLM interactions as a network.

                **Node Colors:**
                - 🟣 Purple: LLM reasoning steps
                - 🟠 Orange: Tool calls
                - 🔵 Blue: Chains/Agents
                - 🔴 Red: Errors
                """)

                # Create and display thought graph
                thought_graph_plot = gr.Plot(
                    value=create_thought_graph(spans, trace_data.get('trace_id', 'Unknown')),
                    label=""
                )

            # Tab 2: Execution Timeline (Waterfall)
            with gr.Tab("⏱️ Execution Timeline"):
                gr.Markdown("""
                ### Waterfall Chart
                Timeline view showing when each span executed and for how long.
                """)

                # Span visualization
                span_viz = gr.Plot(
                    value=create_span_visualization(spans, trace_data.get('trace_id', 'Unknown')),
                    label=""
                )

            # Tab 3: Span Details
            with gr.Tab("📋 Span Details"):
                gr.Markdown("""
                ### Detailed Span Information
                Raw span data with attributes, status, and metadata.
                """)

                # Span details table
                span_table = create_span_table(spans)

        # MCP Q&A Tool (below tabs)
        gr.Markdown("---")
        if mcp_qa_enabled:
            with gr.Accordion("🤖 Ask About This Trace", open=False):
                question_input = gr.Textbox(
                    label="Question",
                    placeholder="e.g., Why was the tool called twice? What tool did the agent use first?",
                    lines=2,
                    info="Ask questions about this trace execution, tool usage, or agent behavior"
                )
                ask_btn = gr.Button("Ask", variant="primary")
                answer_output = gr.Markdown("*Ask a question to get AI-powered insights*")

                # Wire up MCP Q&A (placeholder for now)
                ask_btn.click(
                    fn=lambda q: f"**Answer:** This is a placeholder. MCP integration coming soon.\n\n**Your question:** {q}",
                    inputs=[question_input],
                    outputs=[answer_output]
                )

        # Wire up events
        if on_back:
            back_btn.click(fn=on_back, inputs=[], outputs=[])

    return trace_detail


def process_trace_data(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process trace spans for waterfall visualization"""
    # Ensure spans is a list
    if hasattr(spans, 'tolist'):
        spans = spans.tolist()
    elif not isinstance(spans, list):
        spans = list(spans) if spans is not None else []

    if not spans:
        return []

    # Helper function to get timestamp from span (handles different field names)
    def get_timestamp(span, field_name):
        """Get timestamp handling different OpenTelemetry field name variations"""
        # Try different variations of field names
        variations = [
            field_name,  # e.g., 'startTime'
            field_name.lower(),  # e.g., 'starttime'
            field_name.replace('Time', 'TimeUnixNano'),  # e.g., 'startTimeUnixNano'
            field_name[0].lower() + field_name[1:],  # e.g., 'startTime'
            # Add snake_case variations (start_time, end_time)
            field_name.replace('Time', '_time').lower(),  # e.g., 'start_time'
            field_name.replace('Time', '_time_unix_nano').lower(),  # e.g., 'start_time_unix_nano'
        ]

        for var in variations:
            if var in span:
                value = span[var]
                # Handle both string and numeric timestamps
                if isinstance(value, str):
                    return int(value)
                return value

        # If not found, return 0
        return 0

    # Calculate relative times
    start_times = [get_timestamp(span, 'startTime') for span in spans]
    min_start = min(start_times) if start_times else 0
    max_start = max(start_times) if start_times else 0

    # Check if we have any actual timing data
    has_timing_data = min_start > 0 or max_start > 0

    # Debug: Print first span's raw timestamps
    if spans:
        first_span = spans[0]
        print(f"[DEBUG] First span raw data sample:")
        print(f"  startTime field: {first_span.get('startTime', 'NOT FOUND')}")
        print(f"  endTime field: {first_span.get('endTime', 'NOT FOUND')}")
        print(f"  startTimeUnixNano field: {first_span.get('startTimeUnixNano', 'NOT FOUND')}")
        print(f"  endTimeUnixNano field: {first_span.get('endTimeUnixNano', 'NOT FOUND')}")
        print(f"  HAS_TIMING_DATA: {has_timing_data}")
        if 'attributes' in first_span:
            attrs = first_span['attributes']
            print(f"  Sample attributes: {list(attrs.keys())[:5] if isinstance(attrs, dict) else 'N/A'}")
            if isinstance(attrs, dict):
                # Check for cost fields
                cost_fields = [k for k in attrs.keys() if 'cost' in k.lower() or 'price' in k.lower()]
                if cost_fields:
                    print(f"  Cost-related fields found: {cost_fields}")

    # Auto-detect timestamp unit based on magnitude
    time_divisor = 1000000  # Default: assume nanoseconds, convert to milliseconds
    if start_times and min_start > 0:
        # If timestamp is > 1e15, it's likely nanoseconds
        # If timestamp is > 1e12, it's likely microseconds
        # If timestamp is > 1e9, it's likely milliseconds
        # If timestamp is < 1e9, it's likely seconds
        if min_start > 1e15:
            time_divisor = 1000000  # nanoseconds to milliseconds
            time_unit = "nanoseconds"
        elif min_start > 1e12:
            time_divisor = 1000  # microseconds to milliseconds
            time_unit = "microseconds"
        elif min_start > 1e9:
            time_divisor = 1  # already in milliseconds
            time_unit = "milliseconds"
        else:
            time_divisor = 0.001  # seconds to milliseconds
            time_unit = "seconds"
        print(f"[DEBUG] Auto-detected timestamp unit: {time_unit} (min_start={min_start}, divisor={time_divisor})")

    processed_spans = []
    for idx, span in enumerate(spans):
        start_time = get_timestamp(span, 'startTime')
        end_time = get_timestamp(span, 'endTime')

        # Calculate relative start
        relative_start = (start_time - min_start) / time_divisor if has_timing_data else 0

        # Calculate duration - prefer duration_ms if available
        if 'duration_ms' in span and span['duration_ms'] is not None:
            actual_duration = float(span['duration_ms'])
        else:
            actual_duration = (end_time - start_time) / time_divisor

        # Debug: Print first few durations
        if idx < 3:
            duration_source = 'duration_ms' if 'duration_ms' in span else 'calculated'
            print(f"[DEBUG] Span {idx}: start={start_time}, end={end_time}, duration={actual_duration:.3f}ms ({duration_source})")

        # Handle span ID variations
        span_id = span.get('spanId') or span.get('span_id') or span.get('spanID') or f'span_{idx}'
        parent_id = span.get('parentSpanId') or span.get('parent_span_id') or span.get('parentSpanID')

        # Get span kind - check both top-level and OpenInference attributes
        span_kind = span.get('kind', 'INTERNAL')
        attributes = span.get('attributes', {})

        # Check for OpenInference span kind in attributes
        if isinstance(attributes, dict) and 'openinference.span.kind' in attributes:
            openinference_kind = attributes.get('openinference.span.kind')
            # Map OpenInference kinds to OpenTelemetry kinds for consistency
            # OpenInference kinds: CHAIN, TOOL, LLM, RETRIEVER, EMBEDDING, AGENT, etc.
            if openinference_kind:
                span_kind = openinference_kind.upper()

        # Extract token and cost information from attributes
        token_info = {}
        cost_info = {}
        if isinstance(attributes, dict):
            # Helper to safely extract numeric values
            def safe_numeric(value):
                """Safely convert to numeric, return None if invalid"""
                if value is None:
                    return None
                try:
                    if isinstance(value, (int, float)):
                        return value
                    return float(value)
                except (ValueError, TypeError):
                    return None

            # Check for token usage (various formats)
            prompt_tokens = None
            completion_tokens = None

            if 'gen_ai.usage.prompt_tokens' in attributes:
                prompt_tokens = safe_numeric(attributes['gen_ai.usage.prompt_tokens'])
            if 'gen_ai.usage.completion_tokens' in attributes:
                completion_tokens = safe_numeric(attributes['gen_ai.usage.completion_tokens'])
            if 'llm.token_count.prompt' in attributes and prompt_tokens is None:
                prompt_tokens = safe_numeric(attributes['llm.token_count.prompt'])
            if 'llm.token_count.completion' in attributes and completion_tokens is None:
                completion_tokens = safe_numeric(attributes['llm.token_count.completion'])

            # Store valid token counts
            if prompt_tokens is not None:
                token_info['prompt_tokens'] = int(prompt_tokens)
            if completion_tokens is not None:
                token_info['completion_tokens'] = int(completion_tokens)

            # Calculate total tokens
            if 'prompt_tokens' in token_info and 'completion_tokens' in token_info:
                token_info['total_tokens'] = token_info['prompt_tokens'] + token_info['completion_tokens']
            elif 'llm.usage.total_tokens' in attributes:
                total = safe_numeric(attributes['llm.usage.total_tokens'])
                if total is not None:
                    token_info['total_tokens'] = int(total)

            # Check for cost information (various formats)
            if 'gen_ai.usage.cost.total' in attributes:
                cost = safe_numeric(attributes['gen_ai.usage.cost.total'])
                if cost is not None:
                    cost_info['total_cost'] = cost
            elif 'llm.usage.cost' in attributes:
                cost = safe_numeric(attributes['llm.usage.cost'])
                if cost is not None:
                    cost_info['total_cost'] = cost

            # Debug: Print cost info for LLM spans
            if idx < 2 and span_kind == 'LLM':
                print(f"[DEBUG] LLM Span {idx} cost extraction:")
                print(f"  gen_ai.usage.cost.total: {attributes.get('gen_ai.usage.cost.total', 'NOT FOUND')}")
                print(f"  llm.usage.cost: {attributes.get('llm.usage.cost', 'NOT FOUND')}")
                print(f"  cost_info: {cost_info}")

        # Store actual duration for tooltip, use minimum for visualization
        display_duration = max(actual_duration, 0.1)  # Minimum width for visibility

        processed_spans.append({
            'span_id': span_id,
            'parent_id': parent_id,
            'name': span.get('name', 'Unknown'),
            'kind': span_kind,
            'start_time': relative_start,
            'duration': display_duration,  # For bar width
            'actual_duration': actual_duration,  # For tooltip
            'end_time': relative_start + actual_duration,  # Use actual for end time
            'attributes': attributes,
            'status': span.get('status', {}).get('code', 'UNKNOWN'),
            'tokens': token_info,
            'cost': cost_info
        })

    print(f"[DEBUG] Total spans in input: {len(spans)}")
    print(f"[DEBUG] Processed spans: {len(processed_spans)}")

    # Debug: Show span kinds and statuses detected
    span_kinds = {}
    span_statuses = {}
    durations = []
    spans_with_tokens = 0
    spans_with_cost = 0
    for span in processed_spans:
        kind = span['kind']
        status = span['status']
        span_kinds[kind] = span_kinds.get(kind, 0) + 1
        span_statuses[status] = span_statuses.get(status, 0) + 1
        durations.append(span['actual_duration'])
        if span['tokens']:
            spans_with_tokens += 1
        if span['cost']:
            spans_with_cost += 1

    print(f"[DEBUG] Span kinds detected: {span_kinds}")
    print(f"[DEBUG] Span statuses detected: {span_statuses}")
    if durations:
        print(f"[DEBUG] Duration range: {min(durations):.3f}ms - {max(durations):.3f}ms")
    print(f"[DEBUG] Spans with token info: {spans_with_tokens}/{len(processed_spans)}")
    print(f"[DEBUG] Spans with cost info: {spans_with_cost}/{len(processed_spans)}")

    return processed_spans


def create_span_visualization(spans: List[Dict[str, Any]], trace_id: str = "Unknown") -> go.Figure:
    """Create an interactive Plotly waterfall visualization of spans"""
    processed_spans = process_trace_data(spans)

    print(f"[DEBUG] create_span_visualization - Received {len(spans)} spans")
    print(f"[DEBUG] create_span_visualization - Processed {len(processed_spans)} spans")

    if not processed_spans:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No spans to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Sort spans by start time for better visualization
    processed_spans.sort(key=lambda x: x['start_time'])

    # Create unique labels for each span (include index to ensure uniqueness)
    for idx, span in enumerate(processed_spans):
        # Add span index to make labels unique
        span['display_name'] = f"{span['name']} [{idx}]"

    # Create colors based on span status and kind
    colors = []
    color_map = {}  # Track which colors are assigned to which kinds
    for span in processed_spans:
        status = span['status']
        kind = span['kind']

        # Only show red for actual errors (ERROR status)
        if status == 'ERROR':
            color = '#DC143C'  # Crimson for errors
        else:
            # Color by span kind (supports both OpenTelemetry and OpenInference)
            if kind == 'SERVER':
                color = '#2E8B57'  # Sea Green
            elif kind == 'CLIENT':
                color = '#4169E1'  # Royal Blue
            elif kind == 'LLM':
                color = '#9B59B6'  # Purple for LLM calls
            elif kind == 'TOOL':
                color = '#E67E22'  # Orange for Tool calls
            elif kind == 'CHAIN':
                color = '#3498DB'  # Light Blue for Chains
            elif kind == 'AGENT':
                color = '#1ABC9C'  # Turquoise for Agents
            elif kind == 'RETRIEVER':
                color = '#F39C12'  # Yellow-Orange for Retrievers
            elif kind == 'EMBEDDING':
                color = '#8E44AD'  # Dark Purple for Embeddings
            else:
                color = '#4682B4'  # Steel Blue for INTERNAL/unknown

        colors.append(color)
        if kind not in color_map:
            color_map[kind] = color

    print(f"[DEBUG] Color assignments: {color_map}")

    # Create the waterfall chart
    fig = go.Figure()

    # Prepare custom data for hover tooltips
    customdata = []
    for span in processed_spans:
        # Build token info string
        token_str = ""
        if span['tokens']:
            tokens = span['tokens']
            if 'total_tokens' in tokens:
                token_str = f"<br>Tokens: {tokens['total_tokens']}"
                if 'prompt_tokens' in tokens and 'completion_tokens' in tokens:
                    token_str += f" (prompt: {tokens['prompt_tokens']}, completion: {tokens['completion_tokens']})"
            elif 'prompt_tokens' in tokens or 'completion_tokens' in tokens:
                parts = []
                if 'prompt_tokens' in tokens:
                    parts.append(f"prompt: {tokens['prompt_tokens']}")
                if 'completion_tokens' in tokens:
                    parts.append(f"completion: {tokens['completion_tokens']}")
                token_str = f"<br>Tokens: {', '.join(parts)}"

        # Build cost info string
        cost_str = ""
        if span['cost'] and 'total_cost' in span['cost']:
            cost_str = f"<br>Cost: ${span['cost']['total_cost']:.6f}"

        customdata.append([
            span['name'],
            span['kind'],
            span['span_id'],
            span['end_time'],
            span['actual_duration'],  # Show actual duration, not display duration
            token_str,
            cost_str
        ])

    # Add bars for each span (use display_name for unique y-axis labels)
    fig.add_trace(go.Bar(
        y=[span['display_name'] for span in processed_spans],
        x=[span['duration'] for span in processed_spans],  # Display duration (min 0.1ms)
        base=[span['start_time'] for span in processed_spans],
        orientation='h',
        marker_color=colors,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>" +
            "Type: %{customdata[1]}<br>" +
            "Span ID: %{customdata[2]}<br>" +
            "Duration: %{customdata[4]:.3f} ms<br>" +  # Actual duration with 3 decimal places
            "Start: %{base:.2f} ms<br>" +
            "End: %{customdata[3]:.2f} ms" +
            "%{customdata[5]}" +  # Token info (already formatted)
            "%{customdata[6]}" +  # Cost info (already formatted)
            "<extra></extra>"
        ),
        customdata=customdata,
        name="Spans"
    ))

    # Update layout for better visualization
    fig.update_layout(
        title={
            'text': f"OpenTelemetry Trace: {trace_id}",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Time (milliseconds)",
        yaxis_title="Spans",
        showlegend=False,
        height=400 + len(processed_spans) * 30,  # Dynamic height based on span count
        bargap=0.2,
        hovermode='closest'
    )

    return fig


def create_span_table(spans: List[Dict[str, Any]]) -> gr.JSON:
    """Create detailed span information display"""

    # Ensure spans is a list
    if hasattr(spans, 'tolist'):
        spans = spans.tolist()
    elif not isinstance(spans, list):
        spans = list(spans) if spans is not None else []

    # Helper function to get timestamp (same as in process_trace_data)
    def get_timestamp(span, field_name):
        variations = [
            field_name,
            field_name.lower(),
            field_name.replace('Time', 'TimeUnixNano'),
            field_name[0].lower() + field_name[1:],
        ]
        for var in variations:
            if var in span:
                value = span[var]
                if isinstance(value, str):
                    return int(value)
                return value
        return 0

    # Simplify span data for display
    simplified_spans = []
    for span in spans:
        start_time = get_timestamp(span, 'startTime')
        end_time = get_timestamp(span, 'endTime')
        duration_ms = (end_time - start_time) / 1000000 if (end_time and start_time) else 0

        # Handle span ID variations
        span_id = span.get('spanId') or span.get('span_id') or span.get('spanID') or 'N/A'
        parent_id = span.get('parentSpanId') or span.get('parent_span_id') or span.get('parentSpanID') or 'root'

        simplified_spans.append({
            "Span ID": span_id,
            "Parent": parent_id,
            "Name": span.get('name', 'N/A'),
            "Kind": span.get('kind', 'N/A'),
            "Duration (ms)": round(duration_ms, 2),
            "Attributes": span.get('attributes', {}),
            "Status": span.get('status', {}).get('code', 'UNKNOWN')
        })

    return gr.JSON(value=simplified_spans, label="Span Details")


# GPU Metrics Visualization Functions

def extract_metrics_data(metrics_df):
    """
    Extract and prepare GPU metrics data for visualization

    Args:
        metrics_df: DataFrame with flat metrics structure (from HuggingFace dataset)
                   Expected columns: timestamp, gpu_utilization_percent, gpu_memory_used_mib,
                                   gpu_temperature_celsius, gpu_power_watts, co2_emissions_gco2e

    Returns:
        DataFrame ready for visualization
    """
    if metrics_df is None or metrics_df.empty:
        return pd.DataFrame()

    # Make a copy to avoid modifying original
    df = metrics_df.copy()

    # Ensure timestamp is datetime
    if 'timestamp' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)

    return df


def create_gpu_summary_cards(df):
    """
    Create summary cards for GPU metrics

    Args:
        df: DataFrame with flat metrics structure (columns: gpu_utilization_percent, etc.)

    Returns:
        HTML string with summary cards
    """
    if df is None or df.empty:
        return "<div style='padding: 20px; text-align: center;'>⚠️ No GPU metrics available (expected for API models)</div>"

    # Debug: Print DataFrame info
    print(f"[DEBUG create_gpu_summary_cards] DataFrame shape: {df.shape}")
    print(f"[DEBUG create_gpu_summary_cards] DataFrame columns: {list(df.columns)}")
    if not df.empty:
        print(f"[DEBUG create_gpu_summary_cards] First row sample: {df.iloc[0].to_dict()}")
        print(f"[DEBUG create_gpu_summary_cards] Last row sample: {df.iloc[-1].to_dict()}")

    # Use aggregate statistics (average/max) instead of just last row
    # This is more representative of overall GPU performance
    utilization = df['gpu_utilization_percent'].mean() if 'gpu_utilization_percent' in df.columns else 0
    memory_used = df['gpu_memory_used_mib'].max() if 'gpu_memory_used_mib' in df.columns else 0
    temperature = df['gpu_temperature_celsius'].max() if 'gpu_temperature_celsius' in df.columns else 0

    # CO2 emissions is a cumulative counter - calculate delta (final - initial)
    if 'co2_emissions_gco2e' in df.columns and not df.empty:
        co2_emissions = df['co2_emissions_gco2e'].iloc[-1] - df['co2_emissions_gco2e'].iloc[0]
    else:
        co2_emissions = 0

    power = df['gpu_power_watts'].mean() if 'gpu_power_watts' in df.columns else 0

    # Get GPU name from first row (it's constant across all rows)
    gpu_name = df['gpu_name'].iloc[0] if 'gpu_name' in df.columns and not df.empty else 'Unknown GPU'

    print(f"[DEBUG create_gpu_summary_cards] Aggregated values - util: {utilization:.2f}, mem: {memory_used:.2f}, temp: {temperature:.2f}, co2: {co2_emissions:.4f}, gpu_name: {gpu_name}")

    # Get memory total from max value if available
    memory_total = df['gpu_memory_total_mib'].max() if 'gpu_memory_total_mib' in df.columns else 0
    memory_percent = (memory_used / memory_total * 100) if memory_total > 0 else 0

    cards_html = f"""
    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin: 20px 0;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
            <h3 style="margin: 0 0 10px 0; font-size: 1em;">GPU Name</h3>
            <h2 style="margin: 0; font-size: 1.2em;">{gpu_name}</h2>
        </div>
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
            <h3 style="margin: 0 0 10px 0; font-size: 1em;">GPU Utilization</h3>
            <h2 style="margin: 0; font-size: 2em;">{utilization:.1f}%</h2>
        </div>
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
            <h3 style="margin: 0 0 10px 0; font-size: 1em;">GPU Memory</h3>
            <h2 style="margin: 0; font-size: 2em;">{memory_used:.0f} MiB</h2>
            <p style="margin: 5px 0 0 0; font-size: 0.8em; opacity: 0.9;">{memory_percent:.1f}% of {memory_total:.0f} MiB</p>
        </div>
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
            <h3 style="margin: 0 0 10px 0; font-size: 1em;">GPU Temperature</h3>
            <h2 style="margin: 0; font-size: 2em;">{temperature:.0f}°C</h2>
        </div>
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
            <h3 style="margin: 0 0 10px 0; font-size: 1em;">CO2 Emissions</h3>
            <h2 style="margin: 0; font-size: 2em;">{co2_emissions:.4f} g</h2>
            <p style="margin: 5px 0 0 0; font-size: 0.8em; opacity: 0.9;">Power: {power:.1f} W</p>
        </div>
    </div>
    """

    return cards_html


def create_gpu_metrics_dashboard(metrics_df):
    """
    Create a combined dashboard with GPU metric charts

    Args:
        metrics_df: DataFrame with flat metrics structure (from HuggingFace dataset)

    Returns:
        Plotly figure with GPU metrics time series
    """
    if metrics_df is None or metrics_df.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No GPU metrics available (expected for API models)",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16)
        )
        return fig

    # Prepare data
    df = extract_metrics_data(metrics_df)

    if df.empty:
        return None

    # Create subplots for GPU metrics
    # We'll show: Utilization, Memory, Temperature, Power, CO2, Power Cost
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            'GPU Utilization (%)',
            'GPU Memory (MiB)',
            'GPU Temperature (°C)',
            'GPU Power (W)',
            'CO2 Emissions (g)',
            'Power Cost (USD)'
        ],
        vertical_spacing=0.10,
        horizontal_spacing=0.12,
        specs=[[{}, {}], [{}, {}], [{}, {}]]
    )

    colors = ['#667eea', '#f093fb', '#4facfe', '#FFE66D', '#43e97b', '#FF6B6B']

    # Define metrics to plot
    metrics_config = [
        ('gpu_utilization_percent', 'GPU Utilization (%)', 1, 1, colors[0]),
        ('gpu_memory_used_mib', 'GPU Memory (MiB)', 1, 2, colors[1]),
        ('gpu_temperature_celsius', 'GPU Temperature (°C)', 2, 1, colors[2]),
        ('gpu_power_watts', 'GPU Power (W)', 2, 2, colors[3]),
        ('co2_emissions_gco2e', 'CO2 Emissions (g)', 3, 1, colors[4]),
        ('power_cost_usd', 'Power Cost (USD)', 3, 2, colors[5]),
    ]

    for col_name, title, row, col, color in metrics_config:
        if col_name in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df[col_name],
                    mode='lines+markers',
                    name=title,
                    line=dict(color=color, width=3),
                    marker=dict(size=6, color=color),
                    hovertemplate=(
                        f"<b>{title}</b><br>" +
                        "Time: %{x}<br>" +
                        "Value: %{y:.2f}<br>" +
                        "<extra></extra>"
                    )
                ),
                row=row, col=col
            )

    # Add memory total as a dashed line if available
    if 'gpu_memory_total_mib' in df.columns:
        total_memory = df['gpu_memory_total_mib'].iloc[0]
        fig.add_hline(
            y=total_memory,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Total: {total_memory:.0f} MiB",
            annotation_position="right",
            row=1, col=2
        )

    fig.update_layout(
        title_text="GPU Metrics Over Time",
        height=900,
        template="plotly_white",
        showlegend=False,
        hovermode='x unified'
    )

    # Update x-axes to show time format
    fig.update_xaxes(tickformat='%H:%M:%S')

    return fig
