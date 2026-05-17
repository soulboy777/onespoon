import QtQuick
import QtQuick.Controls
import QtQuick.Effects

Rectangle {
    id: searchBar
    radius: 22
    color: "#1e1e3e"
    border.color: "#7c4dff"
    border.width: activeFocus ? 2 : 1
    height: 44

    property alias placeholderText: placeholder.text
    property var onSubmit: function(text) {}

    function focusInput() {
        inputField.forceActiveFocus()
    }

    Row {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 8
        spacing: 8

        Text {
            text: "🔍"
            font.pixelSize: 16
            anchors.verticalCenter: parent.verticalCenter
            opacity: 0.6
        }

        TextInput {
            id: inputField
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - 80
            color: "#eeeeee"
            font.pixelSize: 15
            clip: true

            Text {
                id: placeholder
                anchors.fill: parent
                text: "输入任何指令..."
                color: "#606080"
                font.pixelSize: 15
                visible: inputField.text === "" && !inputField.activeFocus
            }

            Keys.onReturnPressed: function(event) {
                var text = inputField.text.trim()
                if (text !== "") {
                    searchBar.onSubmit(text)
                    inputField.text = ""
                }
            }
        }

        IconButton {
            iconText: "→"
            anchors.verticalCenter: parent.verticalCenter
            tooltip: "发送 (Enter)"
            onClicked: {
                var text = inputField.text.trim()
                if (text !== "") {
                    searchBar.onSubmit(text)
                    inputField.text = ""
                }
            }
        }
    }

    // 光晕效果
    layer.enabled: activeFocus
    layer.effect: MultiEffect {
        glowEnabled: true
        glowRadius: 8
        glowColor: "#7c4dff"
    }
}
