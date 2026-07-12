# Contributing to CogniFlow

Grazie per il tuo interesse nel contribuire a CogniFlow! Questo documento spiega come contribuire al progetto.

## 🚀 Come Iniziare

1. **Fork** il repository
2. **Clona** il tuo fork: `git clone https://github.com/yourusername/cogniflow.git`
3. **Crea un branch** per le tue modifiche: `git checkout -b feature/nome-feature`
4. **Installa dipendenze**: `pip install -r requirements.txt`
5. **Installa dipendenze dev**: `pip install -e ".[dev]"`

## 📝 Standard di Codice

### Python
- Segui [PEP 8](https://pep8.org/) per lo stile del codice
- Usa [type hints](https://docs.python.org/3/library/typing.html) dove possibile
- Scrivi docstring per tutte le funzioni e classi pubbliche
- Limite righe a 120 caratteri

### Controllo Qualità
```bash
# Linting
flake8 assistente_dsa/

# Type checking (opzionale)
mypy assistente_dsa/

# Formattazione (opzionale)
black assistente_dsa/
```

## 🧪 Testing

- Scrivi test per nuove funzionalità
- Esegui test esistenti prima di pushare
- Mantieni coverage > 80%

```bash
# Esegui tutti i test
pytest

# Con coverage
pytest --cov=assistente_dsa
```

## 📋 Checklist PR

Prima di sottomettere una PR:

- [ ] Codice formattato correttamente
- [ ] Test aggiunti/modificati
- [ ] Documentazione aggiornata
- [ ] Nessun errore di linting
- [ ] Funzionalità testate manualmente
- [ ] Backward compatibility mantenuta

## 🐛 Segnalazione Bug

Usa il template GitHub Issues per segnalare bug. Includi:

- Descrizione chiara del problema
- Steps to reproduce
- Expected vs actual behavior
- Screenshots se applicabile
- Informazioni di sistema (OS, Python version)

## 💡 Suggerimenti per Nuove Feature

- Discuti prima nel repository Issues
- Fornisci mockups/UI designs per features UI
- Considera l'impatto su accessibilità e usabilità
- Valuta complessità di implementazione

## 🎯 Aree di Contributo Prioritarie

1. **Accessibilità**: Miglioramenti per utenti con disabilità
2. **Performance**: Ottimizzazioni e profiling
3. **Test**: Aumento coverage e qualità test
4. **Documentazione**: Guide utente e API docs
5. **Internazionalizzazione**: Supporto lingue multiple
6. **Nuove funzionalità AI**: Integrazione nuovi modelli

## 📞 Contatti

- **Issues**: [GitHub Issues](https://github.com/yourusername/cogniflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cogniflow/discussions)

Grazie per contribuire a rendere CogniFlow migliore! 🎉