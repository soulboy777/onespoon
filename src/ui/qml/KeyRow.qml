import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    property string label: ""
    property string value: ""
    property var onChanged: function(v) {}

    Layout.fillWidth: true
    spacing: 8

    Text {
        text: label
        color: "#a0a0b0"
        font.pixelSize: 12
        Layout.preferredWidth: 130
    }

    TextField {
        id: keyField
        text: value
        color: "#eee"
        font.pixelSize: 12
        echoMode: eyeBtn.checked ? TextInput.Normal : TextInput.Password
        passwordCharacter: "●"
        Layout.fillWidth: true
        background: Rectangle { radius: 6; color: "#1e1e3e"; border.color: "#2a2a4e" }
        onTextChanged: onChanged(text)
    }

    Button {
        id: eyeBtn
        checkable: true
        width: 30; height: 30
        flat: true
        contentItem: Text {
            text: eyeBtn.checked ? "🙈" : "👁"
            font.pixelSize: 14
            horizontalAlignment: Text.AlignHCenter
        }
        background: Rectangle { radius: 6; color: eyeBtn.checked ? "#333" : "transparent" }
    }
}
