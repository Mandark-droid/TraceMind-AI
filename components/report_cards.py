"""
Report Cards Component
Generate downloadable summary cards for leaderboard and runs
"""

import pandas as pd
from datetime import datetime
from typing import Optional
import base64
from pathlib import Path


def _get_logo_base64():
    """Load and encode TraceMind logo as base64"""
    try:
        # Try local file first (for development and GitHub)
        logo_path = Path(__file__).parent.parent / "Logo.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()

        # Fallback: fetch from GitHub raw URL (for HuggingFace Spaces)
        import urllib.request
        github_logo_url = "https://raw.githubusercontent.com/Mandark-droid/TraceMind-AI/main/Logo.png"
        with urllib.request.urlopen(github_logo_url, timeout=5) as response:
            return base64.b64encode(response.read()).decode()

    except Exception as e:
        print(f"Warning: Could not load logo: {e}")
    return None


def generate_leaderboard_summary_card(df: pd.DataFrame, top_n: int = 3) -> str:
    """
    Generate HTML for leaderboard summary card

    Args:
        df: Leaderboard DataFrame
        top_n: Number of top performers to show

    Returns:
        HTML string for summary card
    """

    if df.empty:
        return _create_empty_card_html("No leaderboard data available")

    # Get top performers by success rate
    top_models = df.nlargest(top_n, 'success_rate') if 'success_rate' in df.columns else df.head(top_n)

    # Get logo
    logo_base64 = _get_logo_base64()

    # Card header
    html = f"""
    <div class="tracemind-summary-card" id="summary-card-html">
        <div class="card-header">
            {f'<img src="data:image/png;base64,{logo_base64}" alt="TraceMind Logo" class="card-logo" style="display: block !important; margin: 0 auto 15px auto !important; width: 120px !important; height: auto !important;" />' if logo_base64 else ''}
            <h1>🧠 TraceMind Agent Evaluation Leaderboard</h1>
            <p class="card-date" style="color: #ffffff !important;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>

        <div class="card-body">
            <h2 style="color: #ffffff !important;">🏆 Top Performers</h2>
    """

    # Top models
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for idx, (_, row) in enumerate(top_models.iterrows()):
        if idx >= top_n:
            break

        model_name = row['model'].split('/')[-1] if '/' in str(row['model']) else str(row['model'])

        html += f"""
            <div class="top-model">
                <div class="model-rank">{medals[idx]}</div>
                <div class="model-info">
                    <h3 style="color: #ffffff !important;">{model_name}</h3>
                    <div class="model-metrics">
        """

        # Add metrics
        if 'success_rate' in row and pd.notna(row['success_rate']):
            html += f'<span class="metric" style="color: #ffffff !important;">✓ {row["success_rate"]:.1f}% Success Rate</span>'

        if 'avg_duration_ms' in row and pd.notna(row['avg_duration_ms']):
            duration_s = row['avg_duration_ms'] / 1000
            html += f'<span class="metric" style="color: #ffffff !important;">⚡ {duration_s:.1f}s Avg Duration</span>'

        if 'total_cost_usd' in row and pd.notna(row['total_cost_usd']):
            html += f'<span class="metric" style="color: #ffffff !important;">💰 ${row["total_cost_usd"]:.4f} per run</span>'

        # Add GPU metrics if available
        if 'co2_emissions_g' in row and pd.notna(row['co2_emissions_g']):
            html += f'<span class="metric" style="color: #ffffff !important;">🌱 {row["co2_emissions_g"]:.2f}g CO2</span>'

        if 'gpu_utilization_avg' in row and pd.notna(row['gpu_utilization_avg']):
            html += f'<span class="metric" style="color: #ffffff !important;">🎮 {row["gpu_utilization_avg"]:.1f}% GPU Util</span>'

        html += """
                    </div>
                </div>
            </div>
        """

    # Aggregate stats
    total_runs = len(df)
    unique_models = df['model'].nunique() if 'model' in df.columns else 0
    avg_success = df['success_rate'].mean() if 'success_rate' in df.columns else 0

    html += f"""
            <div class="card-stats">
                <h2 style="color: #ffffff !important;">📊 Leaderboard Stats</h2>
                <ul>
                    <li style="color: #ffffff !important;">• {total_runs} total evaluation runs</li>
                    <li style="color: #ffffff !important;">• {unique_models} unique models tested</li>
                    <li style="color: #ffffff !important;">• {avg_success:.1f}% average success rate</li>
    """

    # Add cost stats if available
    if 'total_cost_usd' in df.columns:
        total_cost = df['total_cost_usd'].sum()
        html += f'<li style="color: #ffffff !important;">• ${total_cost:.2f} total evaluation cost</li>'

    # Add CO2 stats if available
    if 'co2_emissions_g' in df.columns:
        total_co2 = df['co2_emissions_g'].sum()
        html += f'<li style="color: #ffffff !important;">• {total_co2:.2f}g total CO2 emissions</li>'

    html += """
                </ul>
            </div>
        </div>

        <div class="card-footer">
            <p style="margin: 0; color: #ffffff !important;">🔗 <a href="https://huggingface.co/tracemind" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-decoration: none; font-weight: 600;">tracemind @ HuggingFace</a></p>
            <p class="tagline" style="color: rgba(255, 255, 255, 0.7) !important; margin: 10px 0 0 0; font-size: 0.9em;">Built with TraceMind • Powered by SmolTrace & TraceVerde</p>
        </div>
    </div>
    """

    # Add CSS
    html += _get_card_css()

    return html


