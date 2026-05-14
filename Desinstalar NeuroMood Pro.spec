# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\NM_icon.ico', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\LOGO.png', '.')]
binaries = []
hiddenimports = ['PIL', 'win32com', 'win32com.client', 'pywintypes']
tmp_ret = collect_all('shared')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\nosom\\Desktop\\Neuromood V3\\installers\\uninstaller_pro.py'],
    pathex=['C:\\Users\\nosom\\Desktop\\Neuromood V3'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='Desinstalar NeuroMood Pro',
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
    name='Desinstalar NeuroMood Pro',
)
