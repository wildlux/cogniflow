<div align="center">

# 🧠✨ CogniFlow

### L'assistente DSA che si controlla con le mani, la voce e la mente

**[Italiano]** &nbsp;•&nbsp; [**English**](README_EN.md) &nbsp;•&nbsp; Accessibilità &nbsp;•&nbsp; AI Locale &nbsp;•&nbsp; 100% Privacy

</div>

---

> *"Sono dislessico e ho creato questo software per aiutare altre persone con disabilità, offrendo un'interfaccia completamente accessibile e sicura."*

CogniFlow nasce da una storia personale: **cogni** (cognizione) e **flow** (come una freccia che indica direzione). È un assistente progettato per chi vive con DSA o disabilità motorie, capace di trasformare una semplice webcam in un **mano-mouse**, una mano in **parola scritta** e la voce in **comando** — il tutto **offline e senza inviare un solo dato al cloud**.

---

<div align="center">

![Tracciamento dei gesti con la mano davanti alla webcam](Tracking-gesture.png)

</div>

---

## 🚀 Cosa sa fare

| | Funzionalità | Come funziona |
|---|---|---|
| 🖐️ | **Mano-Mouse** | Il cursore segue la tua mano davanti alla webcam: chiudi il pugno per cliccare, alza l'indice per scrivere in aria |
| 🤟 | **Dattilologia** | Scrivi con l'alfabeto manuale A–Y, con calibrazione dei tuoi segni, gesto di cancellazione e lettere a movimento (J, Z) |
| ✍️ | **Inchiostro in aria** | Disegna senza toccare nulla, con un comodo interruttore "💧" e dwell per evitare comandi accidentali |
| 🤲 | **Selezione a due mani** | Indica l'inizio con una mano e la fine con l'altra per selezionare il testo, poi leggi, copia o chiedi all'AI |
| ⏱️ | **Dwell click globale** | Sosta ~1 secondo su un elemento e viene cliccato: funziona con mouse e mano-mouse, ovunque nell'interfaccia |
| ⌨️ | **Tastiera virtuale** | Tasti grandi, predizione parole (italiano + inglese, offline), **scansione** a singolo segnale — il ponte verso le BCI |
| 🗣️ | **Voce** | Riconoscimento vocale multilingua e sintesi vocale leggibile (Vosk + espeak-ng, offline) |
| 🤖 | **AI Locale** | Chat con Ollama per ricevere aiuto sui compiti, riassunti e suggerimenti — senza Internet |
| 👁️ | **Visione & OCR** | OpenCV + webcam e riconoscimento ottico dei caratteri per leggere il mondo intorno a te |

> 🔭 **Sguardo al futuro:** la tastiera virtuale è già predisposta per la *scansione a singolo segnale* — il passo naturale verso il collegamento **brain-computer (BCI)**.

---

## 👨‍🎓 Pensata per l'accessibilità

- **Supporto dislessia**: font OpenDyslexic, layout adattivo, lettura e navigazione vocale
- **Temi multipli**: scuro, chiaro e ad alto contrasto; scala font da 12pt a 24pt
- **Una sola mano basta**: ogni funzione è raggiungibile con il solo puntatore
- **Feedback sempre visibile**: lo stato di ogni gesto è mostrato sull'interfaccia
- 🔒 **Osservazione difficoltà**: (opzionale, con consenso) rileva i momenti di difficoltà e salva uno screenshot dell'interfaccia — mai del volto — per genitori e clinici

---

## 🛡️ Sicurezza e Privacy

CogniFlow è **privato per design**: l'intelligenza artificiale gira interamente sul tuo computer.

- 🔐 **Crittografia AES-256** per i dati sensibili
- 🧂 **PBKDF2 con salt** per password sicure
- 🛡️ **AI 100% locale** — zero dati inviati al cloud
- 🔍 **Scansione vulnerabilità** automatica delle dipendenze
- 🧪 **Validazione input** anti-injection e rate limiting anti brute-force
- 📜 **Audit logging** completo delle attività
- 🚪 **Sessione protetta** con accesso e logout

---

## 🏗️ Architettura

- **Modulare**: componenti isolati e facilmente manutenibili
- **Zero-Trust**: ogni operazione validata e autorizzata
- **Fail-Safe**: degradazione controllata se un componente fallisce
- **Audit-Ready**: logging completo per la conformità

---

## 🚀 Installazione

### Prerequisiti

- **Python 3.8+**
- **Tesseract OCR** (per il riconoscimento testi)
- **Ollama** (opzionale, per l'AI locale)

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip tesseract-ocr

# macOS
brew install python@3.8 tesseract

# Windows
# → Python 3.8+ da python.org
# → Tesseract da https://github.com/UB-Mannheim/tesseract/wiki
```

### Avvio rapido

```bash
# 1. Clona il repository
git clone <repository-url>
cd CogniFlow

# 2. Crea un ambiente virtuale
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Avvia l'assistente
make run
# oppure
./avvia_cogniflow.sh
# oppure
python3 -m assistente_dsa
```

---

## 🧪 Test e sviluppo

```bash
# Esegui la suite di test
make test            # pytest tests/ -v

# Lint e type-check
make lint
make type-check

# Ciclo completo di sviluppo
make dev             # format → lint → test
```

Vuoi contribuire? Leggi [CONTRIBUTING.md](CONTRIBUTING.md) — serve un `Fork`, test approfonditi e nessuna credenziale hardcoded. 🍴

---

## 📦 Requisiti principali

| Categoria | Dipendenza |
|---|---|
| Core | Python 3.8+, PyQt6 |
| AI | Ollama (locale) |
| Voce | Vosk (STT offline), espeak-ng (TTS) |
| Vista | OpenCV 4.8+, Tesseract OCR |
| Sicurezza | cryptography |

---

## 📌 Roadmap

- [ ] Autenticazione a due fattori (2FA)
- [ ] Crittografia a riposo della cartella riservata
- [ ] Report riassuntivo delle difficoltà per il clinico
- [ ] Predisposizione al collegamento brain-computer (BCI)
- [ ] Raffinamento dei suggerimenti AI con il contesto di frase

---

<div align="center">

**🔒 La tua sicurezza è la nostra priorità: CogniFlow è sicuro per default.**

Se hai domande o idee, apri un'issue! Grazie per aver scelto CogniFlow. 🚀

</div>