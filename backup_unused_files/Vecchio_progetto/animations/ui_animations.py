# animations/ui_animations.py - Animazioni per l'interfaccia utente

def toggle_log_panel_visibility(log_widget, log_btn):
    """
    Mostra o nasconde il pannello di log con transizione.

    Args:
        log_widget: Il QTextEdit del log
        log_btn: Il QPushButton per controllare la visibilità
    """
    if log_widget.isVisible():
        log_widget.hide()
        log_btn.setText("📊 Mostra Log")
    else:
        log_widget.show()
        log_btn.setText("📊 Nascondi Log")