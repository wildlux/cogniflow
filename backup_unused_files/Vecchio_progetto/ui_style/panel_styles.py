# styles/panel_styles.py - Stili per i pannelli

def get_scrollable_panel_style(color_class):
    """Restituisce il foglio di stile per ScrollablePanel."""
    colors = {"blue": "#3498db", "red": "#e74c3c", "green": "#2ecc71"}
    border_color = colors.get(color_class, "#bdc3c7")
    return f"""
    QScrollArea {{
        background-color: transparent;
        border: 3px solid {border_color};
        border-radius: 15px;
        margin: 5px;
    }}
    QScrollBar:vertical {{
        background: #c3cfe2;
        width: 12px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: #4a90e2;
        border-radius: 6px;
    }}
    """