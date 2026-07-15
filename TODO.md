# TODO — CogniFlow

## ⚙️ Ripulire le Impostazioni e rendere il cursore un "gioco" — FATTO

Schede (in `UI/settings_dialog.py`):

- [x] Rimossa la scheda "Interfaccia" (`setup_ui_tab`). Le dimensioni
      finestra restano lette all'avvio dai valori salvati/predefiniti
      (`ui.window_*`), gestite in automatico.
- [x] Rimossa la scheda "Test" (`setup_test_tab`) e il salvataggio/
      caricamento dei relativi `test.*`.
- [x] Impostazioni ora con sole schede utili: Generale, AI, 🔒 Osservazione,
      🎨 Personalizza, 📥 Download.

Cursore mano-mouse come gioco (`HandCursorWidget` in `main_01_Aircraft.py`):

- [x] Cursore reso più giocoso: bolla grande (52 px) con alone morbido
      (sfumatura radiale) e riflesso, tipo bolla di sapone.
- [x] Colori configurabili dalle Impostazioni (`cursor.color_open/closed/
      scroll`) tramite un nuovo gruppo "🫧 Colori del cursore" nella scheda
      🎨 Personalizza; applicati a caldo al salvataggio (`reload_colors`).

## 🚪 Logout e 🔒 osservazione difficoltà — FATTO

- [x] Pulsante "🚪 Esci" nella barra in alto: chiude la sessione e torna
      alla schermata di accesso (ciclo login in `main()`).
- [x] Osservazione dei momenti di difficoltà (`core/difficulty_observer.py`):
      quando la webcam rileva una smorfia di difficoltà sostenuta, salva
      uno screenshot dell'INTERFACCIA (non del volto) in
      `Save/Osservazioni_Riservate/` con registro, per genitori/clinici.
      Spenta di default; si attiva da Impostazioni → "🔒 Osservazione" con
      consenso esplicito. Nessun pop-up all'utente. Ritenzione configurabile.

Da valutare più avanti:

- [ ] Informativa adatta all'età mostrata all'utente osservato (una tantum),
      per trasparenza pur senza interrompere la sessione.
- [ ] Cifratura a riposo della cartella riservata / accesso protetto.
- [ ] Report riassuntivo per il clinico (quante difficoltà, in quali attività).

## 🐛 Bug: la tastiera virtuale resta attiva quando si passa al canvas — FATTO

Con la tastiera aperta e poi il passaggio a un'altra pagina dell'area
comune (es. Canvas), la tastiera rimaneva "attiva in memoria": con Eco
acceso, disegnando si sentivano lettere fantasma ("emme", "elle").

- [x] `hideEvent` sospende dwell e scansione (e pulisce le evidenziazioni);
      `showEvent` li riprende se i relativi pulsanti sono attivi. In più,
      `_echo`/`_dwell_tick`/`_scan_tick` hanno una guardia `isVisible()`.
      Test: `tests/test_virtual_keyboard.py::test_nascosta_sospende_dwell_e_scansione`.

## 🔀 Unire "Area di Lavoro" (B) e "Lavagna risposta Interattiva & AI" (C)

Idea: fondere le due colonne in un'unica superficie di lavoro.
Nella superficie unificata, selezione del testo con un gesto a due mani
davanti alla webcam:

- mano SINISTRA: indice alzato = "I" (l'asta, punto di inizio);
- mano DESTRA: indice e pollice rivolti verso il basso = "/\"
  (il cursore a tenda, punto di fine).

- [ ] Unificare le colonne B e C in un'unica area.
- [ ] Riconoscere il gesto a due mani (il rilevamento supporta già più
      mani: num_hands=4 in visual_background) e tradurlo in selezione
      del testo tra i due punti indicati.
- [ ] Definire cosa fare della selezione: lettura TTS, copia nei
      pensierini, domanda all'AI sulla parte selezionata.

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
