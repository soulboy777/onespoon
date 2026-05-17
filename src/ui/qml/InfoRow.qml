import QtQuick
import QtQuick.Layouts

RowLayout {
    property string label: ""
    property string value: ""

    Text {
        text: label
        color: "#808090"
        font.pixelSize: 12
        Layout.preferredWidth: 70
    }

    Text {
        text: value
        color: "#ccc"
        font.pixelSize: 12
    }
}
