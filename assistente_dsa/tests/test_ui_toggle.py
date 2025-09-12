#!/usr/bin/env python3
"""
Script di test per analizzare il comportamento del pulsante toggle degli strumenti.
Questo script avvia l'applicazione e testa automaticamente il pulsante toggle
per raccogliere dati sui movimenti dell'interfaccia.
"""

import sys
import os
import time
import json
from pathlib import Path

# Aggiungi il percorso del progetto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def analyze_ui_logs():
    """Analizza i log delle metriche UI per identificare il problema."""
    log_file = project_root / "assistente_dsa" / "debug_logs" / "ui_metrics.jsonl"

    if not log_file.exists():
        print(
            "❌ File di log non trovato. Avvia prima l'applicazione per generare i dati."
        )
        return

    print("📊 Analisi dei log UI...")
    print("=" * 50)

    # Leggi tutti i log
    logs = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

    if not logs:
        print("❌ Nessun dato valido nei log.")
        return

    # Raggruppa per contesto
    contexts = {}
    for log in logs:
        context = log.get("context", "UNKNOWN")
        if context not in contexts:
            contexts[context] = []
        contexts[context].append(log)

    # Analizza i dati
    for context, context_logs in contexts.items():
        print(f"\n🔍 Contesto: {context}")
        print(f"   Numero di misurazioni: {len(context_logs)}")

        if context_logs:
            # Prendi l'ultimo log per questo contesto
            log = context_logs[-1]
            window = log.get("window", {})
            buttons = log.get("buttons", {})

            print(
                f"   📐 Finestra: {window.get('size', 'N/A')} @ {window.get('pos', 'N/A')}"
            )

            for btn_name, btn_data in buttons.items():
                pos = btn_data.get("pos", "N/A")
                size = btn_data.get("size", "N/A")
                print(f"   🔘 {btn_name}: pos={pos}, size={size}")

            splitter_sizes = log.get("splitter_sizes")
            if splitter_sizes:
                print(f"   📊 Splitter: {splitter_sizes}")

    # Analizza i cambiamenti tra contesti
    print("\n" + "=" * 50)
    print("🔄 Analisi dei cambiamenti:")

    if "BEFORE_TOGGLE" in contexts and "AFTER_TOGGLE_START" in contexts:
        before = contexts["BEFORE_TOGGLE"][-1]
        after = contexts["AFTER_TOGGLE_START"][-1]

        print("\n📈 Cambiamenti finestra:")
        before_window = before.get("window", {})
        after_window = after.get("window", {})

        before_size = before_window.get("size", (0, 0))
        after_size = after_window.get("size", (0, 0))
        print(f"   Dimensione: {before_size} → {after_size}")

        before_pos = before_window.get("pos", (0, 0))
        after_pos = after_window.get("pos", (0, 0))
        print(f"   Posizione: {before_pos} → {after_pos}")

        print("\n🔘 Cambiamenti pulsanti:")
        before_buttons = before.get("buttons", {})
        after_buttons = after.get("buttons", {})

        all_buttons = set(before_buttons.keys()) | set(after_buttons.keys())

        for btn_name in all_buttons:
            before_btn = before_buttons.get(btn_name, {})
            after_btn = after_buttons.get(btn_name, {})

            before_pos = before_btn.get("pos", "N/A")
            after_pos = after_btn.get("pos", "N/A")

            if before_pos != after_pos:
                print(f"   {btn_name}: {before_pos} → {after_pos} ⚠️ CAMBIATO")
            else:
                print(f"   {btn_name}: {before_pos} → {after_pos} ✅ STABILE")

        print("\n📊 Cambiamenti splitter:")
        before_splitter = before.get("splitter_sizes")
        after_splitter = after.get("splitter_sizes")
        print(f"   Splitter: {before_splitter} → {after_splitter}")


def main():
    """Funzione principale per testare l'interfaccia."""
    print("🚀 Avvio test interfaccia CogniFlow...")
    print(
        "Questo script analizzerà i movimenti dell'interfaccia quando premi il pulsante '🔧 Ingranaggi'"
    )
    print()

    # Controlla se ci sono già dei log precedenti
    log_file = project_root / "assistente_dsa" / "debug_logs" / "ui_metrics.jsonl"
    if log_file.exists():
        print("📁 Trovati log precedenti. Li analizzerò dopo il test.")
        print()

    print("📋 Istruzioni:")
    print("1. L'applicazione si avvierà automaticamente")
    print("2. Premi il pulsante '🔧 Ingranaggi' per attivare/disattivare il pannello")
    print("3. Chiudi l'applicazione quando hai finito")
    print("4. Verranno analizzati automaticamente i dati raccolti")
    print()

    try:
        # Importa e avvia l'applicazione
        from assistente_dsa.main_01_Aircraft import MainWindow
        from PyQt6.QtWidgets import QApplication

        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()

        print("✅ Applicazione avviata. Inizia il test!")
        print("Premi Ctrl+C nella console per interrompere...")

        # Avvia l'applicazione
        result = app.exec()

        print("\n🔍 Analisi dei dati raccolti...")
        analyze_ui_logs()

        return result

    except KeyboardInterrupt:
        print("\n⏹️ Test interrotto dall'utente.")
        analyze_ui_logs()
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
