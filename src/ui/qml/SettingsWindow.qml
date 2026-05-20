import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    radius: 12
    color: "#1a1a2e"
    border.color: "#2a2a4e"

    property var onSaved: function() {}
    property var onCanceled: function() {}
    property var uiBackend: null

    // 临时存储设置值
    property string llmModel: "gpt-4o-mini"
    property real temperature: 0.7
    property int maxTokens: 4096
    property bool streaming: true

    property string openaiKey: ""
    property string anthropicKey: ""
    property string dashscopeKey: ""
    property string deepseekKey: ""
    property string ollamaUrl: "http://localhost:11434"

    property string embedModel: "text-embedding-3-small"
    property string embedProvider: "openai"

    property int chunkSize: 500
    property int chunkOverlap: 50
    property string chunkStrategy: "recursive"
    property int ragTopK: 5
    property real hybridAlpha: 0.7

    property int bufferTokens: 4000
    property int semanticTopK: 5

    property string uiTheme: "dark"
    property int fontSize: 14
    property int autoHide: 0
    property string hotkey: "Alt+Space"
    property bool charVisible: true
    property string charPosition: "right"
    property string uiLayout: "sleep"

    // 密钥可见性
    property bool keyVisible: false

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8

        // 标题
        Text {
            text: "⚙ 设置"
            color: "#eeeeee"
            font.pixelSize: 18
            font.bold: true
        }

        // Tab 切换
        TabBar {
            id: tabBar
            Layout.fillWidth: true
            background: Rectangle { color: "transparent" }

            TabButton { text: "LLM"; contentItem: Text { text: "LLM"; color: "#ccc"; font.pixelSize: 12 } }
            TabButton { text: "API"; contentItem: Text { text: "API"; color: "#ccc"; font.pixelSize: 12 } }
            TabButton { text: "嵌入"; contentItem: Text { text: "嵌入"; color: "#ccc"; font.pixelSize: 12 } }
            TabButton { text: "RAG"; contentItem: Text { text: "RAG"; color: "#ccc"; font.pixelSize: 12 } }
            TabButton { text: "记忆"; contentItem: Text { text: "记忆"; color: "#ccc"; font.pixelSize: 12 } }
            TabButton { text: "界面"; contentItem: Text { text: "界面"; color: "#ccc"; font.pixelSize: 12 } }
        }

        // Tab 内容区
        StackLayout {
            id: tabStack
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            // ---- LLM Tab ----
            ColumnLayout {
                spacing: 12
                SettingRow { label: "默认模型"; value: llmModel; edit: true }
                SettingRow { label: "Temperature"; value: temperature; type: "slider" }
                SettingRow { label: "Max Tokens"; value: maxTokens; edit: true }
                SettingRow { label: "Streaming"; value: streaming; type: "toggle" }
            }

            // ---- API Keys Tab ----
            ColumnLayout {
                spacing: 8
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    ColumnLayout {
                        spacing: 10
                        KeyRow { label: "OpenAI API Key"; value: root.openaiKey; onChanged: function(v) { root.openaiKey = v } }
                        KeyRow { label: "Anthropic API Key"; value: root.anthropicKey; onChanged: function(v) { root.anthropicKey = v } }
                        KeyRow { label: "DashScope API Key"; value: root.dashscopeKey; onChanged: function(v) { root.dashscopeKey = v } }
                        KeyRow { label: "DeepSeek API Key"; value: root.deepseekKey; onChanged: function(v) { root.deepseekKey = v } }
                        SettingRow { label: "Ollama URL"; value: root.ollamaUrl; edit: true }
                    }
                }
                Text {
                    text: "🔒 密钥保存在 config/user.yaml (不会上传到 Git)"
                    color: "#606080"
                    font.pixelSize: 11
                }
            }

            // ---- Embedding Tab ----
            ColumnLayout {
                spacing: 12
                SettingRow { label: "Provider"; value: embedProvider; combo: true; comboOptions: ["openai", "ollama", "openai_compatible"] }
                SettingRow { label: "模型"; value: embedModel; edit: true }
            }

            // ---- RAG Tab ----
            ColumnLayout {
                spacing: 12
                SettingRow { label: "分块策略"; value: chunkStrategy; combo: true; comboOptions: ["fixed", "recursive", "sentence"] }
                SettingRow { label: "分块大小"; value: chunkSize; edit: true }
                SettingRow { label: "分块重叠"; value: chunkOverlap; edit: true }
                SettingRow { label: "检索条数"; value: ragTopK; edit: true }
                SettingRow { label: "混合权重"; value: hybridAlpha; type: "slider" }
            }

            // ---- Memory Tab ----
            ColumnLayout {
                spacing: 12
                SettingRow { label: "Buffer Tokens"; value: bufferTokens; edit: true }
                SettingRow { label: "语义检索 Top-K"; value: semanticTopK; edit: true }
            }

            // ---- UI Tab ----
            ColumnLayout {
                spacing: 12
                SettingRow { label: "主题"; value: uiTheme; combo: true; comboOptions: ["dark", "light"] }
                SettingRow { label: "字体大小"; value: fontSize; edit: true }
                SettingRow { label: "自动隐藏 (秒)"; value: autoHide; combo: true; comboOptions: ["0", "10", "30", "60"] }
                SettingRow { label: "快捷键"; value: hotkey; edit: true }
                SettingRow { label: "角色显示"; value: charVisible; type: "toggle" }
                SettingRow { label: "角色位置"; value: charPosition; combo: true; comboOptions: ["left", "right"] }
                SettingRow { label: "布局"; value: uiLayout; combo: true; comboOptions: ["sleep", "classic"] }
            }
        }

        // 底部按钮
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Item { Layout.fillWidth: true }

            Button {
                text: "取消"
                onClicked: onCanceled()
                background: Rectangle { color: "#333"; radius: 6 }
                contentItem: Text { text: "取消"; color: "#ccc"; horizontalAlignment: Text.AlignHCenter }
            }

            Button {
                text: "保存"
                onClicked: {
                    uiBackend.saveSettings({
                        llm_model: llmModel, temperature: temperature, max_tokens: maxTokens, streaming: streaming,
                        openai_key: openaiKey, anthropic_key: anthropicKey, dashscope_key: dashscopeKey,
                        deepseek_key: deepseekKey, ollama_url: ollamaUrl,
                        embed_provider: embedProvider, embed_model: embedModel,
                        chunk_size: chunkSize, chunk_overlap: chunkOverlap, chunk_strategy: chunkStrategy,
                        rag_top_k: ragTopK, hybrid_alpha: hybridAlpha,
                        buffer_tokens: bufferTokens, semantic_top_k: semanticTopK,
                        theme: uiTheme, font_size: fontSize, auto_hide: autoHide, hotkey: hotkey,
                        char_visible: charVisible, char_position: charPosition,
                        ui_layout: uiLayout
                    })
                    onSaved()
                }
                background: Rectangle { color: "#7c4dff"; radius: 6 }
                contentItem: Text { text: "保存"; color: "white"; horizontalAlignment: Text.AlignHCenter }
            }
        }
    }
}
