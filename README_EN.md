<div align="center">

# 🧠✨ CogniFlow

### The DSA assistant you control with your hands, your voice, and your mind

**[English]** &nbsp;•&nbsp; [**Italiano**](README.md) &nbsp;•&nbsp; Accessibility &nbsp;•&nbsp; Local AI &nbsp;•&nbsp; 100% Privacy

</div>

---

> *"I have dyslexia, and I built this software to help other people with disabilities, offering a fully accessible and safe interface."*

CogniFlow comes from a personal story: **cogni** (cognition) and **flow** (like an arrow showing direction). It's an assistant designed for people living with DSA (learning disorders) or motor disabilities — capable of turning a simple webcam into a **hand-mouse**, a hand into **written words**, and your voice into **commands** — all **offline, without sending a single piece of data to the cloud**.

---

<div align="center">

![Hand gesture tracking in front of the webcam](Tracking-gesture.png)

</div>

---

## 🚀 What it can do

| | Feature | How it works |
|---|---|---|
| 🖐️ | **Hand-Mouse** | The cursor follows your hand in front of the webcam: close your fist to click, raise your index finger to write in the air |
| 🤟 | **Fingerspelling (manual alphabet)** | Type with the A–Y manual alphabet, with calibration of your own signs, a deletion gesture, and motion letters (J, Z) |
| ✍️ | **Air drawing (ink)** | Draw without touching anything, with a handy "💧" toggle and dwell to avoid accidental commands |
| 🤲 | **Two-hand selection** | Point to the start with one hand and the end with the other to select text, then read, copy, or ask the AI |
| ⏱️ | **Global dwell click** | Rest ~1 second on an element and it gets clicked: works with both mouse and hand-mouse, anywhere in the interface |
| ⌨️ | **On-screen keyboard** | Large keys, word prediction (Italian + English, offline), single-signal **scanning** — the bridge to BCIs |
| 🗣️ | **Voice** | Multilingual speech recognition and legible text-to-speech (Vosk + espeak-ng, offline) |
| 🤖 | **Local AI** | Chat with Ollama for homework help, summaries, and suggestions — no Internet required |
| 👁️ | **Vision & OCR** | OpenCV + webcam and optical character recognition to read the world around you |

> 🔭 **Looking ahead:** the on-screen keyboard is already built for *single-signal scanning* — the natural stepping stone toward a **brain-computer interface (BCI)**.

---

## 👨‍🎓 Built for accessibility

- **Dyslexia support**: OpenDyslexic font, adaptive layout, voice reading and navigation
- **Multiple themes**: dark, light, and high contrast; font scale from 12pt to 24pt
- **One hand is enough**: every feature is reachable with the pointer alone
- **Always-visible feedback**: the state of every gesture is shown on the interface
- 🔒 **Difficulty observation**: (optional, with consent) detects moments of difficulty and saves a screenshot of the interface — never the face — for parents and clinicians

---

## 🛡️ Security & Privacy

CogniFlow is **private by design**: the artificial intelligence runs entirely on your computer.

- 🔐 **AES-256 encryption** for sensitive data
- 🧂 **PBKDF2 with salt** for strong passwords
- 🛡️ **100% local AI** — zero data sent to the cloud
- 🔍 **Automatic dependency vulnerability scanning**
- 🧪 **Input validation** against injection and rate limiting against brute force
- 📜 **Full audit logging** of activity
- 🚪 **Protected session** with login and logout

---

## 🏗️ Architecture

- **Modular**: isolated, easily maintainable components
- **Zero-Trust**: every operation validated and authorized
- **Fail-Safe**: controlled degradation if a component fails
- **Audit-Ready**: complete logging for compliance

---

## 🚀 Installation

### Prerequisites

- **Python 3.8+**
- **Tesseract OCR** (for text recognition)
- **Ollama** (optional, for local AI)

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip tesseract-ocr

# macOS
brew install python@3.8 tesseract

# Windows
# → Python 3.8+ from python.org
# → Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
```

### Quick start

```bash
# 1. Clone the repository
git clone <repository-url>
cd CogniFlow

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the assistant
make run
# or
./avvia_cogniflow.sh
# or
python3 -m assistente_dsa
```

---

## 🧪 Testing & development

```bash
# Run the test suite
make test            # pytest tests/ -v

# Lint and type-check
make lint
make type-check

# Full development cycle
make dev             # format → lint → test
```

Want to contribute? Read [CONTRIBUTING.md](CONTRIBUTING.md) — you'll need a Fork, thorough testing, and no hardcoded credentials. 🍴

---

## 📦 Main requirements

| Category | Dependency |
|---|---|
| Core | Python 3.8+, PyQt6 |
| AI | Ollama (local) |
| Voice | Vosk (offline STT), espeak-ng (TTS) |
| Vision | OpenCV 4.8+, Tesseract OCR |
| Security | cryptography |

---

## 📌 Roadmap

- [ ] Two-factor authentication (2FA)
- [ ] Encryption at rest for the reserved folder
- [ ] Summary report of difficulties for the clinician
- [ ] Preparation for brain-computer interface (BCI) connection
- [ ] Refining AI suggestions with sentence context

---

<div align="center">

**🔒 Your safety is our priority: CogniFlow is secure by default.**

Questions or ideas? Open an issue! Thanks for choosing CogniFlow. 🚀

</div>