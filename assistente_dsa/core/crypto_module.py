"""
Modulo per la gestione della crittografia e codifica/decodifica base64.

Questo modulo fornisce funzionalità sicure per la codifica e decodifica
base64, con validazione degli input e gestione degli errori. È utilizzato
dal sistema di sicurezza per proteggere i dati sensibili.

Classi:
    Base64Handler: Gestore base per operazioni base64
    SecureEncoder: Encoder sicuro con validazione

Funzionalità:
    - Codifica sicura di stringhe e bytes in base64
    - Decodifica sicura da base64 a stringhe e bytes
    - Validazione automatica degli input
    - Gestione errori robusta
    - Supporto per dati vuoti

Sicurezza:
    - Validazione di tutti gli input
    - Gestione sicura delle eccezioni
    - Nessuna perdita di dati in caso di errore
    - Encoding/decoding consistente

Esempi:
    >>> from core.crypto_module import secure_encoder
    >>> encoded = secure_encoder.safe_encode("Hello World")
    >>> decoded = secure_encoder.safe_decode(encoded)
    >>> print(decoded.decode())  # Hello World
"""
import base64
from typing import Union

class Base64Handler:
    """
    Gestore base per operazioni di codifica/decodifica base64.

    Questa classe fornisce metodi statici per operazioni base64 sicure
    senza validazione aggiuntiva. È la base per operazioni più complesse
    ma richiede attenzione nella gestione degli errori.

    Metodi statici:
        encode_bytes(data: bytes) -> str: Codifica bytes in base64 string
        decode_string(encoded: str) -> bytes: Decodifica base64 string in bytes
        encode_string(text: str) -> str: Codifica stringa in base64
        decode_to_string(encoded: str) -> str: Decodifica base64 in stringa

    Note:
        Questa classe non valida gli input - usare SecureEncoder per
        operazioni sicure con validazione automatica.

    Raises:
        ValueError: Per errori di codifica/decodifica
    """

    @staticmethod
    def encode_bytes(data: bytes) -> str:
        """
        Codifica una sequenza di bytes in una stringa base64.

        Args:
            data (bytes): I dati da codificare

        Returns:
            str: Stringa base64 rappresentante i dati

        Raises:
            ValueError: Se la codifica fallisce

        Example:
            >>> result = Base64Handler.encode_bytes(b"Hello")
            >>> print(result)  # SGVsbG8=
        """
        try:
            return base64.b64encode(data).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Errore nella codifica base64: {e}")

    @staticmethod
    def decode_string(encoded_data: str) -> bytes:
        """
        Decodifica una stringa base64 in bytes.

        Args:
            encoded_data (str): Stringa base64 da decodificare

        Returns:
            bytes: I dati decodificati

        Raises:
            ValueError: Se la decodifica fallisce o i dati non sono validi base64

        Example:
            >>> result = Base64Handler.decode_string("SGVsbG8=")
            >>> print(result)  # b'Hello'
        """
        try:
            return base64.b64decode(encoded_data.encode('utf-8'))
        except Exception as e:
            raise ValueError(f"Errore nella decodifica base64: {e}")

    @staticmethod
    def encode_string(text: str) -> str:
        """
        Codifica una stringa di testo in base64.

        Args:
            text (str): La stringa da codificare

        Returns:
            str: Stringa base64

        Raises:
            ValueError: Se la codifica fallisce

        Example:
            >>> result = Base64Handler.encode_string("Hello World")
            >>> print(result)  # SGVsbG8gV29ybGQ=
        """
        try:
            return Base64Handler.encode_bytes(text.encode('utf-8'))
        except Exception as e:
            raise ValueError(f"Errore nella codifica stringa base64: {e}")

    @staticmethod
    def decode_to_string(encoded_data: str) -> str:
        """
        Decodifica una stringa base64 in testo.

        Args:
            encoded_data (str): Stringa base64 da decodificare

        Returns:
            str: La stringa decodificata

        Raises:
            ValueError: Se la decodifica fallisce

        Example:
            >>> result = Base64Handler.decode_to_string("SGVsbG8gV29ybGQ=")
            >>> print(result)  # Hello World
        """
        try:
            return Base64Handler.decode_string(encoded_data).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Errore nella decodifica stringa base64: {e}")

class SecureEncoder:
    """
    Encoder sicuro con validazione automatica degli input.

    Questa classe fornisce metodi sicuri per la codifica/decodifica base64
    con validazione automatica degli input e gestione robusta degli errori.
    È raccomandata per uso generale rispetto a Base64Handler.

    Metodi statici:
        safe_encode(data) -> str: Codifica sicura con validazione
        safe_decode(encoded) -> bytes: Decodifica sicura con validazione

    Caratteristiche:
        - Validazione automatica del tipo di input
        - Gestione sicura di dati vuoti
        - Messaggi di errore informativi
        - Nessuna eccezione per dati vuoti
        - Supporto per stringhe e bytes

    Sicurezza:
        - Validazione rigorosa degli input
        - Gestione sicura delle eccezioni
        - Nessuna perdita di dati
    """

    @staticmethod
    def safe_encode(data: Union[str, bytes]) -> str:
        """Codifica sicura con validazione input"""
        if isinstance(data, str):
            if not data:
                return ""
            return Base64Handler.encode_string(data)
        elif isinstance(data, bytes):
            if not data:
                return ""
            return Base64Handler.encode_bytes(data)
        else:
            raise TypeError("Input deve essere stringa o bytes")

    @staticmethod
    def safe_decode(encoded_data: str) -> bytes:
        """Decodifica sicura con validazione"""
        if not encoded_data:
            return b""
        if not isinstance(encoded_data, str):
            raise TypeError("Input deve essere stringa")
        return Base64Handler.decode_string(encoded_data)

# Istanza globale per uso semplificato
base64_handler = Base64Handler()
secure_encoder = SecureEncoder()