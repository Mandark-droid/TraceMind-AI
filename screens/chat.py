"""
Chat Screen for TraceMind-AI
Agentic chat interface using smolagents with MCP servers as tools
Demonstrates autonomous Agent behavior for Track 2 submission
"""

import gradio as gr
from typing import List, Tuple, Dict, Any
import json
import os
import yaml

# Smolagents imports
try:
    from smolagents import CodeAgent, InferenceClientModel, LiteLLMModel
    from smolagents.mcp_client import MCPClient
    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False
    print("[WARNING] smolagents not installed - Chat screen will use mock agent")

# TraceMind MCP Server endpoint
MCP_SERVER_URL = "https://kshitijthakkar-tracemind-mcp-server.hf.space/gradio_api/mcp/sse"

# Model configuration - can be set via environment variables
MODEL_TYPE = os.getenv("AGENT_MODEL_TYPE", "hfapi")  # Options: "hfapi", "inference_client", "litellm"
HF_TOKEN = os.getenv("HF_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Global agent and MCP client (reused across requests)
_global_agent = None
_global_mcp_client = None


def create_agent():
    """Create smolagents agent with MCP server tools (singleton pattern)"""
    global _global_agent, _global_mcp_client

    # Return existing agent if already created
    if _global_agent is not None:
        return _global_agent

    if not SMOLAGENTS_AVAILABLE:
        return None

    try:
        # Connect to TraceMind MCP Server using SSE transport
        print(f"Connecting to TraceMind MCP Server at {MCP_SERVER_URL}...")
        print(f"Using SSE transport for Gradio MCP server...")

        # For Gradio MCP servers, must specify transport: "sse"
        # See: https://huggingface.co/learn/mcp-course/unit2/gradio-client
        _global_mcp_client = MCPClient(
            {"url": MCP_SERVER_URL, "transport": "sse"}
        )

        # Get tools from MCP server (MCPClient.get_tools() doesn't support structured_output parameter)
        print("Fetching tools from MCP server...")
        tools = _global_mcp_client.get_tools()

        print(f"Received {len(tools)} tools from MCP server")

        # Log available tools
        tools_array = [{
            "name": tool.name,
            "description": tool.description,
            "inputs": tool.inputs,
            "output_type": tool.output_type,
            "is_initialized": tool.is_initialized
        } for tool in tools]

        tool_names = [tool["name"] for tool in tools_array]
        print(f"Connected to TraceMind MCP server. Available tools: {', '.join(tool_names)}")

        # Create model based on configuration
        if MODEL_TYPE == "inference_client":
            # InferenceClientModel with Nebius provider (DeepSeek-V3)
            model = InferenceClientModel(
                model_id="deepseek-ai/DeepSeek-V3-0324",
                provider="nebius",
                api_key=HF_TOKEN,
            )
            print(f"Using InferenceClientModel: deepseek-ai/DeepSeek-V3-0324 (Nebius)")

        elif MODEL_TYPE == "litellm":
            # LiteLLMModel with Gemini
            model = LiteLLMModel(
                model_id="gemini/gemini-2.5-flash",
                api_key=GEMINI_API_KEY
            )
            print(f"Using LiteLLMModel: gemini/gemini-2.5-flash")

        else:  # Default: hfapi (using InferenceClientModel)
            # InferenceClientModel with Qwen (HF Inference API)
            model = InferenceClientModel(
                model_id='Qwen/Qwen3-Coder-480B-A35B-Instruct',
                token=HF_TOKEN if HF_TOKEN else None,
            )
            print(f"Using InferenceClientModel: Qwen/Qwen3-Coder-480B-A35B-Instruct (HF Inference API)")

        # Load prompt templates from YAML file
        prompt_template_path = os.path.join(os.path.dirname(__file__), "../prompts/code_agent.yaml")
        with open(prompt_template_path, 'r', encoding='utf-8') as stream:
            prompt_templates = yaml.safe_load(stream)

        # Create CodeAgent with MCP server tools and YAML prompt template
        agent = CodeAgent(
            tools=[*tools],
            model=model,
            prompt_templates=prompt_templates,
            max_steps=10,
            planning_interval=5,
            additional_authorized_imports=[
                'time', 'math', 'queue', 're', 'stat', 'collections', 'datetime',
                'statistics', 'itertools', 'unicodedata', 'random',
                'pandas', 'numpy', 'json', 'yaml', 'plotly'
            ]
        )

        # Store agent globally for reuse
        _global_agent = agent
        print("✅ Agent created successfully and cached for reuse")

        return agent

    except Exception as e:
        print(f"[ERROR] Creating agent: {e}")
        import traceback
        traceback.print_exc()
        return None


def cleanup_agent():
    """Cleanup MCP client connection"""
    global _global_agent, _global_mcp_client

    if _global_mcp_client is not None:
        try:
            print("Disconnecting MCP client...")
            _global_mcp_client.disconnect()
            print("✅ MCP client disconnected")
        except Exception as e:
            print(f"[WARNING] Error disconnecting MCP client: {e}")
        finally:
            _global_mcp_client = None
            _global_agent = None


def chat_with_agent(
    message: str,
    history: List[Tuple[str, str]],
    show_reasoning: bool = True
) -> Tuple[List[Tuple[str, str]], str]:
    """
    Process user message with agent

    Args:
        message: User's input message
        history: Chat history
        show_reasoning: Whether to show agent's reasoning steps

    Returns:
        Updated history and reasoning log
    """

    if not SMOLAGENTS_AVAILABLE:
        # Mock response for when smolagents isn't available
        history.append((message, "🤖 Agent not available (smolagents not installed). Install with: pip install smolagents"))
        return history, "No reasoning available"

    try:
        agent = create_agent()
        if agent is None:
            history.append((message, "❌ Failed to initialize agent"))
            return history, "Agent initialization failed"

        # Run agent
        response = agent.run(message)

        # Extract reasoning steps
        reasoning_log = ""
        if hasattr(agent, 'logs') and show_reasoning:
            for log in agent.logs:
                reasoning_log += f"**{log['role']}**: {log['content']}\n\n"

        # Add to history
        history.append((message, str(response)))

        return history, reasoning_log

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        history.append((message, error_msg))
        return history, f"Error during execution: {str(e)}"


def create_chat_ui():
    """
    Create the chat screen UI

    Returns:
        Tuple of (screen_column, component_dict)
    """
    components = {}

    with gr.Column(visible=False) as chat_screen:
        gr.Markdown("# 🤖 Agent Chat")
        gr.Markdown("*Autonomous AI agent powered by smolagents with MCP tools*")

        # Info banner
        with gr.Accordion("💡 About This Agent", open=False):
            gr.Markdown("""
            ### 🎯 What is this?
            This is an **autonomous AI agent** that can:
            - 🔍 **Analyze** evaluation results across the leaderboard
            - 🐛 **Debug** specific traces and identify issues
            - 💰 **Estimate** costs for running evaluations
            - 🧠 **Reason** through complex multi-step tasks
            - 🛠️ **Use MCP servers** as tools for data access

            ### 🚀 Key Features (Track 2 Requirements)
            - ✅ **Autonomous Planning**: Agent decides which tools to use
            - ✅ **Multi-Step Reasoning**: Breaks down complex queries
            - ✅ **MCP Integration**: Uses MCP servers (leaderboard analyzer, trace debugger, cost estimator)
            - ✅ **Tool Execution**: Calls tools based on user intent
            - ✅ **Context Engineering**: Maintains conversation context

            ### 💬 Example Questions
            - "What are the top 3 performing models and how much do they cost?"
            - "Which model should I use for a cost-sensitive project?"
            - "Estimate the cost of evaluating GPT-4 on 200 tests"
            - "Compare Llama 3.1 vs GPT-4 in terms of speed and cost"
            - "Why would I choose H200 over A10 GPU?"

            ### 🧰 Available Tools (MCP Servers)
            1. **analyze_leaderboard**: Get insights from evaluation data
            2. **debug_trace**: Analyze specific trace executions
            3. **estimate_cost**: Calculate evaluation costs and duration
            """)

        with gr.Row():
            with gr.Column(scale=2):
                # Chat interface
                components['chatbot'] = gr.Chatbot(
                    label="Agent Conversation",
                    height=500,
                    show_label=True,
                    avatar_images=(None, "🤖")
                )

                with gr.Row():
                    components['message'] = gr.Textbox(
                        placeholder="Ask me anything about agent evaluations...",
                        label="Your Message",
                        lines=2,
                        scale=4,
                        info="The agent will analyze your question and use appropriate tools"
                    )
                    components['send_btn'] = gr.Button("Send", variant="primary", scale=1)

                with gr.Row():
                    components['clear_btn'] = gr.Button("🗑️ Clear Chat")
                    components['show_reasoning'] = gr.Checkbox(
                        label="Show Agent Reasoning",
                        value=True,
                        info="Display the agent's planning and tool usage steps"
                    )

            with gr.Column(scale=1):
                # Reasoning panel
                gr.Markdown("### 🧠 Agent Reasoning")
                components['reasoning_display'] = gr.Markdown(
                    "*Agent's reasoning steps will appear here...*",
                    label="Reasoning Log"
                )

                # Quick actions
                gr.Markdown("### ⚡ Quick Actions")
                components['quick_analyze'] = gr.Button("🔍 Analyze Leaderboard", size="sm")
                components['quick_costs'] = gr.Button("💰 Compare Costs", size="sm")
                components['quick_recommend'] = gr.Button("🎯 Get Recommendations", size="sm")

    return chat_screen, components


def on_send_message(message, history, show_reasoning):
    """Handle send button click"""
    if not message.strip():
        return history, "", "Please enter a message"

    updated_history, reasoning = chat_with_agent(message, history, show_reasoning)
    return updated_history, "", reasoning


def on_clear_chat():
    """Handle clear button click and cleanup agent connection"""
    # Cleanup agent and MCP client connection
    cleanup_agent()
    return [], "", "*Agent's reasoning steps will appear here...*"


def on_quick_action(action_type):
    """Handle quick action buttons"""
    prompts = {
        "analyze": "Analyze the current leaderboard and show me the top performing models with their costs",
        "costs": "Compare the costs of the top 3 models - which one offers the best value?",
        "recommend": "Based on the leaderboard data, which model would you recommend for a production system that needs both good accuracy and reasonable cost?"
    }
    return prompts.get(action_type, "")
