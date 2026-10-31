#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mise à jour - Lance l'installeur (.msi) d'une nouvelle version, détaché de MyCMS, qui se ferme juste après
pour que l'installeur puisse remplacer MyCMS.exe
"""

import subprocess

# Le processus de l'installeur ne dépend pas de MyCMS : il continue après sa fermeture
DETACHED = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


def installer_command(msi_path):
    """Mode passif : une barre de progression, sans questions (Windows demande seulement l'autorisation
    d'administrateur). LAUNCHAPP=1 relance MyCMS à la fin (Package.wxs)"""
    return ["msiexec", "/i", str(msi_path), "/passive", "LAUNCHAPP=1"]


def launch_installer(msi_path):
    return subprocess.Popen(installer_command(msi_path), creationflags=DETACHED, close_fds=True)
