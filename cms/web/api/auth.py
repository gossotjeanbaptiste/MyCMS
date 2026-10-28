#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentification - Connexion exigée avant chaque requête, création des identifiants au premier lancement
"""

from flask import Blueprint, jsonify, redirect, render_template, request, session

from api.services import error, services

bp = Blueprint("auth", __name__)

# Accessibles sans être connecté : la page de connexion et ce dont elle a besoin
PUBLIC_PATHS = {
    "/login", "/static/scripts/login.js", "/static/style.css",
    "/api/auth/state", "/api/auth/login", "/api/auth/setup",
}


def logged_in():
    s = services()
    return (s.auth.has_credentials()
            and session.get("auth") == s.auth.session_id()
            and session.get("boot") == s.boot_id)


def open_session():
    s = services()
    session.clear()
    session["auth"] = s.auth.session_id()
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
    is_logged_in = logged_in()
    auth = services().auth
    return jsonify({
        "setup_needed": not auth.has_credentials(),
        "logged_in": is_logged_in,
        "username": auth.username() if is_logged_in else None,
    })


@bp.post("/api/auth/setup")
def auth_setup():
    """Premier lancement : créer les identifiants"""
    s = services()
    data = request.get_json(force=True)
    password = str(data.get("password") or "")
    if password != str(data.get("confirm") or ""):
        return error("Les deux mots de passe ne correspondent pas")
    message = s.auth.create(str(data.get("username") or ""), password)
    if message:
        return error(message)
    s.logger.log(f"Identifiants créés pour {s.auth.username()}")
    open_session()
    return jsonify({"success": True})


@bp.post("/api/auth/login")
def auth_login():
    s = services()
    data = request.get_json(force=True)
    message = s.auth.verify(str(data.get("username") or ""), str(data.get("password") or ""))
    if message:
        s.logger.log(f"Échec de connexion: {message}")
        return error(message, 401)
    s.logger.log(f"Connexion de {s.auth.username()}")
    open_session()
    return jsonify({"success": True})


@bp.post("/api/auth/logout")
def auth_logout():
    session.clear()
    return jsonify({"success": True})


@bp.post("/api/auth/password")
def auth_password():
    """Changer le mot de passe : les autres sessions ouvertes sont fermées"""
    s = services()
    data = request.get_json(force=True)
    new = str(data.get("new") or "")
    if new != str(data.get("confirm") or ""):
        return error("Les deux nouveaux mots de passe ne correspondent pas")
    message = s.auth.change_password(str(data.get("current") or ""), new)
    if message:
        return error(message)
    s.logger.log("Mot de passe modifié")
    open_session()
    return jsonify({"success": True, "message": "Mot de passe modifié"})
