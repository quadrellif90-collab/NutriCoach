# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec per NutriCoach v2 (Dietowin-style)."""
import os

block_cipher = None
src = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['launcher_v2.py'],
    pathex=[src],
    binaries=[],
    datas=[
        (os.path.join(src, 'app', 'templates', 'index.html'), 'app/templates'),
        (os.path.join(src, 'app', 'static', 'style.css'), 'app/static'),
    ] + ([(os.path.join(src, 'tesseract'), 'tesseract')] if os.path.isdir(os.path.join(src, 'tesseract')) else []),
    hiddenimports=[
        'app.database', 'app.main',
        'clinical_nutrition', 'meal_planner', 'nutrition_db', 'diet_parser',
        'bia_parser', 'ocr', 'diet_presets', 'anthropometry',
        'fastapi', 'uvicorn', 'reportlab', 'fitz', 'pydantic', 'pytesseract',
        'webview', 'webview.platforms', 'webview.platforms.edgechromium',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
              'numpy.testing', 'PIL.ImageQt', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NutriCoach',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='assets/icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)