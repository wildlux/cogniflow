// AIResultsPanel.qml
// Componente per la visualizzazione dei risultati AI - Ottimizzato per Qt Design Studio

import QtQuick 6.2
import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2

Rectangle {
    id: aiResultsPanel

    // ===== DESIGNER PROPERTIES =====
    // Proprietà principali esposte al designer
    property string titleText: "🤖 Risultati AI"
    property string clearButtonText: "🗑️ Pulisci Tutti i Risultati AI"
    property string processingText: "Elaborazione in corso..."
    property int maxPreviewLength: 50
    property int maxResponseLength: 250

    // ===== DESIGNER APPEARANCE =====
    // Proprietà di aspetto modificabili dal designer
    property color backgroundColor: "#f8f9fa"
    property color textColor: "#000000"
    property color borderColor: "#4a90e2"
    property color primaryColor: "#4a90e2"
    property color alternateBackgroundColor: "#f8f9fa"
    property color timestampColor: "#666"
    property real borderWidth: 0
    property real borderRadius: 0
    property real itemBorderRadius: 5
    property real contentMargins: 10
    property real spacing: 10

    // ===== DESIGNER LAYOUT =====
    // Proprietà di layout modificabili dal designer
    property real titleFontSize: 16
    property real previewFontSize: 11
    property real responseFontSize: 10
    property real timestampFontSize: 9
    property real buttonFontSize: 12
    property real itemHeight: 120
    property bool titleBold: true
    property bool previewBold: true
    property bool buttonBold: true

    // ===== DESIGNER BEHAVIOR =====
    // Proprietà di comportamento
    property bool alternatingColors: true
    property bool showTimestamps: true
    property bool showClearButton: true
    property bool clipResponseText: true

    // ===== DESIGNER ALIASES =====
    // Alias per componenti interni
    property alias resultsList: aiResultsList
    property alias titleLabel: titleLabel
    property alias clearButton: clearButton

    // ===== DESIGNER IMPLEMENTATION =====
    color: backgroundColor
    border.color: borderColor
    border.width: borderWidth
    radius: borderRadius

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: contentMargins
        spacing: spacing

        // Titolo colonna - Designer customizable
        Label {
            id: titleLabel
            text: titleText
            font.bold: titleBold
            font.pixelSize: titleFontSize
            color: textColor
            style: Text.Outline
            styleColor: "white"
            visible: text !== ""
        }

        // Lista dei risultati AI
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: aiResultsList
                model: ListModel {}
                clip: true

                delegate: Rectangle {
                    id: resultItem
                    width: parent.width
                    height: itemHeight
                    color: alternatingColors && (index % 2 === 1) ? alternateBackgroundColor : "transparent"
                    radius: itemBorderRadius

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 5

                        // Preview (troncato a maxPreviewLength caratteri)
                        Label {
                            text: model.preview
                            Layout.fillWidth: true
                            wrapMode: Label.Wrap
                            font.pixelSize: previewFontSize
                            font.bold: previewBold
                            color: textColor
                            style: Text.Outline
                            styleColor: "white"
                        }

                        // Full response with scroll
                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: clipResponseText

                            TextArea {
                                text: clipResponseText && model.response.length > maxResponseLength
                                    ? model.response.substring(0, maxResponseLength) + "..."
                                    : model.response
                                readOnly: true
                                wrapMode: TextArea.Wrap
                                font.pixelSize: responseFontSize
                                background: Rectangle { color: "transparent" }
                                color: textColor
                            }
                        }

                        // Timestamp - Designer controllable
                        Label {
                            text: showTimestamps ? model.timestamp : ""
                            font.pixelSize: timestampFontSize
                            color: timestampColor
                            Layout.alignment: Qt.AlignRight
                            visible: showTimestamps
                        }
                    }
                }
            }
        }

        // Pulsante per pulire risultati - Designer controllable
        Button {
            id: clearButton
            text: clearButtonText
            Layout.fillWidth: true
            Layout.minimumHeight: 35
            font.pixelSize: buttonFontSize
            font.bold: buttonBold
            visible: showClearButton
            onClicked: aiResultsList.model.clear()
        }
    }

    // ===== DESIGNER FUNCTIONS =====
    // Funzione per aggiungere un risultato AI
    function addResult(preview, fullText, response, timestamp) {
        var truncatedPreview = preview.length > maxPreviewLength
            ? preview.substring(0, maxPreviewLength - 3) + "..."
            : preview

        aiResultsList.model.append({
            "preview": truncatedPreview,
            "fullText": fullText,
            "response": response,
            "timestamp": timestamp || new Date().toLocaleString()
        })
    }

    // Funzione per aggiornare una risposta
    function updateResponse(index, response) {
        if (index >= 0 && index < aiResultsList.model.count) {
            aiResultsList.model.setProperty(index, "response", response)
        }
    }

    // Funzione per trovare l'indice di un prompt
    function findPromptIndex(prompt) {
        for (var i = 0; i < aiResultsList.model.count; i++) {
            var item = aiResultsList.model.get(i)
            if (item.fullText === prompt && item.response === processingText) {
                return i
            }
        }
        return -1
    }

    // Funzione per pulire tutti i risultati
    function clearAll() {
        aiResultsList.model.clear()
    }

    // Funzione per ottenere il numero di risultati
    function getResultCount() {
        return aiResultsList.model.count
    }

    // ===== DESIGNER STATES =====
    // Stati per il designer
    states: [
        State {
            name: "noResults"
            when: aiResultsList.model.count === 0
            PropertyChanges { target: clearButton; visible: false }
        },
        State {
            name: "hasResults"
            when: aiResultsList.model.count > 0
            PropertyChanges { target: clearButton; visible: showClearButton }
        },
        State {
            name: "compact"
            PropertyChanges { target: aiResultsPanel; itemHeight: 80 }
            PropertyChanges { target: aiResultsPanel; titleFontSize: 14 }
        }
    ]

    // ===== DESIGNER METADATA =====
    Component.onCompleted: {
        console.log("AIResultsPanel initialized")
    }
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
                    border.color: borderColor
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
                            color: textColor
                            style: Text.Outline
                            styleColor: "white"
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

    // Funzione per aggiungere un risultato AI
    function addResult(preview, fullText, response, timestamp) {
        aiResultsList.model.append({
            "preview": preview,
            "fullText": fullText,
            "response": response,
            "timestamp": timestamp
        })
    }

    // Funzione per aggiornare una risposta
    function updateResponse(index, response) {
        if (index >= 0 && index < aiResultsList.model.count) {
            aiResultsList.model.setProperty(index, "response", response)
        }
    }

    // Funzione per trovare l'indice di un prompt
    function findPromptIndex(prompt) {
        for (var i = 0; i < aiResultsList.model.count; i++) {
            var item = aiResultsList.model.get(i)
            if (item.fullText === prompt && item.response === "Elaborazione in corso...") {
                return i
            }
        }
        return -1
    }

    // Funzione per pulire tutti i risultati
    function clearAll() {
        aiResultsList.model.clear()
    }
}