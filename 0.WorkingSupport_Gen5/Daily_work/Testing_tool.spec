# -*- mode: python ; coding: utf-8 -*-

# Phân tích main script
a = Analysis(
    ['Release_working.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('App.ico', '.'),
        ('template\\template.can', 'template'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

main_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Testing_tool',
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
    icon=['App.ico'],
)

# Phân tích updater script riêng
a2 = Analysis(
    ['updater.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz2 = PYZ(a2.pure)

updater_exe = EXE(
    pyz2,
    a2.scripts,
    [],
    exclude_binaries=True,
    name='updater',
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
    icon=['App.ico'],
)

coll = COLLECT(
    main_exe,
    updater_exe,
    a.binaries + a2.binaries,
    a.datas + a2.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Testing_tool',
)