def generate_run_report_card(run_data: dict) -> str:
    """
    Generate HTML for individual run report card

    Args:
        run_data: Dictionary with run information

    Returns:
        HTML string for run report card
    """

    if not run_data:
        return _create_empty_card_html("No run data available")

    model_name = run_data.get('model', 'Unknown Model')
    model_display = model_name.split('/')[-1] if '/' in model_name else model_name

    run_id = run_data.get('run_id', 'unknown')
    timestamp = run_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M'))

    # Get logo
    logo_base64 = _get_logo_base64()

    html = f"""
    <div class="tracemind-run-card" id="run-card-html">
        <div class="card-header">
            {f'<img src="data:image/png;base64,{logo_base64}" alt="TraceMind Logo" class="card-logo" style="display: block !important; margin: 0 auto 15px auto !important; width: 120px !important; height: auto !important;" />' if logo_base64 else ''}
            <h1>🤖 {model_display} Evaluation Report</h1>
            <p class="card-meta" style="color: rgba(255, 255, 255, 0.7) !important;">Run ID: {run_id}</p>
            <p class="card-date" style="color: rgba(255, 255, 255, 0.7) !important;">{timestamp}</p>
        </div>

        <div class="card-body">
    """

    # Success rate visualization
    success_rate = run_data.get('success_rate', 0)
    stars = "⭐" * int(success_rate / 20)  # 5 stars max

    html += f"""
            <div class="success-section">
                <div class="stars">{stars}</div>
                <div class="success-rate" style="color: #ffffff !important;">{success_rate:.1f}% Success Rate</div>
            </div>
    """

    # Performance metrics
    html += """
            <div class="metrics-section">
                <h2 style="color: #ffffff !important;">📊 Performance Metrics</h2>
                <ul class="metrics-list">
    """

    if 'successful_tests' in run_data and 'total_tests' in run_data:
        html += f'<li style="color: #ffffff !important;">Tests: {run_data["successful_tests"]}/{run_data["total_tests"]} passed</li>'

    if 'avg_steps' in run_data:
        html += f'<li style="color: #ffffff !important;">Avg Steps: {run_data["avg_steps"]:.1f} per test</li>'

    if 'avg_duration_ms' in run_data:
        duration_s = run_data['avg_duration_ms'] / 1000
        html += f'<li style="color: #ffffff !important;">Avg Duration: {duration_s:.1f}s</li>'

    if 'total_duration_ms' in run_data:
        total_duration = run_data['total_duration_ms'] / 1000
        mins = int(total_duration // 60)
        secs = int(total_duration % 60)
        html += f'<li style="color: #ffffff !important;">Total Duration: {mins}m {secs}s</li>'

    html += """
                </ul>
            </div>
    """

    # Cost analysis
    if 'total_tokens' in run_data or 'total_cost_usd' in run_data:
        html += """
            <div class="metrics-section">
                <h2 style="color: #ffffff !important;">💰 Cost Analysis</h2>
                <ul class="metrics-list">
        """

        if 'total_tokens' in run_data:
            html += f'<li style="color: #ffffff !important;">Total Tokens: {run_data["total_tokens"]:,}</li>'

        if 'total_cost_usd' in run_data:
            html += f'<li style="color: #ffffff !important;">Total Cost: ${run_data["total_cost_usd"]:.4f}</li>'

        if 'avg_cost_per_test_usd' in run_data:
            html += f'<li style="color: #ffffff !important;">Cost per Test: ${run_data["avg_cost_per_test_usd"]:.6f}</li>'

        html += """
                </ul>
            </div>
        """

    # Sustainability
    if 'co2_emissions_g' in run_data or 'provider' in run_data:
        html += """
            <div class="metrics-section">
                <h2 style="color: #ffffff !important;">🌱 Sustainability</h2>
                <ul class="metrics-list">
        """

        if 'co2_emissions_g' in run_data:
            html += f'<li style="color: #ffffff !important;">CO2 Emissions: {run_data["co2_emissions_g"]:.2f}g</li>'

        if 'provider' in run_data:
            provider_label = "API" if run_data['provider'] == 'litellm' else "GPU"
            html += f'<li style="color: #ffffff !important;">Provider: {run_data["provider"]} ({provider_label})</li>'

        if 'gpu_utilization_avg' in run_data and pd.notna(run_data['gpu_utilization_avg']):
            html += f'<li style="color: #ffffff !important;">GPU Utilization: {run_data["gpu_utilization_avg"]:.1f}%</li>'

        html += """
                </ul>
            </div>
        """

    # Footer
    html += f"""
        </div>

        <div class="card-footer">
            <p style="margin: 0; color: #ffffff !important;">🔗 <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 600;">View detailed traces at tracemind.huggingface.co</span></p>
        </div>
    </div>
    """

    # Add CSS
    html += _get_card_css()

    return html


def download_card_as_png_js(element_id: str = "summary-card-html") -> str:
    """
    JavaScript to convert HTML card to PNG using html2canvas

    Args:
        element_id: ID of the HTML element to capture

    Returns:
        JavaScript code as string
    """

    return f"""
    () => {{
        // Load html2canvas from CDN if not already loaded
        if (typeof html2canvas === 'undefined') {{
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
            script.onload = captureCard;
            document.head.appendChild(script);
        }} else {{
            captureCard();
        }}

        function captureCard() {{
            console.log('Searching for card element...');

            // Try multiple strategies to find the card
            let card = document.getElementById('{element_id}');

            if (!card) {{
                console.log('ID not found, trying class selectors...');
                card = document.querySelector('.tracemind-run-card, .tracemind-comparison-card, .tracemind-summary-card');
            }}

            if (!card) {{
                console.log('Class not found, trying summary-card-html...');
                card = document.getElementById('summary-card-html');
            }}

            if (!card) {{
                console.log('Still not found, searching all elements with tracemind in class...');
                const cards = document.querySelectorAll('[class*="tracemind"]');
                console.log('Found elements:', cards.length);
                cards.forEach((el, i) => console.log(`Card ${{i}}:`, el.className, el.id));
                if (cards.length > 0) {{
                    card = cards[0];
                }}
            }}

            if (!card) {{
                console.error('Card element not found anywhere!');
                console.log('All IDs on page:', Array.from(document.querySelectorAll('[id]')).map(el => el.id));
                alert('Card element not found. Please make sure you selected a run first.');
                return;
            }}

            console.log('Found card:', card);
            console.log('Card content length:', card.innerHTML?.length || 0);

            // Clone the card to avoid modifying the original
            const cardClone = card.cloneNode(true);
            cardClone.style.position = 'absolute';
            cardClone.style.left = '-9999px';
            cardClone.style.top = '0';
            document.body.appendChild(cardClone);

            // Force all text elements to white in the clone
            const textElements = cardClone.querySelectorAll('h1, h2, h3, p, li, span, a, div');
            textElements.forEach(el => {{
                // Skip elements with gradient text (background-clip: text)
                const computedStyle = window.getComputedStyle(el);
                const hasGradientText = computedStyle.webkitBackgroundClip === 'text' ||
                                       computedStyle.backgroundClip === 'text' ||
                                       el.style.webkitBackgroundClip === 'text' ||
                                       el.style.backgroundClip === 'text';

                if (!hasGradientText) {{
                    el.style.color = '#ffffff';
                    el.style.setProperty('color', '#ffffff', 'important');
                }}
            }});

            // Ensure background is black
            cardClone.style.backgroundColor = '#000000';
            cardClone.style.setProperty('background-color', '#000000', 'important');

            html2canvas(cardClone, {{
                backgroundColor: '#000000',
                scale: 2,
                logging: false,
                useCORS: true,
                allowTaint: true
            }}).then(canvas => {{
                // Remove the clone
                document.body.removeChild(cardClone);

                console.log('Canvas size:', canvas.width, 'x', canvas.height);
                const link = document.createElement('a');
                const timestamp = new Date().toISOString().slice(0, 10);
                link.download = `tracemind-report-${{timestamp}}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();
            }}).catch(err => {{
                // Remove the clone on error
                if (document.body.contains(cardClone)) {{
                    document.body.removeChild(cardClone);
                }}
                console.error('Error capturing card:', err);
                alert('Failed to download card: ' + err.message);
            }});
        }}
    }}
    """


def _create_empty_card_html(message: str) -> str:
    """Create empty card with message"""
    return f"""
    <div class="tracemind-summary-card" id="summary-card-html">
        <div class="card-body" style="text-align: center; padding: 40px;">
            <p style="color: #666; font-size: 1.2em;">{message}</p>
        </div>
    </div>
    {_get_card_css()}
    """


def _get_card_css() -> str:
    """Get CSS for summary cards"""
    return """
    <style>
    .tracemind-summary-card, .tracemind-run-card {
        background: #000000 !important;
        border: 3px solid #667eea;
        border-radius: 24px;
        padding: 40px;
        max-width: 700px;
        margin: 20px auto;
        color: #ffffff !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    .card-header {
        text-align: center;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 20px;
        margin-bottom: 30px;
    }

    .card-logo {
        width: 120px;
        height: auto;
        margin: 0 auto 15px auto;
        display: block;
        filter: brightness(1.1);
    }

    .card-header h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2em;
        margin: 0 0 10px 0;
        font-weight: bold;
    }

    .card-date, .card-meta {
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 0.9em;
        margin: 5px 0;
    }

    .card-body {
        padding: 0;
    }

    .card-body h2 {
        color: #ffffff !important;
        font-size: 1.4em;
        margin: 25px 0 15px 0;
        font-weight: 600;
    }

    .top-model {
        display: flex;
        gap: 16px;
        align-items: flex-start;
        margin: 20px 0;
        padding: 20px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border-left: 4px solid #667eea;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .top-model:hover {
        transform: translateX(5px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }

    .model-rank {
        font-size: 2.5rem;
        line-height: 1;
    }

    .model-info {
        flex: 1;
    }

    .model-info h3 {
        color: #ffffff !important;
        margin: 0 0 10px 0;
        font-size: 1.2em;
        font-weight: 600;
    }

    .model-metrics {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .model-metrics .metric, .model-metrics span {
        font-size: 0.95em;
        color: #ffffff !important;
        line-height: 1.4;
    }

    .success-section {
        text-align: center;
        margin: 30px 0;
        padding: 20px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
    }

    .stars {
        font-size: 2.5em;
        margin-bottom: 10px;
    }

    .success-rate {
        font-size: 2em;
        font-weight: bold;
        color: #ffffff !important;
    }

    .metrics-section {
        margin: 25px 0;
    }

    .metrics-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .metrics-list li {
        padding: 10px 0;
        color: #ffffff !important;
        font-size: 1em;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .metrics-list li:last-child {
        border-bottom: none;
    }

    .card-stats {
        margin-top: 35px;
        padding-top: 25px;
        border-top: 2px solid rgba(255, 255, 255, 0.2);
    }

    .card-stats ul {
        list-style: none;
        padding: 0;
        margin: 15px 0 0 0;
    }

    .card-stats li {
        color: #ffffff !important;
        font-size: 1em;
        padding: 8px 0;
        line-height: 1.6;
    }

    .card-footer {
        margin-top: 35px;
        text-align: center;
        padding-top: 25px;
        border-top: 2px solid rgba(255, 255, 255, 0.2);
    }

    .card-footer a {
        color: #ffffff !important;
        text-decoration: none;
        font-weight: 600;
        transition: opacity 0.2s;
    }

    .card-footer a:hover {
        opacity: 0.8;
    }

    .card-footer p {
        color: #ffffff !important;
    }

    .tagline {
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 0.9em;
        margin: 10px 0 0 0;
    }
    </style>
    """


def generate_comparison_report_card(run_a_data: dict, run_b_data: dict) -> str:
    """
    Generate HTML for comparison report card showing two runs side by side

    Args:
        run_a_data: Dictionary with Run A information
        run_b_data: Dictionary with Run B information

    Returns:
        HTML string for comparison report card
    """

    if not run_a_data or not run_b_data:
        return _create_empty_card_html("Missing run data for comparison")

    model_a = run_a_data.get('model', 'Unknown').split('/')[-1]
    model_b = run_b_data.get('model', 'Unknown').split('/')[-1]

    # Get logo
    logo_base64 = _get_logo_base64()

    # Determine winners for each metric
    success_winner = "A" if run_a_data.get('success_rate', 0) > run_b_data.get('success_rate', 0) else "B"
    cost_winner = "A" if run_a_data.get('total_cost_usd', 999) < run_b_data.get('total_cost_usd', 999) else "B"
    speed_winner = "A" if run_a_data.get('avg_duration_ms', 999999) < run_b_data.get('avg_duration_ms', 999999) else "B"
    eco_winner = "A" if run_a_data.get('co2_emissions_g', 999) < run_b_data.get('co2_emissions_g', 999) else "B"

    # Count overall wins
    a_wins = sum(1 for w in [success_winner, cost_winner, speed_winner, eco_winner] if w == "A")
    b_wins = 4 - a_wins
    overall_winner = "A" if a_wins > b_wins else ("B" if b_wins > a_wins else "Tie")

    html = f"""
    <div class="tracemind-comparison-card" id="comparison-card-content">
        <div class="card-header">
            {f'<img src="data:image/png;base64,{logo_base64}" alt="TraceMind Logo" class="card-logo" style="display: block !important; margin: 0 auto 15px auto !important; width: 120px !important; height: auto !important;" />' if logo_base64 else ''}
            <h1>⚖️ Model Comparison Report</h1>
            <p class="card-meta" style="color: rgba(255, 255, 255, 0.7) !important;">{model_a} vs {model_b}</p>
            <p class="card-date" style="color: rgba(255, 255, 255, 0.7) !important;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>

        <div class="card-body">
            <!-- Overall Winner -->
            <div class="success-section">
                <div class="stars">{'🏆' * 5}</div>
                <div class="success-rate" style="color: #ffffff !important;">
                    Overall Winner: Run {overall_winner} ({a_wins if overall_winner == "A" else b_wins}/4 categories)
                </div>
            </div>

            <!-- Side by Side Comparison -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <!-- Run A -->
                <div style="padding: 15px; background: rgba(102, 126, 234, 0.1); border-radius: 8px; border: 2px solid {'#00ff00' if overall_winner == "A" else '#667eea'};">
                    <h3 style="color: #667eea !important; margin-top: 0;">Run A: {model_a}</h3>
                    <div class="metrics-list">
                        <div style="color: {'#00ff00' if success_winner == "A" else '#ffffff'} !important; font-weight: {'bold' if success_winner == "A" else 'normal'};">
                            {'✅' if success_winner == "A" else '📊'} Success: {run_a_data.get('success_rate', 0):.1f}%
                        </div>
                        <div style="color: {'#00ff00' if cost_winner == "A" else '#ffffff'} !important; font-weight: {'bold' if cost_winner == "A" else 'normal'};">
                            {'✅' if cost_winner == "A" else '💰'} Cost: ${run_a_data.get('total_cost_usd', 0):.4f}
                        </div>
                        <div style="color: {'#00ff00' if speed_winner == "A" else '#ffffff'} !important; font-weight: {'bold' if speed_winner == "A" else 'normal'};">
                            {'✅' if speed_winner == "A" else '⚡'} Speed: {run_a_data.get('avg_duration_ms', 0)/1000:.2f}s
                        </div>
                        <div style="color: {'#00ff00' if eco_winner == "A" else '#ffffff'} !important; font-weight: {'bold' if eco_winner == "A" else 'normal'};">
                            {'✅' if eco_winner == "A" else '🌱'} CO2: {run_a_data.get('co2_emissions_g', 0):.2f}g
                        </div>
                    </div>
                </div>

                <!-- Run B -->
                <div style="padding: 15px; background: rgba(118, 75, 162, 0.1); border-radius: 8px; border: 2px solid {'#00ff00' if overall_winner == "B" else '#764ba2'};">
                    <h3 style="color: #764ba2 !important; margin-top: 0;">Run B: {model_b}</h3>
                    <div class="metrics-list">
                        <div style="color: {'#00ff00' if success_winner == "B" else '#ffffff'} !important; font-weight: {'bold' if success_winner == "B" else 'normal'};">
                            {'✅' if success_winner == "B" else '📊'} Success: {run_b_data.get('success_rate', 0):.1f}%
                        </div>
                        <div style="color: {'#00ff00' if cost_winner == "B" else '#ffffff'} !important; font-weight: {'bold' if cost_winner == "B" else 'normal'};">
                            {'✅' if cost_winner == "B" else '💰'} Cost: ${run_b_data.get('total_cost_usd', 0):.4f}
                        </div>
                        <div style="color: {'#00ff00' if speed_winner == "B" else '#ffffff'} !important; font-weight: {'bold' if speed_winner == "B" else 'normal'};">
                            {'✅' if speed_winner == "B" else '⚡'} Speed: {run_b_data.get('avg_duration_ms', 0)/1000:.2f}s
                        </div>
                        <div style="color: {'#00ff00' if eco_winner == "B" else '#ffffff'} !important; font-weight: {'bold' if eco_winner == "B" else 'normal'};">
                            {'✅' if eco_winner == "B" else '🌱'} CO2: {run_b_data.get('co2_emissions_g', 0):.2f}g
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recommendation -->
            <div class="metrics-section">
                <h2 style="color: #ffffff !important;">💡 Recommendation</h2>
                <p style="color: #ffffff !important; font-size: 1.1em;">
                    {f"<strong style='color: #ffffff !important;'>Run {overall_winner}</strong> ({model_a if overall_winner == 'A' else model_b}) is recommended for most use cases" if overall_winner != "Tie" else "Both runs are evenly matched - choose based on your specific priorities"}
                </p>
            </div>
        </div>

        <div class="card-footer">
            <p style="margin: 0; color: #ffffff !important;">🔗 <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 600;">View detailed comparison at tracemind.huggingface.co</span></p>
        </div>
    </div>

    <style>
    .tracemind-comparison-card {{
        background: #000000 !important;
        border: 3px solid #667eea;
        border-radius: 24px;
        padding: 40px;
        max-width: 900px;
        margin: 20px auto;
        color: #ffffff !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }}

    .tracemind-comparison-card .card-header {{
        text-align: center;
        margin-bottom: 25px;
    }}

    .tracemind-comparison-card h1 {{
        color: white !important;
        font-size: 2em !important;
        margin: 10px 0 !important;
        font-weight: 700 !important;
    }}

    .tracemind-comparison-card .metrics-section h2 {{
        font-size: 1.3em !important;
        margin: 15px 0 10px 0 !important;
        font-weight: 600 !important;
    }}

    .tracemind-comparison-card .metrics-list {{
        margin: 10px 0;
        padding: 0;
        list-style: none;
    }}

    .tracemind-comparison-card .metrics-list div {{
        padding: 8px 0;
        font-size: 1em;
    }}

    .tracemind-comparison-card .card-footer {{
        margin-top: 25px;
        padding-top: 20px;
        border-top: 2px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    }}
    </style>
    """

    return html
