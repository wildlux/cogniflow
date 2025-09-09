// ControlPanel.qml
// Componente per il pannello di controllo principale - Ottimizzato per Qt Design Studio

import QtQuick 6.2
import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2

Rectangle {
    id: controlPanel

    // ===== DESIGNER PROPERTIES =====
    // Proprietà principali esposte al designer
    property bool isReading: false
    property bool isRecording: false
    property string selectedModel: "llama2:7b"
    property var availableModels: ["llama2:7b", "codellama:7b", "llava:7b"]
    property bool useShiftEnterForNewline: true
    property var themeManager: null

    // ===== DESIGNER APPEARANCE =====
    // Proprietà di aspetto modificabili dal designer
    property color backgroundColor: "#f8f9fa"
    property color textColor: "#000000"
    property color borderColor: "#4a90e2"
    property color primaryColor: "#4a90e2"
    property real borderWidth: 0
    property real borderRadius: 0
    property real contentMargins: 10
    property real spacing: 10

    // ===== DESIGNER LAYOUT =====
    // Proprietà di layout modificabili dal designer
    property real titleFontSize: 16
    property real labelFontSize: 12
    property real buttonFontSize: 12
    property bool titleBold: true
    property bool labelBold: true
    property bool buttonBold: true

    // ===== DESIGNER VISIBILITY =====
    // Controllo della visibilità delle sezioni
    property bool showTTSPanel: true
    property bool showThemePanel: true
    property bool showAIPanel: true

    // ===== DESIGNER SIGNALS =====
    // Segnali per il designer
    signal toggleTTS()
    signal toggleSpeechRecognition()
    signal sendToAI()
    signal themeChanged(int index)

    // ===== DESIGNER ALIASES =====
    // Alias per componenti interni
    property alias voiceCombo: voiceCombo
    property alias speedSlider: speedSlider
    property alias themeSelector: themeSelector
    property alias aiModelCombo: aiModelCombo
    property alias shiftEnterNewlineCheck: shiftEnterNewlineCheck

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
            text: "🎛️ Controlli"
            font.bold: titleBold
            font.pixelSize: titleFontSize
            color: textColor
            style: Text.Outline
            styleColor: "white"
            visible: text !== ""
        }

        // Sezione TTS - Designer controllable visibility
        GroupBox {
            title: "🎵 Sintesi Vocale"
            Layout.fillWidth: true
            visible: showTTSPanel
            border.width: 0

            ColumnLayout {
                anchors.fill: parent

                ComboBox {
                    id: voiceCombo
                    Layout.fillWidth: true
                    Layout.minimumWidth: 200
                    Layout.preferredWidth: 250
                    model: ["🇮🇹 Italiano (it-IT)", "🇺🇸 Inglese (en-US)", "🇪🇸 Spagnolo (es-ES)", "🇫🇷 Francese (fr-FR)", "🇩🇪 Tedesco (de-DE)"]
                    currentIndex: 0
                    font.pixelSize: labelFontSize
                    font.bold: labelBold
                }

                Slider {
                    id: speedSlider
                    Layout.fillWidth: true
                    Layout.minimumWidth: 180
                    from: 0.5
                    to: 2.0
                    value: 1.0
                    stepSize: 0.1
                }

                Label {
                    text: "Velocità: " + speedSlider.value.toFixed(1) + "x"
                    font.pixelSize: labelFontSize
                    font.bold: labelBold
                    Layout.alignment: Qt.AlignCenter
                    color: textColor
                }

                Button {
                    text: isReading ? "⏹️ Ferma Lettura" : "🔊 Avvia Lettura"
                    Layout.fillWidth: true
                    Layout.minimumHeight: 35
                    font.pixelSize: buttonFontSize
                    font.bold: buttonBold
                    onClicked: controlPanel.toggleTTS()
                }
            }
        }

        // Sezione Temi e Personalizzazione - Designer controllable
        GroupBox {
            title: "🎨 Temi e Aspetto"
            Layout.fillWidth: true
            visible: showThemePanel
            border.width: 0

            ColumnLayout {
                anchors.fill: parent

                // Selettore tema principale
                Label {
                    text: "Tema Attuale:"
                    font.pixelSize: labelFontSize
                    font.bold: labelBold
                    color: textColor
                }

                ComboBox {
                    id: themeSelector
                    Layout.fillWidth: true
                    Layout.minimumWidth: 180
                    model: themeManager ? themeManager.themeNames : []
                    currentIndex: themeManager ? themeManager.currentTheme : 0
                    font.pixelSize: labelFontSize
                    font.bold: labelBold
                    onCurrentIndexChanged: {
                        if (themeManager && currentIndex !== themeManager.currentTheme) {
                            themeManager.currentTheme = currentIndex
                            controlPanel.themeChanged(currentIndex)
                        }
                    }
                }

                // Anteprima colori tema corrente - Designer friendly
                Rectangle {
                    id: themePreview
                    Layout.fillWidth: true
                    height: 40
                    color: themeManager ? themeManager.backgroundColor : backgroundColor
                    border.color: themeManager ? themeManager.primaryColor : primaryColor
                    border.width: 2
                    radius: 5

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 5

                        Rectangle {
                            width: 20
                            height: 20
                            color: themeManager ? themeManager.primaryColor : primaryColor
                            radius: 3
                        }

                        Rectangle {
                            width: 20
                            height: 20
                            color: themeManager ? themeManager.secondaryColor : "#f39c12"
                            radius: 3
                        }

                        Rectangle {
                            width: 20
                            height: 20
                            color: themeManager ? themeManager.successColor : "#27ae60"
                            radius: 3
                        }

                        Label {
                            text: "Anteprima Tema"
                            font.pixelSize: 10
                            color: themeManager ? themeManager.textColor : textColor
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
                        font.pixelSize: buttonFontSize - 2
                        onClicked: {
                            if (themeManager) {
                                themeManager.resetTheme()
                                controlPanel.themeChanged(themeManager.currentTheme)
                            }
                        }
                    }

                    Button {
                        text: "🎲 Tema Casuale"
                        Layout.fillWidth: true
                        font.pixelSize: buttonFontSize - 2
                        onClicked: {
                            if (themeManager) {
                                themeManager.randomTheme()
                                controlPanel.themeChanged(themeManager.currentTheme)
                            }
                        }
                    }
                }
            }
        }

        // Sezione AI - Designer controllable
        GroupBox {
            title: "🤖 AI Assistant"
            Layout.fillWidth: true
            visible: showAIPanel
            border.width: 0

            ColumnLayout {
                anchors.fill: parent

                ComboBox {
                    id: aiModelCombo
                    Layout.fillWidth: true
                    Layout.minimumWidth: 200
                    Layout.preferredWidth: 250
                    model: availableModels
                    currentIndex: 0
                    font.pixelSize: labelFontSize
                    font.bold: labelBold
                    onCurrentTextChanged: selectedModel = currentText
                }

                CheckBox {
                    id: shiftEnterNewlineCheck
                    text: "Usa Shift+Invio per andare a capo"
                    checked: useShiftEnterForNewline
                    font.pixelSize: labelFontSize
                    font.bold: labelBold
                    onCheckedChanged: useShiftEnterForNewline = checked
                }

                Button {
                    text: "🚀 Chiedi all'AI"
                    Layout.fillWidth: true
                    Layout.minimumHeight: 35
                    font.pixelSize: buttonFontSize
                    font.bold: buttonBold
                    onClicked: controlPanel.sendToAI()
                }
            }
        }
    }

    // ===== DESIGNER STATES =====
    // Stati per il designer
    states: [
        State {
            name: "minimal"
            PropertyChanges { target: controlPanel; showTTSPanel: false }
            PropertyChanges { target: controlPanel; showThemePanel: false }
            PropertyChanges { target: controlPanel; showAIPanel: true }
        },
        State {
            name: "full"
            PropertyChanges { target: controlPanel; showTTSPanel: true }
            PropertyChanges { target: controlPanel; showThemePanel: true }
            PropertyChanges { target: controlPanel; showAIPanel: true }
        }
    ]

    // ===== DESIGNER METADATA =====
    Component.onCompleted: {
        console.log("ControlPanel initialized")
    }
}