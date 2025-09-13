# styles/main_styles.py - Stili principali dell'applicazione

def get_main_stylesheet():
    """Restituisce il foglio di stile principale per MainWindow."""
    return """
    QMainWindow {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                  stop: 0 #667eea, stop: 1 #764ba2);
    }

    QPushButton {
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 12px;
    }

    QPushButton:hover {
        background-color: rgba(255, 255, 255, 0.3);
        border: 2px solid rgba(255, 255, 255, 0.5);
    }

    QPushButton:pressed {
        background-color: rgba(255, 255, 255, 0.4);
    }

    QPushButton:disabled {
        background-color: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.5);
        border: 2px solid rgba(255, 255, 255, 0.2);
    }

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

    QLabel {
        color: white;
    }

    QDialog QLabel {
        color: #333;
    }

    QDialog QPushButton {
        background-color: #4a90e2;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 5px 10px;
    }

    QDialog QPushButton:hover {
        background-color: #3b82f6;
    }

    QComboBox {
        background-color: white;
        border: 2px solid #ccc;
        border-radius: 8px;
        padding: 5px;
        min-width: 100px;
        color: #333;
    }

    QComboBox::drop-down {
        border: none;
    }

    QComboBox::down-arrow {
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTcgMTBMMTIgMTVMMTcgMTBaIiBmaWxsPSIjNDU0NTQ1Ii8+Cjwvc3ZnPg==);
        width: 16px;
        height: 16px;
        margin-right: 5px;
    }

    QTextEdit {
        background-color: #f5f7fa;
        border: 2px solid #ccc;
        border-radius: 8px;
        padding: 8px;
        color: #333;
    }

    QCheckBox {
        color: #333;
        font-weight: bold;
    }

    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 3px;
        border: 2px solid #4a90e2;
        background-color: white;
    }

    QCheckBox::indicator:checked {
        background-color: #4a90e2;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9MTAuNSAyLjVMNC41IDguNUwyLjUgNi41IiBzdHJva2U9IiMxNDEyMTIiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
    }

    QSlider::groove:horizontal {
        border: 1px solid #bbb;
        background: white;
        height: 10px;
        border-radius: 4px;
    }

    QSlider::sub-page:horizontal {
        background: #4a90e2;
        border: 1px solid #777;
        height: 10px;
        border-radius: 4px;
    }

    QSlider::add-page:horizontal {
        background: #fff;
        border: 1px solid #777;
        height: 10px;
        border-radius: 4px;
    }

    QSlider::handle:horizontal {
        background: #4a90e2;
        border: 1px solid #5c5c5c;
        width: 18px;
        margin-top: -2px;
        margin-bottom: -2px;
        border-radius: 3px;
    }

    QTabWidget::pane {
        border: 2px solid #4a90e2;
        border-radius: 8px;
        background-color: white;
    }

    QTabBar::tab {
        background-color: #f5f7fa;
        border: 2px solid #4a90e2;
        border-bottom-color: transparent;
        border-radius: 8px 8px 0px 0px;
        min-width: 120px;
        padding: 8px 16px;
        margin-right: 2px;
        font-weight: bold;
        color: #4a90e2;
    }

    QTabBar::tab:selected {
        background-color: #4a90e2;
        color: white;
    }

    QTabBar::tab:hover {
        background-color: rgba(74, 144, 226, 0.3);
    }

    QDialog {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                  stop: 0 #f5f7fa, stop: 1 #c3cfe2);
    }
    """