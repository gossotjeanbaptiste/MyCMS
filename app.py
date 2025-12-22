#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanceur Simple - Démarre l'application Rout'Art CMS
"""

import subprocess
import sys
import os

# Aller dans le dossier source
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Lancer l'app
try:
    # Ajouter le dossier source au PATH
    sys.path.insert(0, 'cms/source')

    # Lancer l'application
    subprocess.run([sys.executable, 'cms/source/mycms.py'])
except Exception as e:
    print(f"Erreur: {e}")
    sys.exit(1)
