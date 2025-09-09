// WorkspacePensierini.qml
// Componente per la gestione dei pensierini nell'area di lavoro - Ottimizzato per Qt Design Studio

import QtQuick 6.2
import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2

GroupBox {
    id: workspacePensieriniComponent

    // ===== DESIGNER PROPERTIES =====
    // Proprietà principali esposte al designer
    property var workspacePensierini: []
    property string titleText: "💭 Pensierini Area di Lavoro"
    property string placeholderText: "Scrivi un pensierino..."
    property string addButtonText: "➕ Aggiungi Pensierino"
    property string exportButtonText: "📤 Esporta Pensierini"
    property string clearButtonText: "🗑️ Pulisci Tutto"
    property string readButtonText: "🔊 Leggi"
    property string removeButtonText: "🗑️ Rimuovi"
    property string counterText: "📝 Pensierini: "

    // ===== DESIGNER APPEARANCE =====
    // Proprietà di aspetto modificabili dal designer
    property color backgroundColor: "#f8f9fa"
    property color textColor: "#000000"
    property color borderColor: "#4a90e2"
    property color primaryColor: "#4a90e2"
    property color alternateBackgroundColor: "#f8f9fa"
    property real borderWidth: 0
    property real itemBorderRadius: 3
    property real contentMargins: 5
    property real itemHeight: 60

    // ===== DESIGNER LAYOUT =====
    // Proprietà di layout modificabili dal designer
    property real titleFontSize: 14
    property real inputFontSize: 12
    property real buttonFontSize: 11
    property real itemFontSize: 12
    property real counterFontSize: 11
    property bool titleBold: true
    property bool buttonBold: true
    property bool counterBold: false

    // ===== DESIGNER BEHAVIOR =====
    // Proprietà di comportamento
    property bool alternatingColors: true
    property bool showTimestamps: false
    property bool showReadButton: true
    property bool showRemoveButton: true
    property bool showExportButton: true
    property bool showClearButton: true
    property bool showCounter: true

    // ===== DESIGNER ALIASES =====
    // Alias per componenti interni
    property alias pensieriniList: workspacePensieriniList
    property alias inputField: workspacePensierinoInput
    property alias addButton: addButton
    property alias exportButton: exportButton
    property alias clearButton: clearButton

    // ===== DESIGNER SIGNALS =====
    // Segnali per il designer
    signal pensierinoAdded(string text)
    signal pensierinoRemoved(int index)
    signal pensierinoUpdated(int index, string text)
    signal pensierinoRead(string text)
    signal pensieriniExported()
    signal pensieriniCleared()

    // ===== DESIGNER IMPLEMENTATION =====
    title: titleText
    border.width: 0

    ColumnLayout {
        anchors.fill: parent

        // Input per nuovo pensierino
        RowLayout {
            Layout.fillWidth: true
            spacing: 5

            TextField {
                id: workspacePensierinoInput
                Layout.fillWidth: true
                placeholderText: placeholderText
                font.pixelSize: inputFontSize
                onAccepted: addPensierino()
            }

            Button {
                id: addButton
                text: addButtonText
                Layout.minimumWidth: 140
                font.pixelSize: buttonFontSize
                font.bold: buttonBold
                onClicked: addPensierino()
            }

            Button {
                id: exportButton
                text: exportButtonText
                Layout.minimumWidth: 140
                font.pixelSize: buttonFontSize
                font.bold: buttonBold
                visible: showExportButton
                onClicked: exportPensierini()
            }

            Button {
                id: clearButton
                text: clearButtonText
                Layout.minimumWidth: 140
                font.pixelSize: buttonFontSize
                font.bold: buttonBold
                visible: showClearButton
                onClicked: clearPensierini()
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
                    id: pensierinoItem
                    width: parent.width
                    height: itemHeight
                    color: alternatingColors && (index % 2 === 0) ? backgroundColor : "transparent"
                    border.color: borderColor
                    border.width: borderWidth
                    radius: itemBorderRadius

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: contentMargins

                        TextArea {
                            Layout.fillWidth: true
                            text: modelData.text
                            wrapMode: TextArea.Wrap
                            font.pixelSize: itemFontSize
                            background: Rectangle { color: "transparent" }
                            color: textColor
                            onTextChanged: updatePensierino(index, text)
                        }

                        ColumnLayout {
                            Layout.alignment: Qt.AlignRight
                            spacing: 2

                            Button {
                                text: readButtonText
                                Layout.minimumWidth: 70
                                Layout.minimumHeight: 30
                                font.pixelSize: buttonFontSize - 1
                                font.bold: buttonBold
                                visible: showReadButton
                                onClicked: readPensierino(modelData.text)
                            }

                            Button {
                                text: removeButtonText
                                Layout.minimumWidth: 80
                                Layout.minimumHeight: 30
                                font.pixelSize: buttonFontSize - 1
                                font.bold: buttonBold
                                visible: showRemoveButton
                                onClicked: removePensierino(index)
                            }
                        }
                    }
                }
            }
        }

        // Contatore pensierini - Designer controllable
        Label {
            text: showCounter ? counterText + workspacePensierini.length : ""
            font.pixelSize: counterFontSize
            font.bold: counterBold
            color: textColor
            style: Text.Outline
            styleColor: "white"
            visible: showCounter
        }
    }

    // ===== DESIGNER FUNCTIONS =====
    // Funzioni per la gestione dei pensierini
    function addPensierino() {
        if (workspacePensierinoInput.text.trim() !== "") {
            var newPensierino = {
                "text": workspacePensierinoInput.text.trim(),
                "timestamp": new Date().toISOString()
            }
            workspacePensierini.push(newPensierino)
            workspacePensierinoInput.text = ""
            pensierinoAdded(newPensierino.text)
            workspacePensieriniList.model = workspacePensierini
        }
    }

    function removePensierino(index) {
        if (index >= 0 && index < workspacePensierini.length) {
            workspacePensierini.splice(index, 1)
            pensierinoRemoved(index)
            workspacePensieriniList.model = workspacePensierini
        }
    }

    function updatePensierino(index, newText) {
        if (index >= 0 && index < workspacePensierini.length) {
            workspacePensierini[index].text = newText
            workspacePensierini[index].timestamp = new Date().toISOString()
            pensierinoUpdated(index, newText)
        }
    }

    function readPensierino(text) {
        pensierinoRead(text)
    }

    function exportPensierini() {
        pensieriniExported()
    }

    function clearPensierini() {
        workspacePensierini.length = 0
        workspacePensieriniList.model = workspacePensierini
        pensieriniCleared()
    }

    // Funzione per ottenere il numero di pensierini
    function getPensieriniCount() {
        return workspacePensierini.length
    }

    // ===== DESIGNER STATES =====
    // Stati per il designer
    states: [
        State {
            name: "empty"
            when: workspacePensierini.length === 0
            PropertyChanges { target: clearButton; visible: false }
            PropertyChanges { target: exportButton; visible: false }
        },
        State {
            name: "hasItems"
            when: workspacePensierini.length > 0
            PropertyChanges { target: clearButton; visible: showClearButton }
            PropertyChanges { target: exportButton; visible: showExportButton }
        },
        State {
            name: "compact"
            PropertyChanges { target: workspacePensieriniComponent; itemHeight: 40 }
            PropertyChanges { target: workspacePensieriniComponent; buttonFontSize: 9 }
        }
    ]

    // ===== DESIGNER METADATA =====
    Component.onCompleted: {
        console.log("WorkspacePensierini initialized with", workspacePensierini.length, "items")
    }
}

            Button {
                text: "➕ Aggiungi Pensierino"
                Layout.minimumWidth: 140
                font.pixelSize: 11
                font.bold: true
                onClicked: addPensierino()
            }

            Button {
                text: "📤 Esporta Pensierini"
                Layout.minimumWidth: 140
                font.pixelSize: 11
                font.bold: true
                onClicked: exportPensierini()
            }

            Button {
                text: "🗑️ Pulisci Tutto"
                Layout.minimumWidth: 140
                font.pixelSize: 11
                font.bold: true
                onClicked: clearPensierini()
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
                    color: index % 2 === 0 ? backgroundColor : "transparent"
                    border.color: borderColor
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
                            onTextChanged: updatePensierino(index, text)
                        }

                        ColumnLayout {
                            Layout.alignment: Qt.AlignRight

                            Button {
                                text: "🔊 Leggi"
                                Layout.minimumWidth: 70
                                Layout.minimumHeight: 30
                                font.pixelSize: 10
                                font.bold: true
                                onClicked: readPensierino(modelData.text)
                            }

                            Button {
                                text: "🗑️ Rimuovi"
                                Layout.minimumWidth: 80
                                Layout.minimumHeight: 30
                                font.pixelSize: 10
                                font.bold: true
                                onClicked: removePensierino(index)
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
            color: textColor
            style: Text.Outline
            styleColor: "white"
        }
    }

    // Funzioni
    function addPensierino() {
        if (workspacePensierinoInput.text.trim() !== "") {
            workspacePensierini.push({
                "text": workspacePensierinoInput.text.trim(),
                "timestamp": new Date().toISOString()
            })
            workspacePensierinoInput.text = ""
            pensierinoAdded(workspacePensierinoInput.text)
            workspacePensieriniList.model = workspacePensierini
        }
    }

    function removePensierino(index) {
        if (index >= 0 && index < workspacePensierini.length) {
            workspacePensierini.splice(index, 1)
            pensierinoRemoved(index)
            workspacePensieriniList.model = workspacePensierini
        }
    }

    function updatePensierino(index, newText) {
        if (index >= 0 && index < workspacePensierini.length) {
            workspacePensierini[index].text = newText
            workspacePensierini[index].timestamp = new Date().toISOString()
            pensierinoUpdated(index, newText)
        }
    }

    function readPensierino(text) {
        pensierinoRead(text)
    }

    function exportPensierini() {
        pensieriniExported()
    }

    function clearPensierini() {
        workspacePensierini.length = 0
        workspacePensieriniList.model = workspacePensierini
        pensieriniCleared()
    }
}