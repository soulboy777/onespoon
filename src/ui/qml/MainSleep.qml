import QtQuick
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Effects
import QtQuick.Layouts

Window {
    id: mainWindow
    width: 680
    height: 460
    visible: true
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint

    property string currentMode: "execute"
    property string characterState: "idle"
    property bool responseVisible: false
    property string responseText: ""
    property string mainText: ""
    property string subText: ""

    property var theme: ({
        "bg_primary": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_panel": "#0f3460",
        "text_primary": "#eeeeee",
        "text_secondary": "#a0a0b0",
        "accent": "#0f3460",
        "highlight": "#e94560",
        "plan_color": "#4fc3f7",
        "exec_color": "#66bb6a",
        "glow_color": "#7c4dff",
        "border_color": "#2a2a4e",
        "input_bg": "#1e1e3e",
        "pillow_color": "#1e2a3a",
        "blanket_color": "#1a2436"
    })

    // ---- 拖拽 ----
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
        opacity: 0.94
        border.color: theme.border_color
        border.width: 1

        layer.enabled: true
        layer.effect: MultiEffect {
            blurEnabled: true
            blurMax: 32
            blur: 0.3
        }
    }

    // ═══════════════════════════════════
    //  Sleeping Layout
    // ═══════════════════════════════════
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        // ---- 上半：枕头(输入) + 角色 ----
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 90
            spacing: 10

            // 枕头区 → 输入框
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 14
                color: theme.pillow_color
                border.color: Qt.darker(theme.pillow_color, 1.1)

                // 枕头纹理标签
                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    text: "🛏"
                    font.pixelSize: 16
                    opacity: 0.5
                }

                SearchBar {
                    id: searchBar
                    anchors.fill: parent
                    anchors.margins: 8
                    anchors.leftMargin: 40
                    onSubmit: function(text) {
                        mainWindow.characterState = "thinking"
                        mainWindow.responseVisible = true
                        mainWindow.mainText = "思考中..."
                        mainWindow.subText = ""
                        uiBackend.submitInput(text)
                    }
                }
            }

            // 角色 (上部 — 头)
            Item {
                Layout.preferredWidth: 190
                Layout.fillHeight: true

                // 像素画角色 (Image, 呼吸/眨眼由 QML 处理)
                Image {
                    id: charImage
                    anchors.top: parent.top
                    anchors.topMargin: -8
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 170
                    height: 390
                    fillMode: Image.PreserveAspectFit
                    source: characterState === "idle" ? "../resources/characters/sleeping.png"
                            : "../resources/characters/" + characterState + ".png"
                    smooth: false

                    // 呼吸动画 (循环)
                    SequentialAnimation on opacity {
                        running: true
                        loops: Animation.Infinite
                        NumberAnimation { from: 0.85; to: 1.0; duration: 1800; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 1.0; to: 0.85; duration: 1800; easing.type: Easing.InOutSine }
                    }

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

                    Behavior on source {
                        SequentialAnimation {
                            NumberAnimation { target: charImage; property: "opacity"; to: 0; duration: 150 }
                            PropertyAction { target: charImage; property: "source" }
                            NumberAnimation { target: charImage; property: "opacity"; to: 1; duration: 150 }
                        }
                    }
                }

                // Zzz 气泡
                Text {
                    anchors.right: charImage.right
                    anchors.rightMargin: -10
                    anchors.top: charImage.top
                    anchors.topMargin: 20
                    text: characterState === "idle" ? "zZz" : ""
                    color: "#8899bb"
                    font.pixelSize: 13
                    opacity: characterState === "idle" ? 0.6 : 0

                    SequentialAnimation on opacity {
                        running: characterState === "idle"
                        loops: Animation.Infinite
                        NumberAnimation { from: 0.6; to: 0.2; duration: 1800; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 0.2; to: 0.6; duration: 1800; easing.type: Easing.InOutSine }
                    }
                }
            }
        }

        // ---- 下半：被子(响应) + 角色(下部) ----
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            // 被子区 → 响应
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 14
                color: theme.blanket_color
                border.color: Qt.darker(theme.blanket_color, 1.1)

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 4

                    Text {
                        text: "🛌"
                        font.pixelSize: 14
                        opacity: 0.4
                    }

                    ResponsePanel {
                        id: responsePanel
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: mainWindow.responseVisible || true
                        mainContent: mainWindow.mainText
                        subContent: mainWindow.subText
                        clip: true
                    }
                }

            // 角色 (下部 — 脚)
            Item {
                Layout.preferredWidth: 190
                Layout.fillHeight: true
                // 角色图片已在上半区渲染，下半区为脚部视觉占位
            }
        }

        // ---- 底部栏 ----
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            radius: 12
            color: theme.bg_secondary

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 6

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

                // 切换布局按钮
                Button {
                    flat: true
                    contentItem: Text {
                        text: "🔄"
                        font.pixelSize: 14
                        color: "#808090"
                        horizontalAlignment: Text.AlignHCenter
                    }
                    background: Rectangle { radius: 4; color: "transparent" }
                    onClicked: uiBackend.switchLayout("classic")
                    ToolTip.visible: hovered
                    ToolTip.text: "切换竖排布局"
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
        }
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

    // ---- Backend 信号连接 ----
    Connections {
        target: uiBackend
        function onResponseReady(text) { mainWindow.responseText = text }
        function onMainReady(text) { mainWindow.mainText = text }
        function onSubReady(text) { mainWindow.subText = text }
        function onCharacterStateChanged(state) { mainWindow.characterState = state }
        function onModeChanged(mode) { mainWindow.currentMode = mode }
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
    SequentialAnimation on opacity {
        id: showAnimation
        NumberAnimation { from: 0; to: 0.92; duration: 200; easing.type: Easing.OutCubic }
    }

    Component.onCompleted: {
        showAnimation.start()
    }
}
