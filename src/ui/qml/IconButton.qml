import QtQuick
import QtQuick.Controls

Button {
    id: btn
    property string iconText: ""
    property string tooltip: ""
    property string color: "#808090"

    width: 28; height: 28
    flat: true

    contentItem: Text {
        text: iconText
        color: btn.color
        font.pixelSize: 16
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: 6
        color: btn.hovered ? "#2a2a4e" : "transparent"
    }

    ToolTip.visible: hovered && tooltip !== ""
    ToolTip.text: tooltip
}
