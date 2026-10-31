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
        'api', 'api.auth', 'api.branches', 'api.editor', 'api.pages', 'api.repository', 'api.services',
        'api.media', 'api.publish', 'api.settings', 'api.shutdown', 'api.site', 'api.structure', 'api.users',
        'version', 'core.updates',
        'core.auth.auth_file', 'core.auth.auth_manager', 'core.logs.log_buffer', 'core.logs.logger',
        'core.storage.config_manager', 'core.storage.data_dir',
        'content.html.html_manager', 'content.html.html_tree', 'content.html.hybrid_saver', 'content.html.node_diff',
        'content.pages.categories', 'content.pages.css_weights', 'content.pages.page_finder', 'content.pages.structure',
        'content.versions.changes', 'content.versions.published',
        'publishing.git.branches', 'publishing.git.commit_details', 'publishing.git.git_manager', 'publishing.git.git_status',
        'publishing.git.git_sync', 'publishing.git.history',
        'publishing.sitemap.robots', 'publishing.sitemap.site_url', 'publishing.sitemap.sitemap_files',
        'publishing.sitemap.sitemap_generator',
        'publishing.verification.checks', 'publishing.verification.online',
        'desktop.auto_update', 'desktop.folder_picker', 'desktop.installer', 'desktop.server_manager', 'desktop.startup', 'desktop.tray',
        'git',
        'bs4',
        'flask',
        'wsgi',
        'waitress',
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
