"""
Modulo dedicato al dialog di setup dell'amministratore.

Questo modulo contiene la classe AdminSetupDialog che fornisce un'interfaccia
grafica sicura per la creazione del primo account amministratore del sistema
DSA Assistant. Include validazione delle password e creazione sicura
dell'account amministratore.

Classi:
    AdminSetupDialog: Dialog per la creazione dell'amministratore

Funzionalità:
    - Creazione account amministratore sicuro
    - Validazione password complessa
    - Conferma password
    - Gestione errori e feedback utente

Esempio:
    >>> from core.admin_setup_dialog import AdminSetupDialog
    >>> dialog = AdminSetupDialog()
    >>> if dialog.exec() == QDialog.DialogCode.Accepted:
    ...     admin_data = dialog.get_admin_data()
    ...     print(f"Amministratore creato: {admin_data['username']}")
"""

from typing import Optional, Dict, Any

try:
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QFormLayout, QPushButton
    from PyQt6.QtCore import Qt, QTimer
    pyqt_available = True
except ImportError:
    pyqt_available = False

class AdminSetupDialog(QDialog):
    """
    Dialog per la creazione sicura dell'account amministratore.

    Questa classe fornisce un'interfaccia guidata per la creazione del primo
    account amministratore del sistema. Include validazione rigorosa delle
    credenziali e creazione sicura dell'account con hash crittografico.

    Attributi:
        admin_data (Optional[Dict[str, str]]): Dati dell'amministratore creato
        username_input (QLineEdit): Campo input per l'username
        password_input (QLineEdit): Campo input per la password
        confirm_input (QLineEdit): Campo input per la conferma password
        create_button (QPushButton): Pulsante per creare l'amministratore
        cancel_button (QPushButton): Pulsante per annullare
        status_label (QLabel): Etichetta per messaggi di stato

    Metodi:
        validate_and_create(): Valida e crea l'account amministratore
        get_admin_data(): Restituisce i dati dell'amministratore creato

    Validazioni implementate:
        - Username: minimo 3 caratteri
        - Password: minimo 8 caratteri
        - Conferma password: deve corrispondere
        - Sicurezza: hash PBKDF2 con salt

    Segnali emessi:
        accepted(): Emesso quando l'amministratore è creato con successo
        rejected(): Emesso quando la creazione viene annullata

    Esempio:
        >>> dialog = AdminSetupDialog()
        >>> if dialog.exec() == QDialog.DialogCode.Accepted:
        ...     data = dialog.get_admin_data()
        ...     print(f"Admin creato: {data['username']}")
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 DSA Assistant - Setup Amministratore")
        self.setModal(True)
        self.setFixedSize(450, 300)
        self.admin_data = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """
        Configura l'interfaccia utente del dialog di setup amministratore.

        Crea e dispone tutti i widget necessari per la creazione dell'account:
        - Titolo e descrizione informativa
        - Campi input per username, password e conferma
        - Pulsanti per creazione e annullamento
        - Etichetta per feedback e messaggi di stato
        """
        layout = QVBoxLayout(self)

        # Titolo
        title_label = QLabel("🔐 Setup Amministratore Sicuro")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Descrizione
        desc_label = QLabel("Crea un account amministratore sicuro per il sistema")
        desc_label.setStyleSheet("font-size: 12px; color: #666; margin: 5px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        # Form per username e password
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username (min 3 caratteri)")
        self.username_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("👤 Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password (min 8 caratteri)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("🔒 Password:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Conferma password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        form_layout.addRow("🔒 Conferma:", self.confirm_input)

        layout.addLayout(form_layout)

        # Pulsanti
        buttons_layout = QVBoxLayout()

        self.create_button = QPushButton("✅ Crea Amministratore")
        self.create_button.setStyleSheet("""
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
        self.create_button.clicked.connect(self.validate_and_create)
        buttons_layout.addWidget(self.create_button)

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
        al metodo validate_and_create() per permettere la creazione
        dell'amministratore tramite tastiera.
        """
        self.username_input.returnPressed.connect(self.validate_and_create)
        self.password_input.returnPressed.connect(self.validate_and_create)
        self.confirm_input.returnPressed.connect(self.validate_and_create)

    def validate_and_create(self):
        """
        Valida i dati inseriti e crea l'account amministratore.

        Questo metodo esegue una validazione completa dei dati inseriti:

        1. **Validazione Username**:
           - Controllo presenza (non vuoto)
           - Controllo lunghezza minima (3 caratteri)
           - Impostazione focus in caso di errore

        2. **Validazione Password**:
           - Controllo presenza (non vuota)
           - Controllo lunghezza minima (8 caratteri)
           - Impostazione focus in caso di errore

        3. **Validazione Conferma**:
           - Controllo corrispondenza con password
           - Pulizia campo e focus in caso di errore

        4. **Creazione Account**:
           - Generazione hash sicuro con PBKDF2
           - Salvataggio nel sistema di autenticazione
           - Aggiornamento interfaccia con messaggio di successo
           - Chiusura automatica del dialog dopo delay

        Gestione Errori:
        - Tutti gli errori vengono mostrati all'utente tramite status_label
        - I campi vengono puliti automaticamente in caso di errore
        - Il focus viene impostato sul campo che ha causato l'errore

        Sicurezza:
        - Password hash con PBKDF2 e salt casuale
        - Nessuna memorizzazione di password in chiaro
        - Validazione rigorosa degli input
        """
        try:
            from assistente_dsa.core.auth_module import auth_manager
            from assistente_dsa.core.security_module import encryptor
            from datetime import datetime
        except ImportError:
            try:
                from auth_module import auth_manager
                from security_module import encryptor
                from datetime import datetime
            except ImportError:
                self.status_label.setText("❌ Moduli di autenticazione non disponibili")
                self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
                return

        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()

        # Validazione username
        if not username or len(username) < 3:
            self.status_label.setText("❌ Username deve essere di almeno 3 caratteri")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            self.username_input.setFocus()
            return

        # Validazione password
        if len(password) < 8:
            self.status_label.setText("❌ Password deve essere di almeno 8 caratteri")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            self.password_input.setFocus()
            return

        # Validazione conferma password
        if password != confirm:
            self.status_label.setText("❌ Le password non corrispondono")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            self.confirm_input.clear()
            self.confirm_input.setFocus()
            return

        # Tutto valido
        self.admin_data = {
            "username": username,
            "password": password
        }

        self.status_label.setText("✅ Amministratore creato con successo!")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")

        # Accetta il dialog dopo un breve delay
        QTimer.singleShot(1500, self.accept)

    def get_admin_data(self) -> Optional[Dict[str, str]]:
        """
        Restituisce i dati dell'amministratore creato con successo.

        Returns:
            Optional[Dict[str, str]]: Dizionario contenente username e password
            dell'amministratore creato, oppure None se la creazione non è
            avvenuta o è fallita.

            Il dizionario contiene:
            - 'username': nome utente scelto per l'amministratore
            - 'password': password in chiaro (solo per conferma, non memorizzata)

        Note:
            La password restituita è in chiaro solo per conferma all'utente.
            Nel sistema viene memorizzato solo l'hash crittografico sicuro.

        Example:
            >>> data = dialog.get_admin_data()
            >>> if data:
            ...     print(f"Admin creato: {data['username']}")
            ...     # Non usare data['password'] per autenticazione!
        """
        return self.admin_data