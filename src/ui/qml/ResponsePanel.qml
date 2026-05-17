import QtQuick
import QtQuick.Controls

ScrollView {
    id: responsePanel
    visible: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical.policy: ScrollBar.AsNeeded

    property string textContent: ""
    property var theme: ({
        "text_primary": "#eeeeee",
        "text_secondary": "#a0a0b0",
        "bg_secondary": "#16213e"
    })

    Rectangle {
        width: responsePanel.width
        color: "transparent"
        implicitHeight: Math.max(responsePanel.height, contentColumn.height + 24)

        Column {
            id: contentColumn
            width: parent.width - 16
            x: 8
            y: 12
            spacing: 8

            Text {
                id: responseText
                text: textContent
                color: theme.text_primary
                font.pixelSize: 14
                wrapMode: Text.WordWrap
                width: parent.width
                textFormat: Text.MarkdownText
                lineHeight: 1.6
                linkColor: "#7c4dff"

                onLinkActivated: function(link) {
                    Qt.openUrlExternally(link)
                }
            }
        }
    }
}
