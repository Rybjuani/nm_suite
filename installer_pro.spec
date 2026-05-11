# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['installer_pro.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('installer_icon.ico',                    '.'),
        ('NM_icon.ico',                           '.'),
        ('no_symbol.ico',                         '.'),
        ('LOGO.png',                              '.'),
        ('dist/pro/HubProfesional.exe',           'pro'),
        ('dist/pro/Desinstalar NeuroMood Pro.exe','pro'),
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
    name='Instalar NeuroMood Hub Profesional',
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
    icon='installer_icon.ico',
    uac_admin=False,
)
