# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path(__file__).parent

a = Analysis(
    ['src/entry.py'],
    pathex=[],
    binaries=[],
    datas=[
        # QML files
        ('src/ui/qml/*.qml', 'qml'),
        # Config files (non-sensitive)
        ('config/default.yaml', 'config'),
        ('config/models.yaml', 'config'),
        ('config/plan-template.md', 'config'),
        # UI resources
        ('src/ui/resources/icons/*', 'resources/icons'),
        ('src/ui/resources/fonts/*', 'resources/fonts'),
        ('src/ui/resources/character/*', 'resources/character'),
    ],
    hiddenimports=[
        # PySide6 QML
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuick.Controls',
        'PySide6.QtQuick.Layouts',
        'PySide6.QtQuick.Effects',
        # AI / LLM
        'langchain',
        'langchain.agents',
        'langchain.tools',
        'langchain_openai',
        'langchain_community',
        'langchain_community.chat_models',
        'langchain_community.embeddings',
        'langchain_core',
        'langchain_core.language_models',
        'langchain_core.messages',
        'langchain_core.prompts',
        'langchain_text_splitters',
        'langchain_anthropic',
        # litellm
        'litellm',
        # ChromaDB
        'chromadb',
        'chromadb.config',
        'chromadb.api',
        'chromadb.db',
        'chromadb.db.duckdb',
        'chromadb.segment',
        'chromadb.segment.impl.vector',
        'chromadb.utils.embedding_functions',
        'chromadb.telemetry',
        'chromadb.telemetry.product',
        'chromadb.telemetry.product.posthog',
        # hnswlib (ChromaDB dependency)
        'hnswlib',
        # onnxruntime (ChromaDB dependency)
        'onnxruntime',
        # tiktoken
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        # SQLAlchemy
        'sqlalchemy',
        'sqlalchemy.orm',
        'sqlalchemy.ext.declarative',
        # Pydantic
        'pydantic',
        'pydantic_settings',
        # YAML
        'yaml',
        # Logging
        'loguru',
        # CLI
        'typer',
        'rich',
        'rich.console',
        'rich.markdown',
        'rich.panel',
        'rich.table',
        # Scheduling
        'apscheduler',
        'apscheduler.schedulers',
        'apscheduler.schedulers.background',
        'apscheduler.triggers',
        'apscheduler.triggers.cron',
        'apscheduler.triggers.date',
        # File monitoring
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        # Search
        'rank_bm25',
        # Document parsing
        'docx',
        'PyPDF2',
        # HTTP
        'urllib3',
        'requests',
        'certifi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy.testing',
        'numpy.random._examples',
        'IPython',
        'jupyter',
        'notebook',
        'pandas',
        'pandas.tests',
        'PIL',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
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
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['python3*.dll', 'Qt*.dll', 'PySide6/*.dll', 'onnxruntime*.dll'],
    name='agent-dev',
)
