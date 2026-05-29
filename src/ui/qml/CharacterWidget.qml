import QtQuick
import QtQuick.Controls

Item {
    id: character
    width: 150
    height: 300

    property string charState: "idle"
    property string currentImage: "../resources/characters/" + charState + ".png"
    property var theme: ({
        "text_secondary": "#a0a0b0"
    })

    // 角色主体 (PNG) — 顶部对齐
    Image {
        id: charImage
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        width: 140
        height: 280
        fillMode: Image.PreserveAspectFit
        source: currentImage
        smooth: false     // 像素画不需平滑
        opacity: 1

        // 呼吸动画 (循环)
        SequentialAnimation on opacity {
            running: true
            loops: Animation.Infinite
            NumberAnimation { from: 0.85; to: 1.0; duration: 1500; easing.type: Easing.InOutSine }
            NumberAnimation { from: 1.0; to: 0.85; duration: 1500; easing.type: Easing.InOutSine }
        }

        // 悬停放大
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onEntered: scaleAnim.to = 1.04
            onExited: scaleAnim.to = 1.0
        }

        ScaleAnimator on scale {
            id: scaleAnim
            from: 1.0; to: 1.0; duration: 200
        }
    }

    // 表情切换动画
    Behavior on currentImage {
        SequentialAnimation {
            NumberAnimation { target: charImage; property: "opacity"; to: 0; duration: 150 }
            PropertyAction { target: charImage; property: "source"; value: currentImage }
            NumberAnimation { target: charImage; property: "opacity"; to: 1; duration: 150 }
        }
    }

    // 眨眼 (周期性)
    Timer {
        interval: 4000
        running: true
        repeat: true
        onTriggered: blinkAnimation.start()
    }

    SequentialAnimation {
        id: blinkAnimation
        NumberAnimation { target: charImage; property: "scale"; to: 10; duration: 80 }
        NumberAnimation { target: charImage; property: "scale"; to: 1; duration: 120 }
    }

    // 底部状态标签
    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        text: {
            switch (charState) {
                case "idle": return "";
                case "sleeping": return "";
                case "thinking": return "Thinking...";
                case "happy": return "Done!";
                case "busy": return "Oops!";
                default: return "";
            }
        }
        color: theme.text_secondary
        font.pixelSize: 11
        opacity: (charState === "idle" || charState === "sleeping") ? 0 : 0.8
    }
}
