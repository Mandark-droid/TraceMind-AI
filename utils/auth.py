"""
HuggingFace Authentication for MockTraceMind
Using Gradio's built-in OAuth support (simpler than manual OAuth)
"""

import os
import gradio as gr
from typing import Optional
from dataclasses import dataclass

# Development mode flag - set DISABLE_OAUTH=true to skip OAuth for local dev
DEV_MODE = os.getenv("DISABLE_OAUTH", "false").lower() in ("true", "1", "yes")


@dataclass
class User:
    """Authenticated user information"""
    username: str
    name: str
    avatar_url: str
    token: str

    @classmethod
    def from_oauth(cls, token: gr.OAuthToken, profile: gr.OAuthProfile) -> "User":
        """Create User from Gradio OAuth objects"""
        return cls(
            username=profile.username,
            name=profile.name,
            avatar_url=profile.picture,
            token=str(token)
        )

    @classmethod
    def create_dev_user(cls) -> "User":
        """Create a mock user for development mode"""
        return cls(
            username=os.getenv("DEV_USERNAME", "dev_user"),
            name=os.getenv("DEV_NAME", "Development User"),
            avatar_url="https://huggingface.co/avatars/default-avatar.png",
            token="dev_token_12345"
        )


def is_authenticated(token: gr.OAuthToken | None, profile: gr.OAuthProfile | None) -> bool:
    """
    Check if user is authenticated

    Args:
        token: OAuth token from Gradio
        profile: OAuth profile from Gradio

    Returns:
        True if both token and profile are valid, or if in dev mode
    """
    # In dev mode, always consider authenticated
    if DEV_MODE:
        return True

    return token is not None and profile is not None


def get_user_info(token: gr.OAuthToken | None, profile: gr.OAuthProfile | None) -> Optional[User]:
    """
    Get user information from OAuth objects

    Args:
        token: OAuth token from Gradio
        profile: OAuth profile from Gradio

    Returns:
        User object if authenticated, None otherwise
    """
    if not is_authenticated(token, profile):
        return None

    # In dev mode, return mock user
    if DEV_MODE:
        return User.create_dev_user()

    return User.from_oauth(token, profile)


def create_login_handler(on_login_success=None, on_login_failure=None):
    """
    Create a login handler function for Gradio LoginButton

    Args:
        on_login_success: Callback function called when login succeeds
        on_login_failure: Callback function called when login fails

    Returns:
        Handler function compatible with Gradio LoginButton.click()
    """
    def handle_login(token: gr.OAuthToken | None, profile: gr.OAuthProfile | None):
        if is_authenticated(token, profile):
            user = get_user_info(token, profile)
            if on_login_success:
                return on_login_success(user)
            return user
        else:
            if on_login_failure:
                return on_login_failure()
            return None

    return handle_login


def require_auth(func):
    """
    Decorator to require authentication for a function

    Usage:
        @require_auth
        def my_function(user: User, other_args...):
            # user is guaranteed to be valid User object
            pass
    """
    def wrapper(token: gr.OAuthToken | None, profile: gr.OAuthProfile | None, *args, **kwargs):
        if not is_authenticated(token, profile):
            gr.Warning("Please log in to Hugging Face to access this feature!")
            return None

        user = get_user_info(token, profile)
        return func(user, *args, **kwargs)

    return wrapper


# UI component helpers
def create_login_button(visible: bool = True) -> gr.LoginButton:
    """
    Create a styled HuggingFace login button
    Automatically hidden in dev mode
    """
    # Hide login button in dev mode
    if DEV_MODE:
        visible = False

    return gr.LoginButton(visible=visible)


def create_user_info_display(user: Optional[User]) -> str:
    """
    Create HTML for user info display

    Args:
        user: User object or None

    Returns:
        HTML string for display
    """
    if user is None:
        # In dev mode, don't show login prompt
        if DEV_MODE:
            return """
            <div style="text-align: center; padding: 10px; border: 2px solid #ffa500; border-radius: 10px; background-color: #fff4e6;">
                <strong>🛠️ Development Mode</strong>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">OAuth disabled for local testing</p>
            </div>
            """

        return """
        <div style="text-align: center; padding: 20px; border: 2px dashed #ccc; border-radius: 10px;">
            <h3>🔒 Login Required</h3>
            <p>Please log in with your Hugging Face account to access TraceMind</p>
        </div>
        """

    # Add dev mode badge if in dev mode
    dev_badge = ""
    if DEV_MODE:
        dev_badge = '<span style="background: #ffa500; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 10px;">DEV</span>'

    return f"""
    <div style="display: flex; align-items: center; padding: 10px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <img src="{user.avatar_url}" alt="{user.name}"
             style="width: 48px; height: 48px; border-radius: 50%; margin-right: 15px;">
        <div>
            <strong>{user.name}</strong>{dev_badge}<br>
            <small style="color: #666;">@{user.username}</small>
        </div>
    </div>
    """


def create_auth_warning(message: str = "Please login first") -> str:
    """Create a warning message for unauthenticated users"""
    return f"""
    <div style="text-align: center; padding: 20px; border: 2px solid #ff6b6b; border-radius: 10px; background-color: #ffe0e0;">
        <h3>⚠️ Authentication Required</h3>
        <p>{message}</p>
    </div>
    """
