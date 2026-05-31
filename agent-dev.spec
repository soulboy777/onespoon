# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

rich_imports = collect_submodules('rich')

a = Analysis(
    ['src/entry.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/ui/qml/*.qml', 'src/ui/qml'),
        ('config/default.yaml', 'config'),
        ('config/models.yaml', 'config'),
        ('config/plan-template.md', 'config'),
        ('src/ui/resources/characters/*', 'src/ui/resources/characters'),
        ('icon/agent-dev.ico', 'icon'),
    ],
    hiddenimports=[
        # PySide6 QML
        'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtQuickControls2',
        # LLM / AI
        'langchain_openai', 'langchain_community', 'langchain_anthropic', 'langchain_text_splitters',
        'litellm',
        # ChromaDB
        'chromadb',
        # tiktoken
        'tiktoken_ext', 'tiktoken_ext.openai_public',
        # Pydantic
        'pydantic_settings',
        # Config
        'yaml',
        # Logging
        'loguru',
        # CLI
        'typer',
        # Scheduling
        'apscheduler.schedulers.background', 'apscheduler.triggers.cron', 'apscheduler.triggers.date',
        # File monitoring
        'watchdog',
        # Search
        'rank_bm25',
        # Document parsing
        'docx', 'PyPDF2',
        # Support
        'charset_normalizer',
    ] + rich_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'numpy.testing', 'numpy.random._examples',
        'IPython', 'jupyter', 'notebook', 'pandas', 'pandas.tests',
        'PIL', 'unstructured', 'torch',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='agent-dev',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['python3*.dll', 'Qt*.dll', 'PySide6/*.dll', 'onnxruntime*.dll'],
    runtime_tmpdir=None,
    console=True,
    icon='icon/agent-dev.ico',
)

coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=True,
    upx_exclude=['python3*.dll', 'Qt*.dll', 'PySide6/*.dll', 'onnxruntime*.dll'],
    name='agent-dev',
)
