# ===========================================
# SAFE QT WRAPPER - GESTIONE SICURA DELLE OPERAZIONI QT
# ===========================================

class SafeQtWrapper:
    """
    Wrapper sicuro per operazioni Qt che potrebbero fallire.

    Questa classe è essenziale per la stabilità del programma perché:
    - Previene crash quando gli oggetti Qt sono None
    - Gestisce metodi che potrebbero non esistere in alcune versioni
    - Fornisce fallback automatici per compatibilità
    - Logga errori senza interrompere l'esecuzione
    """

    @staticmethod
    def safe_getattr(obj, attr, default=None):
        """
        Ottiene un attributo in modo sicuro.

        Args:
            obj: Oggetto da cui ottenere l'attributo
            attr: Nome dell'attributo
            default: Valore di default se l'attributo non esiste

        Returns:
            Valore dell'attributo o default se non trovato
        """
        if obj is None:
            return default
        try:
            return getattr(obj, attr, default)
        except Exception:
            return default

    @staticmethod
    def safe_call(obj, method_name, *args, **kwargs):
        """
        Chiama un metodo in modo sicuro.

        Args:
            obj: Oggetto su cui chiamare il metodo
            method_name: Nome del metodo
            *args: Argomenti posizionali
            **kwargs: Argomenti nominati

        Returns:
            Risultato del metodo o None se fallisce
        """
        if obj is None:
            return None
        try:
            method = getattr(obj, method_name, None)
            if method and callable(method):
                return method(*args, **kwargs)
        except Exception:
            pass
        return None

    @staticmethod
    def safe_qt_method(obj, method_name, *args, **kwargs):
        """
        Chiama metodi Qt in modo sicuro con fallback automatico.

        Questa funzione è particolarmente importante per:
        - Metodi che cambiano tra versioni di Qt
        - Metodi che potrebbero non esistere in alcune configurazioni
        - Mantenere compatibilità cross-versione

        Args:
            obj: Oggetto Qt
            method_name: Nome del metodo Qt
            *args: Argomenti per il metodo
            **kwargs: Argomenti nominati

        Returns:
            Risultato del metodo o fallback
        """
        if obj is None:
            return None

        # Prova il metodo principale
        result = SafeQtWrapper.safe_call(obj, method_name, *args, **kwargs)
        if result is not None:
            return result

        # SISTEMA DI FALLBACK AUTOMATICO
        # Gestisce le differenze tra versioni di Qt
        if method_name == "setSectionResizeMode":
            # In alcune versioni il metodo si chiama diversamente
            return SafeQtWrapper.safe_call(obj, "setStretchLastSection", True)
        elif method_name == "toPlainText":
            # QLineEdit usa text() invece di toPlainText()
            return SafeQtWrapper.safe_call(obj, "text") or ""
        elif method_name == "recognize_google":
            # Fallback per metodi di riconoscimento vocale
            return SafeQtWrapper.safe_call(obj, "recognize", *args, **kwargs)

        return None
