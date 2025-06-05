# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ETH_Generater.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon\\App.ico', 'icon'),
        ('DBC\\DBC.csv', 'DBC'),
        ('readme.txt', '.'),  # Đặt readme.txt vào cùng thư mục với file exe
        ('template\\ETH_Packet_builder.can','template')
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ETH_Generater',
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
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ETH_Packet_Generater',
)

# Thêm dòng sau vào cuối file để tự động trả lời "yes" khi xóa output dir (PyInstaller >= 5.7)
import PyInstaller.config
PyInstaller.config.CONF['noconfirm'] = True
