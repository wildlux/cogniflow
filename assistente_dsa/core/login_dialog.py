"""
Modulo dedicato al dialog di login per l'autenticazione utente.

Questo modulo contiene la classe LoginDialog che fornisce un'interfaccia
grafica per l'autenticazione degli utenti del sistema DSA Assistant.
Gestisce l'input delle credenziali e la comunicazione con il sistema
di autenticazione.

Classi:
    LoginDialog: Dialog principale per il login utente

Esempio:
    >>> from core.login_dialog import LoginDialog
    >>> dialog = LoginDialog()
    >>> result = dialog.exec()
    >>> if result == QDialog.DialogCode.Accepted:
    ...     user = dialog.get_authenticated_user()
"""

from typing import Optional, Any

try:
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QFormLayout, QPushButton
    from PyQt6.QtCore import Qt, QTimer
    pyqt_available = True
except ImportError:
    pyqt_available = False

class LoginDialog(QDialog):
    """
    Dialog per l'autenticazione utente con interfaccia grafica.

    Questa classe fornisce un'interfaccia utente completa per l'autenticazione
    degli utenti del sistema DSA Assistant. Include campi per username e
    password, validazione degli input, e gestione degli errori.

    Attributi:
        authenticated_user (Optional[dict]): Informazioni dell'utente autenticato
        username_input (QLineEdit): Campo input per l'username
        password_input (QLineEdit): Campo input per la password
        login_button (QPushButton): Pulsante per effettuare il login
        cancel_button (QPushButton): Pulsante per annullare
        status_label (QLabel): Etichetta per messaggi di stato

    Metodi:
        attempt_login(): Tenta l'autenticazione con le credenziali inserite
        get_authenticated_user(): Restituisce l'utente autenticato

    Segnali emessi:
        accepted(): Emesso quando il login ha successo
        rejected(): Emesso quando il login viene annullato

    Esempio:
        >>> dialog = LoginDialog()
        >>> if dialog.exec() == QDialog.DialogCode.Accepted:
        ...     user = dialog.get_authenticated_user()
        ...     print(f"Benvenuto {user['full_name']}")
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 DSA Assistant - Login")
        self.setModal(True)
        self.setFixedSize(400, 250)
        self.authenticated_user = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """
        Configura l'interfaccia utente del dialog di login.

        Crea e dispone tutti i widget necessari per l'autenticazione:
        - Titolo del dialog
        - Campi input per username e password
        - Pulsanti per login e annullamento
        - Etichetta per messaggi di stato
        """
        layout = QVBoxLayout(self)

        # Titolo
        title_label = QLabel("🔐 Autenticazione Richiesta")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Form per username e password
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Inserisci username")
        self.username_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("👤 Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Inserisci password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("🔒 Password:", self.password_input)

        layout.addLayout(form_layout)

        # Pulsanti
        buttons_layout = QVBoxLayout()

        self.login_button = QPushButton("🔐 Login")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.login_button.clicked.connect(self.attempt_login)
        buttons_layout.addWidget(self.login_button)

        self.cancel_button = QPushButton("❌ Annulla")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        # Label per messaggi di stato
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #f44336; font-size: 12px; margin: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        """
        Connette i segnali degli elementi UI ai rispettivi slot.

        Collega gli eventi di pressione del tasto Enter nei campi input
        al metodo attempt_login() per permettere l'autenticazione
        tramite tastiera.
        """
        self.username_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)

    def attempt_login(self):
        """
        Tenta l'autenticazione con le credenziali inserite dall'utente.

        Questo metodo:
        1. Recupera username e password dai campi input
        2. Valida che entrambi i campi siano compilati
        3. Chiama il sistema di autenticazione
        4. Gestisce il successo/fallimento dell'autenticazione
        5. Aggiorna l'interfaccia utente con messaggi appropriati

        In caso di successo:
        - Salva le informazioni dell'utente autenticato
        - Mostra messaggio di benvenuto
        - Chiude il dialog dopo un breve delay

        In caso di fallimento:
        - Mostra messaggio di errore
        - Pulisce il campo password
        - Imposta il focus sul campo password
        """
        try:
            from assistente_dsa.core.auth_module import auth_manager, AUTH_AVAILABLE
        except ImportError:
            try:
                from auth_module import auth_manager, AUTH_AVAILABLE
            except ImportError:
                self.status_label.setText("❌ Sistema di autenticazione non disponibile")
                self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
                return

        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.status_label.setText("❌ Inserisci username e password")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            return

        if AUTH_AVAILABLE and auth_manager:
            user = auth_manager.authenticate(username, password)
            if user:
                self.status_label.setText(f"✅ Benvenuto, {user['full_name']}!")
                self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
                self.authenticated_user = user
                QTimer.singleShot(1000, self.accept)
            else:
                self.status_label.setText("❌ Credenziali non valide")
                self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
                self.password_input.clear()
                self.password_input.setFocus()
        else:
            self.status_label.setText("❌ Sistema di autenticazione non disponibile")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")

    def get_authenticated_user(self) -> Optional[dict[str, Any]]:
        """
        Restituisce le informazioni dell'utente autenticato.

        Returns:
            Optional[dict[str, Any]]: Dizionario contenente le informazioni
            dell'utente se l'autenticazione è riuscita, None altrimenti.

            Il dizionario contiene tipicamente:
            - 'username': nome utente
            - 'full_name': nome completo
            - 'group': gruppo di appartenenza
            - 'is_active': stato dell'account
            - 'last_login': data ultimo accesso

        Example:
            >>> user = dialog.get_authenticated_user()
            >>> if user:
            ...     print(f"Utente: {user['full_name']}")
            ...     print(f"Gruppo: {user['group']}")
        """
        return self.authenticated_user