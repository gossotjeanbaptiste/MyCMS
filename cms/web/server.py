#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur web de MyCMS - Lanceur : instance unique, icône de notification, navigateur, puis l'application
(wsgi.py) servie par Waitress, un serveur WSGI de production. Les routes sont dans api/, le code métier
dans cms/source.
"""

import argparse
import sys
import threading
import webbrowser

from waitress import serve

import wsgi

# Requêtes servies en même temps : certaines attendent longtemps (fenêtre « Choisir un dossier »,
# clone, push, démarrage de l'aperçu) sans devoir bloquer le reste de l'interface
THREADS = 8


def main(host="127.0.0.1", port=5050, open_browser=True, tray=True):
    """Point d'entrée principal"""
    app = wsgi.create_application()
    # Après create_application : les modules de cms/source sont alors importables
    from desktop import startup
    from desktop.auto_update import install_at_startup
    from desktop.tray import start_tray
    from version import VERSION

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

    # Nouvelle version publiée : l'installeur la met en place puis relance MyCMS
    if install_at_startup(services, VERSION, getattr(sys, "frozen", False)):
        return

    if services.config.get_auto_pull():
        logger.log("Pull automatique au démarrage...")
        threading.Thread(target=services.git.pull, args=(str(services.repo_path()),), daemon=True).start()

    if not services.git_found:
        logger.log("Attention: Git est introuvable, pull et push impossibles. "
                   "Installez MyCMS avec le .msi (Git inclus) ou Git depuis https://git-scm.com")

    logger.log(f"MyCMS disponible sur {url}")
    if tray:
        services.tray = start_tray(url, services.resources.icon_file, logger)
    if services.tray is not None:
        logger.log("Icône MyCMS dans la zone de notification : Ouvrir MyCMS / Quitter MyCMS")
    else:
        logger.log("Fermez cette fenêtre pour quitter MyCMS")
    if open_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    try:
        serve(app, host=host, port=port, threads=THREADS, ident="MyCMS")
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
