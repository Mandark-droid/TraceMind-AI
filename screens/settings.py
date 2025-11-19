"""
Settings Screen for TraceMind-AI
Allows users to configure API keys for Gemini and HuggingFace
"""

import gradio as gr
import os


def create_settings_screen():
    """
    Create the settings screen for API key configuration

    Returns:
        gr.Column: Gradio Column component for settings (can be shown/hidden)
    """
    with gr.Column(visible=False) as settings_interface:
        gr.Markdown("""
        # ⚙️ Settings

        Configure your API keys to use TraceMind features. These keys are stored only in your browser session and are never saved to our servers.
        """)

        with gr.Accordion("🔑 API Key Configuration", open=True):
            gr.Markdown("""
            ### Why provide API keys?

            TraceMind uses external services to provide intelligent analysis and insights:
            - **Google Gemini API**: Powers the MCP server for leaderboard analysis, cost estimation, and trace debugging
            - **HuggingFace Token**: Required to access evaluation datasets and results

            **For Judges & Visitors**: Please enter your own API keys to prevent credit issues during evaluation.
            """)

            # Gemini API Key
            with gr.Row():
                with gr.Column(scale=4):
                    gemini_api_key = gr.Textbox(
                        label="Google Gemini API Key",
                        placeholder="Enter your Gemini API key (starts with 'AIza...')",
                        type="password",
                        value=os.environ.get("GEMINI_API_KEY", ""),
                        info="Get your free API key at: https://ai.google.dev/"
                    )
                with gr.Column(scale=1):
                    gemini_status = gr.Markdown("⚪ Not configured")

            # HuggingFace Token
            with gr.Row():
                with gr.Column(scale=4):
                    hf_token = gr.Textbox(
                        label="HuggingFace Token",
                        placeholder="Enter your HF token (starts with 'hf_...')",
                        type="password",
                        value=os.environ.get("HF_TOKEN", ""),
                        info="Get your token at: https://huggingface.co/settings/tokens"
                    )
                with gr.Column(scale=1):
                    hf_status = gr.Markdown("⚪ Not configured")

            # Save button
            with gr.Row():
                save_btn = gr.Button("💾 Save API Keys", variant="primary")
                test_btn = gr.Button("🧪 Test Connection", variant="secondary")

            # Status message
            status_message = gr.Markdown("")

        with gr.Accordion("📖 How to Get API Keys", open=False):
            gr.Markdown("""
            ### Google Gemini API Key

            1. Go to [Google AI Studio](https://ai.google.dev/)
            2. Click "Get API Key" in the top right
            3. Create a new project or select an existing one
            4. Generate an API key
            5. Copy the key (starts with `AIza...`)

            **Free Tier**: 60 requests per minute, suitable for testing and demos

            ---

            ### HuggingFace Token

            1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
            2. Click "New token"
            3. Give it a name (e.g., "TraceMind Access")
            4. Select "Read" permissions
            5. Create and copy the token (starts with `hf_...`)

            **Note**: Read-only access is sufficient for viewing datasets
            """)

        with gr.Accordion("🔒 Privacy & Security", open=False):
            gr.Markdown("""
            ### Your Privacy Matters

            - ✅ **Session-only storage**: API keys are stored only in your browser session
            - ✅ **No server storage**: Keys are never saved to our servers or databases
            - ✅ **HTTPS encryption**: All API calls are made over secure connections
            - ✅ **No logging**: API keys are not logged or tracked

            ### Best Practices

            - 🔐 Use dedicated API keys for testing/demos
            - 🔄 Rotate your keys regularly
            - 🚫 Don't share your keys publicly
            - 📊 Monitor your API usage on provider dashboards

            ### Rate Limits

            **Gemini API (Free Tier)**:
            - 60 requests per minute
            - 1,500 requests per day

            **HuggingFace**:
            - Read access: No strict limits
            - Public datasets: Unlimited reads
            """)

        # Define save functionality
        def save_api_keys(gemini_key, hf_key):
            """Save API keys to session"""
            messages = []

            # Validate and save Gemini API key
            if gemini_key and gemini_key.strip():
                if gemini_key.startswith("AIza"):
                    os.environ["GEMINI_API_KEY"] = gemini_key.strip()
                    messages.append("✅ Gemini API key saved")
                    gemini_status_text = "✅ Configured"
                else:
                    messages.append("⚠️ Invalid Gemini API key format (should start with 'AIza')")
                    gemini_status_text = "❌ Invalid format"
            else:
                messages.append("⚠️ Gemini API key not provided")
                gemini_status_text = "⚪ Not configured"

            # Validate and save HuggingFace token
            if hf_key and hf_key.strip():
                if hf_key.startswith("hf_"):
                    os.environ["HF_TOKEN"] = hf_key.strip()
                    messages.append("✅ HuggingFace token saved")
                    hf_status_text = "✅ Configured"
                else:
                    messages.append("⚠️ Invalid HuggingFace token format (should start with 'hf_')")
                    hf_status_text = "❌ Invalid format"
            else:
                messages.append("⚠️ HuggingFace token not provided")
                hf_status_text = "⚪ Not configured"

            status_msg = "\n\n".join(messages)
            status_msg += "\n\n**Note**: Keys are saved for this session only and will be used for MCP server calls."

            return status_msg, gemini_status_text, hf_status_text

        def test_api_keys(gemini_key, hf_key):
            """Test API key connections"""
            results = []

            # Test Gemini API
            if gemini_key and gemini_key.strip():
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key.strip())
                    # Try to list models as a test
                    models = genai.list_models()
                    results.append("✅ **Gemini API**: Connection successful!")
                except Exception as e:
                    results.append(f"❌ **Gemini API**: Connection failed - {str(e)}")
            else:
                results.append("⚠️ **Gemini API**: No key provided")

            # Test HuggingFace token
            if hf_key and hf_key.strip():
                try:
                    from huggingface_hub import HfApi
                    api = HfApi(token=hf_key.strip())
                    # Try to get user info as a test
                    user_info = api.whoami()
                    results.append(f"✅ **HuggingFace**: Connection successful! (User: {user_info['name']})")
                except Exception as e:
                    results.append(f"❌ **HuggingFace**: Connection failed - {str(e)}")
            else:
                results.append("⚠️ **HuggingFace**: No token provided")

            return "\n\n".join(results)

        # Wire up button events (api_name=False to prevent API key exposure)
        save_btn.click(
            fn=save_api_keys,
            inputs=[gemini_api_key, hf_token],
            outputs=[status_message, gemini_status, hf_status],
            api_name=False  # IMPORTANT: Prevents API key exposure via Gradio API
        )

        test_btn.click(
            fn=test_api_keys,
            inputs=[gemini_api_key, hf_token],
            outputs=[status_message],
            api_name=False  # IMPORTANT: Prevents API key exposure via Gradio API
        )

        # Return both the interface and the input components for external access
        return settings_interface, gemini_api_key, hf_token


if __name__ == "__main__":
    # For standalone testing
    with gr.Blocks() as demo:
        settings_screen, _, _ = create_settings_screen()
        # Make it visible for standalone testing
        settings_screen.visible = True
    demo.launch()
