"""
TraceMind CSS Theme
Central CSS variables and global styling for consistent theming
"""

def get_tracemind_css():
    """
    Return the complete CSS for TraceMind with CSS variables

    Features:
    - Dark theme optimized
    - CSS variables for easy theming
    - Responsive design support
    - Smooth transitions
    """
    return """
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* TraceMind CSS Variables */
    :root {
        /* Primary Brand Colors */
        --tm-primary: #4F46E5;           /* Indigo 600 - Main brand */
        --tm-secondary: #06B6D4;         /* Cyan 500 - Accents */

        /* Semantic Colors */
        --tm-success: #10B981;           /* Green 500 - High scores, success */
        --tm-warning: #F59E0B;           /* Amber 500 - Medium scores, warnings */
        --tm-danger: #EF4444;            /* Red 500 - Low scores, errors */
        --tm-info: #3B82F6;              /* Blue 500 - Info, API badge */

        /* Background Colors (Dark Theme) */
        --tm-bg-dark: #0F172A;           /* Slate 900 - App background */
        --tm-bg-card: #1E293B;           /* Slate 800 - Card background */
        --tm-bg-secondary: #334155;      /* Slate 700 - Secondary elements */
        --tm-bg-hover: rgba(79, 70, 229, 0.15);  /* Hover overlay */
        --tm-bg-stripe: rgba(30, 41, 59, 0.5);   /* Table row stripe */

        /* Text Colors */
        --tm-text-primary: #F1F5F9;      /* Slate 100 - Primary text */
        --tm-text-secondary: #94A3B8;    /* Slate 400 - Secondary text */
        --tm-text-muted: #64748B;        /* Slate 500 - Muted text */

        /* Border Colors */
        --tm-border-subtle: rgba(148, 163, 184, 0.1);
        --tm-border-default: rgba(148, 163, 184, 0.2);
        --tm-border-strong: rgba(148, 163, 184, 0.4);

        /* Badge Colors */
        --tm-badge-tool: #8B5CF6;        /* Purple 500 - Tool agent */
        --tm-badge-code: #F59E0B;        /* Amber 500 - Code agent */
        --tm-badge-both: #06B6D4;        /* Cyan 500 - Both agent */
        --tm-badge-api: #3B82F6;         /* Blue 500 - API provider */
        --tm-badge-gpu: #10B981;         /* Green 500 - GPU provider */

        /* Gradient Definitions */
        --tm-gradient-success: linear-gradient(90deg, #10B981, #06B6D4);
        --tm-gradient-warning: linear-gradient(90deg, #F59E0B, #FBBF24);
        --tm-gradient-danger: linear-gradient(90deg, #EF4444, #F59E0B);
        --tm-gradient-gold: linear-gradient(145deg, #ffd700, #ffc400);
        --tm-gradient-silver: linear-gradient(145deg, #9ca3af, #787C7E);
        --tm-gradient-bronze: linear-gradient(145deg, #CD7F32, #b36a1d);

        /* Shadows */
        --tm-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
        --tm-shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
        --tm-shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
        --tm-shadow-glow: 0 0 20px rgba(79, 70, 229, 0.3);
    }

    /* Global Styles */
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        background: var(--tm-bg-dark) !important;
        color: var(--tm-text-primary) !important;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--tm-text-primary) !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Links */
    a {
        color: var(--tm-secondary) !important;
        text-decoration: none !important;
        transition: color 0.2s ease;
    }

    a:hover {
        color: var(--tm-primary) !important;
    }

    /* Buttons */
    button {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--tm-shadow-lg) !important;
    }

    /* Smooth transitions for all interactive elements */
    * {
        transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--tm-bg-secondary);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--tm-secondary);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--tm-primary);
    }

    /* Responsive breakpoints */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 8px !important;
        }

        h1 {
            font-size: 1.5rem !important;
        }

        h2 {
            font-size: 1.25rem !important;
        }

        h3 {
            font-size: 1.1rem !important;
        }
    }

    @media (max-width: 480px) {
        .gradio-container {
            padding: 4px !important;
        }
    }

    /* Modal Dialog Styles */
    .modal-dialog {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        z-index: 9999 !important;
        background: var(--tm-bg-card) !important;
        border: 2px solid var(--tm-border-strong) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5) !important;
        max-width: 800px !important;
        width: 90% !important;
        max-height: 90vh !important;
        overflow-y: auto !important;
    }

    /* Modal backdrop */
    .modal-dialog::before {
        content: '' !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background: rgba(0, 0, 0, 0.7) !important;
        z-index: -1 !important;
    }

    /* Specific dialog IDs for additional customization */
    #new-eval-dialog,
    #export-dialog {
        animation: modalFadeIn 0.3s ease-out !important;
    }

    @keyframes modalFadeIn {
        from {
            opacity: 0;
            transform: translate(-50%, -55%);
        }
        to {
            opacity: 1;
            transform: translate(-50%, -50%);
        }
    }
    </style>
    """
