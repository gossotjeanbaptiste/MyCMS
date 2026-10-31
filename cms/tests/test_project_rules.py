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
MODULE_OF = {"flask": "flask", "waitress": "waitress", "beautifulsoup4": "bs4", "gitpython": "git", "pystray": "pystray",
             "pillow": "PIL"}


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
    from version import VERSION
    assert package == VERSION


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


def test_interface_logo_matches_the_icon():
    """static/logo.png est extrait de cms/icon/logo.ico : le régénérer quand l'icône change"""
    from PIL import Image, ImageChops
    icon = Image.open(CMS_DIR / "icon" / "logo.ico")
    icon.size = (256, 256)
    logo = Image.open(CMS_DIR / "web" / "static" / "logo.png")
    assert logo.size == (256, 256)
    assert ImageChops.difference(icon.convert("RGBA"), logo.convert("RGBA")).getbbox() is None


def test_wide_logo_for_the_header():
    """static/logo-wide.png : bannière horizontale, nette à 40 px de haut"""
    from PIL import Image
    width, height = Image.open(CMS_DIR / "web" / "static" / "logo-wide.png").size
    assert height == 128 and width > 2 * height


def test_readme_version_badge():
    """Le badge de version du README suit la version de l'application"""
    from version import VERSION
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"badge/Version-{VERSION}-" in readme


def test_mit_license():
    """Licence MIT : le fichier LICENSE existe, et le README l'annonce"""
    assert (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")
    assert "badge/Licence-MIT-" in (ROOT / "README.md").read_text(encoding="utf-8")
