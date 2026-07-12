// LogPanel.qml
// Componente per la visualizzazione e gestione dei log - Ottimizzato per Qt Design Studio

import QtQuick 6.2
import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2

Rectangle {
    id: logPanel

    // ===== DESIGNER PROPERTIES =====
    // Proprietà principali esposte al designer
    property bool showLogMessages: true
    property var logMessages: []
    property string titleText: "📋 Messaggi di Sistema"
    property string emptyMessage: "Nessun messaggio di log disponibile.\nI messaggi verranno mostrati qui quando si verificano errori o warning."
    property string disabledMessage: "Messaggi log disattivati.\nUsa il menu Operazioni > Mostra Messaggi Log per attivarli."

    // ===== DESIGNER APPEARANCE =====
    // Proprietà di aspetto modificabili dal designer
    property color backgroundColor: "#2e2e2e"
    property color textColor: "#ffffff"
    property color borderColor: "#444"
    property color headerBackgroundColor: "#1e1e1e"
    property color footerTextColor: "#cccccc"
    property real borderWidth: 0
    property real borderRadius: 8
    property real contentMargins: 10
    property real spacing: 5

    // ===== DESIGNER LAYOUT =====
    // Proprietà di layout modificabili dal designer
    property real titleFontSize: 14
    property real logFontSize: 11
    property real footerFontSize: 10
    property bool titleBold: true
    property string fontFamily: "Courier New"
    property int maxMessages: 100

    // ===== DESIGNER BEHAVIOR =====
    // Proprietà di comportamento
    property bool autoScroll: true
    property bool showCloseButton: true
    property bool showClearButton: true
    property bool showMessageCount: true

    // ===== DESIGNER SIGNALS =====
    // Segnali per il designer
    signal addLogMessage(string level, string message)
    signal clearLogMessages()
    signal closeRequested()

    // ===== DESIGNER ALIASES =====
    // Alias per componenti interni
    property alias logTextArea: logTextArea
    property alias titleLabel: titleLabel
    property alias closeButton: closeButton
    property alias clearButton: clearButton

    // ===== DESIGNER IMPLEMENTATION =====
    width: 400
    height: 300
    color: backgroundColor
    border.color: borderColor
    border.width: borderWidth
    radius: borderRadius
    visible: showLogMessages

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: contentMargins
        spacing: spacing

        // Header con titolo e pulsante chiudi
        Rectangle {
            id: headerRect
            Layout.fillWidth: true
            height: 30
            color: headerBackgroundColor
            radius: 4

            RowLayout {
                anchors.fill: parent
                anchors.margins: 5

                Text {
                    id: titleLabel
                    text: titleText
                    color: textColor
                    font.bold: titleBold
                    font.pixelSize: titleFontSize
                    Layout.fillWidth: true
                }

                Button {
                    id: closeButton
                    text: "❌"
                    flat: true
                    visible: showCloseButton
                    onClicked: {
                        logPanel.visible = false
                        showLogMessages = false
                        closeRequested()
                    }
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
                font.family: fontFamily
                font.pixelSize: logFontSize
                color: textColor
                background: Rectangle {
                    color: headerBackgroundColor
                    border.color: borderColor
                    border.width: 1
                    radius: 4
                }

                // Auto-scroll alla fine quando vengono aggiunti nuovi messaggi
                onTextChanged: {
                    if (autoScroll && logTextArea.visible) {
                        logTextArea.cursorPosition = logTextArea.length
                    }
                }
            }
        }

        // Footer con controlli
        Rectangle {
            id: footerRect
            Layout.fillWidth: true
            height: 25
            color: headerBackgroundColor
            radius: 4

            RowLayout {
                anchors.fill: parent
                anchors.margins: 5

                Button {
                    id: clearButton
                    text: "🗑️ Pulisci"
                    visible: showClearButton
                    onClicked: clearLogMessages()
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: showMessageCount ? logMessages.length + " messaggi" : ""
                    color: footerTextColor
                    font.pixelSize: footerFontSize
                    visible: showMessageCount
                }
            }
        }
    }

    // ===== DESIGNER FUNCTIONS =====
    // Funzione per ottenere i messaggi di log formattati
    function getLogMessages() {
        if (logMessages.length === 0) {
            return emptyMessage
        }
        if (!showLogMessages) {
            return disabledMessage
        }
        return logMessages.join("\n")
    }

    // Funzione per aggiungere un messaggio
    function appendLogMessage(level, message) {
        var timestamp = new Date().toLocaleTimeString()
        var logEntry = "[" + timestamp + "] " + level + ": " + message
        logMessages.push(logEntry)

        // Mantieni solo gli ultimi N messaggi
        if (logMessages.length > maxMessages) {
            logMessages.shift()
        }

        logTextArea.text = getLogMessages()
    }

    // Funzione per pulire i messaggi
    function clearMessages() {
        logMessages = []
        logTextArea.text = getLogMessages()
    }

    // ===== DESIGNER STATES =====
    // Stati per il designer
    states: [
        State {
            name: "expanded"
            PropertyChanges { target: logPanel; height: 400 }
        },
        State {
            name: "compact"
            PropertyChanges { target: logPanel; height: 200 }
        },
        State {
            name: "minimal"
            PropertyChanges {
                target: logPanel
                showCloseButton: false
                showClearButton: false
                showMessageCount: false
            }
        }
    ]

    // ===== DESIGNER TRANSITIONS =====
    // Transizioni per stati
    transitions: [
        Transition {
            from: "*"
            to: "*"
            NumberAnimation {
                properties: "height"
                duration: 200
                easing.type: Easing.InOutQuad
            }
        }
    ]

    // ===== DESIGNER CONNECTIONS =====
    // Connessione ai segnali
    onAddLogMessage: appendLogMessage(level, message)
    onClearLogMessages: clearMessages()

    // ===== DESIGNER METADATA =====
    Component.onCompleted: {
        console.log("LogPanel initialized with", logMessages.length, "messages")
    }
}

            Item { Layout.fillWidth: true }

            Button {
                text: "❌"
                flat: true
                onClicked: {
                    logPanel.visible = false
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
                color: textColor
                background: Rectangle {
                    color: "#1e1e1e"
                    border.color: borderColor
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

    // Funzione per ottenere i messaggi di log formattati
    function getLogMessages() {
        if (logMessages.length === 0) {
            return "Nessun messaggio di log disponibile.\nI messaggi verranno mostrati qui quando si verificano errori o warning."
        }
        if (!showLogMessages) {
            return "Messaggi log disattivati.\nUsa il menu Operazioni > Mostra Messaggi Log per attivarli."
        }
        return logMessages.join("\n")
    }

    // Funzione per aggiungere un messaggio
    function appendLogMessage(level, message) {
        var timestamp = new Date().toLocaleTimeString()
        var logEntry = "[" + timestamp + "] " + level + ": " + message
        logMessages.push(logEntry)

        // Mantieni solo gli ultimi 100 messaggi
        if (logMessages.length > 100) {
            logMessages.shift()
        }

        logTextArea.text = getLogMessages()
    }

    // Funzione per pulire i messaggi
    function clearMessages() {
        logMessages = []
        logTextArea.text = getLogMessages()
    }

    // Connessione ai segnali
    onAddLogMessage: appendLogMessage(level, message)
    onClearLogMessages: clearMessages()
}