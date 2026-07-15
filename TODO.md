# TODO — CogniFlow

## ⌨️ Tastiera virtuale a schermo

Per chi non può usare la tastiera fisica: scrivere termini in italiano e
inglese usando solo il puntatore (mouse, mano-mouse via webcam, domani BCI).

Requisiti:

- [x] Tasti grandi (minimo 44 px, meglio 60+) con buona spaziatura, layout
      QWERTY italiano; pagina secondaria per numeri e punteggiatura.
      → `UI/virtual_keyboard.py`, con riga delle vocali accentate.
- [x] Integrata nell'area comune del footer (come Testo/Canvas/Strumenti),
      scrive nel campo pensierini attivo.
      → pulsante "⌨️ Tastiera" nella colonna del footer; scrive nel campo
      pensierini e ne mostra un'anteprima sopra i tasti; il tasto 📤 invia.
- [x] Predizione delle parole: 3–5 suggerimenti sopra la tastiera, basati su
      un dizionario di frequenza locale italiano + inglese (offline);
      opzionale raffinamento con Ollama.
      → dizionario di frequenza integrato + parole apprese dall'utente
      (salvate in `Save/SETUP_TOOLS_&_Data/tastiera_parole_apprese.json`)
      + dizionari di sistema come riserva. Raffinamento Ollama: ancora da
      fare (opzionale).
- [x] Compatibile con il mano-mouse: click con mano chiusa già funzionante;
      prevedere il dwell click (sostare sul tasto = pressione) quando verrà
      implementato.
      → dwell click implementato (pulsante "⏱️ Sosta"): funziona col mouse
      e col cursore interno del mano-mouse (via `_hand_pointer_global`).
- [x] Predisposta per la scansione a singolo segnale ("avanti"/"seleziona"):
      evidenziazione che cicla per righe e poi per tasti — è il ponte verso
      il futuro collegamento brain-computer.
      → pulsante "🔦 Scansione"; il segnale è SPAZIO/INVIO oppure una
      chiamata a `VirtualKeyboardWidget.scan_select()` (aggancio BCI).
- [x] Feedback: eco vocale (TTS) opzionale della lettera/parola scritta.
      → pulsante "🔊 Eco" (usa espeak-ng via `MainWindow._speak`).

Rimasto per dopo:

- [ ] Raffinamento opzionale dei suggerimenti con Ollama (contesto di frase).
- [ ] Dwell click anche fuori dalla tastiera (su tutta l'interfaccia).

## 🤟 Scrittura con l'alfabeto manuale (dattilologia) — seguiti

La base c'è (pulsante "🤟 Segni" nel mini WordPad, luglio 2026): lettere
statiche A–Y riconosciute in geometria pura, mano aperta = spazio.

- [ ] Modalità calibrazione: l'utente registra i PROPRI segni (landmark di
      esempio per lettera) e il riconoscimento confronta con quelli — più
      preciso e adattabile, utile per le lettere "a pugno" (A E S T N M).
- [ ] Gesto di cancellazione (backspace) senza toccare la tastiera.
- [ ] Lettere con movimento: J e Z (traiettoria della punta del dito).
