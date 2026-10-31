#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilisateurs - Gestion des comptes, réservée aux administrateurs
"""

from flask import Blueprint, jsonify, request

from api.auth import current_user
from api.services import error, services

bp = Blueprint("users", __name__)


@bp.before_request
def require_admin():
    if not services().auth.is_admin(current_user()):
        return error("Réservé aux administrateurs", 403)
    return None


def users_response(message):
    return jsonify({"success": True, "message": message, "users": services().auth.list_users()})


@bp.get("/api/users")
def list_users():
    return jsonify({"users": services().auth.list_users(), "me": current_user()})


@bp.post("/api/users")
def add_user():
    s = services()
    data = request.get_json(force=True)
    password = str(data.get("password") or "")
    if password != str(data.get("confirm") or ""):
        return error("Les deux mots de passe ne correspondent pas")
    username = str(data.get("username") or "").strip()
    message = s.auth.add_user(username, password, admin=bool(data.get("admin")))
    if message:
        return error(message)
    role = "administrateur" if data.get("admin") else "éditeur"
    s.logger.log(f"Compte {role} « {username} » créé par {current_user()}")
    return users_response(f"Compte « {username} » créé")


@bp.post("/api/users/<username>/password")
def reset_password(username):
    """Nouveau mot de passe pour un compte : ses sessions ouvertes sont fermées"""
    s = services()
    if username == current_user():
        return error("Pour votre propre compte, utilisez « Changer le mot de passe »")
    data = request.get_json(force=True)
    message = s.auth.reset_password(username, str(data.get("password") or ""))
    if message:
        return error(message)
    s.logger.log(f"Mot de passe de « {username} » réinitialisé par {current_user()}")
    return users_response(f"Mot de passe de « {username} » réinitialisé")


@bp.post("/api/users/<username>/role")
def set_role(username):
    s = services()
    admin = bool(request.get_json(force=True).get("admin"))
    message = s.auth.set_admin(username, admin)
    if message:
        return error(message)
    role = "administrateur" if admin else "éditeur"
    s.logger.log(f"« {username} » devient {role} (par {current_user()})")
    return users_response(f"« {username} » est maintenant {role}")


@bp.delete("/api/users/<username>")
def delete_user(username):
    s = services()
    if username == current_user():
        return error("Vous ne pouvez pas supprimer votre propre compte")
    message = s.auth.delete_user(username)
    if message:
        return error(message)
    s.logger.log(f"Compte « {username} » supprimé par {current_user()}")
    return users_response(f"Compte « {username} » supprimé")
