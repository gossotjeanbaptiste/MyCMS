#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Démarrage - Instance déjà lancée, port libre, erreurs visibles sans console
"""

import json
import os
import socket
import urllib.request


def show_error(message, logger):
    """Erreur visible même sans console (exécutable) : boîte de message Windows"""
    logger.log(f"Erreur: {message}")
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, "MyCMS", 0x10)  # MB_ICONERROR
        except Exception:
            pass


def running_instance(url):
    """MyCMS répond-il déjà à cette adresse ?"""
    try:
        with urllib.request.urlopen(f"{url}/api/auth/state", timeout=2) as response:
            return "setup_needed" in json.loads(response.read().decode("utf-8"))
    except Exception:
        return False


def port_free(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
            return True
        except OSError:
            return False
