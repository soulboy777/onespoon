import QtQuick
import QtQuick.Controls

Row {
    id: modeIndicator
    spacing: 6
    height: 28

    property string mode: "execute"
    property var theme: ({
        "plan_color": "#4fc3f7",
        "exec_color": "#66bb6a",
        "text_secondary": "#a0a0b0"
    })

    Rectangle {
        width: 10
        height: 10
        radius: 5
        anchors.verticalCenter: parent.verticalCenter
        color: mode === "plan" ? theme.plan_color : theme.exec_color

        SequentialAnimation on opacity {
            running: true
            loops: Animation.Infinite
            NumberAnimation { from: 1.0; to: 0.3; duration: 800; easing.type: Easing.InOutSine }
            NumberAnimation { from: 0.3; to: 1.0; duration: 800; easing.type: Easing.InOutSine }
        }
    }

    Text {
        text: mode === "plan" ? "PLAN" : "EXEC"
        color: mode === "plan" ? theme.plan_color : theme.exec_color
        font.pixelSize: 11
        font.bold: true
        anchors.verticalCenter: parent.verticalCenter
    }
}
