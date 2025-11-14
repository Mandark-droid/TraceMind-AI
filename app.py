"""
TraceMind-AI - Agent Evaluation Platform
MCP Client consuming TraceMind-mcp-server for intelligent analysis
"""

import os
import gradio as gr
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Import utilities
from utils.auth import is_authenticated, get_user_info, create_login_button, create_user_info_display, DEV_MODE
from utils.navigation import Navigator, Screen
from data_loader import create_data_loader_from_env
from styles.tracemind_theme import get_tracemind_css
from mcp_client.sync_wrapper import get_sync_mcp_client

# Initialize
data_loader = create_data_loader_from_env()
navigator = Navigator()
mcp_client = get_sync_mcp_client()

# Global state
current_selected_run = None


def load_leaderboard_view(token, profile):
    """Load and display the leaderboard with MCP-powered insights"""
    if not is_authenticated(token, profile):
        return "Please log in to view the leaderboard", ""

    try:
        # Load real data from HuggingFace
        leaderboard_df = data_loader.load_leaderboard()

        if leaderboard_df.empty:
            return "No evaluation runs found in the leaderboard", ""

        # Format dataframe for display
        display_df = leaderboard_df[[
            'model', 'agent_type', 'success_rate', 'total_tests',
            'avg_duration_ms', 'total_cost_usd', 'co2_emissions_g'
        ]].copy()

        # Round numeric columns
        display_df['success_rate'] = display_df['success_rate'].round(1)
        display_df['avg_duration_ms'] = display_df['avg_duration_ms'].round(0)
        display_df['total_cost_usd'] = display_df['total_cost_usd'].round(4)
        display_df['co2_emissions_g'] = display_df['co2_emissions_g'].round(2)

        # Get MCP-powered insights
        try:
            insights = mcp_client.analyze_leaderboard(
                metric_focus="overall",
                time_range="all_time",
                top_n=5,
                hf_token=os.getenv('HF_TOKEN'),
                gemini_api_key=os.getenv('GEMINI_API_KEY')
            )
        except Exception as e:
            insights = f"⚠️ MCP analysis unavailable: {str(e)}\n\n(Server may need initialization)"

        return display_df, insights

    except Exception as e:
        return f"Error loading leaderboard: {e}", ""


def estimate_evaluation_cost(model, agent_type, num_tests):
    """Estimate cost for a new evaluation using MCP server"""
    try:
        cost_estimate = mcp_client.estimate_cost(
            model=model,
            agent_type=agent_type,
            num_tests=int(num_tests),
            hf_token=os.getenv('HF_TOKEN'),
            gemini_api_key=os.getenv('GEMINI_API_KEY')
        )
        return cost_estimate
    except Exception as e:
        return f"❌ Error estimating cost: {str(e)}"


def build_ui():
    """Build the Gradio UI"""

    with gr.Blocks(css=get_tracemind_css(), title="TraceMind-AI") as demo:
        # Header
        gr.Markdown("""
        # 🔍 TraceMind-AI
        ### Agent Evaluation Platform with MCP-Powered Intelligence

        **Powered by:**
        - 📊 Real data from HuggingFace datasets
        - 🤖 MCP Server for AI-powered insights ([TraceMind-mcp-server](https://huggingface.co/spaces/kshitijthakkar/TraceMind-mcp-server))
        - 🧠 Google Gemini 2.5 Flash for analysis
        """)

        # Authentication
        with gr.Row():
            with gr.Column(scale=2):
                user_display = gr.HTML(create_user_info_display(None))
            with gr.Column(scale=1):
                login_btn = create_login_button()

        # Main content (shown when authenticated)
        with gr.Column(visible=DEV_MODE) as main_content:
            with gr.Tabs() as tabs:
                # Tab 1: Leaderboard
                with gr.Tab("📊 Leaderboard"):
                    gr.Markdown("### Agent Evaluation Leaderboard")
                    gr.Markdown("Real-time data from `kshitijthakkar/smoltrace-leaderboard`")

                    load_leaderboard_btn = gr.Button("🔄 Load Leaderboard", variant="primary")

                    with gr.Row():
                        with gr.Column(scale=2):
                            leaderboard_table = gr.Dataframe(
                                headers=["Model", "Agent Type", "Success Rate %", "Total Tests", "Avg Duration (ms)", "Cost ($)", "CO2 (g)"],
                                label="Evaluation Runs",
                                interactive=False
                            )
                        with gr.Column(scale=1):
                            leaderboard_insights = gr.Markdown("**MCP Analysis:**\n\nClick 'Load Leaderboard' to see AI-powered insights")

                # Tab 2: Cost Estimator
                with gr.Tab("💰 Cost Estimator"):
                    gr.Markdown("### Estimate Evaluation Costs")
                    gr.Markdown("Uses MCP server to calculate costs for different models and configurations")

                    with gr.Row():
                        model_input = gr.Textbox(
                            label="Model",
                            placeholder="openai/gpt-4 or meta-llama/Llama-3.1-8B",
                            value="openai/gpt-4"
                        )
                        agent_type_input = gr.Dropdown(
                            ["tool", "code", "both"],
                            label="Agent Type",
                            value="both"
                        )
                        num_tests_input = gr.Number(
                            label="Number of Tests",
                            value=100
                        )

                    estimate_btn = gr.Button("💵 Estimate Cost", variant="primary")
                    cost_output = gr.Markdown("**Cost Estimate:**\n\nEnter details and click 'Estimate Cost'")

                # Tab 3: MCP Server Status
                with gr.Tab("🔧 MCP Status"):
                    gr.Markdown("### TraceMind MCP Server Connection")

                    mcp_url_display = gr.Textbox(
                        label="MCP Server URL",
                        value=os.getenv('MCP_SERVER_URL', 'https://kshitijthakkar-tracemind-mcp-server.hf.space/gradio_api/mcp/'),
                        interactive=False
                    )

                    test_mcp_btn = gr.Button("🧪 Test MCP Connection", variant="secondary")
                    mcp_status = gr.Markdown("**Status:** Not tested yet")

        # Event handlers
        def handle_login(token, profile):
            user = get_user_info(token, profile)
            return create_user_info_display(user), gr.update(visible=True)

        login_btn.click(
            fn=handle_login,
            inputs=[login_btn, login_btn],  # Gradio provides token/profile automatically
            outputs=[user_display, main_content]
        )

        load_leaderboard_btn.click(
            fn=load_leaderboard_view,
            inputs=[login_btn, login_btn],
            outputs=[leaderboard_table, leaderboard_insights]
        )

        estimate_btn.click(
            fn=estimate_evaluation_cost,
            inputs=[model_input, agent_type_input, num_tests_input],
            outputs=[cost_output]
        )

        def test_mcp_connection():
            try:
                mcp_client.initialize()
                return "✅ **Connected Successfully!**\n\nMCP server is online and ready"
            except Exception as e:
                return f"❌ **Connection Failed**\n\nError: {str(e)}"

        test_mcp_btn.click(
            fn=test_mcp_connection,
            outputs=[mcp_status]
        )

    return demo


if __name__ == "__main__":
    print("🚀 Starting TraceMind-AI...")
    print(f"📊 Leaderboard: {os.getenv('LEADERBOARD_REPO', 'kshitijthakkar/smoltrace-leaderboard')}")
    print(f"🤖 MCP Server: {os.getenv('MCP_SERVER_URL', 'https://kshitijthakkar-tracemind-mcp-server.hf.space/gradio_api/mcp/')}")
    print(f"🛠️  Dev Mode: {DEV_MODE}")

    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
