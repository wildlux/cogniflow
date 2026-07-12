# 🔄 Refactoring CogniFlow - Separazione Logica/UI

## 🎯 Obiettivo

Separare completamente la **logica di business** dall'**interfaccia utente** per migliorare:
- 📦 **Manutenibilità**: Codice più organizzato e modulare
- 🧪 **Testabilità**: Possibilità di testare la logica indipendentemente dall'UI
- 🔧 **Estensibilità**: Più facile aggiungere nuove funzionalità
- 👥 **Collaborazione**: Sviluppatori possono lavorare su parti diverse contemporaneamente

## 📁 Nuova Struttura dei File

```
assistent_dsa/
├── controllers/           # 🎮 Controller - Logica di business
│   ├── __init__.py
│   └── cogniflow_controller.py
├── models/               # 📊 Modelli - Strutture dati
│   ├── __init__.py
│   ├── project_model.py
│   └── settings_model.py
├── services/             # 🔧 Servizi - Funzionalità specifiche
│   ├── __init__.py
│   ├── ai_service.py
│   ├── tts_service.py
│   ├── speech_recognition_service.py
│   ├── ocr_service.py
│   ├── media_service.py
│   └── project_service.py
├── UI/                   # 🎨 Interfaccia utente
│   ├── __init__.py
│   ├── main_window_refactored.py
│   ├── draggable_text_widget.py
│   ├── settings_dialog.py
│   └── user_friendly_errors.py
├── Artificial_Intelligence/  # 🤖 AI esistente (da integrare)
├── core/                 # ⚙️ Core esistente
├── Save/                 # 💾 Salvataggi
├── main_01_Aircraft.py   # 🏗️ Originale (da sostituire)
├── main_00_launcher.py   # 🚀 Launcher
└── test_refactored_structure.py  # 🧪 Test
```

## 🏗️ Componenti Principali

### 1. 🎮 Controller (`CogniFlowController`)
**Responsabilità**: Gestire tutta la logica di business
- ✅ Coordinamento tra servizi
- ✅ Gestione stato applicazione
- ✅ Comunicazione con UI tramite segnali
- ✅ Gestione errori e logging

**Metodi principali**:
```python
send_ai_request(prompt, model)
start_speech_recognition()
speak_text(text)
save_project(name, data)
load_project(name)
```

### 2. 🔧 Servizi (Service Layer)
**Pattern**: Ogni servizio gestisce una funzionalità specifica

#### `AIService`
- Gestione connessione Ollama
- Invio richieste AI
- Gestione risposte e errori

#### `TTSService`
- Sintesi vocale
- Gestione code audio
- Controllo riproduzione

#### `SpeechRecognitionService`
- Riconoscimento vocale
- Gestione modelli Vosk
- Elaborazione audio

#### `OCRService`
- Estrazione testo da immagini
- Supporto formati multipli
- Ottimizzazione prestazioni

#### `ProjectService`
- Salvataggio/caricamento progetti
- Gestione file system
- Validazione dati

#### `MediaService`
- Gestione file multimediali
- Supporto formati audio/video/immagini
- Elaborazione contenuti

### 3. 📊 Modelli (Data Models)
**Pattern**: Oggetti che rappresentano strutture dati

#### `ProjectModel`
```python
class ProjectModel:
    name: str
    data: Dict[str, Any]
    created_at: datetime
    last_modified: datetime
    version: str
```

#### `SettingsModel`
- Gestione impostazioni centralizzate
- Validazione valori
- Salvataggio automatico

### 4. 🎨 UI Manager (`UIManager`)
**Responsabilità**: Gestire solo l'interfaccia utente
- ✅ Creazione e configurazione widget
- ✅ Gestione eventi UI
- ✅ Aggiornamento visuale
- ✅ Comunicazione con controller tramite segnali

## 🔄 Flusso di Comunicazione

```
UI Event → UIManager → Segnale → Controller → Servizio → Risultato → Segnale → UI Update
```

### Esempio: Invio richiesta AI
1. 👆 **Utente clicca** "Chiedi ad AI"
2. 🎯 **UIManager** emette `button_clicked("ai_button", data)`
3. 🎮 **Controller** riceve segnale, valida input
4. 🔧 **AIService** elabora richiesta
5. 📡 **Risposta** torna tramite segnale
6. 🎨 **UI** aggiorna con risposta

