// main_interface.qml
// Interfaccia principale QML per l'Assistente DSA - Versione Rifattorizzata

import QtQuick 6.2
import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2
import QtQuick.Dialogs 6.2
import "components"
import "js/ui_functions.js" as UiFunctions
import "js/ai_functions.js" as AiFunctions
import "js/log_functions.js" as LogFunctions
import "js/pensierini_functions.js" as PensieriniFunctions

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
    property bool useShiftEnterForNewline: true
    property string selectedModel: "llama2:7b"
    property var availableModels: ["llama2:7b", "codellama:7b", "llava:7b"]
    property bool showLogMessages: true
    property var workspacePensierini: []

    // Componenti - Ottimizzati per Qt Design Studio
    ThemeManager {
        id: themeManager
        // Proprietà esposte al designer per personalizzazione
        currentTheme: 0  // Designer può cambiare questo valore
    }

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
                filePath = filePath.substring(7)
            }

            var jsonString = JSON.stringify(exportData, null, 2)
            console.log("💾 Salvataggio su file:", filePath)
            console.log("📄 Contenuto:", jsonString)

            LogFunctions.addLogMessage("INFO", "Pensierini esportati su file: " + filePath)
        }
    }

    // Keyboard shortcuts
    Shortcut {
        sequence: "Ctrl+S"
        onActivated: UiFunctions.saveContent()
    }

    Shortcut {
        sequence: "Ctrl+L"
        onActivated: UiFunctions.loadContent()
    }

    // Menu principale
    menuBar: MenuBar {
        Menu {
            title: "📝 Documenti"
            MenuItem {
                text: "🆕 Nuovo"
                onTriggered: UiFunctions.clearAll(mainEditor, aiResultsPanel.aiResultsList, logPanel.logTextArea)
            }
            MenuItem {
                text: "💾 Salva"
                onTriggered: UiFunctions.saveContent()
            }
            MenuItem {
                text: "📂 Apri"
                onTriggered: UiFunctions.openFile()
            }
            MenuItem {
                text: "📤 Esporta Pensierini"
                onTriggered: workspacePensieriniComponent.exportPensierini()
            }
            MenuItem {
                text: "🚪 Esci"
                onTriggered: Qt.quit()
            }
        }

        Menu {
            title: "🎯 Operazioni"
            font.pixelSize: 16
            font.bold: true
            MenuItem {
                text: "🎤 Sintesi Vocale"
                onTriggered: controlPanel.toggleTTS()
            }
            MenuItem {
                text: "🎧 Riconoscimento Vocale"
                onTriggered: controlPanel.toggleSpeechRecognition()
            }
            MenuItem {
                text: "🤖 AI Assistant"
                onTriggered: UiFunctions.openAIAssistant()
            }
            MenuItem {
                text: "📊 Log"
                onTriggered: logPanel.visible = !logPanel.visible
            }
            MenuItem {
                text: showLogMessages ? "🔴 Nascondi Messaggi Log" : "🟢 Mostra Messaggi Log"
                checkable: true
                checked: showLogMessages
                onTriggered: {
                    showLogMessages = !showLogMessages
                    LogFunctions.toggleLogMessages(showLogMessages, function(level, message) {
                        LogFunctions.addLogMessage(level, message)
                    })
                }
            }
        }

        Menu {
            title: "⚙️ Configurazione"
            MenuItem {
                text: "⚙️ Configurazione Generale"
                onTriggered: UiFunctions.openSettings()
            }
            MenuItem {
                text: "🎨 Gestione Temi"
                onTriggered: {
                    // Scroll automatico alla scheda temi nel pannello sinistro
                }
            }
            MenuItem {
                text: "🎵 Sintesi Vocale"
                onTriggered: UiFunctions.openTTSSettings()
            }
            MenuItem {
                text: "🤖 AI e Ollama"
                onTriggered: UiFunctions.openAISettings()
            }
        }

        Menu {
            title: "📚 Guida"
            MenuItem {
                text: "📚 Documentazione"
                onTriggered: UiFunctions.openDocumentation()
            }
            MenuItem {
                text: "ℹ️ Informazioni"
                onTriggered: UiFunctions.showAbout()
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
                    onClicked: UiFunctions.clearAll(mainEditor, aiResultsPanel.aiResultsList, logPanel.logTextArea)
                }

                ToolButton {
                    text: "💾 Salva Documento"
                    Layout.minimumWidth: 120
                    font.pixelSize: 11
                    font.bold: true
                    onClicked: UiFunctions.saveContent()
                }

                ToolButton {
                    text: "📂 Apri Documento"
                    Layout.minimumWidth: 120
                    font.pixelSize: 11
                    font.bold: true
                    onClicked: UiFunctions.openFile()
                }

                ToolButton {
                    text: isReading ? "⏹️ Ferma Lettura" : "🔊 Avvia Lettura"
                    Layout.minimumWidth: 110
                    font.pixelSize: 11
                    font.bold: true
                    onClicked: controlPanel.toggleTTS()
                }

                ToolButton {
                    text: isRecording ? "⏹️ Ferma Registrazione" : "🎤 Avvia Registrazione"
                    Layout.minimumWidth: 130
                    font.pixelSize: 11
                    font.bold: true
                    onClicked: controlPanel.toggleSpeechRecognition()
                }

                ToolButton {
                    text: "🤖 AI Assistant"
                    Layout.minimumWidth: 110
                    font.pixelSize: 11
                    font.bold: true
                    onClicked: UiFunctions.openAIAssistant()
                }

                ToolButton {
                    text: "📊 Mostra Log"
                    Layout.minimumWidth: 110
                    font.pixelSize: 11
                    font.bold: true
                    onClicked: logPanel.visible = !logPanel.visible
                }

                ToolButton {
                    text: "⚙️ Apri Impostazioni"
                    Layout.minimumWidth: 130
                    font.pixelSize: 11
                    font.bold: true
                    onClicked: UiFunctions.openSettings()
                }
            }
        }

        // Layout fisso senza SplitView
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            // Colonna sinistra - Controlli e opzioni
            ControlPanel {
                id: controlPanel
                Layout.preferredWidth: 300
                Layout.minimumWidth: 250
                Layout.maximumWidth: 350

                // Proprietà sincronizzate con la finestra principale
                isReading: mainWindow.isReading
                isRecording: mainWindow.isRecording
                selectedModel: mainWindow.selectedModel
                availableModels: mainWindow.availableModels
                useShiftEnterForNewline: mainWindow.useShiftEnterForNewline

                // Tema manager
                themeManager: themeManager

                // Proprietà di aspetto collegate al tema
                backgroundColor: themeManager.backgroundColor
                textColor: themeManager.textColor
                borderColor: themeManager.primaryColor
                primaryColor: themeManager.primaryColor

                // Proprietà di layout personalizzabili dal designer
                contentMargins: 10
                spacing: 10
                titleFontSize: 16
                labelFontSize: 12
                buttonFontSize: 12

                // Visibilità sezioni (designer può controllare)
                showTTSPanel: true
                showThemePanel: true
                showAIPanel: true

                onToggleTTS: {
                    mainWindow.isReading = !mainWindow.isReading
                    if (mainWindow.isReading) {
                        console.log("Avvio lettura TTS...")
                    } else {
                        console.log("Fermata lettura TTS...")
                    }
                }

                onToggleSpeechRecognition: {
                    mainWindow.isRecording = !mainWindow.isRecording
                    if (mainWindow.isRecording) {
                        console.log("Avvio riconoscimento vocale...")
                    } else {
                        console.log("Fermato riconoscimento vocale...")
                    }
                }

                onSendToAI: AiFunctions.sendToAI(mainEditor, selectedModel, aiResultsPanel, function(level, message) {
                    LogFunctions.addLogMessage(level, message)
                }, typeof ollamaBridge !== "undefined" ? ollamaBridge : null)

                onThemeChanged: {
                    // Tema aggiornato automaticamente tramite binding
                    console.log("Tema cambiato a:", themeManager.currentTheme)
                }
            }

            // Colonna centrale - Area di lavoro
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: themeManager.backgroundColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    // Titolo area di lavoro
                    Label {
                        text: "🎯 Area di Lavoro Principale"
                        font.bold: true
                        font.pixelSize: 16
                        color: themeManager.textColor
                        style: Text.Outline
                        styleColor: "white"
                    }

                    // Layout fisso per editor e pensierini
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 10

                        // Editor principale
                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.minimumHeight: 200

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
                                                AiFunctions.sendToAI(mainEditor, selectedModel, aiResultsPanel, function(level, message) {
                                                    LogFunctions.addLogMessage(level, message)
                                                }, typeof ollamaBridge !== "undefined" ? ollamaBridge : null)
                                            }
                                        } else {
                                            if (event.modifiers & Qt.ShiftModifier) {
                                                // Shift+Enter: send to AI
                                                event.accepted = true
                                                AiFunctions.sendToAI(mainEditor, selectedModel, aiResultsPanel, function(level, message) {
                                                    LogFunctions.addLogMessage(level, message)
                                                }, typeof ollamaBridge !== "undefined" ? ollamaBridge : null)
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
                        WorkspacePensierini {
                            id: workspacePensieriniComponent
                            Layout.fillWidth: true
                            Layout.preferredHeight: 200
                            Layout.minimumHeight: 150
                            Layout.maximumHeight: 300

                            // Lista dei pensierini
                            workspacePensierini: mainWindow.workspacePensierini

                            // Proprietà di aspetto collegate al tema
                            backgroundColor: themeManager.backgroundColor
                            textColor: themeManager.textColor
                            borderColor: themeManager.primaryColor
                            primaryColor: themeManager.primaryColor

                            // Proprietà di layout personalizzabili dal designer
                            contentMargins: 5
                            itemHeight: 60
                            titleFontSize: 14
                            inputFontSize: 12
                            buttonFontSize: 11
                            itemFontSize: 12
                            counterFontSize: 11

                            // Proprietà di comportamento
                            alternatingColors: true
                            showTimestamps: false
                            showReadButton: true
                            showRemoveButton: true
                            showExportButton: true
                            showClearButton: true
                            showCounter: true

                            onPensierinoAdded: function(text) {
                                PensieriniFunctions.addWorkspacePensierino(text, workspacePensierini, null, function(level, message) {
                                    LogFunctions.addLogMessage(level, message)
                                })
                            }

                            onPensierinoRemoved: function(index) {
                                PensieriniFunctions.removeWorkspacePensierini(index, workspacePensierini, function(level, message) {
                                    LogFunctions.addLogMessage(level, message)
                                })
                            }

                            onPensierinoUpdated: function(index, text) {
                                PensieriniFunctions.updateWorkspacePensierino(index, text, workspacePensierini)
                            }

                            onPensierinoRead: function(text) {
                                PensieriniFunctions.readWorkspacePensierino(text, function(level, message) {
                                    LogFunctions.addLogMessage(level, message)
                                })
                            }

                            onPensieriniExported: function() {
                                exportPensieriniDialog.open()
                            }

                            onPensieriniCleared: function() {
                                PensieriniFunctions.clearWorkspacePensierini(workspacePensierini, function(level, message) {
                                    LogFunctions.addLogMessage(level, message)
                                })
                            }
                        }
                    }

                    // Barra di stato
                    Rectangle {
                        Layout.fillWidth: true
                        height: 30
                        color: themeManager.primaryColor
                        radius: 5

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 5

                            Label {
                                text: "📝 Caratteri: " + mainEditor.text.length
                                color: "black"
                                style: Text.Outline
                                styleColor: "white"
                                font.pixelSize: 12
                            }

                            Label {
                                text: "📄 Parole: " + (mainEditor.text.split(/\s+/).filter(word => word.length > 0).length)
                                color: "black"
                                style: Text.Outline
                                styleColor: "white"
                                font.pixelSize: 12
                            }

                            Item { Layout.fillWidth: true }

                            Label {
                                text: isReading ? "🔊 Lettura in corso..." : "⏸️ Pronto"
                                color: isReading ? themeManager.successColor : "white"
                                font.pixelSize: 12
                            }
                        }
                    }
                }
            }

            // Colonna destra - Risultati AI
            AIResultsPanel {
                id: aiResultsPanel
                Layout.preferredWidth: 300
                Layout.minimumWidth: 250
                Layout.maximumWidth: 350

                // Proprietà di aspetto collegate al tema
                backgroundColor: themeManager.backgroundColor
                textColor: themeManager.textColor
                borderColor: themeManager.primaryColor
                primaryColor: themeManager.primaryColor

                // Proprietà di layout personalizzabili dal designer
                contentMargins: 10
                spacing: 10
                titleFontSize: 16
                previewFontSize: 11
                responseFontSize: 10
                buttonFontSize: 12
                itemHeight: 120

                // Proprietà di comportamento
                alternatingColors: true
                showTimestamps: true
                showClearButton: true
                clipResponseText: true
                maxPreviewLength: 50
                maxResponseLength: 250
            }
        }
                    }

                    onToggleSpeechRecognition: {
                        mainWindow.isRecording = !mainWindow.isRecording
                        if (mainWindow.isRecording) {
                            console.log("Avvio riconoscimento vocale...")
                        } else {
                            console.log("Fermato riconoscimento vocale...")
                        }
                    }

                    onSendToAI: AiFunctions.sendToAI(mainEditor, selectedModel, aiResultsPanel, function(level, message) {
                        LogFunctions.addLogMessage(level, message)
                    }, typeof ollamaBridge !== "undefined" ? ollamaBridge : null)

                    onThemeChanged: {
                        // Tema aggiornato automaticamente tramite binding
                        console.log("Tema cambiato a:", themeManager.currentTheme)
                    }
                }

                // Colonna centrale - Area di lavoro
                Rectangle {
                    SplitView.fillWidth: true
                    color: themeManager.backgroundColor
                    border.color: themeManager.primaryColor
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
                            color: themeManager.textColor
                            style: Text.Outline
                            styleColor: "white"
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
                                                    AiFunctions.sendToAI(mainEditor, selectedModel, aiResultsPanel, function(level, message) {
                                                        LogFunctions.addLogMessage(level, message)
                                                    }, typeof ollamaBridge !== "undefined" ? ollamaBridge : null)
                                                }
                                            } else {
                                                if (event.modifiers & Qt.ShiftModifier) {
                                                    // Shift+Enter: send to AI
                                                    event.accepted = true
                                                    AiFunctions.sendToAI(mainEditor, selectedModel, aiResultsPanel, function(level, message) {
                                                        LogFunctions.addLogMessage(level, message)
                                                    }, typeof ollamaBridge !== "undefined" ? ollamaBridge : null)
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
                            WorkspacePensierini {
                                id: workspacePensieriniComponent
                                Layout.preferredHeight: 200

                                // Lista dei pensierini
                                workspacePensierini: mainWindow.workspacePensierini

                                // Proprietà di aspetto collegate al tema
                                backgroundColor: themeManager.backgroundColor
                                textColor: themeManager.textColor
                                borderColor: themeManager.primaryColor
                                primaryColor: themeManager.primaryColor

                                // Proprietà di layout personalizzabili dal designer
                                contentMargins: 5
                                itemHeight: 60
                                titleFontSize: 14
                                inputFontSize: 12
                                buttonFontSize: 11
                                itemFontSize: 12
                                counterFontSize: 11

                                // Proprietà di comportamento
                                alternatingColors: true
                                showTimestamps: false
                                showReadButton: true
                                showRemoveButton: true
                                showExportButton: true
                                showClearButton: true
                                showCounter: true

                                onPensierinoAdded: function(text) {
                                    PensieriniFunctions.addWorkspacePensierino(text, workspacePensierini, null, function(level, message) {
                                        LogFunctions.addLogMessage(level, message)
                                    })
                                }

                                onPensierinoRemoved: function(index) {
                                    PensieriniFunctions.removeWorkspacePensierini(index, workspacePensierini, function(level, message) {
                                        LogFunctions.addLogMessage(level, message)
                                    })
                                }

                                onPensierinoUpdated: function(index, text) {
                                    PensieriniFunctions.updateWorkspacePensierino(index, text, workspacePensierini)
                                }

                                onPensierinoRead: function(text) {
                                    PensieriniFunctions.readWorkspacePensierino(text, function(level, message) {
                                        LogFunctions.addLogMessage(level, message)
                                    })
                                }

                                onPensieriniExported: function() {
                                    exportPensieriniDialog.open()
                                }

                                onPensieriniCleared: function() {
                                    PensieriniFunctions.clearWorkspacePensierini(workspacePensierini, function(level, message) {
                                        LogFunctions.addLogMessage(level, message)
                                    })
                                }
                            }
                        }

                        // Barra di stato
                        Rectangle {
                            Layout.fillWidth: true
                            height: 30
                            color: themeManager.primaryColor
                            radius: 5

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 5

                                Label {
                                    text: "📝 Caratteri: " + mainEditor.text.length
                                    color: "black"
                                    style: Text.Outline
                                    styleColor: "white"
                                    font.pixelSize: 12
                                }

                                Label {
                                    text: "📄 Parole: " + (mainEditor.text.split(/\s+/).filter(word => word.length > 0).length)
                                    color: "black"
                                    style: Text.Outline
                                    styleColor: "white"
                                    font.pixelSize: 12
                                }

                                Item { Layout.fillWidth: true }

                                Label {
                                    text: isReading ? "🔊 Lettura in corso..." : "⏸️ Pronto"
                                    color: isReading ? themeManager.successColor : "white"
                                    font.pixelSize: 12
                                }
                            }
                        }
                }
            }

                // Colonna destra - Risultati AI
                AIResultsPanel {
                    id: aiResultsPanel
                    Layout.preferredWidth: 300

                    // Proprietà di aspetto collegate al tema
                    backgroundColor: themeManager.backgroundColor
                    textColor: themeManager.textColor
                    borderColor: themeManager.primaryColor
                    primaryColor: themeManager.primaryColor

                    // Proprietà di layout personalizzabili dal designer
                    contentMargins: 10
                    spacing: 10
                    titleFontSize: 16
                    previewFontSize: 11
                    responseFontSize: 10
                    buttonFontSize: 12
                    itemHeight: 120

                    // Proprietà di comportamento
                    alternatingColors: true
                    showTimestamps: true
                    showClearButton: true
                    clipResponseText: true
                    maxPreviewLength: 50
                    maxResponseLength: 250
                }
        }
    }

    // Connessioni ai segnali del bridge Ollama
    Connections {
        target: typeof ollamaBridge !== "undefined" ? ollamaBridge : null
        ignoreUnknownSignals: false

        function onResponseReceived(prompt, response) {
            AiFunctions.handleResponseReceived(prompt, response, aiResultsPanel, function(level, message) {
                LogFunctions.addLogMessage(level, message)
            })
        }

        function onErrorOccurred(error) {
            AiFunctions.handleErrorOccurred(error, aiResultsPanel, function(level, message) {
                LogFunctions.addLogMessage(level, message)
            })
        }

        function onModelsLoaded(models) {
            var loadedModels = AiFunctions.handleModelsLoaded(models, function(level, message) {
                LogFunctions.addLogMessage(level, message)
            })
            availableModels = loadedModels
            if (loadedModels.length > 0) {
                selectedModel = loadedModels[0]
            }
        }

        function onStatusChanged(status) {
            AiFunctions.handleStatusChanged(status, function(level, message) {
                LogFunctions.addLogMessage(level, message)
            })
        }

        function onLogMessage(level, message) {
            LogFunctions.handleLogMessage(level, message, function(lvl, msg) {
                LogFunctions.addLogMessage(lvl, msg)
            })
        }
    }

    // Componente Log Panel - Ottimizzato per il designer
    LogPanel {
        id: logPanel
        visible: showLogMessages
        showLogMessages: mainWindow.showLogMessages

        // Proprietà di aspetto
        backgroundColor: "#1e1e1e"
        textColor: "#ffffff"
        borderColor: "#444"
        headerBackgroundColor: "#1e1e1e"
        footerTextColor: "#cccccc"

        // Proprietà di layout personalizzabili dal designer
        contentMargins: 10
        spacing: 5
        titleFontSize: 14
        logFontSize: 11
        footerFontSize: 10

        // Proprietà di comportamento
        autoScroll: true
        showCloseButton: true
        showClearButton: true
        showMessageCount: true
        maxMessages: 100

        // Testi personalizzabili
        titleText: "📋 Messaggi di Sistema"
        emptyMessage: "Nessun messaggio di log disponibile.\nI messaggi verranno mostrati qui quando si verificano errori o warning."
        disabledMessage: "Messaggi log disattivati.\nUsa il menu Operazioni > Mostra Messaggi Log per attivarli."

        anchors {
            right: parent.right
            bottom: logToggleButton.top
            margins: 20
        }

        onAddLogMessage: appendLogMessage(level, message)
        onClearLogMessages: clearMessages()
        onCloseRequested: {
            visible = false
            showLogMessages = false
        }
    }

    // Pulsante toggle per log in basso a destra
    Rectangle {
        id: logToggleButton
        width: 60
        height: 60
        radius: 30
        color: showLogMessages ? "#ff6b6b" : "#4CAF50"

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
                LogFunctions.toggleLogMessages(showLogMessages, function(level, message) {
                    LogFunctions.addLogMessage(level, message)
                })
                logPanel.visible = showLogMessages
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

    // Debug: verifica che il bridge sia disponibile
    Component.onCompleted: {
        console.log("🔍 QML: Component completato")
        console.log("🔍 QML: Bridge disponibile:", typeof ollamaBridge !== "undefined")
        if (typeof ollamaBridge !== "undefined") {
            console.log("🔍 QML: Tipo del bridge:", typeof ollamaBridge)
        }

        LogFunctions.addLogMessage("INFO", "Applicazione CogniFlow avviata")
        LogFunctions.addLogMessage("INFO", "Sistema di log inizializzato")

        var firstModel = AiFunctions.selectFirstModel(availableModels, null)
        if (firstModel) {
            selectedModel = firstModel
        }

        // Carica i modelli disponibili da Ollama
        if (typeof ollamaBridge !== "undefined") {
            LogFunctions.addLogMessage("INFO", "Bridge AI disponibile - caricamento modelli...")
            ollamaBridge.loadModels()
        } else {
            LogFunctions.addLogMessage("WARNING", "Bridge AI non disponibile")
        }
    }
}