#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur web de MyCMS - Point d'entrée : prépare l'environnement, puis lance l'interface
(les routes sont dans api/, le code métier dans cms/source)
"""

import argparse
import os
import shutil
import sys
import threading
import webbrowser
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
        sys.path.insert(0, str(web_dir.parent / "source"))

    # Sans Git, GitPython refuse de s'importer : l'application démarre quand même et l'indique dans les logs
    os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")
    return resources, shutil.which("git") is not None


def main(host="127.0.0.1", port=5050, open_browser=True, tray=True):
    """Point d'entrée principal"""
    resources, git_found = prepare_environment()
    # Après prepare_environment : les modules de cms/source sont alors importables
    from api import create_app
    from desktop import startup
    from desktop.tray import start_tray

    app = create_app(resources, git_found)
    services = app.extensions["mycms"]
    logger = services.logger
    url = f"http://{host}:{port}"

    # Double-clic alors que MyCMS tourne déjà : ouvrir l'interface de l'instance en cours
    if startup.running_instance(url):
        logger.log("MyCMS est déjà lancé : ouverture de l'interface")
        if open_browser:
            webbrowser.open(url)
        return
    if not startup.port_free(host, port):
        startup.show_error(f"Impossible de démarrer MyCMS : le port {port} est déjà utilisé par un autre programme.\n\n"
                           "Fermez ce programme puis relancez MyCMS, ou lancez MyCMS avec un autre port (option --port).",
                           logger)
        sys.exit(1)

    if services.config.get_auto_pull():
        logger.log("Pull automatique au démarrage...")
        threading.Thread(target=services.git.pull, args=(str(services.repo_path()),), daemon=True).start()

    if not git_found:
        logger.log("Attention: Git est introuvable, pull et push impossibles. "
                   "Installez MyCMS avec le .msi (Git inclus) ou Git depuis https://git-scm.com")

    logger.log(f"MyCMS disponible sur {url}")
    if tray:
        services.tray = start_tray(url, resources.icon_file, logger)
    if services.tray is not None:
        logger.log("Icône MyCMS dans la zone de notification : Ouvrir MyCMS / Quitter MyCMS")
    else:
        logger.log("Fermez cette fenêtre pour quitter MyCMS")
    if open_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    try:
        app.run(host=host, port=port, threaded=True)
    except Exception as e:
        startup.show_error(f"MyCMS s'est arrêté à cause d'une erreur :\n\n{e}", logger)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MyCMS - interface web")
    parser.add_argument("--port", type=int, default=5050, help="port de l'interface (défaut : 5050)")
    parser.add_argument("--no-browser", action="store_true", help="ne pas ouvrir le navigateur au démarrage")
    parser.add_argument("--no-tray", action="store_true", help="pas d'icône dans la zone de notification")
    args = parser.parse_args()
    main(port=args.port, open_browser=not args.no_browser, tray=not args.no_tray)
