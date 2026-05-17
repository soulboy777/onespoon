import QtQuick
import QtQuick.Controls

Rectangle {
    id: planPanel
    color: "transparent"

    property var plans: []
    property var onExecutePlan: function(id) {}

    Column {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        Text {
            text: "计划列表"
            color: "#eeeeee"
            font.pixelSize: 14
            font.bold: true
        }

        ListView {
            width: parent.width
            height: parent.height - 40
            model: plans
            clip: true
            spacing: 6

            delegate: Rectangle {
                width: ListView.view.width
                height: 60
                radius: 8
                color: "#16213e"

                Column {
                    anchors.left: parent.left
                    anchors.leftMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4

                    Text {
                        text: modelData.title || "Untitled"
                        color: "#eeeeee"
                        font.pixelSize: 13
                    }

                    Text {
                        text: (modelData.status || "") + " | " + (modelData.completed_steps || 0) + "/" + (modelData.total_steps || 0) + " steps"
                        color: "#808090"
                        font.pixelSize: 11
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: onExecutePlan(modelData.id)
                }
            }
        }
    }
}
