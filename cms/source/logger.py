#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger - Système de journalisation centralisé
"""

from pathlib import Path
from datetime import datetime
from collections import deque

from data_dir import data_dir


class Logger:
    """Système de logs simple et efficace"""

    def __init__(self, max_logs=500):
        self.logs = deque(maxlen=max_logs)
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

    def log_error(self, message):
        """Ajouter un log d'erreur"""
        self.log(message, "ERROR")

    def log_warning(self, message):
        """Ajouter un log d'avertissement"""
        self.log(message, "WARNING")

    def log_success(self, message):
        """Ajouter un log de succès"""
        self.log(message, "SUCCESS")

    def get_logs(self):
        """Récupérer tous les logs"""
        return list(self.logs)

    def get_recent_logs(self, count=50):
        """Récupérer les logs récents"""
        return list(self.logs)[-count:]

    def clear_logs(self):
        """Effacer les logs en mémoire"""
        self.logs.clear()

    def export_logs(self, file_path):
        """Exporter les logs vers un fichier"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for log in self.logs:
                    f.write(log + "\n")
            return True
        except Exception as e:
            print(f"Erreur lors de l'export: {e}")
            return False
