# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# Auto-discover all submodules for problematic packages
rich_imports = collect_submodules('rich')
langchain_imports = collect_submodules('langchain')
pydantic_imports = collect_submodules('pydantic')

ROOT = Path(".").resolve()

a = Analysis(
    ['src/entry.py'],
    pathex=[],
    binaries=[],
    datas=[
        # QML files
        ('src/ui/qml/*.qml', 'src/ui/qml'),
        # Config files (non-sensitive)
        ('config/default.yaml', 'config'),
        ('config/models.yaml', 'config'),
        ('config/plan-template.md', 'config'),
        # UI resources
        ('src/ui/resources/characters/*', 'src/ui/resources/characters'),
        # App icon
        ('icon/agent-dev.ico', 'icon'),
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
        # Rich (all submodules auto)
    ] + rich_imports + [
        # LangChain (all submodules auto)
    ] + langchain_imports + [
        # Pydantic (all submodules auto)
    ] + pydantic_imports + [
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
        # langchain_anthropic
        'langchain_openai',
        'langchain_community',
        'langchain_anthropic',
        'langchain_text_splitters',
        # CLI
        'typer',
        # rich (full, auto-discovered already)
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
        'unstructured',
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
