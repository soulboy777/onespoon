# ============================================================
# 一键构建脚本 — PyInstaller 打包 + Inno Setup 安装器
# ============================================================

param(
    [switch]$SkipInstaller,
    [switch]$CleanOnly
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT = Split-Path -Parent $ROOT

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Agent 开发助手 v1.0.1 — 构建脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 清理旧构建
if ($CleanOnly) {
    Write-Host "[1/2] 清理旧构建..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "$ROOT\build", "$ROOT\dist" -ErrorAction SilentlyContinue
    Write-Host "  ✓ 清理完成" -ForegroundColor Green
    exit 0
}

# 重新打包：先清理
Write-Host "[1/4] 清理旧构建..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "$ROOT\build", "$ROOT\dist" -ErrorAction SilentlyContinue

# 2. PyInstaller 打包
Write-Host "[2/4] PyInstaller 打包..." -ForegroundColor Yellow
Push-Location $ROOT
try {
    $result = pyinstaller agent-dev.spec --clean --noconfirm 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ PyInstaller 失败!" -ForegroundColor Red
        Write-Host $result
        exit 1
    }
    Write-Host "  ✓ PyInstaller 完成" -ForegroundColor Green
}
finally {
    Pop-Location
}

# 3. 复制额外文件
Write-Host "[3/4] 复制运行时文件..." -ForegroundColor Yellow
$distDir = "$ROOT\dist\agent-dev"

# data 目录结构
$dataDirs = @("data\logs", "data\notes", "data\plans")
foreach ($dir in $dataDirs) {
    New-Item -ItemType Directory -Force -Path "$distDir\$dir" | Out-Null
}

# user.yaml 模板 (非敏感)
@"
# 用户配置 — 启动后由 UI 设置面板管理
# 或手动编辑此文件后重启应用

ui:
  theme: dark
  font_size: 14
  auto_hide_seconds: 0
  hotkey: Alt+Space
  character_visible: true
  character_position: right
  auto_start: true
  layout: sleep

api_keys:
  openai_api_key: ""
  anthropic_api_key: ""
  dashscope_api_key: ""
  deepseek_api_key: ""
  ollama_base_url: "http://localhost:11434"

llm:
  default_model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 4096
  streaming: true

memory:
  buffer_max_tokens: 4000
  semantic_top_k: 5
  episodic_top_k: 3
  importance_threshold: 0.5

rag:
  embedding_provider: "openai"
  embedding_model: "text-embedding-3-small"
  embedding_base_url: ""
  chunk_size: 500
  chunk_overlap: 50
  chunk_strategy: "recursive"
  default_top_k: 5
  hybrid_alpha: 0.7
"@ | Out-File -FilePath "$distDir\config\user.yaml" -Encoding utf8

Write-Host "  ✓ 运行时文件已复制" -ForegroundColor Green

# 4. 压缩包
Write-Host "[4/4] 生成压缩包..." -ForegroundColor Yellow
$zipPath = "$ROOT\dist\agent-dev-v0.2.0.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$distDir\*" -DestinationPath $zipPath -Force
Write-Host "  ✓ 压缩包: $zipPath" -ForegroundColor Green

# 5. Inno Setup (可选)
if (-not $SkipInstaller) {
    $innoPaths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $inno = $null
    foreach ($p in $innoPaths) {
        if (Test-Path $p) { $inno = $p; break }
    }

    if ($inno) {
        Write-Host "[5] Inno Setup 打包..." -ForegroundColor Yellow
        Push-Location "$ROOT\installer"
        try {
            & $inno setup.iss
            Write-Host "  ✓ 安装器: $ROOT\installer\dist\AgentDev-Setup-0.2.0.exe" -ForegroundColor Green
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Host "[5] Inno Setup 未安装，跳过安装器生成" -ForegroundColor DarkYellow
        Write-Host "    下载: https://jrsoftware.org/isdl.php" -ForegroundColor DarkYellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 构建完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  目录:   $distDir" -ForegroundColor White
Write-Host "  压缩包: $zipPath" -ForegroundColor White
if (-not $SkipInstaller -and $inno) {
    Write-Host "  安装器: $ROOT\installer\dist\AgentDev-Setup-0.2.0.exe" -ForegroundColor White
}
Write-Host ""
