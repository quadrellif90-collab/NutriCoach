# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec per NutriCoach (app desktop nutrizionista, locale)."""

import os

block_cipher = None

# cartella sorgenti (PyInstaller espone SPEC come path dello spec)
src = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['launcher.py'],
    pathex=[src],
    binaries=[],
    datas=[
        (os.path.join(src, 'templates', 'dashboard.html'), 'templates'),
        # Tesseract bundlato (se presente nella cartella sorgente) -> incluso nell'EXE
    ] + ([(os.path.join(src, 'tesseract'), 'tesseract')] if os.path.isdir(os.path.join(src, 'tesseract')) else []),
    hiddenimports=[
        'db', 'diet_parser', 'bia_parser', 'nutrition_engine', 'anthropometry',
        'charts', 'pdf_export', 'auth', 'notifications', 'nutrition_db',
        'meal_planner', 'ocr', 'diet_presets', 'sport_science',
        'fastapi', 'uvicorn', 'reportlab', 'fitz', 'pydantic', 'pytesseract',
        # finestra nativa pywebview (come PCC)
        'webview', 'webview.platforms', 'webview.platforms.edgechromium',
        'webview.platforms.cocoa', 'webview.platforms.gtk',
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
