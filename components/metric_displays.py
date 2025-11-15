"""
Metric Display Components
Reusable HTML generators for badges, progress bars, and visual metrics
"""

def get_rank_badge(rank: int) -> str:
    """
    Generate HTML for rank badge with medal styling for top 3

    Args:
        rank: Position in leaderboard (1-indexed)

    Returns:
        HTML string for rank badge

    Examples:
        >>> get_rank_badge(1)
        '<span ...>🥇 1st</span>'
    """
    badge_styles = {
        1: ("🥇 1st", "linear-gradient(145deg, #ffd700, #ffc400)", "#000", "0 2px 8px rgba(255, 215, 0, 0.4)"),
        2: ("🥈 2nd", "linear-gradient(145deg, #9ca3af, #787C7E)", "#fff", "0 2px 8px rgba(156, 163, 175, 0.4)"),
        3: ("🥉 3rd", "linear-gradient(145deg, #CD7F32, #b36a1d)", "#fff", "0 2px 8px rgba(205, 127, 50, 0.4)"),
    }

    if rank in badge_styles:
        label, gradient, text_color, shadow = badge_styles[rank]
        return f"""
            <span style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 60px;
                padding: 6px 12px;
                background: {gradient};
                color: {text_color};
                border-radius: 8px;
                font-weight: 700;
                font-size: 0.9em;
                box-shadow: {shadow};
                letter-spacing: 0.5px;
            ">
                {label}
            </span>
        """
    else:
        return f"""
            <span style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 32px;
                color: var(--tm-text-muted, #64748B);
                font-weight: 500;
                font-size: 0.95em;
            ">
                {rank}
            </span>
        """


def get_success_rate_bar(success_rate: float) -> str:
    """
    Generate HTML for success rate progress bar with color gradient

    Args:
        success_rate: Success percentage (0-100)

    Returns:
        HTML string with progress bar and numeric value

    Color Logic:
        - < 50%: Red → Orange (danger)
        - 50-79%: Orange → Yellow (warning)
        - 80-100%: Green → Cyan (success)
    """
    width = min(max(success_rate, 0), 100)  # Clamp to 0-100

    # Dynamic gradient based on performance
    if success_rate < 50:
        gradient = "linear-gradient(90deg, #EF4444, #F59E0B)"  # Red → Orange
        bar_color = "#EF4444"
    elif success_rate < 80:
        gradient = "linear-gradient(90deg, #F59E0B, #FBBF24)"  # Orange → Yellow
        bar_color = "#F59E0B"
    else:
        gradient = "linear-gradient(90deg, #10B981, #06B6D4)"  # Green → Cyan
        bar_color = "#10B981"

    return f"""
    <div style="display: flex; align-items: center; gap: 10px; width: 100%;">
        <div style="
            flex: 1;
            height: 8px;
            background: rgba(148, 163, 184, 0.15);
            border-radius: 4px;
            overflow: hidden;
            max-width: 160px;
            position: relative;
        ">
            <div style="
                width: {width}%;
                height: 100%;
                background: {gradient};
                border-radius: 4px;
                transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 0 8px {bar_color}40;
            "></div>
        </div>
        <span style="
            font-family: 'Monaco', 'Menlo', monospace;
            font-weight: 600;
            color: var(--tm-text-primary, #000000);
            min-width: 55px;
            font-size: 0.9em;
        ">{success_rate:.1f}%</span>
    </div>
    """


def get_gpu_utilization_bar(utilization: float) -> str:
    """
    Generate HTML for GPU utilization progress bar

    Args:
        utilization: GPU utilization percentage (0-100)

    Returns:
        HTML string with progress bar

    Color Logic:
        - < 30%: Low utilization (yellow/amber)
        - 30-70%: Medium utilization (orange)
        - > 70%: High utilization (red/orange) - good efficiency!
    """
    width = min(max(utilization, 0), 100)

    # Higher GPU utilization = better efficiency
    if utilization < 30:
        gradient = "linear-gradient(90deg, #FBBF24, #F59E0B)"  # Yellow → Amber
    elif utilization < 70:
        gradient = "linear-gradient(90deg, #F59E0B, #FB923C)"  # Amber → Orange
    else:
        gradient = "linear-gradient(90deg, #FB923C, #F97316)"  # Orange → Deep Orange

    return f"""
    <div style="display: flex; align-items: center; gap: 8px;">
        <div style="
            flex: 1;
            height: 6px;
            background: rgba(148, 163, 184, 0.15);
            border-radius: 3px;
            max-width: 100px;
        ">
            <div style="
                width: {width}%;
                height: 100%;
                background: {gradient};
                border-radius: 3px;
                transition: width 0.4s ease;
            "></div>
        </div>
        <span style="
            font-family: monospace;
            font-size: 0.85em;
            color: var(--tm-text-secondary, #000000);
            min-width: 45px;
        ">{utilization:.1f}%</span>
    </div>
    """


