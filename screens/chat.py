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
    from smolagents.agent_types import AgentAudio, AgentImage, AgentText
    from smolagents.agents import MultiStepAgent, PlanningStep
    from smolagents.memory import ActionStep, FinalAnswerStep
    from smolagents.models import ChatMessageStreamDelta
    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False
    print("[WARNING] smolagents not installed - Chat screen will use mock agent")

# TraceMind MCP Server endpoint
MCP_SERVER_URL = "https://mcp-1st-birthday-tracemind-mcp-server.hf.space/gradio_api/mcp/sse"

# Model configuration - can be set via environment variables
MODEL_TYPE = os.getenv("AGENT_MODEL_TYPE", "hfapi")  # Options: "hfapi", "inference_client", "litellm"
HF_TOKEN = os.getenv("HF_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Global MCP client (shared, stateless connection to MCP server)
# Agent instances are session-specific via gr.State
_global_mcp_client = None


# ============================================================================
# Helper Functions for Agent Step Processing
# ============================================================================

def get_step_footnote_content(step_log: ActionStep | PlanningStep, step_name: str) -> str:
    """Get a footnote string for a step log with duration and token information"""
    step_footnote = f"**{step_name}**"

    # Check if token_usage attribute exists and is not None
    if hasattr(step_log, 'token_usage') and step_log.token_usage is not None:
        step_footnote += f" | Input tokens: {step_log.token_usage.input_tokens:,} | Output tokens: {step_log.token_usage.output_tokens:,}"

    # Add duration information if available
    if hasattr(step_log, 'timing') and step_log.timing and step_log.timing.duration:
        step_footnote += f" | Duration: {round(float(step_log.timing.duration), 2)}s"

    step_footnote_content = f"""<span style="color: #bbbbc2; font-size: 12px;">{step_footnote}</span> """
    return step_footnote_content


def _clean_model_output(model_output: str) -> str:
    """Clean up model output by removing trailing tags and extra backticks."""
    if not model_output:
        return ""
    model_output = model_output.strip()
    # Remove any trailing <end_code> and extra backticks, handling multiple possible formats
    import re
    model_output = re.sub(r"```\s*<end_code>", "```", model_output)
    model_output = re.sub(r"<end_code>\s*```", "```", model_output)
    model_output = re.sub(r"```\s*\n\s*<end_code>", "```", model_output)
    return model_output.strip()


def _format_code_content(content: str) -> str:
    """Format code content as Python code block if it's not already formatted."""
    import re
    content = content.strip()
    # Remove existing code blocks and end_code tags
    content = re.sub(r"```.*?\n", "", content)
    content = re.sub(r"\s*<end_code>\s*", "", content)
    content = content.strip()
    # Add Python code block formatting if not already present
    if not content.startswith("```python"):
        content = f"```python\n{content}\n```"
    return content


def _process_action_step(step_log: ActionStep, skip_model_outputs: bool = False):
    """Process an ActionStep and yield appropriate Gradio ChatMessage objects."""
    import re

    # Output the step number
    step_number = f"🔧 Step {step_log.step_number}"
    if not skip_model_outputs:
        yield gr.ChatMessage(role="assistant", content=f"**{step_number}**", metadata={"status": "done"})

    # First yield the thought/reasoning from the LLM (collapsed)
    if not skip_model_outputs and getattr(step_log, "model_output", ""):
        model_output = _clean_model_output(step_log.model_output)
        yield gr.ChatMessage(
            role="assistant",
            content=model_output,
            metadata={"title": "💭 Reasoning", "status": "done"}
        )

    # For tool calls, create a parent message
    if getattr(step_log, "tool_calls", []):
        first_tool_call = step_log.tool_calls[0]
        used_code = first_tool_call.name in ["python_interpreter", "execute_code", "final_answer"]

        # Process arguments based on type
        args = first_tool_call.arguments
        if isinstance(args, dict):
            content = str(args.get("answer", str(args)))
        else:
            content = str(args).strip()

        # Format code content if needed
        if used_code and "```" not in content:
            content = _format_code_content(content)

        # Choose appropriate emoji and title based on tool
        tool_emoji = "🛠️"
        tool_title = f"Used tool: {first_tool_call.name}"

        # Specific tool icons for TraceMind MCP tools
        if "leaderboard" in first_tool_call.name.lower():
            tool_emoji = "📊"
            tool_title = f"Analyzed Leaderboard using {first_tool_call.name}"
        elif "trace" in first_tool_call.name.lower() or "debug" in first_tool_call.name.lower():
            tool_emoji = "🔍"
            tool_title = f"Debugged Trace using {first_tool_call.name}"
        elif "cost" in first_tool_call.name.lower() or "estimate" in first_tool_call.name.lower():
            tool_emoji = "💰"
            tool_title = f"Estimated Cost using {first_tool_call.name}"
        elif used_code:
            tool_emoji = "💻"
            tool_title = f"Executed Code using {first_tool_call.name}"

        # Create the tool call message
        parent_message_tool = gr.ChatMessage(
            role="assistant",
            content=content,
            metadata={
                "title": f"{tool_emoji} {tool_title}",
                "status": "done",
            },
        )
        yield parent_message_tool

    # Display execution logs if they exist
    if getattr(step_log, "observations", "") and step_log.observations.strip():
        import re
        log_content = step_log.observations.strip()
        if log_content:
            log_content = re.sub(r"^Execution logs:\s*", "", log_content)
            yield gr.ChatMessage(
                role="assistant",
                content=f"```bash\n{log_content}\n```",
                metadata={"title": "📋 Execution Logs", "status": "done"},
            )

    # Handle errors
    if getattr(step_log, "error", None):
        error_msg = f"⚠️ **Error:** {str(step_log.error)}"
        yield gr.ChatMessage(
            role="assistant", content=error_msg, metadata={"title": "🚫 Error", "status": "done"}
        )

    # Add step footnote and separator
    yield gr.ChatMessage(
        role="assistant", content=get_step_footnote_content(step_log, step_number), metadata={"status": "done"}
    )
    yield gr.ChatMessage(role="assistant", content="---", metadata={"status": "done"})


def _process_planning_step(step_log: PlanningStep, skip_model_outputs: bool = False):
    """Process a PlanningStep and yield appropriate gradio.ChatMessage objects."""
    if not skip_model_outputs:
        # Show planning phase as collapsible section
        yield gr.ChatMessage(
            role="assistant",
            content=step_log.plan,
            metadata={"title": "🧠 Planning Phase", "status": "done"}
        )
    yield gr.ChatMessage(
        role="assistant", content=get_step_footnote_content(step_log, "Planning Phase"), metadata={"status": "done"}
    )
    yield gr.ChatMessage(role="assistant", content="---", metadata={"status": "done"})


def _process_final_answer_step(step_log: FinalAnswerStep):
    """Process a FinalAnswerStep and yield appropriate gradio.ChatMessage objects."""
    # Try different possible attribute names for the final answer
    final_answer = None
    possible_attrs = ['output', 'answer', 'result', 'content', 'final_answer']

    for attr in possible_attrs:
        if hasattr(step_log, attr):
            final_answer = getattr(step_log, attr)
            break

    # If no known attribute found, use string representation of the step
    if final_answer is None:
        yield gr.ChatMessage(
            role="assistant",
            content=f"**Final answer:** {str(step_log)}",
            metadata={"status": "done"}
        )
        return

    # Process the final answer based on its type (NOT collapsed - visible by default)
    if isinstance(final_answer, AgentText):
        yield gr.ChatMessage(
            role="assistant",
            content=f"📜 **Final Answer:**\n\n{final_answer.to_string()}",
            metadata={"status": "done"},
        )
    elif isinstance(final_answer, AgentImage):
        # Handle image if needed
        yield gr.ChatMessage(
            role="assistant",
            content=f"🎨 **Image Result:**\n\n![Image]({final_answer.to_string()})",
            metadata={"status": "done"},
        )
    elif isinstance(final_answer, AgentAudio):
        yield gr.ChatMessage(
            role="assistant",
            content={"path": final_answer.to_string(), "mime_type": "audio/wav"},
            metadata={"status": "done"},
        )
    else:
        # Assume markdown content and render as-is
        yield gr.ChatMessage(
            role="assistant",
            content=f"📜 **Final Answer:**\n\n{str(final_answer)}",
            metadata={"status": "done"},
        )


def pull_messages_from_step(step_log: ActionStep | PlanningStep | FinalAnswerStep, skip_model_outputs: bool = False):
    """Extract Gradio ChatMessage objects from agent steps with proper nesting."""
    if isinstance(step_log, ActionStep):
        yield from _process_action_step(step_log, skip_model_outputs)
    elif isinstance(step_log, PlanningStep):
        yield from _process_planning_step(step_log, skip_model_outputs)
    elif isinstance(step_log, FinalAnswerStep):
        yield from _process_final_answer_step(step_log)
    else:
        raise ValueError(f"Unsupported step type: {type(step_log)}")


def stream_to_gradio(
        agent,
        task: str,
        reset_agent_memory: bool = False,
):
    """Runs an agent with the given task and streams the messages from the agent as gradio ChatMessages."""
    intermediate_text = ""

    for event in agent.run(
            task, stream=True, max_steps=20, reset=reset_agent_memory
    ):
        if isinstance(event, ActionStep | PlanningStep | FinalAnswerStep):
            intermediate_text = ""
            for message in pull_messages_from_step(
                    event,
                    skip_model_outputs=getattr(agent, "stream_outputs", False),
            ):
                yield message
        elif isinstance(event, ChatMessageStreamDelta):
            intermediate_text += event.content or ""
            yield intermediate_text


def get_mcp_tools():
    """Get tools from MCP server (shared connection, stateless)"""
    global _global_mcp_client

    # Reuse MCP client connection if already established
    if _global_mcp_client is None:
        try:
            print(f"Connecting to TraceMind MCP Server at {MCP_SERVER_URL}...")
            print(f"Using SSE transport for Gradio MCP server...")

            # For Gradio MCP servers, must specify transport: "sse"
            _global_mcp_client = MCPClient(
                {"url": MCP_SERVER_URL, "transport": "sse"}
            )

            print("Fetching tools from MCP server...")
            tools = _global_mcp_client.get_tools()
            print(f"Received {len(tools)} tools from MCP server")

            # Log available tools
            tool_names = [tool.name for tool in tools]
            print(f"✅ Connected to TraceMind MCP server")
            print(f"✅ Received {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.name}")

            return tools

        except Exception as e:
            print(f"[ERROR] Connecting to MCP server: {e}")
            import traceback
            traceback.print_exc()
            return []
    else:
        # Return tools from existing connection
        return _global_mcp_client.get_tools()


def create_agent():
    """Create smolagents agent with MCP server tools (per-session instance)"""
    if not SMOLAGENTS_AVAILABLE:
        return None

    try:
        # Get tools from shared MCP connection
        tools = get_mcp_tools()
        if not tools:
            print("[ERROR] No tools available from MCP server")
            return None

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

        # Create NEW CodeAgent instance for this session
        agent = CodeAgent(
            tools=[*tools],
            model=model,
            prompt_templates=prompt_templates,
            max_steps=10,
            planning_interval=5,
            additional_authorized_imports=[
                'time', 'math', 'queue', 're', 'stat', 'collections', 'datetime',
                'statistics', 'itertools', 'unicodedata', 'random',
                'pandas', 'numpy', 'json', 'yaml', 'plotly', 'ast'
            ]
        )

        print("✅ Agent created successfully (session-specific instance)")
        print(f"✅ Agent has {len(agent.tools)} tools registered:")
        for tool_name in agent.tools.keys():
            print(f"   - {tool_name}")
        return agent

    except Exception as e:
        print(f"[ERROR] Creating agent: {e}")
        import traceback
        traceback.print_exc()
        return None


def cleanup_agent():
    """
    Cleanup MCP client connection (global, shared connection)
    Note: Individual agent instances are garbage collected automatically
    """
    global _global_mcp_client

    if _global_mcp_client is not None:
        try:
            print("Disconnecting MCP client...")
            _global_mcp_client.disconnect()
            print("✅ MCP client disconnected")
        except Exception as e:
            print(f"[WARNING] Error disconnecting MCP client: {e}")
        finally:
            _global_mcp_client = None


def chat_with_agent(message: str, history: list, agent_state):
    """
    Process user message with agent using streaming

    Args:
        message: User's input message
        history: Chat history (list of ChatMessage objects)
        agent_state: Session-specific agent instance (gr.State)

    Yields:
        Tuple of (updated_history, updated_agent_state)
    """

    if not SMOLAGENTS_AVAILABLE:
        # Mock response for when smolagents isn't available
        history.append(gr.ChatMessage(role="user", content=message, metadata={"status": "done"}))
        history.append(gr.ChatMessage(
            role="assistant",
            content="🤖 Agent not available (smolagents not installed). Install with: pip install smolagents",
            metadata={"status": "done"}
        ))
        yield history, agent_state
        return

    try:
        # Create agent if not exists in session state
        if agent_state is None:
            agent_state = create_agent()
            if agent_state is None:
                history.append(gr.ChatMessage(role="user", content=message, metadata={"status": "done"}))
                history.append(gr.ChatMessage(
                    role="assistant",
                    content="❌ Failed to initialize agent",
                    metadata={"status": "done"}
                ))
                yield history, agent_state
                return

        # Add user message
        history.append(gr.ChatMessage(role="user", content=message, metadata={"status": "done"}))
        yield history, agent_state

        # Stream agent responses (agent maintains its own memory across messages in this session)
        for msg in stream_to_gradio(agent_state, task=message, reset_agent_memory=False):
            if isinstance(msg, gr.ChatMessage):
                # Mark previous message as done if it was pending
                if history and history[-1].metadata.get("status") == "pending":
                    history[-1].metadata["status"] = "done"
                history.append(msg)
            elif isinstance(msg, str):  # Streaming text delta
                msg = msg.replace("<", r"\<").replace(">", r"\>")  # HTML tags seem to break Gradio Chatbot
                if history and history[-1].metadata.get("status") == "pending":
                    history[-1].content = msg
                else:
                    history.append(gr.ChatMessage(role="assistant", content=msg, metadata={"status": "pending"}))
            yield history, agent_state

        # Mark final message as done
        if history and history[-1].metadata.get("status") == "pending":
            history[-1].metadata["status"] = "done"
        yield history, agent_state

    except Exception as e:
        import traceback
        error_msg = f"❌ Error: {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        history.append(gr.ChatMessage(
            role="assistant",
            content=error_msg,
            metadata={"title": "🚫 Error", "status": "done"}
        ))
        yield history, agent_state


