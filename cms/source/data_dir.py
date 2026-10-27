#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dossier de données de MyCMS (~/.mycms) : configuration, identifiants et journal.
Créé caché ; repris de l'ancien dossier ~/.rout_art_cms s'il existe.
"""

import os
import shutil
import subprocess
from pathlib import Path

DATA_DIR_NAME = ".mycms"
LEGACY_DIR_NAME = ".rout_art_cms"

FILE_ATTRIBUTE_HIDDEN = 0x2
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
# « Tout le monde » : le SID ne dépend pas de la langue de Windows (contrairement à « Everyone »)
EVERYONE_SID = "*S-1-1-0"


def data_dir():
    """Dossier de données, créé si besoin, et caché"""
    path = Path.home() / DATA_DIR_NAME
    legacy = Path.home() / LEGACY_DIR_NAME
    if not path.exists() and legacy.is_dir():
        # Ancien nom : on garde la configuration et les identifiants existants
        try:
            legacy.rename(path)
        except OSError:
            shutil.copytree(legacy, path)
    path.mkdir(parents=True, exist_ok=True)
    hide(path)
    return path


def hide(path):
    """Attribut « caché » de Windows (le point au début du nom ne cache rien sous Windows)"""
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        attributes = kernel32.GetFileAttributesW(str(path))
        if attributes != INVALID_FILE_ATTRIBUTES and not attributes & FILE_ATTRIBUTE_HIDDEN:
            kernel32.SetFileAttributesW(str(path), attributes | FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        pass


def _icacls(*args):
    # Sortie ignorée (encodage OEM de la console, illisible en UTF-8) : seul le code de retour compte.
    # Pas de fenêtre de console qui clignote dans l'exécutable sans terminal.
    return subprocess.run(["icacls", *args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).returncode == 0


def lock_file(path):
    """Interdire de modifier le contenu du fichier (lecture et suppression restent possibles).
    Sous Windows : règle NTFS qui refuse l'écriture ; ailleurs : lecture seule (chmod 400).
    Ce n'est pas une protection contre le propriétaire du fichier, qui peut retirer la règle :
    cela évite surtout une modification à la main, par erreur."""
    path = Path(path)
    if not path.exists():
        return False
    if os.name == "nt":
        _icacls(str(path), "/remove:d", EVERYONE_SID)  # Pas de règle en double
        return _icacls(str(path), "/deny", f"{EVERYONE_SID}:(WD,AD)")
    try:
        path.chmod(0o400)
        return True
    except OSError:
        return False


def unlock_file(path):
    """Lever le verrou le temps que MyCMS écrive le fichier"""
    path = Path(path)
    if not path.exists():
        return
    if os.name == "nt":
        _icacls(str(path), "/remove:d", EVERYONE_SID)
    else:
        try:
            path.chmod(0o600)
        except OSError:
            pass
