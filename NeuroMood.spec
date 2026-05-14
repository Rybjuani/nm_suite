# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\nosom\\Desktop\\Neuromood V3\\app\\main_qt.py'],
    pathex=['C:\\Users\\nosom\\Desktop\\Neuromood V3'],
    binaries=[],
    datas=[('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\LOGO.png', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\assets\\NM_icon.ico', '.'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\shared', 'shared'), ('C:\\Users\\nosom\\Desktop\\Neuromood V3\\app', 'app')],
    hiddenimports=['PyQt6', 'shared', 'supabase', 'sqlite3', 'PIL', 'pystray', 'pystray._win32', 'winotify', 'app.home_qt', 'app.modules.animo_qt', 'app.modules.respiracion_qt', 'app.modules.registro_tcc_qt', 'app.modules.rutina_qt', 'app.modules.actividades_qt', 'app.modules.timer_qt', 'app.modules.avisos_qt', 'app.motor_activacion', 'app.avisos_daemon'],
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
    name='NeuroMood',
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
    name='NeuroMood',
)
