"""
Leaderboard Screen for TraceMind-AI
Displays evaluation runs with MCP-powered insights
"""

import pandas as pd
import gradio as gr
from typing import Optional, Tuple


def prepare_leaderboard_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare leaderboard dataframe for display

    Args:
        df: Raw leaderboard dataframe from HuggingFace

    Returns:
        Formatted dataframe for display
    """
    if df.empty:
        return pd.DataFrame()

    # Select and reorder columns for display
    display_columns = [
        'model', 'agent_type', 'provider', 'success_rate',
        'total_tests', 'avg_duration_ms', 'total_cost_usd',
        'co2_emissions_g', 'gpu_utilization_avg', 'submitted_by', 'timestamp'
    ]

    # Only include columns that exist
    available_columns = [col for col in display_columns if col in df.columns]
    display_df = df[available_columns].copy()

    # Round numeric columns
    if 'success_rate' in display_df.columns:
        display_df['success_rate'] = display_df['success_rate'].round(1)
    if 'avg_duration_ms' in display_df.columns:
        display_df['avg_duration_ms'] = display_df['avg_duration_ms'].round(0)
    if 'total_cost_usd' in display_df.columns:
        display_df['total_cost_usd'] = display_df['total_cost_usd'].round(4)
    if 'co2_emissions_g' in display_df.columns:
        display_df['co2_emissions_g'] = display_df['co2_emissions_g'].round(2)
    if 'gpu_utilization_avg' in display_df.columns:
        display_df['gpu_utilization_avg'] = display_df['gpu_utilization_avg'].round(1)

    # Sort by success rate descending by default
    if 'success_rate' in display_df.columns:
        display_df = display_df.sort_values('success_rate', ascending=False)

    return display_df


def get_run_id_from_selection(
    df: pd.DataFrame,
    evt: gr.SelectData
) -> Optional[str]:
    """
    Extract run_id from a selected row in the dataframe

    Args:
        df: Full leaderboard dataframe (with run_id column)
        evt: Gradio SelectData event from dataframe click

    Returns:
        run_id string or None
    """
    if df.empty or evt is None:
        return None

    try:
        row_index = evt.index[0]  # evt.index is (row, col)
        if row_index < len(df):
            return df.iloc[row_index]['run_id']
    except (IndexError, KeyError, AttributeError):
        return None

    return None
