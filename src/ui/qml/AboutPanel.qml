import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    radius: 12
    color: "#1a1a2e"
    border.color: "#2a2a4e"

    property var onClose: function() {}

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 12

        Text {
            text: "ℹ 关于"
            color: "#eeeeee"
            font.pixelSize: 18
            font.bold: true
        }

        Item { Layout.preferredHeight: 8 }

        // 标题
        Text {
            text: "Agent 开发助手"
            color: "#7c4dff"
            font.pixelSize: 20
            font.bold: true
        }

        Text {
            text: "v0.2.0"
            color: "#a0a0b0"
            font.pixelSize: 13
        }

        Item { Layout.preferredHeight: 4 }

        Text {
            text: "桌面 AI 智能助手"
            color: "#ccc"
            font.pixelSize: 13
        }

        Text {
            text: "多模型 · 记忆 · RAG · 计划执行"
            color: "#808090"
            font.pixelSize: 12
        }

        Item { Layout.preferredHeight: 8 }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#2a2a4e"
        }

        GridLayout {
            columns: 2
            rowSpacing: 6
            columnSpacing: 16

            InfoRow { label: "版本"; value: "v0.2.0" }
            InfoRow { label: "构建日期"; value: "2026-05-17" }
            InfoRow { label: "Python"; value: "3.11" }
            InfoRow { label: "Qt"; value: "6.6 (PySide6)" }
            InfoRow { label: "开发"; value: "soulboy777" }
            InfoRow { label: "画师"; value: "神启小白" }
        }

        Item { Layout.fillHeight: true }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#2a2a4e"
        }

        RowLayout {
            spacing: 16

            TextButton {
                text: "GitHub"
                onClicked: Qt.openUrlExternally("https://github.com/soulboy777/onespoon")
            }

            TextButton {
                text: "更新日志"
                onClicked: Qt.openUrlExternally("https://github.com/soulboy777/onespoon/releases")
            }

            TextButton {
                text: "反馈问题"
                onClicked: Qt.openUrlExternally("https://github.com/soulboy777/onespoon/issues")
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "关闭"
                onClicked: onClose()
                background: Rectangle { color: "#333"; radius: 6 }
                contentItem: Text { text: "关闭"; color: "#ccc"; horizontalAlignment: Text.AlignHCenter }
            }
        }
    }
}
