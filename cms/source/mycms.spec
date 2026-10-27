# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de spécification PyInstaller pour MyCMS (version web)
Compile le serveur Flask + l'interface web en un exécutable Windows
"""

import os

block_cipher = None

a = Analysis(
    ['../web/server.py'],
    # Les modules de cms/source sont importés par nom depuis server.py
    # (pathex est relatif au dossier courant, d'où SPECPATH = dossier de ce fichier)
    pathex=[SPECPATH, os.path.join(SPECPATH, '..', 'web')],
    binaries=[],
    # Interface web (HTML, JS, CSS Tailwind compilé) et icône
    datas=[('../web/static', 'static'), ('../icon', 'icon')],
    hiddenimports=[
        'auth_manager',
        'config_manager',
        'css_weights',
        'data_dir',
        'folder_picker',
        'git_manager',
        'html_manager',
        'html_source',
        'logger',
        'page_finder',
        'server_manager',
        'sitemap_generator',
        'git',
        'bs4',
        'flask',
        'pystray',
        'pystray._win32',
        'PIL.Image',
        'xml.dom.minidom',
        'xml.etree.ElementTree',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Modules inutiles à MyCMS, embarqués sinon parce qu'ils sont installés sur le poste de compilation
    # (Pillow importe numpy s'il est présent ; seule l'icône de notification utilise Pillow)
    excludes=[
        'tkinter', 'customtkinter',
        'numpy', 'psutil', 'yaml', 'setuptools', 'pkg_resources',
        'unittest', 'pydoc', 'pydoc_data', '_pyrepl', 'doctest', 'lib2to3',
        'PIL._avif', 'PIL._webp', 'PIL._imagingcms', 'PIL._imagingtk', 'PIL._imagingmath',
        'PIL.ImageQt', 'PIL.ImageTk', 'PIL.ImageCms', 'PIL.ImageMath',
        'PIL.AvifImagePlugin', 'PIL.WebPImagePlugin',
    ],
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
    # Pas de terminal : MyCMS se quitte par son bouton Quitter ou l'icône de la zone de notification,
    # et les erreurs de démarrage s'affichent dans une boîte de message Windows
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../icon/logo.ico',
)
