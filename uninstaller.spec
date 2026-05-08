# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['uninstaller.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('no_symbol.ico', '.'),
        ('LOGO.png',      '.'),
    ],
    hiddenimports=['PIL', 'PIL._tkinter_finder', 'win32com', 'win32com.client', 'win32com.shell', 'pywintypes'],
    hookspath=[],
    hooksconfig={},
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Desinstalar NeuroMood',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='no_symbol.ico',
    uac_admin=False,
)
