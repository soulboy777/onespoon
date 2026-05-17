import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    property string label: ""
    property var value
    property bool edit: false
    property bool combo: false
    property var comboOptions: []
    property string type: ""   // slider, toggle

    spacing: 12
    Layout.fillWidth: true

    Text {
        text: label
        color: "#a0a0b0"
        font.pixelSize: 12
        Layout.preferredWidth: 100
    }

    TextField {
        visible: edit
        text: String(value || "")
        color: "#eee"
        font.pixelSize: 12
        Layout.fillWidth: true
        background: Rectangle { radius: 6; color: "#1e1e3e"; border.color: "#2a2a4e" }
        onTextChanged: value = text
    }

    ComboBox {
        visible: combo
        model: comboOptions
        currentIndex: comboOptions.indexOf(String(value))
        Layout.fillWidth: true
        contentItem: Text { text: currentText; color: "#eee"; font.pixelSize: 12 }
        background: Rectangle { radius: 6; color: "#1e1e3e"; border.color: "#2a2a4e" }
        onCurrentTextChanged: value = currentText
    }

    Slider {
        visible: type === "slider"
        from: 0.0; to: 1.0
        value: Number(value) || 0.7
        Layout.fillWidth: true
        onValueChanged: value = value
        background: Rectangle { radius: 3; color: "#333"; height: 6 }
        handle: Rectangle { width: 16; height: 16; radius: 8; color: "#7c4dff" }
    }

    Switch {
        visible: type === "toggle"
        checked: Boolean(value)
        Layout.alignment: Qt.AlignRight
        onCheckedChanged: value = checked
    }
}
