#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Serveur HTTP - Serveur local pour prévisualisation
"""

import http.server
from datetime import datetime
from functools import partial
from pathlib import Path
from urllib.parse import unquote


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP personnalisé"""

    def __init__(self, *args, directory=None, on_log=None, **kwargs):
        self.on_log = on_log
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
        message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}"
        if self.on_log:
            self.on_log(message)
        else:
            print(message)

    def end_headers(self):
        """Ajouter les headers personnalisés"""
        self.send_header(
            'Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()


class PreviewHTTPServer(http.server.ThreadingHTTPServer):
    """Une connexion par thread : une connexion ouverte sans requête (préconnexion
    des navigateurs) ne bloque plus les autres"""
    daemon_threads = True
    allow_reuse_address = True


class ServerManager:
    """Gère le serveur HTTP local"""

    def __init__(self, logger):
        self.logger = logger
        self.server = None
        self.running = False

    def start(self, repo_path, port=8000, callback=None):
        """Démarrer le serveur HTTP (bloquant jusqu'à stop())"""
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

            handler = partial(CustomHTTPRequestHandler, directory=str(repo_path), on_log=callback)
            self.server = PreviewHTTPServer(("127.0.0.1", port), handler)
            self.running = True

            message = f"✓ Serveur démarré sur http://127.0.0.1:{port}"
            if callback:
                callback(message)
            self.logger.log(message)
            self.server.serve_forever(poll_interval=0.5)
        except OSError as e:
            if e.errno in (98, 10048) or "Address already in use" in str(e):
                message = f"❌ Le port {port} est déjà utilisé. Essayez un autre port."
            else:
                message = f"❌ Erreur OS: {str(e)}"
            if callback:
                callback(message)
            self.logger.log(message)
        except Exception as e:
            message = f"❌ Erreur serveur: {str(e)}"
            if callback:
                callback(message)
            self.logger.log(message)
        finally:
            self.running = False
            if self.server:
                try:
                    self.server.server_close()
                except Exception:
                    pass
                self.server = None

    def stop(self):
        """Arrêter le serveur HTTP"""
        try:
            server = self.server
            if server:
                # shutdown() attend la fin de serve_forever(), lancé dans un autre thread
                server.shutdown()
            self.running = False
            self.logger.log("Serveur arrêté")
            return True
        except Exception as e:
            error_msg = f"Erreur lors de l'arrêt: {str(e)}"
            self.logger.log(error_msg)
            return False

    def is_running(self):
        """Vérifier si le serveur est actif"""
        return self.running