def get_provider_badge(provider: str) -> str:
    """
    Generate HTML for provider type badge

    Args:
        provider: Provider name (litellm, transformers, etc.)

    Returns:
        HTML string for colored badge

    Colors:
        - litellm: Blue (API providers)
        - transformers: Green (GPU/local models)
    """
    provider_colors = {
        "litellm": "#3B82F6",      # Blue - API providers
        "transformers": "#10B981",  # Green - GPU/local
        "openai": "#10A37F",       # OpenAI green
        "anthropic": "#D97757",    # Anthropic orange
    }

    bg_color = provider_colors.get(provider.lower(), "#6B7280")  # Default gray

    return f"""
    <span style="
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        background: {bg_color};
        color: white;
        border-radius: 5px;
        font-size: 0.75em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    ">
        {provider.upper()}
    </span>
    """


def get_agent_type_badge(agent_type: str) -> str:
    """
    Generate HTML for agent type badge

    Args:
        agent_type: Agent type (tool, code, both)

    Returns:
        HTML string for colored badge

    Colors:
        - tool: Purple
        - code: Amber/Orange
        - both: Cyan
    """
    type_colors = {
        "tool": "#8B5CF6",   # Purple
        "code": "#F59E0B",   # Amber
        "both": "#06B6D4",   # Cyan
    }

    bg_color = type_colors.get(agent_type.lower(), "#6B7280")

    return f"""
    <span style="
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        background: {bg_color};
        color: white;
        border-radius: 5px;
        font-size: 0.75em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    ">
        {agent_type.upper()}
    </span>
    """


def get_hardware_badge(has_gpu: bool) -> str:
    """
    Generate HTML for hardware type badge

    Args:
        has_gpu: Whether job used GPU

    Returns:
        HTML string for badge
    """
    if has_gpu:
        return """
        <span style="
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            background: linear-gradient(135deg, #F59E0B, #EF4444);
            color: white;
            border-radius: 5px;
            font-size: 0.75em;
            font-weight: 600;
            letter-spacing: 0.5px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        ">
            🖥️ GPU
        </span>
        """
    else:
        return """
        <span style="
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            background: #6B7280;
            color: white;
            border-radius: 5px;
            font-size: 0.75em;
            font-weight: 600;
            letter-spacing: 0.5px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        ">
            💻 CPU
        </span>
        """


def format_cost(cost_usd: float) -> str:
    """
    Format cost with color coding

    Args:
        cost_usd: Cost in USD

    Returns:
        HTML string with formatted cost
    """
    # Color code by cost magnitude
    if cost_usd < 0.01:
        color = "#10B981"  # Green - very cheap
    elif cost_usd < 0.05:
        color = "#F59E0B"  # Amber - moderate
    else:
        color = "#EF4444"  # Red - expensive

    return f"""
    <span style="
        font-family: monospace;
        font-weight: 600;
        color: {color};
        font-size: 0.9em;
    ">
        ${cost_usd:.4f}
    </span>
    """


def format_duration(duration_ms: float) -> str:
    """
    Format duration with appropriate units

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        HTML string with formatted duration
    """
    if duration_ms < 1000:
        value = duration_ms
        unit = "ms"
        color = "#10B981"  # Green - fast
    elif duration_ms < 10000:
        value = duration_ms / 1000
        unit = "s"
        color = "#F59E0B"  # Amber - moderate
    else:
        value = duration_ms / 1000
        unit = "s"
        color = "#EF4444"  # Red - slow

    return f"""
    <span style="
        font-family: monospace;
        color: {color};
        font-weight: 500;
        font-size: 0.9em;
    ">
        {value:.1f}{unit}
    </span>
    """


def get_tooltip_icon(tooltip_text: str) -> str:
    """
    Generate info icon with tooltip

    Args:
        tooltip_text: Text to show in tooltip

    Returns:
        HTML string for icon with tooltip
    """
    return f"""
    <span title="{tooltip_text}" style="
        color: var(--tm-secondary, #06B6D4);
        cursor: help;
        font-size: 0.9em;
        margin-left: 4px;
    ">ⓘ</span>
    """
