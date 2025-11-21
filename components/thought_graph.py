"""
Thought Graph Visualization Component
Visualizes agent reasoning flow as an interactive network graph
"""

import plotly.graph_objects as go
import networkx as nx
from typing import List, Dict, Any, Tuple
import colorsys


def create_thought_graph(spans: List[Dict[str, Any]], trace_id: str = "Unknown") -> go.Figure:
    """
    Create an interactive thought graph showing agent reasoning flow

    This is different from the waterfall chart - it shows the logical flow
    of the agent's thinking process (LLM calls, Tool calls, etc.) as a
    directed graph rather than a timeline.

    Args:
        spans: List of OpenTelemetry span dictionaries
        trace_id: Trace identifier

    Returns:
        Plotly figure with interactive network graph
    """

    # Ensure spans is a list
    if hasattr(spans, 'tolist'):
        spans = spans.tolist()
    elif not isinstance(spans, list):
        spans = list(spans) if spans is not None else []

    if not spans:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No reasoning steps to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Build graph from spans
    G = nx.DiGraph()

    # First pass: Add all nodes and build span_map
    span_map = {}
    for span in spans:
        span_id = span.get('spanId') or span.get('span_id') or span.get('spanID')
        if not span_id:
            continue

        # Get span details
        name = span.get('name', 'Unknown')
        kind = span.get('kind', 'INTERNAL')
        attributes = span.get('attributes', {})

        # Check for OpenInference span kind
        if isinstance(attributes, dict) and 'openinference.span.kind' in attributes:
            openinference_kind = attributes.get('openinference.span.kind', kind)
            if openinference_kind:  # Only call .upper() if not None
                kind = openinference_kind.upper()

        # Extract metadata for node
        node_data = {
            'span_id': span_id,
            'name': name,
            'kind': kind,
            'attributes': attributes,
            'status': span.get('status', {}).get('code', 'OK')
        }

        # Add token and cost info if available
        if isinstance(attributes, dict):
            # Token info
            if 'gen_ai.usage.prompt_tokens' in attributes:
                node_data['prompt_tokens'] = attributes['gen_ai.usage.prompt_tokens']
            if 'gen_ai.usage.completion_tokens' in attributes:
                node_data['completion_tokens'] = attributes['gen_ai.usage.completion_tokens']

            # Cost info
            if 'gen_ai.usage.cost.total' in attributes:
                node_data['cost'] = attributes['gen_ai.usage.cost.total']
            elif 'llm.usage.cost' in attributes:
                node_data['cost'] = attributes['llm.usage.cost']

            # Model info
            if 'gen_ai.request.model' in attributes:
                node_data['model'] = attributes['gen_ai.request.model']
            elif 'llm.model' in attributes:
                node_data['model'] = attributes['llm.model']

            # Tool info
            if 'tool.name' in attributes:
                node_data['tool_name'] = attributes['tool.name']

        # Add node to graph
        G.add_node(span_id, **node_data)
        span_map[span_id] = span

    # Second pass: Add all edges (now all nodes exist in span_map)
    for span in spans:
        span_id = span.get('spanId') or span.get('span_id') or span.get('spanID')
        if not span_id:
            continue

        parent_id = span.get('parentSpanId') or span.get('parent_span_id') or span.get('parentSpanID')
        if parent_id and parent_id in span_map:
            G.add_edge(parent_id, span_id)
            print(f"[DEBUG] Added edge: {parent_id} → {span_id}")

    print(f"[DEBUG] Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    if G.number_of_nodes() == 0:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No valid spans to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Calculate layout using hierarchical layout
    try:
        # Try to use hierarchical layout (for DAGs)
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        # If graph is a DAG, use hierarchical layout
        if nx.is_directed_acyclic_graph(G):
            # Get levels using longest_path_length
            levels = {}
            for node in G.nodes():
                # Find longest path from any root to this node
                try:
                    # Get all paths from roots to this node
                    roots = [n for n in G.nodes() if G.in_degree(n) == 0]
                    max_depth = 0
                    for root in roots:
                        if nx.has_path(G, root, node):
                            paths = list(nx.all_simple_paths(G, root, node))
                            max_depth = max(max_depth, max(len(p) for p in paths) if paths else 0)
                    levels[node] = max_depth
                except:
                    levels[node] = 0

            # Create hierarchical layout
            pos = create_hierarchical_layout(G, levels)
    except Exception as e:
        print(f"[DEBUG] Layout calculation error: {e}")
        # Fallback to circular layout
        pos = nx.circular_layout(G)

    # Extract node positions
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_sizes = []
    hover_text = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        # Get node data
        node_data = G.nodes[node]
        name = node_data.get('name', 'Unknown')
        kind = node_data.get('kind', 'INTERNAL')

        # Create label (shortened)
        label = shorten_label(name, max_length=20)
        node_text.append(label)

        # Assign color based on kind
        color = get_node_color(kind, node_data.get('status', 'OK'))
        node_colors.append(color)

        # Size based on importance (LLM and AGENT nodes are larger)
        size = 40 if kind in ['LLM', 'AGENT', 'CHAIN'] else 30
        node_sizes.append(size)

        # Create detailed hover text
        hover = f"<b>{name}</b><br>"
        hover += f"Type: {kind}<br>"
        hover += f"Status: {node_data.get('status', 'OK')}<br>"

        if 'model' in node_data:
            hover += f"Model: {node_data['model']}<br>"
        if 'tool_name' in node_data:
            hover += f"Tool: {node_data['tool_name']}<br>"
        if 'prompt_tokens' in node_data or 'completion_tokens' in node_data:
            # Ensure values are integers, not strings
            prompt = int(node_data.get('prompt_tokens', 0) or 0)  # Handle None values and convert to int
            completion = int(node_data.get('completion_tokens', 0) or 0)  # Handle None values and convert to int
            hover += f"Tokens: {prompt + completion} (p:{prompt}, c:{completion})<br>"
        if 'cost' in node_data and node_data['cost'] is not None:
            cost = float(node_data['cost'])  # Handle string values
            hover += f"Cost: ${cost:.6f}<br>"

        hover_text.append(hover)

    # Extract edges
    edge_x = []
    edge_y = []
    edge_traces = []

    print(f"[DEBUG] Drawing {G.number_of_edges()} edges")
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        print(f"[DEBUG] Edge from ({x0:.2f}, {y0:.2f}) to ({x1:.2f}, {y1:.2f})")

        # Create edge line (make it thicker and darker for visibility)
        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=3, color='#555'),  # Increased width from 2 to 3, darker color
            hoverinfo='none',
            showlegend=False
        )
        edge_traces.append(edge_trace)

        # Add arrow annotation
        edge_traces.append(create_arrow_annotation(x0, y0, x1, y1))

    # Create node trace
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color='white')
        ),
        text=node_text,
        textposition='bottom center',
        textfont=dict(size=10, color='#333'),
        hovertext=hover_text,
        hoverinfo='text',
        showlegend=False
    )

    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])

    # Update layout with better visibility settings
    fig.update_layout(
        title={
            'text': f"🧠 Agent Thought Graph: {trace_id}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        showlegend=False,
        hovermode='closest',
        margin=dict(t=100, b=40, l=40, r=40),
        height=600,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.1, 1.1]  # Add padding to see edges at boundaries
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.1, 1.1]  # Add padding to see edges at boundaries
        ),
        plot_bgcolor='white',  # Pure white background for maximum contrast
        paper_bgcolor='#f8f9fa',  # Light gray paper
        annotations=[
            dict(
                text="💡 Hover over nodes to see details | Arrows show execution flow",
                xref="paper", yref="paper",
                x=0.5, y=-0.05, xanchor='center', yanchor='top',
                showarrow=False,
                font=dict(size=11, color='#666')
            )
        ]
    )

    # Add legend for node types
    legend_items = create_legend_items()
    fig.add_annotation(
        text=legend_items,
        xref="paper", yref="paper",
        x=1.0, y=1.0, xanchor='right', yanchor='top',
        showarrow=False,
        font=dict(size=10),
        align='left',
        bgcolor='white',
        bordercolor='#ccc',
        borderwidth=1,
        borderpad=8
    )

    return fig


