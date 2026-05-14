# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\nosom\\Desktop\\Neuromood V3\\installers\\installer_pro.py'],
    pathex=['C:\\Users\\nosom\\Desktop\\Neuromood V3'],
    binaries=[],
    datas=[('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\installer_icon.ico', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\NM_icon.ico', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\no_symbol.ico', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\LOGO.png', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\.env', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\dist\\HubProfesional', 'HubProfesional'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\dist\\Desinstalar NeuroMood Pro', 'Desinstalar NeuroMood Pro')],
    hiddenimports=['shared', 'PIL', 'win32com', 'win32com.client', 'pywintypes'],
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
    name='Instalar NeuroMood Hub Profesional',
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
    icon=['C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\installer_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Instalar NeuroMood Hub Profesional',
)
