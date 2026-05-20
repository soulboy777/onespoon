import QtQuick
import QtQuick.Controls

Item {
    id: character
    width: 150
    height: 300

    property string charState: "idle"
    property string currentImage: "resources/characters/" + charState + ".apng"
    property var theme: ({
        "text_secondary": "#a0a0b0"
    })

    // 角色动态 APNG — 呼吸/眨眼/表情由画师做到图里
    AnimatedImage {
        id: charImage
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        width: 140
        height: 280
        fillMode: Image.PreserveAspectFit
        source: currentImage
        smooth: true
        playing: true
        paused: false

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

    // 底部状态标签
    Text {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        text: {
            switch (charState) {
                case "idle": return "";
                case "sleeping": return "";
                case "thinking": return "思考中...";
                case "happy": return "完成!";
                case "busy": return "处理中";
                default: return "";
            }
        }
        color: theme.text_secondary
        font.pixelSize: 11
        opacity: (charState === "idle" || charState === "sleeping") ? 0 : 0.8
    }
}