def create_hierarchical_layout(G: nx.DiGraph, levels: Dict[str, int]) -> Dict[str, Tuple[float, float]]:
    """Create a hierarchical layout for the graph"""
    pos = {}

    # Group nodes by level
    level_nodes = {}
    for node, level in levels.items():
        if level not in level_nodes:
            level_nodes[level] = []
        level_nodes[level].append(node)

    # Assign positions
    max_level = max(levels.values()) if levels else 0
    for level, nodes in level_nodes.items():
        y = 1.0 - (level / max(max_level, 1))  # Top to bottom
        num_nodes = len(nodes)
        for i, node in enumerate(nodes):
            x = (i + 1) / (num_nodes + 1)  # Spread evenly
            pos[node] = (x, y)

    return pos


def get_node_color(kind: str, status: str) -> str:
    """Get color for node based on kind and status"""

    # Error status overrides kind color
    if status == 'ERROR':
        return '#DC143C'  # Crimson

    # Color by kind
    color_map = {
        'LLM': '#9B59B6',  # Purple
        'AGENT': '#1ABC9C',  # Turquoise
        'CHAIN': '#3498DB',  # Light Blue
        'TOOL': '#E67E22',  # Orange
        'RETRIEVER': '#F39C12',  # Yellow-Orange
        'EMBEDDING': '#8E44AD',  # Dark Purple
        'CLIENT': '#4169E1',  # Royal Blue
        'SERVER': '#2E8B57',  # Sea Green
        'INTERNAL': '#95A5A6',  # Gray
    }

    return color_map.get(kind, '#4682B4')  # Steel Blue default


def shorten_label(text: str, max_length: int = 20) -> str:
    """Shorten label for display"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'


def create_arrow_annotation(x0: float, y0: float, x1: float, y1: float) -> go.Scatter:
    """Create an arrow annotation between two points"""
    # Calculate arrow position (70% along the line, closer to end)
    arrow_x = x0 + 0.7 * (x1 - x0)
    arrow_y = y0 + 0.7 * (y1 - y0)

    # Calculate angle for arrow direction
    import math
    angle = math.atan2(y1 - y0, x1 - x0)

    # Create arrow head (larger and more visible)
    arrow_size = 0.03  # Increased from 0.02
    arrow_dx = arrow_size * math.cos(angle + 2.8)
    arrow_dy = arrow_size * math.sin(angle + 2.8)

    arrow_trace = go.Scatter(
        x=[arrow_x - arrow_dx, arrow_x, arrow_x + arrow_size * math.cos(angle - 2.8)],
        y=[arrow_y - arrow_dy, arrow_y, arrow_y + arrow_size * math.sin(angle - 2.8)],
        mode='lines',
        line=dict(width=2, color='#555'),  # Match edge color
        fill='toself',
        fillcolor='#555',  # Darker fill color
        hoverinfo='none',
        showlegend=False
    )

    return arrow_trace


def create_legend_items() -> str:
    """Create HTML legend for node types"""
    legend = "<b>Node Types:</b><br>"
    legend += "🟣 LLM Call<br>"
    legend += "🟠 Tool Call<br>"
    legend += "🔵 Chain/Agent<br>"
    legend += "⚪ Other<br>"
    legend += "🔴 Error"
    return legend
