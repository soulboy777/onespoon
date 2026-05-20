import QtQuick
import QtQuick.Controls

ScrollView {
    id: responsePanel
    visible: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical.policy: ScrollBar.AsNeeded

    property string mainContent: ""
    property string subContent: ""
    property var theme: ({
        "text_primary": "#eeeeee",
        "text_secondary": "#808090",
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
            spacing: 6

            // 主句 — 正常字号，白色
            Text {
                id: mainText
                text: mainContent
                color: theme.text_primary
                font.pixelSize: 15
                font.bold: true
                wrapMode: Text.WordWrap
                width: parent.width
                textFormat: Text.MarkdownText
                lineHeight: 1.6
                linkColor: "#7c4dff"
                visible: mainContent !== ""

                onLinkActivated: function(link) {
                    Qt.openUrlExternally(link)
                }
            }

            // 副句 — 小字号，暗色
            Text {
                id: subText
                text: subContent
                color: theme.text_secondary
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                width: parent.width
                textFormat: Text.MarkdownText
                lineHeight: 1.4
                linkColor: "#7c4dff"
                visible: subContent !== ""
                topPadding: 8

                onLinkActivated: function(link) {
                    Qt.openUrlExternally(link)
                }
            }
        }
    }
}
