"""主题色彩"""

THEMES = {
    "dark": {
        "bg_primary": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_panel": "#0f3460",
        "text_primary": "#eeeeee",
        "text_secondary": "#a0a0b0",
        "accent": "#0f3460",
        "highlight": "#e94560",
        "plan_color": "#4fc3f7",
        "exec_color": "#66bb6a",
        "glow_color": "#7c4dff",
        "border_color": "#2a2a4e",
        "input_bg": "#1e1e3e",
        "scrollbar_bg": "#2a2a4e",
        "scrollbar_handle": "#4a4a6e",
    },
    "light": {
        "bg_primary": "#f8f9fa",
        "bg_secondary": "#e9ecef",
        "bg_panel": "#dee2e6",
        "text_primary": "#212529",
        "text_secondary": "#6c757d",
        "accent": "#dee2e6",
        "highlight": "#007bff",
        "plan_color": "#0288d1",
        "exec_color": "#2e7d32",
        "glow_color": "#2962ff",
        "border_color": "#ced4da",
        "input_bg": "#ffffff",
        "scrollbar_bg": "#e9ecef",
        "scrollbar_handle": "#adb5bd",
    },
}


def get_theme(name: str = "dark") -> dict:
    return THEMES.get(name, THEMES["dark"])
