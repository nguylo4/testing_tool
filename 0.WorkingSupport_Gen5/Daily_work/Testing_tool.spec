# -*- mode: python ; coding: utf-8 -*-

# Phân tích main script
a = Analysis(
    ['Main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon\\App.ico', 'icon'),
        ('template\\template.can', 'template'),
        ('template\\DXL_template_testrun_gen.can', 'template')
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
    icon=['icon\\App.ico'],
)

# Phân tích updater script riêng
a2 = Analysis(
    ['updater\\updater.py'],
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
    icon=[],
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