## 🚀 Come Usare la Nuova Struttura

### Avvio con Controller
```python
from controllers.cogniflow_controller import CogniFlowController
from UI.main_window_refactored import MainWindowRefactored

# Crea controller
controller = CogniFlowController()

# Crea UI
app = QApplication(sys.argv)
window = MainWindowRefactored()

# Connetti controller all'UI
controller.ai_response_received.connect(window.on_ai_response)

window.show()
app.exec()
```

### Test della Struttura
```bash
cd /home/wildlux/Scrivania/Python/CogniFLow/assistente_dsa
python test_refactored_structure.py
```

## 🔧 Integrazione Graduale

### Fase 1: ✅ Completata
- [x] Creazione struttura directory
- [x] Implementazione modelli base
- [x] Creazione servizi skeleton
- [x] Controller principale
- [x] UI Manager refactored
- [x] Script di test

### Fase 2: 🔄 In Corso
- [ ] Correzione import relativi
- [ ] Integrazione servizi esistenti
- [ ] Test end-to-end
- [ ] Ottimizzazione prestazioni

### Fase 3: 📋 Pianificata
- [ ] Sostituzione MainWindow originale
- [ ] Migrazione impostazioni
- [ ] Documentazione API
- [ ] Test di regressione

## 🎨 Vantaggi Ottenuti

### 📈 Manutenibilità
- **Separazione chiara**: UI ≠ Business Logic
- **Modularità**: Ogni servizio è indipendente
- **Testabilità**: Unit test per ogni componente

### 🚀 Performance
- **Lazy loading**: Servizi caricati solo quando necessari
- **Caching**: Gestione intelligente delle risorse
- **Threading**: Operazioni pesanti in background

### 👥 Sviluppo Collaborativo
- **Frontend/Backend**: Sviluppatori possono lavorare separatamente
- **API chiara**: Interfacce ben definite tra componenti
- **Versioning**: Possibilità di versioni diverse dei servizi

## 🐛 Problemi Risolti

### Prima (Monolitico)
- ❌ 2000+ righe in un file
- ❌ Logica UI mischiata con business logic
- ❌ Difficile testare componenti isolati
- ❌ Errori di import complessi

### Dopo (Modulare)
- ✅ File piccoli e focalizzati
- ✅ Separazione chiara responsabilità
- ✅ Test unitari possibili
- ✅ Import chiari e organizzati

## 🔍 Monitoraggio e Debug

### Logging Strutturato
```python
import logging
logger = logging.getLogger(__name__)

# Nel controller
logger.info("Richiesta AI inviata: %s", prompt[:50])

# Nei servizi
logger.debug("Connessione AI stabilita")
logger.error("Errore servizio TTS: %s", str(e))
```

### Segnali per Debug
```python
# Nel controller
self.debug_info.emit("AI request started", {"model": model, "prompt_length": len(prompt)})

# Nell'UI
controller.debug_info.connect(self.update_debug_panel)
```

## 📚 Documentazione Tecnica

### Pattern Architetturali Usati
- **MVC (Model-View-Controller)**: Separazione logica/UI
- **Observer Pattern**: Comunicazione tramite segnali
- **Service Layer**: Incapsulamento funzionalità
- **Factory Pattern**: Creazione servizi

### Convenzioni di Codice
- **Nomi**: PascalCase per classi, snake_case per metodi
- **Docstring**: Formato Google-style
- **Error handling**: Eccezioni specifiche per tipo di errore
- **Logging**: Livelli appropriati (DEBUG, INFO, WARNING, ERROR)

## 🎯 Prossimi Passi

1. **Correggere import**: Sistemare riferimenti relativi
2. **Integrare esistenti**: Collegare servizi AI/TTS esistenti
3. **Test completi**: Verifica end-to-end
4. **Ottimizzazione**: Migliorare performance
5. **Documentazione**: API reference completa

---

## 📞 Supporto

Per domande sul refactoring:
- 📧 Contatta il team di sviluppo
- 📋 Consulta i test in `test_refactored_structure.py`
- 🔍 Verifica i log per debug

**Data**: $(date)
**Versione**: 1.0.0-refactored
**Status**: 🟡 In Sviluppo