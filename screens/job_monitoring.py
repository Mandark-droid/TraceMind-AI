"""
Job Monitoring Screen for TraceMind-AI
Allows users to monitor HuggingFace Jobs status and view logs
"""

import gradio as gr
import os
from typing import Optional


def create_job_monitoring_screen():
    """
    Create the job monitoring screen for HF Jobs

    Returns:
        gr.Column: Gradio Column component for job monitoring
    """
    with gr.Column(visible=False) as job_monitoring_interface:
        gr.Markdown("""
        # 🔍 Job Monitoring

        Monitor your HuggingFace Jobs in real-time. Check job status, view logs, and track evaluation progress.
        """)

        with gr.Tabs():
            # Tab 1: Single Job Inspection
            with gr.Tab("📋 Inspect Job"):
                gr.Markdown("""
                ### Inspect a Specific Job

                Enter a HuggingFace Job ID to view its status and logs.
                """)

                with gr.Row():
                    job_id_input = gr.Textbox(
                        label="HF Job ID",
                        placeholder="e.g., kshitijthakkar/691eb073748f86bfa7144fcc",
                        info="Format: username/job_hash"
                    )

                with gr.Row():
                    inspect_btn = gr.Button("🔍 Inspect Job", variant="primary")
                    refresh_btn = gr.Button("🔄 Refresh", variant="secondary")

                # Job Status Section
                with gr.Accordion("📊 Job Status", open=True):
                    job_status_display = gr.Markdown("Enter a Job ID and click 'Inspect Job' to view status")

                # Job Logs Section
                with gr.Accordion("📜 Job Logs", open=True):
                    with gr.Row():
                        show_logs_btn = gr.Button("📥 Load Logs", variant="secondary")
                        auto_refresh_logs = gr.Checkbox(
                            label="Auto-refresh logs (every 5s)",
                            value=False
                        )

                    job_logs_display = gr.Code(
                        label="Job Logs",
                        language="shell",
                        value="Click 'Load Logs' to view job output",
                        lines=20
                    )

            # Tab 2: Recent Jobs List
            with gr.Tab("📑 Recent Jobs"):
                gr.Markdown("""
                ### Your Recent Jobs

                View a list of your recent HuggingFace Jobs.
                """)

                with gr.Row():
                    list_jobs_btn = gr.Button("📋 Load Recent Jobs", variant="primary")
                    jobs_limit = gr.Slider(
                        minimum=5,
                        maximum=50,
                        value=10,
                        step=5,
                        label="Number of jobs to fetch"
                    )

                recent_jobs_display = gr.Markdown("Click 'Load Recent Jobs' to view your jobs")

            # Tab 3: Job Monitoring Guide
            with gr.Tab("📖 Guide"):
                gr.Markdown("""
                ### Using Job Monitoring

                #### How to Get Your Job ID

                After submitting an evaluation from the "New Evaluation" tab, you'll receive:
                - **Run ID (SMOLTRACE)**: Used for tracking results in datasets (e.g., `job_3a22ceca`)
                - **HF Job ID**: Used for monitoring the actual job (e.g., `kshitijthakkar/691eb073748f86bfa7144fcc`)

                Use the **HF Job ID** here to monitor your job.

                #### Job Status Values

                - **QUEUED**: Job is waiting to start
                - **STARTING**: Job is being initialized
                - **RUNNING**: Job is currently executing
                - **SUCCEEDED**: Job completed successfully
                - **FAILED**: Job encountered an error
                - **CANCELLED**: Job was manually cancelled
                - **STOPPED**: Job was stopped by the system

                #### CLI Commands Reference

                You can also use the HuggingFace CLI to monitor jobs:

                ```bash
                # List your running jobs
                hf jobs ps

                # Inspect a specific job
                hf jobs inspect <job_id>

                # View logs from a job
                hf jobs logs <job_id>

                # Follow logs in real-time
                hf jobs logs <job_id> --follow

                # Cancel a job
                hf jobs cancel <job_id>
                ```

                #### Tips

                - 💡 **Bookmark your Job ID** after submission for easy access
                - 🔄 **Use auto-refresh** for logs when job is running
                - 📊 **Check status regularly** to catch any issues early
                - 📝 **Review logs** if your job fails to understand what went wrong
                - 🎯 **Results appear in leaderboard** once job succeeds and uploads datasets
                """)

        # Functions for job monitoring
        def inspect_job(job_id: str):
            """Inspect a specific job's status"""
            import os

            if not job_id or not job_id.strip():
                return gr.update(value="❌ Please enter a Job ID")

            # Check if token is configured before making API call
            token = os.environ.get("HF_TOKEN")
            if not token or not token.strip():
                return gr.update(
                    value="""
### ⚠️ HuggingFace Token Not Configured

**Action Required**:
1. Go to "⚙️ Settings" in the sidebar
2. Enter your HuggingFace token (must have "Run Jobs" permission)
3. Click "💾 Save API Keys"
4. Return to this tab and try again
                    """
                )

            from utils.hf_jobs_submission import check_job_status

            result = check_job_status(job_id.strip())

            if not result.get("success"):
                error_msg = result.get('error', 'Unknown error')

                return gr.update(
                    value=f"""
### ❌ Failed to Fetch Job Status

**Error**: {error_msg}

**Job ID**: `{job_id}`

**Troubleshooting**:
- Verify the Job ID format is correct (format: `username/job_hash`)
- Check that the job exists in your account
- Ensure your HF token has the correct permissions
- Token must have **Run Jobs** permission enabled
                    """
                )

            # Format status with emoji
            status = result.get("status", "unknown")
            # Convert status to string if it's an enum
            status_str = str(status).upper() if status else "UNKNOWN"

            status_emoji = {
                "QUEUED": "⏳",
                "STARTING": "🔄",
                "RUNNING": "▶️",
                "SUCCEEDED": "✅",
                "COMPLETED": "✅",  # Alternative success status
                "FAILED": "❌",
                "ERROR": "❌",  # Alternative failure status
                "CANCELLED": "🚫",
                "CANCELED": "🚫",  # US spelling variant
                "STOPPED": "⏹️",
                "TIMEOUT": "⏱️"
            }.get(status_str, "❓")

            status_color = {
                "QUEUED": "#FFA500",
                "STARTING": "#1E90FF",
                "RUNNING": "#00CED1",
                "SUCCEEDED": "#32CD32",
                "COMPLETED": "#32CD32",  # Alternative success status
                "FAILED": "#DC143C",
                "ERROR": "#DC143C",  # Alternative failure status
                "CANCELLED": "#696969",
                "CANCELED": "#696969",  # US spelling variant
                "STOPPED": "#A9A9A9",
                "TIMEOUT": "#FF8C00"
            }.get(status_str, "#888888")

            created_at = result.get("created_at", "N/A")
            flavor = result.get("flavor", "N/A")
            job_url = result.get("url", None)

            # Format job URL as clickable link
            job_url_display = f"[Open in HuggingFace]({job_url})" if job_url else "N/A"

            return gr.update(
                value=f"""
### {status_emoji} Job Status: <span style="color: {status_color};">{status_str}</span>

**Job ID**: `{job_id}`

#### Details

- **Created**: {created_at}
- **Hardware**: {flavor}
- **Job URL**: {job_url_display}

#### Next Steps

{_get_next_steps(status_str)}

---

💡 **Tip**: Use "📥 Load Logs" button below to view detailed execution logs and check progress.
                """
            )

        def _get_next_steps(status: str) -> str:
            """Get next steps based on job status"""
            status_upper = str(status).upper() if status else "UNKNOWN"

            if status_upper == "QUEUED":
                return "⏳ Your job is waiting in the queue. It will start soon."
            elif status_upper == "STARTING":
                return "🔄 Your job is being initialized. This usually takes 1-2 minutes."
            elif status_upper == "RUNNING":
                return "▶️ Your job is running! Click 'Load Logs' below to view progress."
            elif status_upper in ["SUCCEEDED", "COMPLETED"]:
                return "✅ Your job completed successfully! Check the Leaderboard tab for results."
            elif status_upper in ["FAILED", "ERROR"]:
                return "❌ Your job failed. Click 'Load Logs' below to see what went wrong."
            elif status_upper in ["CANCELLED", "CANCELED", "STOPPED"]:
                return "🚫 Your job was stopped. You can submit a new job from the 'New Evaluation' tab."
            elif status_upper == "TIMEOUT":
                return "⏱️ Your job exceeded the time limit. Consider optimizing your model or increasing the timeout."
            else:
                return "❓ Unknown status. Try refreshing or check the HF Jobs dashboard."

        def load_job_logs(job_id: str):
            """Load logs for a specific job"""
            import os

            if not job_id or not job_id.strip():
                return gr.update(value="❌ Please enter a Job ID first")

            # Check if token is configured before making API call
            token = os.environ.get("HF_TOKEN")
            if not token or not token.strip():
                return gr.update(
                    value="⚠️ HuggingFace Token Not Configured\n\nPlease configure your HF token in Settings first."
                )

            from utils.hf_jobs_submission import get_job_logs

            result = get_job_logs(job_id.strip())

            if not result.get("success"):
                return gr.update(
                    value=f"❌ Failed to fetch logs: {result.get('error', 'Unknown error')}\n\nEnsure your HF token has 'Run Jobs' permission."
                )

            logs = result.get("logs", "")
            if not logs or not logs.strip():
                return gr.update(value="ℹ️ No logs available yet. Job may not have started.\n\nTry refreshing after a minute.")

            return gr.update(value=logs)

        def list_recent_jobs(limit: int):
            """List user's recent jobs"""
            import os
            from utils.hf_jobs_submission import list_user_jobs

            # Check if token is configured before making API call
            token = os.environ.get("HF_TOKEN")
            if not token or not token.strip():
                return gr.update(
                    value="""
### ⚠️ HuggingFace Token Not Configured

**Action Required**:
1. Go to "⚙️ Settings" in the sidebar
2. Enter your HuggingFace token (must have "Run Jobs" permission)
3. Click "💾 Save API Keys"
4. Return to this tab and try again

**Note**: Your HF token must:
- Start with `hf_`
- Have **Read**, **Write**, AND **Run Jobs** permissions
- Be from a HuggingFace Pro account ($9/month)

Get your token at: https://huggingface.co/settings/tokens
                    """
                )

            result = list_user_jobs(limit=int(limit))

            if not result.get("success"):
                error_msg = result.get('error', 'Unknown error')

                # Check for common error patterns
                if "invalid" in error_msg.lower() or "token" in error_msg.lower():
                    troubleshooting = """
**Troubleshooting**:
- ⚠️ **Token may be invalid** - Regenerate your token at HuggingFace settings
- ✅ Ensure token has **Run Jobs** permission (not just Read/Write)
- ✅ Verify you have an active **HuggingFace Pro account**
- ✅ Token should start with `hf_`
                    """
                else:
                    troubleshooting = """
**Troubleshooting**:
- Refresh this page and try again
- Check your internet connection
- Verify HuggingFace services are operational
                    """

                return gr.update(
                    value=f"""
### ❌ Failed to Fetch Jobs

**Error**: {error_msg}

{troubleshooting}
                    """
                )

            jobs = result.get("jobs", [])
            if not jobs:
                return gr.update(
                    value="""
### ℹ️ No Jobs Found

You haven't submitted any jobs yet.

**Get Started**:
1. Go to the "New Evaluation" tab
2. Configure your model and settings
3. Submit an evaluation job
4. Come back here to monitor progress!
                    """
                )

            # Build jobs table
            jobs_table = "### 📋 Your Recent Jobs\n\n"
            jobs_table += "| Job ID | Status | Created At |\n"
            jobs_table += "|--------|--------|------------|\n"

            for job in jobs:
                job_id = job.get("job_id", "N/A")
                status = job.get("status", "unknown")
                created = job.get("created_at", "N/A")

                # Convert status to string if it's an enum
                status_str = str(status).upper() if status else "UNKNOWN"

                status_emoji = {
                    "QUEUED": "⏳",
                    "STARTING": "🔄",
                    "RUNNING": "▶️",
                    "SUCCEEDED": "✅",
                    "COMPLETED": "✅",  # Alternative success status
                    "FAILED": "❌",
                    "ERROR": "❌",  # Alternative failure status
                    "CANCELLED": "🚫",
                    "CANCELED": "🚫",  # US spelling variant
                    "STOPPED": "⏹️",
                    "TIMEOUT": "⏱️"
                }.get(status_str, "❓")

                jobs_table += f"| `{job_id}` | {status_emoji} {status} | {created} |\n"

            jobs_table += f"\n**Total Jobs**: {len(jobs)}\n\n"
            jobs_table += "💡 **Tip**: Copy a Job ID and paste it in the 'Inspect Job' tab to view details and logs."

            return gr.update(value=jobs_table)

        # Wire up button events
        inspect_btn.click(
            fn=inspect_job,
            inputs=[job_id_input],
            outputs=[job_status_display]
        )

        refresh_btn.click(
            fn=inspect_job,
            inputs=[job_id_input],
            outputs=[job_status_display]
        )

        show_logs_btn.click(
            fn=load_job_logs,
            inputs=[job_id_input],
            outputs=[job_logs_display]
        )

        list_jobs_btn.click(
            fn=list_recent_jobs,
            inputs=[jobs_limit],
            outputs=[recent_jobs_display]
        )

        # Auto-refresh functionality (handled by Gradio's auto-update)
        # Note: For production, consider using gr.Timer or similar for automatic refreshes

        return job_monitoring_interface


if __name__ == "__main__":
    # For standalone testing
    with gr.Blocks() as demo:
        job_monitoring = create_job_monitoring_screen()
        # Make it visible for standalone testing
        job_monitoring.visible = True
    demo.launch()
