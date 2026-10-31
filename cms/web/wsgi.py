#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée WSGI de MyCMS : prépare l'environnement et fournit l'application Flask (app).

server.py la sert avec Waitress (serveur de production) et s'occupe du reste : instance unique,
icône de notification, navigateur. Un autre serveur WSGI peut aussi la servir, depuis cms/web :
    waitress-serve --listen=127.0.0.1:5050 wsgi:app
L'application n'est construite qu'au moment où app est demandée : importer ce module ne crée rien.
"""

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Resources:
    """Fichiers de l'interface : dans le dossier du projet, ou extraits de l'exécutable (sys._MEIPASS)"""
    static_dir: Path
    templates_dir: Path
    icon_file: Path


def prepare_environment():
    """Chemins des modules et de l'interface, Git portable du .msi. Retourne (Resources, Git trouvé)"""
    if getattr(sys, "frozen", False):
        # Exécutable PyInstaller : modules intégrés, interface extraite dans sys._MEIPASS
        base = Path(sys._MEIPASS)
        resources = Resources(base / "static", base / "templates", base / "icon" / "logo.ico")
        # Installé par le .msi : Git portable (MinGit) à côté de l'exécutable, si Git n'est pas sur le poste
        bundled_git = Path(sys.executable).parent / "git" / "cmd"
        if not shutil.which("git") and (bundled_git / "git.exe").exists():
            os.environ["PATH"] = str(bundled_git) + os.pathsep + os.environ.get("PATH", "")
    else:
        web_dir = Path(__file__).resolve().parent
        resources = Resources(web_dir / "static", web_dir / "templates", web_dir.parent / "icon" / "logo.ico")
        source_dir = str(web_dir.parent / "source")
        if source_dir not in sys.path:
            sys.path.insert(0, source_dir)

    # Sans Git, GitPython refuse de s'importer : l'application démarre quand même et l'indique dans les logs
    os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")
    return resources, shutil.which("git") is not None


def create_application():
    """Application Flask de MyCMS, prête à être servie par un serveur WSGI"""
    resources, git_found = prepare_environment()
    # Après prepare_environment : les modules de cms/source sont alors importables
    from api import create_app
    return create_app(resources, git_found)


def __getattr__(name):
    """wsgi.app : l'application, construite à la demande (convention des serveurs WSGI : module:app)"""
    if name == "app":
        return create_application()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
