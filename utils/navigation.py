"""
Navigation utilities for MockTraceMind screen flow
"""

import gradio as gr
from enum import Enum
from typing import Dict, Any, Tuple


class Screen(Enum):
    """Available screens in MockTraceMind"""
    LEADERBOARD = "leaderboard"
    COMPARE = "compare"
    RUN_DETAIL = "run_detail"
    TRACE_DETAIL = "trace_detail"


class Navigator:
    """
    Manages screen navigation and state

    Screen Flow:
    - Leaderboard (Screen 1)
      - Click row → Run Detail (Screen 3)
      - Select 2+ rows + Compare → Compare View (Screen 2)
        - Click either run → Run Detail (Screen 3)
    - Run Detail (Screen 3)
      - Click test case row → Trace Detail (Screen 4)
    - Trace Detail (Screen 4)
      - Back → Run Detail (Screen 3)
    """

    def __init__(self):
        self.current_screen = Screen.LEADERBOARD
        self.navigation_stack = [Screen.LEADERBOARD]
        self.screen_context: Dict[str, Any] = {}

    def navigate_to(
        self,
        screen: Screen,
        context: Dict[str, Any] = None,
        add_to_stack: bool = True
    ) -> Tuple[Screen, Dict[str, Any]]:
        """
        Navigate to a screen with optional context

        Args:
            screen: Target screen
            context: Data to pass to the screen
            add_to_stack: Whether to add to navigation stack

        Returns:
            Tuple of (screen, context)
        """
        self.current_screen = screen

        if context:
            self.screen_context.update(context)

        if add_to_stack:
            self.navigation_stack.append(screen)

        return screen, self.screen_context

    def back(self) -> Tuple[Screen, Dict[str, Any]]:
        """
        Navigate back in the navigation stack

        Returns:
            Tuple of (previous_screen, context)
        """
        if len(self.navigation_stack) > 1:
            self.navigation_stack.pop()  # Remove current
            previous = self.navigation_stack[-1]
            self.current_screen = previous
            return previous, self.screen_context

        # Already at root
        return self.current_screen, self.screen_context

    def get_current_screen(self) -> Screen:
        """Get current active screen"""
        return self.current_screen

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from screen context"""
        return self.screen_context.get(key, default)

    def set_context(self, key: str, value: Any) -> None:
        """Set value in screen context"""
        self.screen_context[key] = value

    def clear_context(self) -> None:
        """Clear all screen context"""
        self.screen_context.clear()

    def reset(self) -> None:
        """Reset navigation to initial state"""
        self.current_screen = Screen.LEADERBOARD
        self.navigation_stack = [Screen.LEADERBOARD]
        self.screen_context.clear()


# Gradio visibility update helpers
def show_screen(screen: Screen) -> Dict[gr.Component, gr.update]:
    """
    Generate Gradio updates to show specific screen

    Returns:
        Dictionary of component updates for gr.update
    """
    return {
        "leaderboard_container": gr.update(visible=(screen == Screen.LEADERBOARD)),
        "compare_container": gr.update(visible=(screen == Screen.COMPARE)),
        "run_detail_container": gr.update(visible=(screen == Screen.RUN_DETAIL)),
        "trace_detail_container": gr.update(visible=(screen == Screen.TRACE_DETAIL)),
    }


def create_back_button(visible: bool = True) -> gr.Button:
    """Create a consistent back button"""
    return gr.Button("⬅️ Back", visible=visible, variant="secondary", size="sm")


def create_breadcrumb(navigation_stack: list) -> str:
    """
    Create breadcrumb navigation HTML

    Args:
        navigation_stack: List of Screen enums

    Returns:
        HTML string for breadcrumb
    """
    breadcrumb_names = {
        Screen.LEADERBOARD: "Leaderboard",
        Screen.COMPARE: "Compare",
        Screen.RUN_DETAIL: "Run Detail",
        Screen.TRACE_DETAIL: "Trace Detail"
    }

    breadcrumb_items = []
    for i, screen in enumerate(navigation_stack):
        name = breadcrumb_names.get(screen, screen.value)
        if i < len(navigation_stack) - 1:
            # Not the last item - make it a link
            breadcrumb_items.append(f'<span style="color: #666;">{name}</span>')
        else:
            # Last item - current screen
            breadcrumb_items.append(f'<strong>{name}</strong>')

    breadcrumb_html = " > ".join(breadcrumb_items)

    return f"""
    <div style="padding: 10px; background-color: #f5f5f5; border-radius: 5px; margin-bottom: 10px;">
        {breadcrumb_html}
    </div>
    """
