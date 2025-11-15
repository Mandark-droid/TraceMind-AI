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
from mcp_client.sync_wrapper import get_sync_mcp_client
from screens.leaderboard import prepare_leaderboard_data, get_run_id_from_selection

# Initialize
data_loader = create_data_loader_from_env()
navigator = Navigator()
mcp_client = get_sync_mcp_client()

# Global state
current_selected_run = None
leaderboard_df_cache = None  # Cache full leaderboard with run_id column


def load_leaderboard_view():
    """Load and display the leaderboard with MCP-powered insights"""
    global leaderboard_df_cache

    # OAuth disabled for now
    # if not is_authenticated(token, profile):
    #     return "Please log in to view the leaderboard", ""

    try:
        # Load real data from HuggingFace
        leaderboard_df = data_loader.load_leaderboard()

        if leaderboard_df.empty:
            return "No evaluation runs found in the leaderboard", ""

        # Cache the full dataframe (with run_id) for navigation
        leaderboard_df_cache = leaderboard_df.copy()

        # Prepare dataframe for display (formatted, sorted)
        display_df = prepare_leaderboard_data(leaderboard_df)

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

    with gr.Blocks(title="TraceMind-AI") as demo:
        # Header
        gr.Markdown("""
        # 🔍 TraceMind-AI
        ### Agent Evaluation Platform with MCP-Powered Intelligence

        **Powered by:**
        - 📊 Real data from HuggingFace datasets
        - 🤖 MCP Server for AI-powered insights ([TraceMind-mcp-server](https://huggingface.co/spaces/kshitijthakkar/TraceMind-mcp-server))
        - 🧠 Google Gemini 2.5 Flash for analysis
        """)

        # # OAuth Authentication (disabled for now)
        # with gr.Row():
        #     with gr.Column(scale=2):
        #         user_display = gr.HTML(create_user_info_display(None))
        #     with gr.Column(scale=1):
        #         login_btn = create_login_button()

        # Main content (always visible - OAuth disabled)
        with gr.Column(visible=True) as main_content:
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
                        interactive=True,
                        placeholder="Enter MCP server URL"
                    )

                    test_mcp_btn = gr.Button("🧪 Test MCP Connection", variant="secondary")
                    mcp_status = gr.Markdown("**Status:** Not tested yet")

        # Event handlers (OAuth disabled)
        # def handle_login(token, profile):
        #     user = get_user_info(token, profile)
        #     return create_user_info_display(user), gr.update(visible=True)
        #
        # login_btn.click(
        #     fn=handle_login,
        #     inputs=[login_btn, login_btn],  # Gradio provides token/profile automatically
        #     outputs=[user_display, main_content]
        # )

        load_leaderboard_btn.click(
            fn=load_leaderboard_view,
            inputs=[],
            outputs=[leaderboard_table, leaderboard_insights]
        )

        estimate_btn.click(
            fn=estimate_evaluation_cost,
            inputs=[model_input, agent_type_input, num_tests_input],
            outputs=[cost_output]
        )

        def test_mcp_connection(mcp_url):
            """Test MCP server connection"""
            print(f"[DEBUG] Testing connection to: {mcp_url}")

            if not mcp_url or not mcp_url.strip():
                return "❌ **Error**\n\nPlease enter a valid URL"

            try:
                import requests

                print(f"[DEBUG] Making HTTP GET request...")
                # Test with SSE headers
                headers = {
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache'
                }
                response = requests.get(mcp_url, headers=headers, timeout=5, stream=True)
                print(f"[DEBUG] Response status: {response.status_code}")

                if response.status_code == 200:
                    response.close()
                    return f"✅ **MCP Server Online!**\n\nServer at: `{mcp_url}`\n\nStatus: {response.status_code} OK\n\nThe MCP server is accessible and ready to use."
                elif response.status_code == 406:
                    # 406 Not Acceptable - server is online but rejecting the request type (expected for MCP endpoints)
                    return f"✅ **MCP Server Online!**\n\nServer at: `{mcp_url}`\n\nStatus: 406 (Not Acceptable)\n\n**This is expected behavior** - MCP servers reject simple HTTP requests but accept SSE connections from MCP clients.\n\nThe server is working correctly!"
                elif response.status_code == 404:
                    return f"❌ **Endpoint Not Found**\n\nURL: `{mcp_url}`\n\nStatus: 404\n\nThe MCP endpoint doesn't exist at this URL. Check the path is correct."
                else:
                    return f"⚠️ **Server Responded**\n\nURL: `{mcp_url}`\n\nStatus: {response.status_code}\n\nServer is online but returned unexpected status."
            except requests.exceptions.Timeout:
                print(f"[DEBUG] Timeout error")
                # Timeout on SSE endpoint might mean it's waiting for connection - could be OK
                return f"⚠️ **Connection Timeout**\n\nURL: `{mcp_url}`\n\nThe server may be waiting for an SSE connection (streaming). This could mean:\n- ✅ Server is online but requires proper MCP client\n- ❌ Server is slow or overloaded\n\nTry using the MCP tools in the other tabs to test actual functionality."
            except requests.exceptions.ConnectionError as e:
                print(f"[DEBUG] Connection error: {e}")
                return f"❌ **Connection Failed**\n\nURL: `{mcp_url}`\n\nCannot reach the server. Check:\n- URL is correct\n- Server is running\n- Network/firewall not blocking"
            except Exception as e:
                print(f"[DEBUG] Unexpected error: {e}")
                return f"❌ **Error**\n\nURL: `{mcp_url}`\n\nError: {str(e)}"

        test_mcp_btn.click(
            fn=test_mcp_connection,
            inputs=[mcp_url_display],
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
