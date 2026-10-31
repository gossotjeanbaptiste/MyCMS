# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de spécification PyInstaller pour MyCMS (version web)
Compile le serveur Flask + l'interface web en un exécutable Windows
"""

import os

block_cipher = None

a = Analysis(
    ['../web/server.py'],
    # Les paquets de cms/source (core, content, publishing, desktop) et cms/web (api) sont importés
    # par nom depuis server.py (pathex est relatif au dossier courant, d'où SPECPATH = dossier de ce fichier)
    pathex=[os.path.join(SPECPATH, '..', 'source'), os.path.join(SPECPATH, '..', 'web')],
    binaries=[],
    # Interface web (modèles HTML, JS, CSS Tailwind compilé) et icône
    datas=[('../web/static', 'static'), ('../web/templates', 'templates'), ('../icon', 'icon')],
    hiddenimports=[
        'api', 'api.auth', 'api.editor', 'api.pages', 'api.repository', 'api.services',
        'api.media', 'api.publish', 'api.settings', 'api.shutdown', 'api.site', 'api.structure', 'api.users',
        'core.auth_file', 'core.auth_manager', 'core.config_manager', 'core.data_dir', 'core.logger',
        'content.categories', 'content.css_weights', 'content.html_manager', 'content.html_tree', 'content.hybrid_saver',
        'content.node_diff', 'content.page_finder', 'content.published', 'content.structure',
        'publishing.checks', 'publishing.git_manager', 'publishing.git_status', 'publishing.git_sync', 'publishing.history', 'publishing.online', 'publishing.robots', 'publishing.site_url',
        'publishing.sitemap_files', 'publishing.sitemap_generator',
        'desktop.folder_picker', 'desktop.server_manager', 'desktop.startup', 'desktop.tray',
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
