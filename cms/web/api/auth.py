#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentification - Connexion exigée avant chaque requête, création du premier compte au premier lancement
"""

from flask import Blueprint, jsonify, redirect, render_template, request, session

from api.services import error, services

bp = Blueprint("auth", __name__)

# Accessibles sans être connecté : la page de connexion et ce dont elle a besoin
PUBLIC_PATHS = {
    "/login", "/static/scripts/login.js", "/static/style.css",
    "/api/auth/state", "/api/auth/login", "/api/auth/setup",
}


def current_user():
    """Identifiant du compte connecté, ou None (session fermée, compte supprimé, mot de passe changé)"""
    s = services()
    username = session.get("user")
    if (username and session.get("boot") == s.boot_id
            and session.get("auth") == s.auth.session_id(username)):
        return username
    return None


def logged_in():
    return current_user() is not None


def open_session(username):
    s = services()
    session.clear()
    session["user"] = username
    session["auth"] = s.auth.session_id(username)
    session["boot"] = s.boot_id


@bp.before_app_request
def require_login():
    if request.path in PUBLIC_PATHS or logged_in():
        return None
    if request.path.startswith("/api/"):
        return error("Session expirée : reconnectez-vous", 401)
    return redirect("/login")


@bp.get("/login")
def login_page():
    if logged_in():
        return redirect("/")
    return render_template("login.html")


@bp.get("/api/auth/state")
def auth_state():
    username = current_user()
    auth = services().auth
    return jsonify({
        "setup_needed": not auth.has_credentials(),
        "logged_in": username is not None,
        "username": username,
        "admin": auth.is_admin(username),
    })


@bp.post("/api/auth/setup")
def auth_setup():
    """Premier lancement : créer le premier compte, administrateur"""
    s = services()
    data = request.get_json(force=True)
    password = str(data.get("password") or "")
    if password != str(data.get("confirm") or ""):
        return error("Les deux mots de passe ne correspondent pas")
    message = s.auth.create(str(data.get("username") or ""), password)
    if message:
        return error(message)
    username = s.auth.find(data.get("username"))
    s.logger.log(f"Compte administrateur créé pour {username}")
    open_session(username)
    return jsonify({"success": True})


@bp.post("/api/auth/login")
def auth_login():
    s = services()
    data = request.get_json(force=True)
    username, message = s.auth.verify(str(data.get("username") or ""), str(data.get("password") or ""))
    if message:
        s.logger.log(f"Échec de connexion: {message}")
        return error(message, 401)
    s.logger.log(f"Connexion de {username}")
    open_session(username)
    return jsonify({"success": True})


@bp.post("/api/auth/logout")
def auth_logout():
    username = current_user()
    if username:
        services().logger.log(f"Déconnexion de {username}")
    session.clear()
    return jsonify({"success": True})


@bp.get("/api/auth/profile")
def get_profile():
    """Nom et e-mail du compte connecté : auteur de ses commits"""
    s = services()
    username = current_user()
    name, email = s.auth.author(username)
    return jsonify({**s.auth.profile(username), "author": f"{name} <{email}>"})


@bp.post("/api/auth/profile")
def save_profile():
    s = services()
    data = request.get_json(force=True)
    message = s.auth.set_profile(current_user(), data.get("name"), data.get("email"))
    if message:
        return error(message)
    return jsonify({"success": True, "message": "Profil enregistré"})


@bp.post("/api/auth/password")
def auth_password():
    """Changer son mot de passe : ses autres sessions ouvertes sont fermées"""
    s = services()
    data = request.get_json(force=True)
    new = str(data.get("new") or "")
    if new != str(data.get("confirm") or ""):
        return error("Les deux nouveaux mots de passe ne correspondent pas")
    username = current_user()
    message = s.auth.change_password(username, str(data.get("current") or ""), new)
    if message:
        return error(message)
    s.logger.log(f"Mot de passe modifié par {username}")
    open_session(username)
    return jsonify({"success": True, "message": "Mot de passe modifié"})
