import QtQuick
import QtQuick.Controls

Button {
    id: btn
    property string color: "#7c4dff"

    contentItem: Text {
        text: btn.text
        color: btn.color
        font.pixelSize: 12
        horizontalAlignment: Text.AlignHCenter
    }

    background: Rectangle {
        radius: 4
        color: "transparent"
    }
}
