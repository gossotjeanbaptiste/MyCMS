#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL publique du site - Détectée depuis la configuration, le robots.txt, le sitemap, le CNAME ou le remote GitHub
"""

import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from publishing.sitemap.sitemap_files import find_sitemap, read_existing


def detect_base_url(repo_path, logger, configured="", sitemap_relative="sitemap.xml"):
    """URL publique du site, sans '/' final, ou '' si introuvable.
    Ordre : paramètre configuré, robots.txt, sitemap existant, fichier CNAME, remote GitHub Pages.
    sitemap_relative : emplacement du sitemap auquel la ligne 'Sitemap:' du robots.txt fait référence."""
    repo_path = Path(repo_path)
    if configured.strip():
        return configured.strip().rstrip("/")

    # Ligne "Sitemap: https://site/<sitemap_relative>" du robots.txt
    robots_path = repo_path / "robots.txt"
    if robots_path.exists():
        match = re.search(r"(?im)^sitemap:\s*(\S+)", robots_path.read_text(encoding="utf-8", errors="replace"))
        if match:
            url = match.group(1)
            suffix = "/" + sitemap_relative
            return url[:-len(suffix)] if url.endswith(suffix) else url.rsplit("/", 1)[0]

    # Plus courte URL du sitemap existant se terminant par '/' (la page d'accueil)
    sitemap_path = find_sitemap(repo_path)
    if sitemap_path:
        locs = list(read_existing(sitemap_path, logger))
        home = sorted((loc for loc in locs if loc.endswith("/")), key=len)
        if home:
            return home[0].rstrip("/")
        if locs:
            parts = urlsplit(locs[0])
            return f"{parts.scheme}://{parts.netloc}"

    # Domaine personnalisé GitHub Pages
    cname_path = repo_path / "CNAME"
    if cname_path.exists():
        domain = cname_path.read_text(encoding="utf-8").strip().splitlines()
        if domain and domain[0].strip():
            return f"https://{domain[0].strip()}"

    return github_pages_url(repo_path)


def github_pages_url(repo_path):
    """URL GitHub Pages déduite du remote origin (git@github.com:owner/repo ou https://github.com/owner/repo)"""
    try:
        remote = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=str(repo_path), capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except Exception:
        return ""
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", remote)
    if not match:
        return ""
    owner, repo = match.groups()
    if repo.lower() == f"{owner.lower()}.github.io":
        return f"https://{repo.lower()}"
    return f"https://{owner.lower()}.github.io/{repo}"
