#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Icône de la zone de notification - Montre que MyCMS tourne, permet de l'ouvrir ou de le quitter
"""

import threading
import webbrowser


def start_tray(url, icon_file, logger):
    """Afficher l'icône (thread à part). Retourne l'icône, ou None si pystray n'est pas installé"""
    try:
        import pystray
        from PIL import Image
    except ImportError:
        logger.log("Icône de notification indisponible : pystray ou Pillow n'est pas installé "
                   "(python -m pip install -r cms/requirements.txt)")
        return None
    menu = pystray.Menu(
        pystray.MenuItem("Ouvrir MyCMS", lambda: webbrowser.open(url), default=True),
        # Même fenêtre que le bouton Quitter de l'interface : ce qui n'est pas publié est proposé avant de fermer
        pystray.MenuItem("Quitter MyCMS…", lambda: webbrowser.open(f"{url}/#quit")),
    )
    icon = pystray.Icon("MyCMS", Image.open(icon_file), "MyCMS", menu)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon


def stop_tray(icon):
    """Retirer l'icône (sinon elle reste affichée jusqu'au survol de la souris)"""
    if icon is not None:
        try:
            icon.stop()
        except Exception:
            pass
