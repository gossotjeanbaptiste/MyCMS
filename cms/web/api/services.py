#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Services partagés par les routes : gestionnaires de cms/source et état de l'application.
Une seule instance, créée par create_app() et rangée dans app.extensions["mycms"].
"""

import hashlib
import secrets
from collections import deque
from pathlib import Path

from flask import current_app, jsonify

from content.html_manager import HTMLManager
from content.page_finder import find_html_pages
from core.auth_manager import AuthManager
from core.config_manager import ConfigManager
from core.logger import Logger
from desktop.folder_picker import FolderPicker
from desktop.server_manager import ServerManager
from publishing.git_manager import GitManager
from publishing.sitemap_generator import SitemapGenerator


class Services:
    """Gestionnaires et état de MyCMS pour la durée du processus"""

    def __init__(self, resources, git_found):
        self.resources = resources  # Dossiers static et templates, icône
        self.git_found = git_found
        self.config = ConfigManager()
        self.auth = AuthManager(self.config.config_dir)
        self.logger = Logger()
        self.git = GitManager(self.logger)
        self.html = HTMLManager(self.logger)
        self.preview = ServerManager(self.logger)
        self.sitemap = SitemapGenerator(self.logger)
        self.folder_picker = FolderPicker()
        # Tiré au hasard à chaque démarrage et jamais enregistré : après un relancement de MyCMS,
        # les sessions ouvertes avant ne sont plus valides et il faut se reconnecter
        self.boot_id = secrets.token_hex(16)
        self.preview_port = None
        self.preview_logs = deque(maxlen=200)
        self.tray = None  # Icône de la zone de notification (pystray), posée par server.main

    # ======= Repository et pages =======

    def repo_path(self):
        return Path(self.config.get_repo_path())

    def has_repository(self):
        return (self.repo_path() / ".git").exists()

    def page_files(self):
        """Toutes les pages HTML du repository (chemins relatifs)"""
        if not self.repo_path().is_dir():
            return []
        return find_html_pages(self.repo_path())

    def resolve_page(self, name):
        """Chemin d'une page de la liste, ou None si elle n'en fait pas partie"""
        if name not in self.page_files():
            return None
        return self.repo_path() / name

    def update_sitemap(self):
        """Régénérer le sitemap et décrire ce qui a été fait"""
        result = self.sitemap.update_sitemap(str(self.repo_path()), self.config.get_site_url())
        if not result["success"]:
            self.logger.log(f"Attention: {result['error']}")
            return result

        if result["created"]:
            summary = "Sitemap créé à la racine"
        elif result["moved_from"]:
            summary = f"Sitemap déplacé à la racine (depuis {result['moved_from']})"
        else:
            summary = "Sitemap mis à jour"
        result["message"] = f"{summary} : {len(result['included'])} pages"
        if result["excluded"]:
            result["message"] += f", {len(result['excluded'])} exclues ({', '.join(result['excluded'])})"
        self.logger.log(result["message"])
        return result

    # ======= Prévisualisation =======

    def preview_status(self):
        return {
            "running": self.preview.is_running(),
            "port": self.preview_port,
            "logs": list(self.preview_logs),
        }


def services():
    """Services de l'application en cours (dans une route)"""
    return current_app.extensions["mycms"]


def error(message, status=400):
    return jsonify({"success": False, "error": message}), status


def read_page(file_path):
    """Contenu exact du fichier (sans conversion des fins de ligne)"""
    with open(file_path, encoding="utf-8", newline="") as f:
        return f.read()


def content_hash(content):
    return hashlib.sha1(content.encode("utf-8")).hexdigest()
