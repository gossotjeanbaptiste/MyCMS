# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de spécification PyInstaller pour Rout'Art CMS
Compile l'application Python en exécutable Windows
"""

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

a = Analysis(
    ['mycms.py'],
    pathex=['.'],
    binaries=[],
    datas=[('../icon', 'icon'), ('../../page', 'page'), ('../../style', 'style'), ('../../script', 'script'), ('.', '.')],
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'git',
        'bs4',
        'http.server',
        'socketserver',
        'git_manager',
        'html_manager',
        'server_manager',
        'config_manager',
        'logger',
        'sitemap_generator',
        'xml.dom',
        'xml.dom.minidom',
        'xml.etree.ElementTree',
    ] + collect_submodules('customtkinter'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MyCMS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console (application GUI)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../icon/logo.png',
)
