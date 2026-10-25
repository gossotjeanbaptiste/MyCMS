#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanceur Simple - Démarre l'interface web de MyCMS
"""

import subprocess
import sys
import os

# Aller dans le dossier du projet
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Lancer l'app
try:
    subprocess.run([sys.executable, 'cms/web/server.py'])
except Exception as e:
    print(f"Erreur: {e}")
    sys.exit(1)
