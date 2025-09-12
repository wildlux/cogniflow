import QtQuick 6.2
import QtQuick.Controls 6.2
import QtQuick.Layouts 6.2

ApplicationWindow {
    id: mainWindow
    width: 800
    height: 600
    visible: true
    title: "Test MediaPipe Integration"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10

        Text {
            text: "🤖 MediaPipe Integration Test"
            font.pixelSize: 20
            font.bold: true
        }

        Button {
            text: "Test MediaPipe Bridge"
            onClicked: {
                if (typeof mediaPipeBridge !== "undefined") {
                    console.log("MediaPipe bridge available")
                    mediaPipeBridge.toggleWebcam()
                } else {
                    console.log("MediaPipe bridge not available")
                }
            }
        }

        TextArea {
            id: logArea
            Layout.fillWidth: true
            Layout.fillHeight: true
            readOnly: true
            placeholderText: "Log messages will appear here..."
        }
    }

    // MediaPipe bridge connections
    Connections {
        target: typeof mediaPipeBridge !== "undefined" ? mediaPipeBridge : null
        ignoreUnknownSignals: false

        function onStatusChanged(status) {
            logArea.append("Status: " + status)
        }

        function onWebcamToggled(enabled) {
            logArea.append("Webcam: " + (enabled ? "started" : "stopped"))
        }
    }
}
