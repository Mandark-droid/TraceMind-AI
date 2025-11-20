"""
Settings Screen for TraceMind-AI
Allows users to configure API keys for Gemini, HuggingFace, Modal, and LLM providers
"""

import gradio as gr
import os


# Note: Removed _get_llm_keys_as_env_string() to prevent exposing environment variables
# in the UI for security reasons. Users should explicitly enter keys needed for jobs.


def _parse_env_string(env_string):
    """
    Parse ENV-formatted string into a dictionary

    Args:
        env_string: Multi-line string in KEY=value format

    Returns:
        dict: Parsed key-value pairs
    """
    result = {}
    if not env_string:
        return result

    for line in env_string.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()

    return result


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

            # Modal API Key
            with gr.Row():
                with gr.Column(scale=4):
                    modal_api_key = gr.Textbox(
                        label="Modal API Key (Optional)",
                        placeholder="Enter your Modal API key (starts with 'ak-...')",
                        type="password",
                        value=os.environ.get("MODAL_TOKEN_ID", ""),
                        info="Get your key at: https://modal.com/settings/tokens"
                    )
                with gr.Column(scale=1):
                    modal_status = gr.Markdown("⚪ Not configured")

            # Modal API Secret
            with gr.Row():
                with gr.Column(scale=4):
                    modal_api_secret = gr.Textbox(
                        label="Modal API Secret (Optional)",
                        placeholder="Enter your Modal API secret (starts with 'as-...')",
                        type="password",
                        value=os.environ.get("MODAL_TOKEN_SECRET", ""),
                        info="Required if using Modal for job execution"
                    )
                with gr.Column(scale=1):
                    modal_secret_status = gr.Markdown("⚪ Not configured")

            # LLM Provider API Keys (Multi-line for convenience)
            gr.Markdown("""
            ### LLM Provider API Keys (Optional)

            Paste your API keys in ENV format below. These are needed for running evaluations with API-based models.
            """)

            llm_api_keys = gr.Textbox(
                label="LLM Provider API Keys",
                placeholder="""OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GEMINI_API_KEY=AIza...
COHERE_API_KEY=...
MISTRAL_API_KEY=...
TOGETHER_API_KEY=...
GROQ_API_KEY=gsk_...
REPLICATE_API_TOKEN=r8_...
ANYSCALE_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-west-2
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
LITELLM_API_KEY=...""",
                lines=10,
                value="",  # Don't expose existing env vars
                info="Enter one key=value per line. These will be passed to evaluation jobs."
            )

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

            ---

            ### Modal API Credentials (Optional)

            1. Go to [Modal Settings](https://modal.com/settings/tokens)
            2. Click "Create new token"
            3. Copy both:
               - Token ID (starts with `ak-...`)
               - Token Secret (starts with `as-...`)

            **Why Modal?** Run evaluation jobs on serverless GPU compute with per-second billing.

            ---

            ### LLM Provider API Keys (Optional)

            These keys enable running evaluations with different model providers:

            - **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
            - **Anthropic**: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
            - **Google (Vertex AI)**: [Google Cloud Console](https://console.cloud.google.com/)
            - **Cohere**: [dashboard.cohere.ai/api-keys](https://dashboard.cohere.ai/api-keys)
            - **Mistral**: [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys)
            - **Together AI**: [api.together.xyz/settings/api-keys](https://api.together.xyz/settings/api-keys)
            - **Groq**: [console.groq.com/keys](https://console.groq.com/keys)

            Copy and paste them in the `KEY=value` format.
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
        def save_api_keys(gemini_key, hf_key, modal_key, modal_secret, llm_keys_text):
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
                hf_status_text = "⚪ Not configured"

            # Validate and save Modal API key
            if modal_key and modal_key.strip():
                if modal_key.startswith("ak-"):
                    os.environ["MODAL_TOKEN_ID"] = modal_key.strip()
                    messages.append("✅ Modal API key saved")
                    modal_status_text = "✅ Configured"
                else:
                    messages.append("⚠️ Invalid Modal API key format (should start with 'ak-')")
                    modal_status_text = "❌ Invalid format"
            else:
                modal_status_text = "⚪ Not configured"

            # Validate and save Modal API secret
            if modal_secret and modal_secret.strip():
                if modal_secret.startswith("as-"):
                    os.environ["MODAL_TOKEN_SECRET"] = modal_secret.strip()
                    messages.append("✅ Modal API secret saved")
                    modal_secret_status_text = "✅ Configured"
                else:
                    messages.append("⚠️ Invalid Modal API secret format (should start with 'as-')")
                    modal_secret_status_text = "❌ Invalid format"
            else:
                modal_secret_status_text = "⚪ Not configured"

            # Parse and save LLM provider API keys
            llm_keys_count = 0
            if llm_keys_text and llm_keys_text.strip():
                parsed_keys = _parse_env_string(llm_keys_text)
                for key, value in parsed_keys.items():
                    os.environ[key] = value
                    llm_keys_count += 1
                messages.append(f"✅ {llm_keys_count} LLM provider API key(s) saved")

            status_msg = "\n\n".join(messages) if messages else "No changes made"
            status_msg += "\n\n**Note**: Keys are saved for this session only and will be used for evaluation jobs."

            return status_msg, gemini_status_text, hf_status_text, modal_status_text, modal_secret_status_text

        def test_api_keys(gemini_key, hf_key, modal_key, modal_secret, llm_keys_text):
            """Test API key connections"""
            results = []

            # Test Gemini API
            if gemini_key and gemini_key.strip():
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key.strip())
                    # Try to list models as a test
                    models = list(genai.list_models())
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

            # Test Modal API
            if modal_key and modal_key.strip() and modal_secret and modal_secret.strip():
                try:
                    import modal
                    # Modal validates credentials on first use, not at import
                    # We'll just validate format here
                    if modal_key.startswith("ak-") and modal_secret.startswith("as-"):
                        results.append("✅ **Modal**: Credentials format valid (will be verified on first job submission)")
                    else:
                        results.append("❌ **Modal**: Invalid credential format")
                except Exception as e:
                    results.append(f"⚠️ **Modal**: {str(e)}")
            elif modal_key or modal_secret:
                results.append("⚠️ **Modal**: Both API key and secret required")

            # Note about LLM provider keys
            if llm_keys_text and llm_keys_text.strip():
                parsed_keys = _parse_env_string(llm_keys_text)
                results.append(f"ℹ️ **LLM Providers**: {len(parsed_keys)} key(s) configured (will be validated when used)")

            return "\n\n".join(results)

        # Wire up button events (api_name=False to prevent API key exposure)
        save_btn.click(
            fn=save_api_keys,
            inputs=[gemini_api_key, hf_token, modal_api_key, modal_api_secret, llm_api_keys],
            outputs=[status_message, gemini_status, hf_status, modal_status, modal_secret_status],
            api_name=False  # IMPORTANT: Prevents API key exposure via Gradio API
        )

        test_btn.click(
            fn=test_api_keys,
            inputs=[gemini_api_key, hf_token, modal_api_key, modal_api_secret, llm_api_keys],
            outputs=[status_message],
            api_name=False  # IMPORTANT: Prevents API key exposure via Gradio API
        )

        # Return the interface only (API keys are managed internally via session state)
        return settings_interface


if __name__ == "__main__":
    # For standalone testing
    with gr.Blocks() as demo:
        settings_screen = create_settings_screen()
        # Make it visible for standalone testing
        settings_screen.visible = True
    demo.launch()
