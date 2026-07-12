# CogniFlow - Assistente DSA

**Versione Sicura e Accessibile - Ultimo Aggiornamento: 2025**

Questo software si chiama CogniFlow perché usa "cogni" (cognizione) e "flow" (come una freccia che indica direzione).

Sono dislessico e ho creato questo software per aiutare altre persone con disabilità, offrendo un'interfaccia completamente accessibile e sicura.

## 🔒 Sicurezza e Privacy

**🛡️ Caratteristiche di Sicurezza:**
- ✅ **Crittografia AES-256** per dati sensibili
- ✅ **Password sicure** con PBKDF2 e salt
- ✅ **Scansione vulnerabilità** automatica delle dipendenze
- ✅ **Validazione input** avanzata contro injection
- ✅ **Rate limiting** per prevenzione brute force
- ✅ **Audit logging** completo delle attività
- ✅ **AI Locale** - Nessun dato inviato al cloud

## 🎯 Funzionalità Principali

1. ✅ **Lettura Testo Accessibile** - Sintesi vocale con supporto dislessia
2. ✅ **Input Vocale Intelligente** - Riconoscimento vocale multilingua
3. ✅ **AI Locale Sicura** - Chat con Ollama (100% privacy)
4. 🔄 **Visione Artificiale** - OpenCV + webcam per riconoscimento
5. ✅ **Setup Sicuro** - Configurazione guidata con validazione
6. ✅ **Gestione Documenti** - Salvataggio/caricamento sicuro
7. 🔄 **Menu Aiuto Avanzato** - Snippet codice e workflow automatizzati
8. 🔄 **OCR Intelligente** - Riconoscimento ottico caratteri

## 🏗️ Architettura Sicura

- **Modulare**: Componenti isolati per massima sicurezza
- **Zero-Trust**: Ogni operazione validata e autorizzata
- **Fail-Safe**: Graceful degradation se componenti falliscono
- **Audit-Ready**: Logging completo per compliance

## 🚀 Installazione Sicura

### Prerequisiti di Sistema
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.8 python3-pip tesseract-ocr

# macOS
brew install python@3.8 tesseract

# Windows
# Installa Python 3.8+ da python.org
# Installa Tesseract da https://github.com/UB-Mannheim/tesseract/wiki
```

### Installazione Guidata
```bash
# 1. Clona il repository
git clone <repository-url>
cd CogniFlow

# 2. Crea ambiente virtuale (raccomandato)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# 3. Installa dipendenze sicure
pip install -r requirements.txt

# 4. Verifica sicurezza
python3 -c "from assistente_dsa.core.security_monitor import security_monitor; print('✅ Sicurezza OK')"

# 5. Setup iniziale sicuro
python3 assistente_dsa/main_00_launcher.py
```

### Configurazione Post-Installazione
1. **Primo Avvio**: Il sistema richiede configurazione amministratore sicura
2. **Password Sicura**: Minimo 12 caratteri con maiuscole, minuscole, numeri, speciali
3. **Verifica Dipendenze**: Scansione automatica vulnerabilità
4. **Test Sicurezza**: Esecuzione test di sicurezza integrati

## 📋 Requisiti Dettagliati

### Dipendenze Core (Sicure)
- **Python 3.8+** - Versione LTS con supporto sicurezza
- **PyQt6 6.5.0+** - GUI moderna e sicura
- **cryptography** - Crittografia avanzata
- **Ollama** - AI locale (esterno, sicuro)

### Dipendenze Opzionali
- **OpenCV 4.8.0+** - Visione artificiale
- **Tesseract OCR** - Riconoscimento testo
- **Vosk** - Riconoscimento vocale offline

## 🔐 Sicurezza Avanzata

### Autenticazione
- **Multi-fattore**: Supporto futuro per 2FA
- **Session Management**: Timeout automatico sessioni
- **Brute Force Protection**: Rate limiting intelligente
- **Password Policy**: Complessità configurabile

### Crittografia
- **AES-256**: Per dati a riposo
- **TLS 1.3**: Per comunicazioni (quando applicabile)
- **Hash Sicuri**: PBKDF2 con salt per password
- **Key Management**: Rotazione chiavi automatica

### Monitoraggio
- **Security Dashboard**: Monitoraggio real-time
- **Alert System**: Notifiche sicurezza automatiche
- **Audit Logs**: Tracciamento completo attività
- **Performance Monitoring**: Rilevamento anomalie

## 🎨 Accessibilità

### Supporto Dislessia
- **Font Specializzati**: OpenDyslexic integrato
- **Layout Adattivo**: Spaziatura e colori ottimizzati
- **Lettura Vocale**: Sintesi naturale e chiara
- **Navigazione Vocale**: Comandi vocali completi

### Inclusione
- **Temi Multipli**: Scuro, chiaro, ad alto contrasto
- **Scala Font**: Da 12pt a 24pt
- **Keyboard Navigation**: Accessibilità completa tastiera
- **Screen Reader**: Supporto completo

## 🛠️ Sviluppo e Contributi

### Setup Sviluppo Sicuro
```bash
# Installa dipendenze sviluppo
pip install -r requirements-dev.txt

# Esegui test sicurezza
python3 -m pytest tests/test_security.py -v

# Verifica vulnerabilità
python3 -c "from assistente_dsa.main_00_launcher import check_dependency_vulnerabilities; check_dependency_vulnerabilities()"
```

### Linee Guida Sicurezza
1. **Mai hardcoded credentials** nel codice
2. **Sempre validare input** utente
3. **Usare parameterized queries** per database
4. **Log attività sensibili** senza esporre dati
5. **Test sicurezza** prima del commit

### Contributi
- 🍴 **Fork** il progetto
- 🐛 **Segnala** vulnerabilità in privato
- 📝 **Documenta** nuove funzionalità
- ✅ **Test** thoroughly prima del PR

## 📞 Supporto e Sicurezza

### Segnalazione Vulnerabilità
- 📧 **Email**: security@cogniflow.local
- 🔒 **PGP Key**: Disponibile su richiesta
- ⏰ **Response Time**: < 24 ore per vulnerabilità critiche

### Documentazione Tecnica
- 📚 **API Docs**: `/docs/api/`
- 🔧 **Setup Guide**: `/docs/setup/`
- 🛡️ **Security Guide**: `/docs/security/`

## 📈 Roadmap Sicurezza

### Q1 2025
- [ ] Implementazione 2FA
- [ ] Encryption at-rest completa
- [ ] Security dashboard avanzato

### Q2 2025
- [ ] Audit logging centralizzato
- [ ] Container security hardening
- [ ] Automated security testing

### Q3 2025
- [ ] Zero-trust architecture
- [ ] Advanced threat detection
- [ ] Compliance automation

---

**🔒 La tua sicurezza è la nostra priorità. CogniFlow è progettato per essere sicuro per default.**

Grazie per aver scelto CogniFlow! 🚀
