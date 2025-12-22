#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Serveur HTTP - Serveur local pour prévisualisation
"""

import http.server
import socketserver
import os
import threading
import webbrowser
from pathlib import Path
from urllib.parse import unquote


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP personnalisé"""

    def __init__(self, *args, directory=None, **kwargs):
        self.base_directory = directory
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        """Traiter les requêtes GET"""
        path = unquote(self.path)
        if path == '/' or path == '':
            path = '/index.html'
        self.path = path
        return super().do_GET()

    def log_message(self, format, *args):
        """Logger les messages du serveur"""
        message = format % args
        timestamp = self._get_timestamp()
        print(f"[{timestamp}] {self.client_address[0]} - {message}")

    def _get_timestamp(self):
        """Obtenir le timestamp formaté"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def end_headers(self):
        """Ajouter les headers personnalisés"""
        self.send_header(
            'Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()


class ServerManager:
    """Gère le serveur HTTP local"""

    def __init__(self, logger):
        self.logger = logger
        self.server = None
        self.thread = None
        self.running = False
        self.request_handler = None
        self._stop_requested = False

    def start(self, repo_path, port=8000, callback=None):
        """Démarrer le serveur HTTP"""
        try:
            # Valider et corriger le port
            if not isinstance(port, int) or port < 1 or port > 65535:
                message = f"⚠️  Port invalide: {port}. Utilisation du port par défaut: 8000"
                if callback:
                    callback(message)
                self.logger.log(message)
                port = 8000

            repo_path = Path(repo_path)
            if not repo_path.exists():
                message = f"❌ Le chemin n'existe pas: {repo_path}"
                if callback:
                    callback(message)
                self.logger.log(message)
                return False
            os.chdir(repo_path)

            def create_handler(*args, **kwargs):
                return CustomHTTPRequestHandler(
                    *args, directory=str(repo_path), **kwargs
                )
            socketserver.TCPServer.allow_reuse_address = True
            self.server = socketserver.TCPServer(
                ("localhost", port), create_handler)

            # Timeout court pour permettre l'arrêt
            self.server.timeout = 0.5
            self.running = True
            self._stop_requested = False

            message = f"✓ Serveur démarré sur http://localhost:{port}"
            if callback:
                callback(message)
            self.logger.log(message)
            while self.running and not self._stop_requested:
                try:
                    self.server.handle_request()
                except Exception as e:
                    if self.running and not self._stop_requested:
                        self.logger.log(f"Erreur serveur: {e}")
        except OSError as e:
            if "Address already in use" in str(e):
                message = f"❌ Le port {port} est déjà utilisé. Essayez un autre port."
            else:
                message = f"❌ Erreur OS: {str(e)}"
            if callback:
                callback(message)
            self.logger.log(message)
            self.running = False
        except Exception as e:
            message = f"❌ Erreur serveur: {str(e)}"
            if callback:
                callback(message)
            self.logger.log(message)
            self.running = False
        finally:
            self.running = False
            if self.server:
                try:
                    self.server.server_close()
                except:
                    pass

    def stop(self):
        """Arrêter le serveur HTTP"""
        try:
            self._stop_requested = True
            self.running = False
            if self.server:
                try:
                    self.server.server_close()
                except:
                    pass
            self.logger.log("Serveur arrêté")
            return True
        except Exception as e:
            error_msg = f"Erreur lors de l'arrêt: {str(e)}"
            self.logger.log(error_msg)
            return False

    def is_running(self):
        """Vérifier si le serveur est actif"""
        return self.running
