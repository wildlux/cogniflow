# styles/widget_styles.py - Stili per i widget specifici

DRAGGABLE_WIDGET_STYLE = """
QFrame {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                              stop: 0 #667eea, stop: 1 #764ba2);
    border-radius: 15px;
    margin: 5px;
    color: white;
}
QPushButton {
    background-color: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    padding: 5px 10px;
    color: white;
    font-weight: bold;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.3);
}
"""

LOG_WIDGET_STYLE = """
QTextEdit {
    background-color: #333;
    color: #fff;
    border: 2px solid #555;
    border-radius: 8px;
    padding: 10px;
    font-family: monospace;
}
"""

TEXT_INPUT_STYLE = """
QLineEdit {
    background-color: #fff;
    border: 2px solid #ddd;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    color: #333;
}
QLineEdit:focus {
    border: 2px solid #4a90e2;
    background-color: white;
}
"""

AI_RESULTS_STYLE = """
QTextEdit {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px;
    font-size: 12px;
}
"""