def create_chat_ui():
    """
    Create the chat screen UI

    Returns:
        Tuple of (screen_column, component_dict)
    """
    components = {}

    # Session-specific agent state (each browser tab gets its own agent instance)
    components['agent_state'] = gr.State(value=None)

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
                # Chat interface (using type="messages" for rich ChatMessage display)
                components['chatbot'] = gr.Chatbot(
                    label="Agent Conversation",
                    type="messages",
                    height=500,
                    show_label=True,
                    show_copy_button=True,
                    avatar_images=(
                        "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/smolagents/mascot_smol.png",
                        "https://raw.githubusercontent.com/Mandark-droid/TraceMind-AI/assets/Logo.png"
                    )
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

            with gr.Column(scale=1):
                # Info panel
                gr.Markdown("### ℹ️ Agent Status")
                gr.Markdown("""
                The agent's reasoning, tool calls, and execution logs are displayed inline in the chat.

                **Look for:**
                - 💭 **Reasoning** - Agent's thought process
                - 🛠️ **Tool Calls** - MCP server invocations
                - 📋 **Execution Logs** - Tool outputs
                - 📜 **Final Answer** - Agent's response
                """)

                # Quick actions
                gr.Markdown("### ⚡ Quick Actions")
                gr.Markdown("**Basic:**")
                components['quick_analyze'] = gr.Button("🔍 Analyze Leaderboard", size="sm")
                components['quick_costs'] = gr.Button("💰 Compare Costs", size="sm")
                components['quick_recommend'] = gr.Button("🎯 Get Recommendations", size="sm")

                gr.Markdown("**Advanced:**")
                components['quick_multi_tool'] = gr.Button("🔗 Multi-Tool Analysis", size="sm")
                components['quick_synthetic'] = gr.Button("🧪 Generate Synthetic Data", size="sm")

    return chat_screen, components


def on_send_message(message, history, agent_state):
    """Handle send button click - now uses streaming with per-session agent"""
    if not message.strip():
        yield history, "", agent_state
        return

    # Stream agent responses with session-specific agent
    for updated_history, updated_agent in chat_with_agent(message, history, agent_state):
        yield updated_history, "", updated_agent


def on_clear_chat(agent_state):
    """
    Handle clear button click
    Note: Does NOT cleanup global MCP connection (shared across sessions)
    Only resets this session's agent instance
    """
    # Return empty history and None agent (will create new agent on next message)
    return [], None


def on_quick_action(action_type):
    """Handle quick action buttons"""
    prompts = {
        "analyze": "Analyze the current leaderboard and show me the top performing models with their costs",
        "costs": "Compare the costs of the top 3 models - which one offers the best value?",
        "recommend": "Based on the leaderboard data, which model would you recommend for a production system that needs both good accuracy and reasonable cost?",
        "multi_tool": "Analyze the leaderboard with focus on cost and accuracy, identify the top 2 models, compare them, and estimate the cost of running 500 evaluations on the cheaper one",
        "synthetic": "Generate a synthetic test dataset with 100 tasks for the food-delivery domain using these tools: search_restaurants, view_menu, place_order, track_delivery, apply_promo, rate_restaurant, contact_driver with difficulty_distribution='balanced' and agent_type='both'. Then create a prompt template for the same domain and tools using agent_type='tool', and push the dataset to MCP-1st-Birthday/smoltrace-food-delivery-tasks-v2"
    }
    return prompts.get(action_type, "")
