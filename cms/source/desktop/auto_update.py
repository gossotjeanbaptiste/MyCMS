#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mise à jour automatique au démarrage (réglage « auto_update », actif par défaut) : si une nouvelle version
est publiée, son .msi est téléchargé et l'installeur lancé à la place de MyCMS, qu'il relance à la fin.
Une seule tentative par version : si l'installation est refusée ou échoue, MyCMS démarre normalement au
lancement suivant, et le bouton « Nouvelle version » reste disponible.
"""

import tempfile
from pathlib import Path

from core import updates
from desktop import installer


def install_at_startup(services, current, frozen):
    """True si l'installeur est lancé : MyCMS doit alors s'arrêter sans démarrer son serveur"""
    config, logger = services.config, services.logger
    if not frozen or not config.get_auto_update():
        return False
    services.update = updates.update_info(current, updates.fetch_latest())  # Réutilisé par /api/update
    version, msi = services.update["latest"], services.update["installer"]
    if not msi:
        return False
    if config.get_update_tried() == version:
        logger.log(f"Mise à jour automatique vers {version} déjà tentée : MyCMS démarre normalement")
        return False
    logger.log(f"Nouvelle version {version} : téléchargement de l'installeur...")
    try:
        path = updates.download(msi, Path(tempfile.gettempdir()) / "MyCMS-update")
        config.set_update_tried(version)
        installer.launch_installer(path)
    except (OSError, ValueError) as e:
        logger.log(f"Mise à jour automatique impossible : {e}")
        return False
    logger.log(f"Installation de MyCMS {version} : MyCMS se relancera à la fin")
    return True
