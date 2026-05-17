import QtQuick
import QtQuick.Controls

Button {
    id: btn
    property bool active: false
    property string color: "#7c4dff"

    contentItem: Text {
        text: btn.text
        color: active ? "white" : "#808090"
        font.pixelSize: 10
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: 4
        color: active ? btn.color : "#1e1e3e"
        border.color: active ? btn.color : "#2a2a4e"
    }
}
