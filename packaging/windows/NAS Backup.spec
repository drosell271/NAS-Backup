# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules


block_cipher = None
spec_dir = Path(SPECPATH).resolve()
project_dir = spec_dir.parents[1]
hidden_imports = collect_submodules("watchdog")


a = Analysis(
    [str(project_dir / "main.py")],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (str(project_dir / "app/ui/main_window.ui"), "app/ui"),
        (str(project_dir / "app/ui/task_dialog.ui"), "app/ui"),
        (str(project_dir / "app/ui/settings_dialog.ui"), "app/ui"),
        (str(project_dir / "app/assets/icon.ico"), "app/assets"),
        (str(project_dir / "app/assets/logo.png"), "app/assets"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NAS Backup",
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
    icon=str(project_dir / "app/assets/icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="NAS Backup",
)
