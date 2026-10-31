#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger - Système de journalisation centralisé
"""

from datetime import datetime

from core.data_dir import data_dir
from core.log_buffer import LogBuffer


class Logger:
    """Système de logs simple et efficace"""

    def __init__(self, max_logs=500):
        self.logs = LogBuffer(max_logs)
        self.log_file = data_dir() / "app.log"

    def log(self, message, level="INFO"):
        """Ajouter un log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}] [{level}] {message}"
        self.logs.append(formatted_message)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(formatted_message + "\n")
        except Exception as e:
            print(f"Erreur lors de l'écriture du log: {e}")
        try:
            print(formatted_message)
        except UnicodeEncodeError:
            # Console non UTF-8 (ex: sortie redirigée sous Windows) : ne pas faire planter l'appelant
            print(formatted_message.encode('ascii', 'replace').decode('ascii'))

    def get_logs(self):
        """Récupérer tous les logs"""
        return list(self.logs)

    def logs_since(self, seen):
        """Lignes ajoutées depuis les seen premières (voir LogBuffer.since)"""
        return self.logs.since(seen)

    def clear_logs(self):
        """Effacer les logs en mémoire"""
        self.logs.clear()
