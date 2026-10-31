# -*- coding: utf-8 -*-
"""
API et pages de MyCMS : create_app() construit l'application Flask, ses services et ses routes
"""

from flask import Flask

from api import auth, branches, editor, media, pages, publish, repository, settings, shutdown, site, structure, users
from api.services import Services


def create_app(resources, git_found):
    """Application Flask de MyCMS.
    resources : dossiers static_dir et templates_dir, icon_file (voir server.Resources)"""
    app = Flask(__name__, static_folder=None, template_folder=str(resources.templates_dir))
    services = Services(resources, git_found)
    app.extensions["mycms"] = services

    app.secret_key = services.auth.secret_key()
    # Cookie de session : supprimé à la fermeture du navigateur, illisible par les scripts, jamais envoyé depuis un autre site
    app.config.update(
        SESSION_COOKIE_NAME="mycms_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
    )
    for module in (auth, users, pages, settings, repository, branches, publish, editor, structure, media, site,
                   shutdown):
        app.register_blueprint(module.bp)
    return app
