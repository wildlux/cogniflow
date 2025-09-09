# Qt Design Studio Optimization Guide

## Overview
L'interfaccia QML è stata ottimizzata per Qt Design Studio e Qt Creator's Design mode, rendendo più facile la modifica visuale e la personalizzazione dei componenti.

## Ottimizzazioni Implementate

### 1. Proprietà Designer-Friendly
Tutti i componenti principali espongono proprietà facilmente modificabili dal designer:

#### ThemeManager
```qml
ThemeManager {
    currentTheme: 0  // Cambia da 0-9 per temi diversi
}
```

#### ControlPanel
```qml
ControlPanel {
    // Layout
    contentMargins: 10
    spacing: 10
    titleFontSize: 16

    // Visibilità sezioni
    showTTSPanel: true
    showThemePanel: true
    showAIPanel: true

    // Aspetto
    backgroundColor: themeManager.backgroundColor
    borderRadius: 5
}
```

#### AIResultsPanel
```qml
AIResultsPanel {
    // Layout
    itemHeight: 120
    maxPreviewLength: 50
    maxResponseLength: 250

    // Comportamento
    alternatingColors: true
    showTimestamps: true
    clipResponseText: true
}
```

#### WorkspacePensierini
```qml
WorkspacePensierini {
    // Layout
    itemHeight: 60
    buttonFontSize: 11

    // Comportamento
    showReadButton: true
    showExportButton: true
    alternatingColors: true
}
```

#### LogPanel
```qml
LogPanel {
    // Aspetto
    backgroundColor: "#1e1e1e"
    borderRadius: 8

    // Comportamento
    autoScroll: true
    maxMessages: 100
    showMessageCount: true
}
```

### 2. Stati Visivi
I componenti supportano stati per differenti modalità di visualizzazione:

```qml
ControlPanel {
    states: [
        State {
            name: "minimal"
            PropertyChanges { target: controlPanel; showTTSPanel: false }
        },
        State {
            name: "full"
            PropertyChanges { target: controlPanel; showTTSPanel: true }
        }
    ]
}
```

### 3. Alias per Componenti Interni
Ogni componente espone alias per accedere facilmente ai sotto-componenti:

```qml
ControlPanel {
    // Accesso diretto ai controlli interni
    property alias voiceCombo: voiceCombo
    property alias speedSlider: speedSlider
    property alias themeSelector: themeSelector
}
```

### 4. File di Risorse
È stato creato un file `resources.qrc` per gestire le risorse:

```xml
<!DOCTYPE RCC>
<RCC version="1.0">
<qresource>
    <file>../ICO-fonts-wallpaper/icon.png</file>
    <file>../ICO-fonts-wallpaper/ICONA.ico</file>
    <!-- ... altri file ... -->
</qresource>
</RCC>
```

## Come Usare in Qt Design Studio

### 1. Aprire il Progetto
1. Apri Qt Design Studio
2. Carica il progetto QML dalla cartella `UI/`
3. Il file principale è `main_interface.qml`

### 2. Modificare le Proprietà
1. Seleziona un componente nel pannello Navigator
2. Usa il pannello Properties per modificare:
   - Dimensioni e posizione
   - Colori e aspetto
   - Proprietà di layout
   - Stati e transizioni

### 3. Personalizzare i Temi
```qml
ThemeManager {
    currentTheme: 2  // Cambia per vedere temi diversi
}
```

### 4. Modificare il Layout
```qml
ControlPanel {
    SplitView.preferredWidth: 350  // Cambia larghezza
    contentMargins: 15             // Cambia margini
    spacing: 12                    // Cambia spaziatura
}
```

### 5. Controllare la Visibilità
```qml
ControlPanel {
    showTTSPanel: false    // Nasconde pannello TTS
    showThemePanel: true   // Mostra pannello temi
    showAIPanel: true      // Mostra pannello AI
}
```

## Proprietà Comuni

### Layout
- `contentMargins`: Margini interni
- `spacing`: Spaziatura tra elementi
- `preferredWidth/preferredHeight`: Dimensioni preferite

### Aspetto
- `backgroundColor`: Colore di sfondo
- `textColor`: Colore del testo
- `borderColor`: Colore del bordo
- `borderWidth`: Spessore del bordo
- `borderRadius`: Raggio degli angoli

### Tipografia
- `titleFontSize`: Dimensione titolo
- `labelFontSize`: Dimensione etichette
- `buttonFontSize`: Dimensione pulsanti
- `fontFamily`: Famiglia di font

### Comportamento
- `visible`: Visibilità componente
- `enabled`: Abilitazione interazione
- `clip`: Ritaglio contenuto

## Stati Disponibili

### ControlPanel
- `minimal`: Solo pannello AI
- `full`: Tutti i pannelli
- `compact`: Layout compatto

### LogPanel
- `expanded`: Altezza aumentata
- `compact`: Altezza ridotta
- `minimal`: Controlli nascosti

### AIResultsPanel
- `noResults`: Nessun risultato
- `hasResults`: Risultati presenti
- `compact`: Elementi più piccoli

### WorkspacePensierini
- `empty`: Nessun pensierino
- `hasItems`: Pensierini presenti
- `compact`: Layout compatto

## Transizioni

I componenti supportano transizioni fluide:

```qml
transitions: [
    Transition {
        NumberAnimation {
            properties: "height,width"
            duration: 200
            easing.type: Easing.InOutQuad
        }
    }
]
```

## Suggerimenti per il Designer

1. **Inizia dal ThemeManager** per impostare il tema base
2. **Usa gli stati** per creare diverse modalità di visualizzazione
3. **Modifica le proprietà di layout** per adattare alle tue esigenze
4. **Personalizza i colori** usando le proprietà esposte
5. **Testa le transizioni** cambiando stati diversi

## Esportazione

Una volta completata la personalizzazione:
1. Salva il progetto in Qt Design Studio
2. Esporta come file QML standard
3. Integra nel tuo progetto principale

## Risorse Aggiuntive

- [Qt Design Studio Documentation](https://doc.qt.io/qtdesignstudio/)
- [QML Property Documentation](https://doc.qt.io/qt-6/qml-properties.html)
- [Qt Quick Controls](https://doc.qt.io/qt-6/qtquickcontrols-index.html)