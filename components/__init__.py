"""
Components package for TraceMind UI
Contains reusable visual components
"""

from .metric_displays import (
    get_rank_badge,
    get_success_rate_bar,
    get_gpu_utilization_bar,
    get_provider_badge,
    get_agent_type_badge,
    get_hardware_badge,
    format_cost,
    format_duration,
    get_tooltip_icon
)

from .leaderboard_table import (
    generate_leaderboard_html,
    generate_empty_state_html,
    generate_filter_summary_html
)

from .analytics_charts import (
    create_trends_plot,
    create_performance_heatmap,
    create_speed_accuracy_scatter,
    create_cost_efficiency_scatter,
    create_comparison_radar
)

# Additional components (to be added)
# from .thought_graph import create_thought_graph
# from .report_cards import (
#     generate_leaderboard_summary_card,
#     generate_run_report_card,
#     download_card_as_png_js
# )

__all__ = [
    'get_rank_badge',
    'get_success_rate_bar',
    'get_gpu_utilization_bar',
    'get_provider_badge',
    'get_agent_type_badge',
    'get_hardware_badge',
    'format_cost',
    'format_duration',
    'get_tooltip_icon',
    'generate_leaderboard_html',
    'generate_empty_state_html',
    'generate_filter_summary_html',
    'create_trends_plot',
    'create_performance_heatmap',
    'create_speed_accuracy_scatter',
    'create_cost_efficiency_scatter',
    'create_comparison_radar',
]
