# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\nosom\\Desktop\\Neuromood V3\\hub\\main_qt.py'],
    pathex=['C:\\Users\\nosom\\Desktop\\Neuromood V3'],
    binaries=[],
    datas=[('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\LOGO.png', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\NM_icon.ico', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\shared', 'shared'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\hub', 'hub')],
    hiddenimports=['PyQt6', 'pyqtgraph', 'shared', 'supabase', 'sqlite3', 'PIL', 'pystray', 'pystray._win32', 'winotify', 'groq', 'google.generativeai', 'openai', 'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes', 'reportlab.lib.styles', 'reportlab.lib.units', 'reportlab.platypus', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HubProfesional',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\NM_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HubProfesional',
)
