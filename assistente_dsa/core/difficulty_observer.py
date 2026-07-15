"""Osservazione dei momenti di difficoltà per genitori e clinici.

Molti utenti, quando faticano a fare qualcosa, fanno una smorfia. Questa
funzione, SE abilitata e con consenso, coglie quei momenti: quando la
webcam rileva una smorfia di difficoltà tenuta per qualche secondo,
cattura uno screenshot dell'INTERFACCIA (non del volto) e lo salva in una
cartella riservata, con un registro dei momenti. Il materiale è pensato
per essere riletto da un genitore o da uno psicologo, per capire dove il
percorso si inceppa.

Scelte a tutela della persona (in particolare se è un minore/DSA):
 - SPENTA per impostazione predefinita; si attiva solo dalle Impostazioni,
   che sono pensate per il genitore/educatore, e richiede un consenso
   esplicito registrato (chi e quando);
 - cattura la SCHERMATA dell'app, non l'immagine della webcam: si vede
   cosa stava facendo la persona, non il suo viso;
 - niente pop-up nel momento: non si mostra nulla all'utente, per non
   metterlo in imbarazzo o interromperlo mentre è già in difficoltà;
 - i file restano in locale, in una cartella dedicata con un README che
   ne spiega natura e uso, e vengono cancellati dopo N giorni (ritenzione).

La funzione NON è una sorveglianza nascosta di terzi: presuppone che
l'utente osservato sia sotto la responsabilità di chi attiva la funzione
(un genitore/tutore) e che vi sia una relazione di cura. Per questo è
giusto informare l'osservato, in modo adatto alla sua età.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta

README = """CARTELLA RISERVATA — Osservazione dei momenti di difficoltà
============================================================

Contiene screenshot dell'interfaccia di CogniFlow catturati quando la
webcam ha rilevato una smorfia di difficoltà tenuta per qualche secondo,
insieme a un registro (eventi.jsonl) con data/ora e intensità.

A cosa serve
------------
Aiutare un genitore o uno psicologo a capire in quali attività l'utente
fatica di più, rileggendo insieme quei momenti.

Privacy
-------
- Sono immagini della SCHERMATA dell'app, non del volto della persona.
- Riguardano spesso un minore e possono rivelare informazioni sensibili:
  custodiscile con cura, non condividerle senza necessità e senza il
  consenso di chi esercita la responsabilità genitoriale.
- I file più vecchi del periodo di ritenzione impostato vengono
  cancellati automaticamente.
- Puoi svuotare questa cartella in qualsiasi momento.

Chi ha attivato la funzione se ne assume la responsabilità e dovrebbe
informare la persona osservata in modo adatto alla sua età.
"""


class DifficultyObserver:
    """Riceve l'indice di difficoltà e cattura la schermata quando serve.

    Non è un QObject: si collega a `VideoThread.difficulty_signal` da fuori
    e usa un `screenshot_provider` (callable che restituisce un QPixmap
    della finestra) per catturare senza dipendere dalla UI.
    """

    def __init__(
        self,
        output_dir,
        screenshot_provider,
        enabled=False,
        threshold=0.5,
        sustain_s=1.5,
        cooldown_s=20.0,
        retention_days=30,
        context_provider=None,
    ):
        self.output_dir = output_dir
        self._screenshot = screenshot_provider
        self.enabled = enabled
        self.threshold = threshold  # sopra questo indice è "difficoltà"
        self.sustain_s = sustain_s  # per quanto va tenuta prima di catturare
        self.cooldown_s = cooldown_s  # pausa minima tra due catture
        self.retention_days = retention_days
        self._context = context_provider  # opzionale: descrive cosa fa l'utente

        self._over_since = None
        self._last_capture = 0.0
        self._readme_done = False

    def on_difficulty(self, score):
        """Slot per VideoThread.difficulty_signal (indice 0..1)."""
        if not self.enabled:
            self._over_since = None
            return
        now = time.monotonic()
        if score < self.threshold:
            self._over_since = None
            return
        if self._over_since is None:
            self._over_since = now
            return
        if now - self._over_since < self.sustain_s:
            return
        if now - self._last_capture < self.cooldown_s:
            return
        self._last_capture = now
        self._over_since = None  # una cattura per episodio
        self._capture(score)

    def _ensure_dir(self):
        os.makedirs(self.output_dir, exist_ok=True)
        if not self._readme_done:
            readme_path = os.path.join(self.output_dir, "LEGGIMI.txt")
            try:
                if not os.path.exists(readme_path):
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(README)
            except OSError:
                pass
            self._readme_done = True

    def _capture(self, score):
        """Salva lo screenshot dell'interfaccia e registra l'evento.

        Silenzioso per l'utente: nessun pop-up, nessun suono. Gli errori
        vengono solo loggati, non devono mai disturbare la sessione.
        """
        try:
            pixmap = self._screenshot() if self._screenshot else None
            if pixmap is None or pixmap.isNull():
                return
            self._ensure_dir()
            self.purge_old()
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_name = f"difficolta_{stamp}.png"
            if not pixmap.save(os.path.join(self.output_dir, img_name), "PNG"):
                return
            entry = {
                "istante": datetime.now().isoformat(timespec="seconds"),
                "indice_difficolta": round(float(score), 3),
                "immagine": img_name,
            }
            if self._context is not None:
                try:
                    entry["contesto"] = str(self._context())
                except Exception:
                    pass
            with open(
                os.path.join(self.output_dir, "eventi.jsonl"),
                "a",
                encoding="utf-8",
            ) as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logging.info("Osservazione difficoltà: momento registrato (riservato)")
        except Exception as e:
            logging.warning(f"Osservazione difficoltà non riuscita: {e}")

    def purge_old(self):
        """Cancella gli screenshot più vecchi del periodo di ritenzione."""
        if self.retention_days <= 0 or not os.path.isdir(self.output_dir):
            return
        limite = datetime.now() - timedelta(days=self.retention_days)
        for name in os.listdir(self.output_dir):
            if not name.startswith("difficolta_") or not name.endswith(".png"):
                continue
            path = os.path.join(self.output_dir, name)
            try:
                if datetime.fromtimestamp(os.path.getmtime(path)) < limite:
                    os.remove(path)
            except OSError:
                pass
