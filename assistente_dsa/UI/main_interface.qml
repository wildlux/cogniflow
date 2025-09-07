// main_interface.qml
// Interfaccia principale QML per l'Assistente DSA

import QtQuick 6.2
import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2
import QtQuick.Dialogs 6.2

ApplicationWindow {
    id: mainWindow
    width: 1400
    height: 800
    visible: true
    title: "🤖 Assistente DSA - Interfaccia Principale"

    // Proprietà per la gestione dello stato
    property bool isReading: false
    property bool isRecording: false
    property string currentText: ""
    property var settings: ({})
    property bool useShiftEnterForNewline: true  // Configurable setting
    property string selectedModel: "llama2:7b"  // Selected AI model
    property var availableModels: ["llama2:7b", "codellama:7b", "llava:7b"]  // Available models
    property bool showLogMessages: true  // Toggle per visualizzare messaggi log (ora visibile per default)
    property var workspacePensierini: []  // Pensierini nell'area di lavoro

    // FileDialog per esportare pensierini
    FileDialog {
        id: exportPensieriniDialog
        title: "Esporta Pensierini"
        nameFilters: ["File JSON (*.json)", "File di testo (*.txt)"]
        defaultSuffix: "json"
        onAccepted: {
            var exportData = {
                "export_timestamp": new Date().toISOString(),
                "pensierini_count": workspacePensierini.length,
                "pensierini": workspacePensierini
            }

            var filePath = exportPensieriniDialog.selectedFile.toString()
            if (filePath.startsWith("file://")) {
                filePath = filePath.substring(7) // Rimuovi "file://" prefix
            }

            var jsonString = JSON.stringify(exportData, null, 2)

            // Qui dovremmo salvare su file, ma per ora mostriamo il contenuto
            console.log("💾 Salvataggio su file:", filePath)
            console.log("📄 Contenuto:", jsonString)

            addLogMessage("INFO", "Pensierini esportati su file: " + filePath)
        }
    }

    // Keyboard shortcuts
    Shortcut {
        sequence: "Ctrl+S"
        onActivated: saveContent()
    }

    Shortcut {
        sequence: "Ctrl+L"
        onActivated: loadContent()
    }

    // Sistema di temi dell'applicazione
    property int currentTheme: 0  // 0-9 per 10 temi diversi

    // Definizione dei 10 temi
    property var themes: [
        // Tema 0: Classico (Blu)
        {
            primaryColor: "#4a90e2",
            secondaryColor: "#f39c12",
            successColor: "#27ae60",
            errorColor: "#e74c3c",
            backgroundColor: "#f8f9fa",
            textColor: "#000000"
        },
        // Tema 1: Scuro
        {
            primaryColor: "#6c757d",
            secondaryColor: "#495057",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#343a40",
            textColor: "#ffffff"
        },
        // Tema 2: Chiaro
        {
            primaryColor: "#007bff",
            secondaryColor: "#6c757d",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#ffffff",
            textColor: "#000000"
        },
        // Tema 3: Natura (Verdi)
        {
            primaryColor: "#28a745",
            secondaryColor: "#20c997",
            successColor: "#17a2b8",
            errorColor: "#dc3545",
            backgroundColor: "#f8fff8",
            textColor: "#155724"
        },
        // Tema 4: Sunset (Arancione/Rosso)
        {
            primaryColor: "#fd7e14",
            secondaryColor: "#e83e8c",
            successColor: "#ffc107",
            errorColor: "#dc3545",
            backgroundColor: "#fff8f3",
            textColor: "#721c24"
        },
        // Tema 5: Oceano (Blu/Azzurro)
        {
            primaryColor: "#17a2b8",
            secondaryColor: "#6f42c1",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#f0f8ff",
            textColor: "#0c5460"
        },
        // Tema 6: Lavanda (Viola)
        {
            primaryColor: "#6f42c1",
            secondaryColor: "#e83e8c",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#faf5ff",
            textColor: "#4b0082"
        },
        // Tema 7: Moderno (Grigio/Nero)
        {
            primaryColor: "#000000",
            secondaryColor: "#6c757d",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#f8f9fa",
            textColor: "#000000"
        },
        // Tema 8: Arcobaleno (Colori Vivaci)
        {
            primaryColor: "#ff6b6b",
            secondaryColor: "#4ecdc4",
            successColor: "#45b7d1",
            errorColor: "#f9ca24",
            backgroundColor: "#fff5f5",
            textColor: "#2d3436"
        },
        // Tema 9: Minimal (Bianco/Nero)
        {
            primaryColor: "#000000",
            secondaryColor: "#ffffff",
            successColor: "#000000",
            errorColor: "#ff0000",
            backgroundColor: "#ffffff",
            textColor: "#000000"
        }
    ]

    // Proprietà calcolate per il tema corrente
    property color primaryColor: themes[currentTheme].primaryColor
    property color secondaryColor: themes[currentTheme].secondaryColor
    property color successColor: themes[currentTheme].successColor
    property color errorColor: themes[currentTheme].errorColor
    property color backgroundColor: themes[currentTheme].backgroundColor
    property color textColor: themes[currentTheme].textColor

    // Menu principale
    menuBar: MenuBar {
        Menu {
            title: "📁 File"
            MenuItem {
                text: "🆕 Nuovo"
                onTriggered: clearAll()
            }
            MenuItem {
                text: "💾 Salva"
                onTriggered: saveContent()
            }
             MenuItem {
                text: "📂 Apri"
                onTriggered: openFile()
             }
             MenuSeparator {}
             MenuItem {
                text: "📤 Esporta Pensierini"
                onTriggered: exportWorkspacePensierini()
             }
            MenuSeparator {}
            MenuItem {
                text: "🚪 Esci"
                onTriggered: Qt.quit()
            }
        }

        Menu {
            title: "⚙️ Strumenti"
            font.pixelSize: 16
            font.bold: true
            MenuItem {
                text: "🎤 Sintesi Vocale"
                onTriggered: toggleTTS()
            }
            MenuItem {
                text: "🎧 Riconoscimento Vocale"
                onTriggered: toggleSpeechRecognition()
            }
            MenuItem {
                text: "🤖 AI Assistant"
                onTriggered: openAIAssistant()
            }
            MenuItem {
                text: "📊 Log"
                onTriggered: toggleLog()
            }
            MenuSeparator {}
            MenuItem {
                text: showLogMessages ? "🔴 Nascondi Messaggi Log" : "🟢 Mostra Messaggi Log"
                checkable: true
                checked: showLogMessages
                onTriggered: {
                    showLogMessages = !showLogMessages
                    toggleLogMessages()
                }
            }
        }

        Menu {
            title: "🔧 Opzioni"
            MenuItem {
                text: "⚙️ Configurazione Generale"
                onTriggered: openSettings()
            }
            MenuItem {
                text: "🎨 Gestione Temi"
                onTriggered: {
                    // Scroll automatico alla scheda temi nel pannello sinistro
                    // Questa funzionalità potrebbe richiedere implementazione aggiuntiva
                }
            }
            MenuItem {
                text: "🎵 Sintesi Vocale"
                onTriggered: openTTSSettings()
            }
            MenuItem {
                text: "🤖 AI e Ollama"
                onTriggered: openAISettings()
            }
        }

        Menu {
            title: "❓ Aiuto"
            MenuItem {
                text: "📚 Documentazione"
                onTriggered: openDocumentation()
            }
            MenuItem {
                text: "ℹ️ Informazioni"
                onTriggered: showAbout()
            }
        }
    }

    // Layout principale
    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        // Barra degli strumenti
        ToolBar {
            Layout.fillWidth: true

            RowLayout {
                anchors.fill: parent
                spacing: 10

                 // Pulsanti principali
                 ToolButton {
                     text: "🆕 Nuovo Documento"
                     Layout.minimumWidth: 120
                     font.pixelSize: 11
                     font.bold: true
                     onClicked: clearAll()
                 }

                 ToolButton {
                     text: "💾 Salva Documento"
                     Layout.minimumWidth: 120
                     font.pixelSize: 11
                     font.bold: true
                     onClicked: saveContent()
                 }

                 ToolButton {
                     text: "📂 Apri Documento"
                     Layout.minimumWidth: 120
                     font.pixelSize: 11
                     font.bold: true
                     onClicked: openFile()
                 }

                ToolSeparator {}

                 ToolButton {
                     text: isReading ? "⏹️ Ferma Lettura" : "🔊 Avvia Lettura"
                     Layout.minimumWidth: 110
                     font.pixelSize: 11
                     font.bold: true
                     onClicked: toggleTTS()
                 }

                 ToolButton {
                     text: isRecording ? "⏹️ Ferma Registrazione" : "🎤 Avvia Registrazione"
                     Layout.minimumWidth: 130
                     font.pixelSize: 11
                     font.bold: true
                     onClicked: toggleSpeechRecognition()
                 }

                 ToolButton {
                     text: "🤖 AI Assistant"
                     Layout.minimumWidth: 110
                     font.pixelSize: 11
                     font.bold: true
                     onClicked: openAIAssistant()
                 }

                 ToolButton {
                     text: "📊 Mostra Log"
                     Layout.minimumWidth: 110
                     font.pixelSize: 11
                     font.bold: true
                     onClicked: toggleLog()
                 }

                ToolSeparator {}

                 ToolButton {
                     text: "⚙️ Apri Impostazioni"
                     Layout.minimumWidth: 130
                     font.pixelSize: 11
                     font.bold: true
                     onClicked: openSettings()
                 }
            }
        }

        // SplitView verticale per area principale e pensierini
        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Vertical

            // Area di lavoro principale
            SplitView {
                SplitView.fillWidth: true
                SplitView.fillHeight: true
                orientation: Qt.Horizontal

            // Colonna sinistra - Controlli e opzioni
            Rectangle {
                SplitView.preferredWidth: 300
                color: backgroundColor
                border.color: primaryColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    // Titolo colonna
                    Label {
                        text: "🎛️ Controlli"
                        font.bold: true
                        font.pixelSize: 16
                        color: textColor; style: Text.Outline; styleColor: "white"
                    }

                    // Sezione TTS
                    GroupBox {
                        title: "🎵 Sintesi Vocale"
                        Layout.fillWidth: true

                        ColumnLayout {
                            anchors.fill: parent

                             ComboBox {
                                 id: voiceCombo
                                 Layout.fillWidth: true
                                 Layout.minimumWidth: 200
                                 Layout.preferredWidth: 250
                                 model: ["🇮🇹 Italiano (it-IT)", "🇺🇸 Inglese (en-US)", "🇪🇸 Spagnolo (es-ES)", "🇫🇷 Francese (fr-FR)", "🇩🇪 Tedesco (de-DE)"]
                                 currentIndex: 0
                                 font.pixelSize: 12
                                 font.bold: true
                             }

                             Slider {
                                 id: speedSlider
                                 Layout.fillWidth: true
                                 Layout.minimumWidth: 180
                                 from: 0.5
                                 to: 2.0
                                 value: 1.0
                             }

                             Label {
                                 text: "Velocità: " + speedSlider.value.toFixed(1) + "x"
                                 font.pixelSize: 12
                                 font.bold: true
                                 Layout.alignment: Qt.AlignCenter
                             }

                             Button {
                                 text: isReading ? "⏹️ Ferma Lettura" : "🔊 Avvia Lettura"
                                 Layout.fillWidth: true
                                 Layout.minimumHeight: 35
                                 font.pixelSize: 12
                                 font.bold: true
                                 onClicked: toggleTTS()
                             }
                        }
                     }

                     // Sezione Temi e Personalizzazione
                     GroupBox {
                         title: "🎨 Temi e Aspetto"
                         Layout.fillWidth: true

                         ColumnLayout {
                             anchors.fill: parent

                             // Selettore tema principale
                             Label {
                                 text: "Tema Attuale:"
                                 font.pixelSize: 12
                                 font.bold: true
                                 color: textColor
                             }

                             ComboBox {
                                 id: themeSelector
                                 Layout.fillWidth: true
                                 Layout.minimumWidth: 180
                                 model: ["🔵 Classico (Blu)", "⚫ Scuro", "⚪ Chiaro", "🌿 Natura (Verde)", "🌅 Sunset (Arancione)", "🌊 Oceano (Azzurro)", "💜 Lavanda (Viola)", "🎯 Moderno (Nero)", "🌈 Arcobaleno", "🎨 Minimal (Bianco/Nero)"]
                                 currentIndex: currentTheme
                                 font.pixelSize: 11
                                 font.bold: true
                                 onCurrentIndexChanged: {
                                     if (currentIndex !== currentTheme) {
                                         currentTheme = currentIndex
                                     }
                                 }
                             }

                             // Anteprima colori tema corrente
                             Rectangle {
                                 Layout.fillWidth: true
                                 height: 40
                                 color: backgroundColor
                                 border.color: primaryColor
                                 border.width: 2
                                 radius: 5

                                 RowLayout {
                                     anchors.fill: parent
                                     anchors.margins: 5

                                     Rectangle {
                                         width: 20
                                         height: 20
                                         color: primaryColor
                                         radius: 3
                                     }

                                     Rectangle {
                                         width: 20
                                         height: 20
                                         color: secondaryColor
                                         radius: 3
                                     }

                                     Rectangle {
                                         width: 20
                                         height: 20
                                         color: successColor
                                         radius: 3
                                     }

                                     Label {
                                         text: "Anteprima Tema"
                                         font.pixelSize: 10
                                         color: textColor
                                         Layout.fillWidth: true
                                         horizontalAlignment: Text.AlignHCenter
                                     }
                                 }
                             }

                             // Pulsanti di azione tema
                             RowLayout {
                                 Layout.fillWidth: true

                                 Button {
                                     text: "🔄 Reset Tema"
                                     Layout.fillWidth: true
                                     font.pixelSize: 10
                                     onClicked: currentTheme = 0  // Torna al tema classico
                                 }

                                 Button {
                                     text: "🎲 Tema Casuale"
                                     Layout.fillWidth: true
                                     font.pixelSize: 10
                                     onClicked: currentTheme = Math.floor(Math.random() * 10)
                                 }
                             }
                         }
                     }

                     // Sezione AI
                     GroupBox {
                         title: "🤖 AI Assistant"
                         Layout.fillWidth: true

                        ColumnLayout {
                            anchors.fill: parent

                             ComboBox {
                                 id: aiModelCombo
                                 Layout.fillWidth: true
                                 Layout.minimumWidth: 200
                                 Layout.preferredWidth: 250
                                 model: availableModels
                                 currentIndex: 0
                                 font.pixelSize: 11
                                 font.bold: true
                                 onCurrentTextChanged: selectedModel = currentText
                             }

                             CheckBox {
                                 id: shiftEnterNewlineCheck
                                 text: "Usa Shift+Invio per andare a capo"
                                 checked: useShiftEnterForNewline
                                 font.pixelSize: 11
                                 font.bold: true
                                 onCheckedChanged: useShiftEnterForNewline = checked
                             }

                             Button {
                                 text: "🚀 Chiedi all'AI"
                                 Layout.fillWidth: true
                                 Layout.minimumHeight: 35
                                 font.pixelSize: 12
                                 font.bold: true
                                 onClicked: sendToAI()
                             }
                        }
                    }

                    // Sezione log
                    GroupBox {
                        title: "📊 Log"
                        Layout.fillWidth: true

                        ColumnLayout {
                            anchors.fill: parent

                            // Indicatore stato messaggi log
                            Label {
                                text: showLogMessages ? "🟢 Messaggi Log ATTIVI" : "🔴 Messaggi Log DISATTIVI"
                                font.pixelSize: 11
                                color: showLogMessages ? "green" : "red"
                                font.bold: true
                            }

                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                TextArea {
                                    id: logArea
                                    readOnly: true
                                    font.family: "monospace"
                                    background: Rectangle { color: "#2e2e2e" }
                                    color: "#ffffff"
                                    text: showLogMessages ? getLogMessages() : "Messaggi log disattivati.\nUsa il menu Strumenti > Mostra Messaggi Log per attivarli."
                                }
                            }

                            RowLayout {
                                Button {
                                    text: "🗑️ Pulisci Log"
                                    Layout.fillWidth: true
                                    onClicked: clearLogMessages()
                                }

                                Button {
                                    text: showLogMessages ? "🔴 Disattiva" : "🟢 Attiva"
                                    Layout.fillWidth: true
                                    onClicked: {
                                        showLogMessages = !showLogMessages
                                        toggleLogMessages()
                                        logArea.text = showLogMessages ? getLogMessages() : "Messaggi log disattivati.\nUsa il menu Strumenti > Mostra Messaggi Log per attivarli."
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Colonna centrale - Area di lavoro
            Rectangle {
                SplitView.fillWidth: true
                color: backgroundColor
                border.color: primaryColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    // Titolo area di lavoro
                    Label {
                        text: "🎯 Area di Lavoro Principale"
                        font.bold: true
                        font.pixelSize: 16
                        color: textColor; style: Text.Outline; styleColor: "white"
                    }

                    // SplitView verticale per editor e pensierini
                    SplitView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        orientation: Qt.Vertical

                        // Editor principale
                        ScrollView {
                            SplitView.fillWidth: true
                            SplitView.fillHeight: true

                            TextArea {
                                id: mainEditor
                                placeholderText: "Inserisci qui il tuo testo...\n\nUsa i controlli a sinistra per:\n- Sintetizzare vocalmente il testo\n- Interagire con l'AI\n- Salvare e aprire file\n\nPremi Invio per chiedere all'AI, Shift+Invio per andare a capo"
                                font.pixelSize: 14
                                wrapMode: TextArea.Wrap

                                Keys.onPressed: function(event) {
                                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                                        if (useShiftEnterForNewline) {
                                            if (event.modifiers & Qt.ShiftModifier) {
                                                // Shift+Enter: new line
                                                event.accepted = false
                                            } else {
                                                // Enter: send to AI
                                                event.accepted = true
                                                sendToAI()
                                            }
                                        } else {
                                            if (event.modifiers & Qt.ShiftModifier) {
                                                // Shift+Enter: send to AI
                                                event.accepted = true
                                                sendToAI()
                                            } else {
                                                // Enter: new line
                                                event.accepted = false
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        // Sezione Pensierini nell'Area di Lavoro
                        GroupBox {
                            title: "💭 Pensierini Area di Lavoro"
                            SplitView.preferredHeight: 200

                            ColumnLayout {
                                anchors.fill: parent

                                // Input per nuovo pensierino
                                RowLayout {
                                    Layout.fillWidth: true

                                    TextField {
                                        id: workspacePensierinoInput
                                        Layout.fillWidth: true
                                        placeholderText: "Scrivi un pensierino..."
                                        onAccepted: addWorkspacePensierino()
                                    }

                                     Button {
                                         text: "➕ Aggiungi Pensierino"
                                         Layout.minimumWidth: 140
                                         font.pixelSize: 11
                                         font.bold: true
                                         onClicked: addWorkspacePensierino()
                                     }

                                     Button {
                                         text: "📤 Esporta Pensierini"
                                         Layout.minimumWidth: 140
                                         font.pixelSize: 11
                                         font.bold: true
                                         onClicked: exportWorkspacePensierini()
                                     }

                                     Button {
                                         text: "🗑️ Pulisci Tutto"
                                         Layout.minimumWidth: 140
                                         font.pixelSize: 11
                                         font.bold: true
                                         onClicked: clearWorkspacePensierini()
                                     }
                                }

                                // Lista pensierini
                                ScrollView {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true

                                    ListView {
                                        id: workspacePensieriniList
                                        model: workspacePensierini
                                        clip: true

                                         delegate: Rectangle {
                                             width: parent.width
                                             height: 60
                                             color: index % 2 === 0 ? "#f8f9fa" : "transparent"
                                             border.color: primaryColor
                                             border.width: 1
                                             radius: 3

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 5

                                                TextArea {
                                                    Layout.fillWidth: true
                                                    text: modelData.text
                                                    wrapMode: TextArea.Wrap
                                                    background: Rectangle { color: "transparent" }
                                                    onTextChanged: updateWorkspacePensierino(index, text)
                                                }

                                                ColumnLayout {
                                                    Layout.alignment: Qt.AlignRight

                                                     Button {
                                                         text: "🔊 Leggi"
                                                         Layout.minimumWidth: 70
                                                         Layout.minimumHeight: 30
                                                         font.pixelSize: 10
                                                         font.bold: true
                                                         onClicked: readWorkspacePensierino(modelData.text)
                                                     }

                                                     Button {
                                                         text: "🗑️ Rimuovi"
                                                         Layout.minimumWidth: 80
                                                         Layout.minimumHeight: 30
                                                         font.pixelSize: 10
                                                         font.bold: true
                                                         onClicked: removeWorkspacePensierino(index)
                                                     }
                                                }
                                            }
                                        }
                                    }
                                }

                                // Contatore pensierini
                                Label {
                                    text: "📝 Pensierini: " + workspacePensierini.length
                                    font.pixelSize: 11
                                    color: textColor; style: Text.Outline; styleColor: "white"
                                }
                            }
                        }
                    }

                    // Barra di stato
                    Rectangle {
                        Layout.fillWidth: true
                        height: 30
                        color: primaryColor
                        radius: 5

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 5

                            Label {
                                text: "📝 Caratteri: " + mainEditor.text.length
                                color: "black"; style: Text.Outline; styleColor: "white"
                                font.pixelSize: 12
                            }

                            Label {
                                text: "📄 Parole: " + (mainEditor.text.split(/\s+/).filter(word => word.length > 0).length)
                                color: "black"; style: Text.Outline; styleColor: "white"
                                font.pixelSize: 12
                            }

                            Item { Layout.fillWidth: true }

                            Label {
                                text: isReading ? "🔊 Lettura in corso..." : "⏸️ Pronto"
                                color: isReading ? successColor : "white"
                                font.pixelSize: 12
                            }
                        }
                    }
                }
            }

            // Colonna destra - Risultati AI
            Rectangle {
                SplitView.preferredWidth: 300
                color: backgroundColor
                border.color: primaryColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    // Titolo colonna
                    Label {
                        text: "🤖 Risultati AI"
                        font.bold: true
                        font.pixelSize: 16
                        color: textColor; style: Text.Outline; styleColor: "white"
                    }

                    // Lista dei risultati AI
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        ListView {
                            id: aiResultsList
                            model: ListModel {}

                             delegate: Rectangle {
                                 width: parent.width
                                 height: 120
                                 color: index % 2 === 0 ? "transparent" : "#f8f9fa"
                                 border.color: primaryColor
                                 border.width: 1
                                 radius: 5

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 5

                                    // Preview (50 caratteri)
                                    Label {
                                        text: model.preview
                                        Layout.fillWidth: true
                                        wrapMode: Label.Wrap
                                        font.pixelSize: 11
                                        font.bold: true
                                        color: textColor; style: Text.Outline; styleColor: "white"
                                    }

                                    // Full response with scroll (250 caratteri alla volta)
                                    ScrollView {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        clip: true

                                        TextArea {
                                            text: model.response.length > 250 ? model.response.substring(0, 250) + "..." : model.response
                                            readOnly: true
                                            wrapMode: TextArea.Wrap
                                            font.pixelSize: 10
                                            background: Rectangle { color: "transparent" }
                                        }
                                    }

                                    // Timestamp
                                    Label {
                                        text: model.timestamp
                                        font.pixelSize: 9
                                        color: "#666"
                                        Layout.alignment: Qt.AlignRight
                                    }
                                }
                            }
                        }
                    }

                     // Pulsante per pulire risultati
                     Button {
                         text: "🗑️ Pulisci Tutti i Risultati AI"
                         Layout.fillWidth: true
                         Layout.minimumHeight: 35
                         font.pixelSize: 12
                         font.bold: true
                         onClicked: aiResultsList.model.clear()
                     }
                }
            }
        }
    }

    // Funzioni JavaScript per l'interazione
    function clearAll() {
        mainEditor.text = ""
        aiResultsList.model.clear()
        logArea.text = ""
    }

    function saveContent() {
        // Implementazione salvataggio
        console.log("Salvataggio contenuto...")
    }

    function openFile() {
        // Implementazione apertura file
        console.log("Apertura file...")
    }

    function toggleTTS() {
        isReading = !isReading
        if (isReading) {
            // Avvia lettura
            console.log("Avvio lettura TTS...")
        } else {
            // Ferma lettura
            console.log("Fermata lettura TTS...")
        }
    }

    function toggleSpeechRecognition() {
        isRecording = !isRecording
        if (isRecording) {
            console.log("Avvio riconoscimento vocale...")
        } else {
            console.log("Fermato riconoscimento vocale...")
        }
    }

    function openAIAssistant() {
        console.log("Apertura AI Assistant...")
    }

    function toggleLog() {
                systemLogArea.visible = !systemLogArea.visible
    }

    property var logMessages: []  // Array per memorizzare i messaggi di log

    function toggleLogMessages() {
        if (showLogMessages) {
            console.log("🔍 Log Messages: Attivati - Verranno mostrati errori e warning")
            addLogMessage("INFO", "Sistema di log attivato - Verranno mostrati errori e warning")
        } else {
            console.log("🔍 Log Messages: Disattivati - Messaggi nascosti")
            addLogMessage("INFO", "Sistema di log disattivato")
        }
    }

    function addLogMessage(level, message) {
        var timestamp = new Date().toLocaleTimeString()
        var logEntry = "[" + timestamp + "] " + level + ": " + message
        logMessages.push(logEntry)

        // Mantieni solo gli ultimi 100 messaggi
        if (logMessages.length > 100) {
            logMessages.shift()
        }

        // Aggiorna l'area log se è visibile
        if (showLogMessages) {
            logArea.text = getLogMessages()
        }
    }

    function getLogMessages() {
        if (logMessages.length === 0) {
            return "Nessun messaggio di log disponibile.\nI messaggi verranno mostrati qui quando si verificano errori o warning."
        }
        return logMessages.join("\n")
    }

    function clearLogMessages() {
        logMessages = []
        logArea.text = showLogMessages ? getLogMessages() : "Messaggi log disattivati.\nUsa il menu Strumenti > Mostra Messaggi Log per attivarli."
    }

    function openSettings() {
        console.log("Apertura impostazioni...")
    }

    function openThemeSettings() {
        console.log("Apertura impostazioni tema...")
    }

    function openTTSSettings() {
        console.log("Apertura impostazioni TTS...")
    }

    function openAISettings() {
        console.log("Apertura impostazioni AI...")
    }

    function openDocumentation() {
        console.log("Apertura documentazione...")
    }

    function showAbout() {
        console.log("Mostra informazioni...")
    }

    function readPensierino(text) {
        console.log("Lettura pensierino:", text)
    }

    function deletePensierino(index) {
        pensieriniList.model.remove(index)
    }

    function addPensierino() {
        if (newPensierinoField.text.trim() !== "") {
            pensieriniList.model.append({"text": newPensierinoField.text})
            newPensierinoField.text = ""
        }
    }

    // Funzioni per gestire i pensierini nell'area di lavoro
    function addWorkspacePensierino() {
        if (workspacePensierinoInput.text.trim() !== "") {
            workspacePensierini.push({
                "text": workspacePensierinoInput.text.trim(),
                "timestamp": new Date().toISOString()
            })
            workspacePensieriniList.model = workspacePensierini
            workspacePensierinoInput.text = ""

            addLogMessage("INFO", "Pensierino aggiunto all'area di lavoro")
        }
    }

    function removeWorkspacePensierino(index) {
        if (index >= 0 && index < workspacePensierini.length) {
            workspacePensierini.splice(index, 1)
            workspacePensieriniList.model = workspacePensierini
            addLogMessage("INFO", "Pensierino rimosso dall'area di lavoro")
        }
    }

    function updateWorkspacePensierino(index, newText) {
        if (index >= 0 && index < workspacePensierini.length) {
            workspacePensierini[index].text = newText
            workspacePensierini[index].timestamp = new Date().toISOString()
        }
    }

    function readWorkspacePensierino(text) {
        console.log("Lettura pensierino area di lavoro:", text)
        addLogMessage("INFO", "Lettura pensierino: " + text.substring(0, 30) + "...")
        // Qui potresti integrare con TTS
    }

    function exportWorkspacePensierini() {
        if (workspacePensierini.length === 0) {
            addLogMessage("WARNING", "Nessun pensierino da esportare")
            return
        }

        // Apri il dialog per scegliere dove salvare
        exportPensieriniDialog.open()
    }

    function clearWorkspacePensierini() {
        workspacePensierini = []
        workspacePensieriniList.model = workspacePensierini
        addLogMessage("INFO", "Tutti i pensierini dell'area di lavoro sono stati eliminati")
    }



    function sendToAI() {
        console.log("🔍 QML: sendToAI chiamata")
        console.log("🔍 QML: Testo:", mainEditor.text.substring(0, 50) + "...")
        console.log("🔍 QML: Modello selezionato:", selectedModel)

        if (mainEditor.text.trim() !== "") {
            addLogMessage("INFO", "Invio prompt AI: " + mainEditor.text.substring(0, 30) + "...")

            // Add to AI results list
            var preview = mainEditor.text.length > 50 ? mainEditor.text.substring(0, 47) + "..." : mainEditor.text
            aiResultsList.model.append({
                "preview": preview,
                "fullText": mainEditor.text,
                "response": "Elaborazione in corso...",
                "timestamp": new Date().toLocaleString()
            })

            // Integrazione con Ollama tramite bridge
            if (typeof ollamaBridge !== "undefined") {
                console.log("🔍 QML: Bridge disponibile, invio prompt")
                ollamaBridge.sendPrompt(mainEditor.text, selectedModel)
            } else {
                console.log("🔍 QML: Bridge non disponibile, uso simulazione")
                addLogMessage("WARNING", "Bridge AI non disponibile, uso simulazione")
                // Fallback alla simulazione se il bridge non è disponibile
                simulateAIResponse(mainEditor.text)
            }
        } else {
            console.log("🔍 QML: Testo vuoto, nessuna azione")
            addLogMessage("WARNING", "Tentativo di invio prompt vuoto")
        }
    }

    function simulateAIResponse(prompt) {
        // Simulate AI response - fallback quando il bridge non è disponibile
        var response = "Questa è una risposta simulata dall'AI per il prompt: '" + prompt + "'. In un'implementazione reale, questa risposta verrebbe generata dal modello " + selectedModel + " tramite Ollama."

        // Update the last item in the list
        if (aiResultsList.model.count > 0) {
            var lastIndex = aiResultsList.model.count - 1
            aiResultsList.model.setProperty(lastIndex, "response", response)
        }
    }

    // Connessioni ai segnali del bridge Ollama
    Connections {
        target: typeof ollamaBridge !== "undefined" ? ollamaBridge : null
        ignoreUnknownSignals: false

        function onResponseReceived(prompt, response) {
            console.log("🔍 QML: Segnale responseReceived ricevuto")
            console.log("🔍 QML: Prompt:", prompt.substring(0, 50) + "...")
            console.log("🔍 QML: Lunghezza risposta:", response.length)

            addLogMessage("INFO", "Risposta AI ricevuta per prompt: " + prompt.substring(0, 30) + "...")

            // Trova l'elemento corrispondente e aggiorna la risposta
            for (var i = 0; i < aiResultsList.model.count; i++) {
                var item = aiResultsList.model.get(i)
                if (item.fullText === prompt && item.response === "Elaborazione in corso...") {
                    console.log("🔍 QML: Aggiornamento risposta per elemento", i)
                    aiResultsList.model.setProperty(i, "response", response)
                    break
                }
            }
        }

        function onErrorOccurred(error) {
            console.log("🔍 QML: Segnale errorOccurred ricevuto:", error)
            addLogMessage("ERROR", "Errore AI: " + error)

            // Mostra l'errore nell'ultimo elemento
            if (aiResultsList.model.count > 0) {
                var lastIndex = aiResultsList.model.count - 1
                aiResultsList.model.setProperty(lastIndex, "response", "Errore: " + error)
            }
        }

        function onModelsLoaded(models) {
            console.log("🔍 QML: Modelli caricati:", models.length)
            console.log("🔍 QML: Lista modelli:", models)

            addLogMessage("INFO", "Caricati " + models.length + " modelli AI disponibili")

            // Aggiorna la lista dei modelli disponibili
            availableModels = models
            if (models.length > 0) {
                selectedModel = models[0]
                aiModelCombo.currentIndex = 0
                console.log("🔍 QML: Modello selezionato:", selectedModel)
                addLogMessage("INFO", "Modello selezionato: " + selectedModel)
            } else {
                console.log("🔍 QML: Nessun modello disponibile")
                addLogMessage("WARNING", "Nessun modello AI disponibile")
            }
        }

        function onStatusChanged(status) {
            console.log("🔍 QML: Stato cambiato:", status)
            addLogMessage("INFO", "Stato sistema: " + status)
        }

        function onLogMessage(level, message) {
            console.log("🔍 QML: Messaggio di log ricevuto:", level, message)
            addLogMessage(level, message)
        }
    }

    function loadContent() {
        // Implementazione caricamento contenuto
        console.log("Caricamento contenuto...")
        // Qui implementeresti il caricamento da file
    }

    function selectFirstModel() {
        if (availableModels.length > 0) {
            selectedModel = availableModels[0]
            aiModelCombo.currentIndex = 0
        }
    }

    // Debug: verifica che il bridge sia disponibile
    Component.onCompleted: {
        console.log("🔍 QML: Component completato")
        console.log("🔍 QML: Bridge disponibile:", typeof ollamaBridge !== "undefined")
        if (typeof ollamaBridge !== "undefined") {
            console.log("🔍 QML: Tipo del bridge:", typeof ollamaBridge)
        }

        addLogMessage("INFO", "Applicazione CogniFlow avviata")
        addLogMessage("INFO", "Sistema di log inizializzato")

        selectFirstModel()
        // Carica i modelli disponibili da Ollama
        if (typeof ollamaBridge !== "undefined") {
            addLogMessage("INFO", "Bridge AI disponibile - caricamento modelli...")
            ollamaBridge.loadModels()
        } else {
            addLogMessage("WARNING", "Bridge AI non disponibile")
        }
    }

    // Pulsante toggle per log in basso a destra
    Rectangle {
        id: logToggleButton
        width: 60
        height: 60
        radius: 30
        color: showLogMessages ? "#ff6b6b" : "#4CAF50"
        border.color: "#333"
        border.width: 2

        anchors {
            right: parent.right
            bottom: parent.bottom
            margins: 20
        }

        Text {
            anchors.centerIn: parent
            text: showLogMessages ? "🚨" : "📊"
            font.pixelSize: 24
        }

        MouseArea {
            anchors.fill: parent
            onClicked: {
                showLogMessages = !showLogMessages
                toggleLogMessages()
                systemLogArea.visible = showLogMessages
            }
        }

        // Tooltip
        ToolTip {
            visible: logToggleButtonMouseArea.containsMouse
            text: showLogMessages ? "Nascondi messaggi di log" : "Mostra messaggi di log"
        }

        MouseArea {
            id: logToggleButtonMouseArea
            anchors.fill: parent
            hoverEnabled: true
        }
    }

    // Area log scorrevole
    Rectangle {
        id: systemLogArea
        visible: true
        width: 400
        height: 300
        color: "#ff6600"
        border.color: "#ffaa00"
        border.width: 2
        radius: 8

        anchors {
            right: parent.right
            bottom: logToggleButton.top
            margins: 20
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5

            // Header con titolo e pulsante chiudi
            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: "📋 Messaggi di Sistema"
                    color: "#ffffff"
                    font.bold: true
                    font.pixelSize: 14
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "❌"
                    flat: true
                    onClicked: {
                        logArea.visible = false
                        showLogMessages = false
                    }
                }
            }

            // Area di testo per i log
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true

                TextArea {
                    id: logTextArea
                    text: getLogMessages()
                    readOnly: true
                    wrapMode: TextArea.Wrap
                    font.family: "Courier New"
                    font.pixelSize: 11
                    color: "#ffffff"
                    background: Rectangle {
                        color: "#1e1e1e"
                        border.color: "#444"
                        border.width: 1
                    }

                    // Auto-scroll alla fine quando vengono aggiunti nuovi messaggi
                    onTextChanged: {
                        if (logTextArea.visible) {
                            logTextArea.cursorPosition = logTextArea.length
                        }
                    }
                }
            }

            // Footer con controlli
            RowLayout {
                Layout.fillWidth: true

                Button {
                    text: "🗑️ Pulisci"
                    onClicked: clearLogMessages()
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: logMessages.length + " messaggi"
                    color: "#cccccc"
                    font.pixelSize: 10
                }
            }
        }
    }
}