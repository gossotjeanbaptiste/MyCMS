#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Règles du projet (AGENTS.md) vérifiées automatiquement : taille des fichiers, pas de variable globale,
version, modules déclarés pour l'exécutable, dépendances vérifiées par run.bat"""

import json
import re

import pytest

from conftest import CMS_DIR

ROOT = CMS_DIR.parent
# Fichiers de l'application : Python, JS, HTML, CSS (le CSS compilé par Tailwind n'est pas écrit à la main)
SOURCES = sorted(
    path for pattern in ("source/**/*.py", "web/*.py", "web/api/*.py", "web/static/scripts/**/*.js",
                         "web/templates/**/*.html", "web/src/**/*.css", "web/static/highlight.css")
    for path in CMS_DIR.glob(pattern))
PYTHON_MODULES = sorted(path for path in SOURCES if path.suffix == ".py" and path.name != "__init__.py"
                        and path.parent.name != "web")
# Nom du paquet (requirements.txt) -> nom du module importé
MODULE_OF = {"flask": "flask", "beautifulsoup4": "bs4", "gitpython": "git", "pystray": "pystray", "pillow": "PIL"}


def name(path):
    return path.relative_to(CMS_DIR).as_posix()


@pytest.mark.parametrize("path", SOURCES, ids=name)
def test_at_most_200_lines(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 200, f"{len(lines)} lignes : découper par fonctionnalité"


@pytest.mark.parametrize("path", [p for p in SOURCES if p.suffix == ".py"], ids=name)
def test_no_global_statement(path):
    assert not re.search(r"^\s*global\s", path.read_text(encoding="utf-8"), re.M)


def test_versions_match():
    package = json.loads((CMS_DIR / "web" / "package.json").read_text(encoding="utf-8"))["version"]
    python = re.search(r'__version__ = "([^"]+)"', (CMS_DIR / "source" / "__init__.py").read_text(encoding="utf-8"))
    assert package == python.group(1)


@pytest.mark.parametrize("path", PYTHON_MODULES, ids=name)
def test_module_declared_for_the_executable(path):
    """Un nouveau module Python doit être ajouté aux hiddenimports de mycms.spec"""
    base = CMS_DIR / ("web" if "web" in path.parts[-3:] else "source")
    module = ".".join(path.relative_to(base).with_suffix("").parts)
    assert f"'{module}'" in (CMS_DIR / "installer" / "mycms.spec").read_text(encoding="utf-8")


def test_run_bat_checks_every_dependency():
    """Une dépendance de requirements.txt doit aussi être vérifiée par run.bat (nom du module)"""
    run_bat = (ROOT / "run.bat").read_text(encoding="utf-8", errors="replace")
    for line in (CMS_DIR / "requirements.txt").read_text(encoding="utf-8").splitlines():
        package = re.match(r"[A-Za-z0-9_-]+", line.strip())
        if package and not line.startswith("#"):
            assert f"'{MODULE_OF[package.group(0).lower()]}'" in run_bat, package.group(0)


def test_compiled_css_contains_the_classes_of_new_features():
    """style.css est versionné : il doit être recompilé après l'ajout de classes Tailwind"""
    css = (CMS_DIR / "web" / "static" / "style.css").read_text(encoding="utf-8")
    for selector in (".chip", ".category-title", ".max-w-72", ".badge-on"):
        assert selector in css
