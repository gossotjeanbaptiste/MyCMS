#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur web de MyCMS - API JSON + interface web
Réutilise les gestionnaires de cms/source (Git, HTML, config, logs, sitemap)
"""

import hashlib
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory, session

if getattr(sys, "frozen", False):
    # Exécutable PyInstaller : modules intégrés, interface extraite dans sys._MEIPASS
    STATIC_DIR = Path(sys._MEIPASS) / "static"
    # Installé par le .msi : Git portable (MinGit) à côté de l'exécutable, si Git n'est pas sur le poste
    bundled_git = Path(sys.executable).parent / "git" / "cmd"
    if not shutil.which("git") and (bundled_git / "git.exe").exists():
        os.environ["PATH"] = str(bundled_git) + os.pathsep + os.environ.get("PATH", "")
else:
    SOURCE_DIR = Path(__file__).resolve().parent.parent / "source"
    STATIC_DIR = Path(__file__).resolve().parent / "static"
    sys.path.insert(0, str(SOURCE_DIR))

# Sans Git, GitPython refuse de s'importer : l'application démarre quand même et l'indique dans les logs
GIT_FOUND = shutil.which("git") is not None
os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")

from auth_manager import AuthManager  # noqa: E402
from config_manager import ConfigManager  # noqa: E402
from css_weights import bold_info  # noqa: E402
from git_manager import GitManager  # noqa: E402
from html_manager import HTMLManager  # noqa: E402
from logger import Logger  # noqa: E402
from page_finder import find_html_pages  # noqa: E402
from server_manager import ServerManager  # noqa: E402
from sitemap_generator import SitemapGenerator  # noqa: E402

app = Flask(__name__, static_folder=None)

config_manager = ConfigManager()
auth_manager = AuthManager(config_manager.config_dir)
logger = Logger()

app.secret_key = auth_manager.secret_key()
# Cookie de session : supprimé à la fermeture du navigateur, illisible par les scripts, jamais envoyé depuis un autre site
app.config.update(
    SESSION_COOKIE_NAME="mycms_session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
)
git_manager = GitManager(logger)
html_manager = HTMLManager(logger)
server_manager = ServerManager(logger)
sitemap_generator = SitemapGenerator(logger)

preview_state = {"port": None, "thread": None}
preview_logs = deque(maxlen=200)


def _repo_path():
    return Path(config_manager.get_repo_path())


def _error(message, status=400):
    return jsonify({"success": False, "error": message}), status


def _get_page_files():
    """Toutes les pages HTML du repository (chemins relatifs)"""
    if not _repo_path().is_dir():
        return []
    return find_html_pages(_repo_path())


def _resolve_page(name):
    """Chemin d'une page de la liste, ou None si elle n'en fait pas partie"""
    if name not in _get_page_files():
        return None
    return _repo_path() / name


def _update_sitemap():
    """Régénérer le sitemap et décrire ce qui a été fait"""
    result = sitemap_generator.update_sitemap(str(_repo_path()), config_manager.get_site_url())
    if not result["success"]:
        logger.log(f"Attention: {result['error']}")
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
    logger.log(result["message"])
    return result


def _read_page(file_path):
    """Contenu exact du fichier (sans conversion des fins de ligne)"""
    with open(file_path, encoding="utf-8", newline="") as f:
        return f.read()


def _hash(content):
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


# ======= Authentification =======

# Accessibles sans être connecté : la page de connexion et ce dont elle a besoin
PUBLIC_PATHS = {
    "/login", "/static/login.js", "/static/style.css",
    "/api/auth/state", "/api/auth/login", "/api/auth/setup",
}


def _logged_in():
    return auth_manager.has_credentials() and session.get("auth") == auth_manager.session_id()


def _open_session():
    session.clear()
    session["auth"] = auth_manager.session_id()


@app.before_request
def require_login():
    if request.path in PUBLIC_PATHS or _logged_in():
        return None
    if request.path.startswith("/api/"):
        return _error("Session expirée : reconnectez-vous", 401)
    return redirect("/login")


@app.get("/login")
def login_page():
    if _logged_in():
        return redirect("/")
    return send_from_directory(STATIC_DIR, "login.html")


@app.get("/api/auth/state")
def auth_state():
    logged_in = _logged_in()
    return jsonify({
        "setup_needed": not auth_manager.has_credentials(),
        "logged_in": logged_in,
        "username": auth_manager.username() if logged_in else None,
    })


@app.post("/api/auth/setup")
def auth_setup():
    """Premier lancement : créer les identifiants"""
    data = request.get_json(force=True)
    password = str(data.get("password") or "")
    if password != str(data.get("confirm") or ""):
        return _error("Les deux mots de passe ne correspondent pas")
    error = auth_manager.create(str(data.get("username") or ""), password)
    if error:
        return _error(error)
    logger.log(f"Identifiants créés pour {auth_manager.username()}")
    _open_session()
    return jsonify({"success": True})


@app.post("/api/auth/login")
def auth_login():
    data = request.get_json(force=True)
    error = auth_manager.verify(str(data.get("username") or ""), str(data.get("password") or ""))
    if error:
        logger.log(f"Échec de connexion: {error}")
        return _error(error, 401)
    logger.log(f"Connexion de {auth_manager.username()}")
    _open_session()
    return jsonify({"success": True})


@app.post("/api/auth/logout")
def auth_logout():
    session.clear()
    return jsonify({"success": True})


@app.post("/api/auth/password")
def auth_password():
    """Changer le mot de passe : les autres sessions ouvertes sont fermées"""
    data = request.get_json(force=True)
    new = str(data.get("new") or "")
    if new != str(data.get("confirm") or ""):
        return _error("Les deux nouveaux mots de passe ne correspondent pas")
    error = auth_manager.change_password(str(data.get("current") or ""), new)
    if error:
        return _error(error)
    logger.log("Mot de passe modifié")
    _open_session()
    return jsonify({"success": True, "message": "Mot de passe modifié"})


# ======= Interface =======

@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


# ======= Configuration =======

@app.get("/api/config")
def get_config():
    return jsonify(config_manager.get_all_config())


@app.post("/api/config")
def save_config():
    data = request.get_json(force=True)
    try:
        if "repo_path" in data:
            config_manager.set_repo_path(data["repo_path"])
        if "site_url" in data:
            config_manager.set_site_url(data["site_url"])
        if "auto_pull" in data:
            config_manager.set_auto_pull(data["auto_pull"])
        if "auto_refresh" in data:
            config_manager.set_auto_refresh(data["auto_refresh"])
        if "show_guide" in data:
            config_manager.set_show_guide(data["show_guide"])
        if "default_port" in data:
            config_manager.set_default_port(int(data["default_port"]))
    except (ValueError, TypeError) as e:
        return _error(str(e))
    return jsonify({"success": True, "config": config_manager.get_all_config()})


@app.post("/api/config/reset")
def reset_config():
    config_manager.reset_to_defaults()
    return jsonify({"success": True, "config": config_manager.get_all_config()})


# ======= Git =======

@app.post("/api/git/verify")
def git_verify():
    result = git_manager.verify_repo(str(_repo_path()))
    return jsonify({"success": result["valid"], "message": result["message"]})


@app.post("/api/git/clone")
def git_clone():
    """Récupérer le site depuis GitHub ; le dossier cloné devient le repository courant"""
    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()
    if not url:
        return _error("Veuillez entrer l'adresse du repository")
    destination = (data.get("path") or "").strip()
    if destination:
        path = Path(destination).expanduser()
    else:
        # Par défaut : dossier personnel / nom du repository
        name = url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1].removesuffix(".git")
        path = Path.home() / (name or "site")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        return _error(f"Le dossier existe déjà et n'est pas vide: {path}")

    result = git_manager.clone(url, str(path))
    if not result["success"]:
        return _error(result["message"], 500)
    config_manager.set_repo_path(str(path))
    return jsonify({**result, "path": str(path)})


@app.post("/api/git/pull")
def git_pull():
    return jsonify(git_manager.pull(str(_repo_path())))


@app.post("/api/git/push")
def git_push():
    message = (request.get_json(force=True).get("message") or "").strip()
    if not message:
        return _error("Veuillez entrer un message de commit")
    return jsonify(git_manager.push(str(_repo_path()), message))


@app.get("/api/git/status")
def git_status():
    # has_git : le dossier choisi est un repository (sinon l'interface propose de récupérer le site)
    return jsonify({**git_manager.get_status(str(_repo_path())), "has_git": (_repo_path() / ".git").exists()})


@app.post("/api/git/discard")
def git_discard():
    """Revenir au dernier commit (les fichiers nouveaux ne sont supprimés que si demandé)"""
    remove_untracked = bool(request.get_json(force=True).get("remove_untracked"))
    result = git_manager.discard(str(_repo_path()), remove_untracked)
    if not result["success"]:
        return _error(result["message"], 500)
    return jsonify(result)


@app.post("/api/git/add")
def git_add_untracked():
    """Ajouter tous les fichiers non suivis"""
    try:
        result = subprocess.run(
            ["git", "add", "."],
            cwd=str(_repo_path()),
            capture_output=True,
            text=True,
            timeout=30
        )
    except Exception as e:
        logger.log(f"Erreur: {e}")
        return _error(str(e), 500)

    if result.returncode == 0:
        logger.log("Fichiers non suivis ajoutés avec succès")
        return jsonify({"success": True, "message": "Tous les fichiers non suivis ont été ajoutés"})
    logger.log(f"Erreur ajout: {result.stderr}")
    return _error(f"Erreur lors de l'ajout: {result.stderr}", 500)


# ======= Éditeur =======

@app.get("/api/files")
def list_files():
    return jsonify({"success": True, "files": _get_page_files()})


@app.get("/api/files/<path:name>")
def load_file(name):
    file_path = _resolve_page(name)
    if file_path is None:
        return _error(f"Fichier introuvable: {name}", 404)

    content = _read_page(file_path)
    start = time.perf_counter()
    result = html_manager.extract_editable_elements(content)
    sources = html_manager.extract_editable_sources(content)
    bold_flags, bold_selectors = bold_info(_repo_path(), name, content)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if not len(sources) == len(bold_flags) == len(result["elements"]):
        return _error("Structure HTML non reconnue : le nombre d'éléments éditables ne correspond pas", 500)

    # value : texte (ou src d'une iframe) ; html : contenu source exact, édité en texte enrichi
    elements = [
        {
            "index": e["index"],
            "id": e["id"],
            "tag": e["tag"],
            "is_iframe": e["is_iframe"],
            "value": e["editable_value"],
            "html": source["html"],
            "nested": source["nested"],
            "bold": bold,
        }
        for e, source, bold in zip(result["elements"], sources, bold_flags)
    ]
    # Version envoyée sur GitHub de chaque élément (null : absent de cette version), pour les marqueurs +/−/~
    published_known = False
    if GIT_FOUND and (_repo_path() / ".git").exists():
        published_known, published_content = git_manager.published_file(str(_repo_path()), name)
        if published_known:
            published = [s["html"] for s in html_manager.extract_editable_sources(published_content or "")]
            # value : texte, ou src d'une iframe (qui n'est pas dans le contenu)
            values = [e["editable_value"] for e in
                      html_manager.extract_editable_elements(published_content or "").get("elements", [])]
            for i, element in enumerate(elements):
                element["published_html"] = published[i] if i < len(published) else None
                element["published_value"] = values[i] if i < len(values) else None

    logger.log(f"Fichier ouvert: {name} ({len(elements)} éléments éditables, {elapsed_ms:.0f} ms)")
    # Une page sans élément éditable n'est pas une erreur : le message est affiché à la place de la liste
    return jsonify({
        "success": True,
        "notice": result.get("error"),
        "elements": elements,
        "bold_selectors": bold_selectors,
        "published_known": published_known,
        "hash": _hash(content),
        "parse_ms": round(elapsed_ms),
    })


@app.post("/api/files/<path:name>")
def save_file(name):
    file_path = _resolve_page(name)
    if file_path is None:
        return _error(f"Fichier introuvable: {name}", 404)

    data = request.get_json(force=True)
    content = _read_page(file_path)

    # Les éléments sont repérés par leur index : refuser si le fichier a changé depuis le chargement
    if data.get("hash") != _hash(content):
        return _error("Le fichier a été modifié depuis son chargement. Rechargez-le avant de sauvegarder.", 409)

    values = {int(k): v for k, v in data.get("values", {}).items()}
    result = html_manager.apply_editable_html(content, values)
    if not result["success"]:
        logger.log(f"Erreur sauvegarde: {result['error']}")
        return _error(f"Impossible de sauvegarder: {result['error']}", 500)

    html_manager.write_file(file_path, result["content"])

    # Générer automatiquement le sitemap après la sauvegarde
    sitemap_result = _update_sitemap()

    return jsonify({
        "success": True,
        "message": f"Fichier sauvegardé: {name} ({result['changed']} élément(s) modifié(s))",
        "sitemap": sitemap_result.get("message") or sitemap_result.get("error"),
        "hash": _hash(result["content"]),
    })


@app.post("/api/snippet/<path:name>")
def file_snippet(name):
    """Code source d'un élément tel qu'il serait sauvegardé, sans écrire le fichier"""
    file_path = _resolve_page(name)
    if file_path is None:
        return _error(f"Fichier introuvable: {name}", 404)

    data = request.get_json(force=True)
    content = _read_page(file_path)
    if data.get("hash") != _hash(content):
        return _error("Le fichier a été modifié depuis son chargement. Rechargez-le.", 409)

    values = {int(k): v for k, v in data.get("values", {}).items()}
    result = html_manager.apply_editable_html(content, values)
    if not result["success"]:
        return _error(f"Aperçu du code impossible: {result['error']}", 500)

    snippet = html_manager.editable_snippet(result["content"], int(data.get("index", -1)))
    if snippet is None:
        return _error("Élément introuvable", 404)
    return jsonify({"success": True, **snippet})


# ======= Sitemap =======

@app.get("/api/sitemap")
def sitemap_info():
    repo_path = _repo_path()
    if not repo_path.is_dir():
        return jsonify({"success": True, "location": None, "base_url": ""})
    location = sitemap_generator.find_sitemap(repo_path)
    relative = location.relative_to(repo_path).as_posix() if location else "sitemap.xml"
    return jsonify({
        "success": True,
        "location": relative if location else None,
        "base_url": sitemap_generator.detect_base_url(repo_path, config_manager.get_site_url(), relative),
    })


@app.post("/api/sitemap")
def sitemap_generate():
    result = _update_sitemap()
    if not result["success"]:
        return _error(result["error"], 500)
    return jsonify({"success": True, "message": result["message"], "base_url": result["base_url"]})


# ======= Prévisualisation =======

def _preview_status():
    return {
        "running": server_manager.is_running(),
        "port": preview_state["port"],
        "logs": list(preview_logs),
    }


@app.get("/api/preview")
def preview_status():
    return jsonify(_preview_status())


@app.post("/api/preview/start")
def preview_start():
    if server_manager.is_running():
        return jsonify({"success": True, **_preview_status()})

    try:
        port = int(request.get_json(force=True).get("port"))
    except (TypeError, ValueError):
        return _error("Le port doit être un nombre valide")
    if not 1 <= port <= 65535:
        return _error(f"Le port doit être entre 1 et 65535 (reçu: {port})")
    if not _repo_path().exists():
        return _error("Le chemin du repository n'existe pas")

    # Script injecté dans les pages ouvertes par l'aperçu en direct de l'éditeur
    preview_script = (STATIC_DIR / "preview-helper.js").read_text(encoding="utf-8")
    thread = threading.Thread(
        target=server_manager.start,
        args=(str(_repo_path()), port, preview_logs.append, preview_script),
        daemon=True
    )
    thread.start()
    preview_state.update(port=port, thread=thread)

    # Laisser le temps au serveur de démarrer (ou d'échouer, ex: port occupé)
    for _ in range(20):
        if server_manager.is_running() or not thread.is_alive():
            break
        time.sleep(0.05)

    status = _preview_status()
    if not status["running"]:
        return jsonify({"success": False, "error": preview_logs[-1] if preview_logs else "Échec du démarrage", **status})
    return jsonify({"success": True, **status})


@app.post("/api/preview/stop")
def preview_stop():
    server_manager.stop()
    preview_logs.append("Serveur arrêté")
    return jsonify({"success": True, **_preview_status()})


# ======= Logs =======

@app.get("/api/logs")
def get_logs():
    return jsonify({"logs": logger.get_logs()})


@app.delete("/api/logs")
def clear_logs():
    logger.clear_logs()
    return jsonify({"success": True})


# ======= Quitter =======

@app.get("/api/quit/check")
def quit_check():
    """Ce qui reste à faire avant de quitter : modifications non publiées, prévisualisation active"""
    git = {"available": False, "message": ""}
    if not GIT_FOUND:
        git["message"] = "Git est introuvable : la publication est impossible depuis MyCMS"
    elif not (_repo_path() / ".git").exists():
        git["message"] = "Le dossier du site n'est pas un repository Git : rien à publier"
    else:
        result = git_manager.pending(str(_repo_path()))
        if result["success"]:
            git = {**result, "available": True}
        else:
            git["message"] = result["message"]
    return jsonify({"success": True, "git": git, "preview_running": server_manager.is_running()})


@app.post("/api/quit")
def quit_app():
    """Arrêter MyCMS : prévisualisation, session, puis le processus une fois la réponse envoyée"""
    if server_manager.is_running():
        server_manager.stop()
    session.clear()
    logger.log("MyCMS fermé depuis l'interface")
    # Le serveur de développement Flask n'a pas d'arrêt propre : sortie du processus juste après la réponse
    threading.Timer(0.5, os._exit, args=(0,)).start()
    return jsonify({"success": True})


# ======= Démarrage =======

def main(host="127.0.0.1", port=5050, open_browser=True):
    """Point d'entrée principal"""
    if config_manager.get_auto_pull():
        logger.log("Pull automatique au démarrage...")
        threading.Thread(target=git_manager.pull, args=(str(_repo_path()),), daemon=True).start()

    if not GIT_FOUND:
        logger.log("Attention: Git est introuvable, pull et push impossibles. "
                   "Installez MyCMS avec le .msi (Git inclus) ou Git depuis https://git-scm.com")

    url = f"http://{host}:{port}"
    logger.log(f"MyCMS disponible sur {url}")
    logger.log("Fermez cette fenêtre pour quitter MyCMS")
    if open_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MyCMS - interface web")
    parser.add_argument("--port", type=int, default=5050, help="port de l'interface (défaut : 5050)")
    parser.add_argument("--no-browser", action="store_true", help="ne pas ouvrir le navigateur au démarrage")
    args = parser.parse_args()
    main(port=args.port, open_browser=not args.no_browser)
