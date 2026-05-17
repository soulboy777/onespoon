import QtQuick
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Effects
import QtQuick.Layouts

Window {
    id: mainWindow
    width: 620
    height: 420
    visible: true
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint

    property string currentMode: "execute"
    property string characterState: "idle"
    property bool responseVisible: false
    property string responseText: ""
    
    property var theme: ({
        "bg_primary": "#1a1a2e",
        "bg_secondary": "#16213e",
        "text_primary": "#eeeeee",
        "text_secondary": "#a0a0b0",
        "accent": "#0f3460",
        "highlight": "#e94560",
        "plan_color": "#4fc3f7",
        "exec_color": "#66bb6a",
        "glow_color": "#7c4dff",
        "border_color": "#2a2a4e",
        "input_bg": "#1e1e3e"
    })

    // ---- 窗口拖拽 ----
    MouseArea {
        id: dragArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        property point lastPos: Qt.point(0, 0)
        onPressed: { lastPos = Qt.point(mouseX, mouseY) }
        onPositionChanged: {
            if (pressed) {
                mainWindow.x += mouseX - lastPos.x
                mainWindow.y += mouseY - lastPos.y
            }
        }
    }

    // ---- 主容器 ----
    Rectangle {
        anchors.fill: parent
        radius: 16
        color: theme.bg_primary
        opacity: 0.92
        border.color: theme.border_color
        border.width: 1

        // ---- 透明模糊背景 ----
        layer.enabled: true
        layer.effect: MultiEffect {
            blurEnabled: true
            blurMax: 32
            blur: 0.3
        }
    }

    // ---- 布局 ----
    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // 左侧：角色
        Item {
            Layout.preferredWidth: 160
            Layout.fillHeight: true
            visible: true

            CharacterWidget {
                anchors.centerIn: parent
                charState: mainWindow.characterState
            }
        }

        // 右侧：搜索 + 响应
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            // 顶部按钮行
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Item { Layout.fillWidth: true }

                ModeIndicator {
                    mode: mainWindow.currentMode
                }

                IconButton {
                    iconText: "⚙"
                    tooltip: "设置"
                    onClicked: settingsPopup.open()
                }

                IconButton {
                    iconText: "ℹ"
                    tooltip: "关于"
                    onClicked: aboutPopup.open()
                }

                IconButton {
                    iconText: "−"
                    tooltip: "最小化"
                    onClicked: mainWindow.visible = false
                }

                IconButton {
                    iconText: "×"
                    tooltip: "退出"
                    color: theme.highlight
                    onClicked: Qt.quit()
                }
            }

            // 搜索框
            SearchBar {
                id: searchBar
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                onSubmit: function(text) {
                    mainWindow.characterState = "thinking"
                    mainWindow.responseVisible = true
                    mainWindow.responseText = "思考中..."
                    uiBackend.submitInput(text)
                }
            }

            // 响应面板
            ResponsePanel {
                id: responsePanel
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: mainWindow.responseVisible
                textContent: mainWindow.responseText

                Behavior on Layout.preferredHeight {
                    NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                }
            }

            // 底部模式栏
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                ModeButton {
                    text: "PLAN"
                    active: mainWindow.currentMode === "plan"
                    color: theme.plan_color
                    onClicked: {
                        mainWindow.currentMode = "plan"
                        uiBackend.toggleMode()
                    }
                }

                ModeButton {
                    text: "EXEC"
                    active: mainWindow.currentMode === "execute"
                    color: theme.exec_color
                    onClicked: {
                        mainWindow.currentMode = "execute"
                        uiBackend.toggleMode()
                    }
                }

                Item { Layout.fillWidth: true }

                SmallLabel {
                    text: mainWindow.currentMode === "plan" ? "只读" : "完全"
                    color: mainWindow.currentMode === "plan" ? theme.plan_color : theme.exec_color
                }
            }
        }
    }

    // ---- 呼入动画 ----
    SequentialAnimation on opacity {
        id: showAnimation
        NumberAnimation { from: 0; to: 0.92; duration: 200; easing.type: Easing.OutCubic }
    }

    // ---- 快捷键 ----
    Shortcut {
        sequence: "Alt+Space"
        onActivated: {
            mainWindow.visible = !mainWindow.visible
            if (mainWindow.visible) {
                mainWindow.show()
                mainWindow.raise()
                mainWindow.requestActivate()
                searchBar.focusInput()
            }
        }
    }

    Shortcut {
        sequence: "Esc"
        onActivated: mainWindow.visible = false
    }

    // ---- 弹出窗口 ----
    Popup {
        id: settingsPopup
        width: 520
        height: 440
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        anchors.centerIn: parent

        SettingsWindow {
            anchors.fill: parent
            onSaved: settingsPopup.close()
            onCanceled: settingsPopup.close()
        }
    }

    Popup {
        id: aboutPopup
        width: 380
        height: 340
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        anchors.centerIn: parent

        AboutPanel {
            anchors.fill: parent
            onClose: aboutPopup.close()
        }
    }

    // ---- 初始动画 ----
    Component.onCompleted: {
        showAnimation.start()
    }
}
