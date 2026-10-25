#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de Sitemap - Génération automatique du sitemap.xml
Génère automatiquement le sitemap avec les vraies dates de modification des fichiers
"""

import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from urllib.parse import urlsplit
from xml.dom import minidom
import xml.etree.ElementTree as ET

from page_finder import find_files, find_html_pages

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


class SitemapGenerator:
    """Génère le sitemap.xml en fonction des fichiers HTML du projet"""

    DEFAULT_CHANGEFREQ = "weekly"
    DEFAULT_PRIORITY = 0.5
    HOME_PRIORITY = 1.0

    def __init__(self, logger):
        self.logger = logger

    # ======= Emplacement du sitemap =======

    def find_sitemap(self, repo_path):
        """Chemin du sitemap.xml : à la racine en priorité, sinon le premier trouvé"""
        repo_path = Path(repo_path)
        if (repo_path / "sitemap.xml").exists():
            return repo_path / "sitemap.xml"
        found = sorted(find_files(repo_path, lambda name: name.lower() == "sitemap.xml"),
                       key=lambda p: p.count("/"))
        return repo_path / found[0] if found else None

    def ensure_sitemap_at_root(self, repo_path):
        """Déplacer le sitemap à la racine s'il est ailleurs. Retourne l'ancien chemin relatif si déplacé."""
        repo_path = Path(repo_path)
        current = self.find_sitemap(repo_path)
        if current is None or current == repo_path / "sitemap.xml":
            return None

        old_relative = current.relative_to(repo_path).as_posix()
        shutil.move(str(current), str(repo_path / "sitemap.xml"))
        self.logger.log(f"Sitemap déplacé à la racine: {old_relative} -> sitemap.xml")
        return old_relative

    def _update_robots_sitemap_line(self, repo_path, base_url):
        """Faire pointer la ligne 'Sitemap:' du robots.txt vers <base_url>/sitemap.xml"""
        robots_path = Path(repo_path) / "robots.txt"
        if not robots_path.exists():
            return
        with open(robots_path, encoding="utf-8", newline="") as f:
            content = f.read()
        # \S+ n'avale pas le \r d'une fin de ligne CRLF
        new_content = re.sub(r"(?im)^(sitemap:[ \t]*)\S+", lambda m: f"{m.group(1)}{base_url}/sitemap.xml", content)
        if new_content != content:
            with open(robots_path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
            self.logger.log("robots.txt: ligne Sitemap mise à jour")

    # ======= URL du site =======

    def detect_base_url(self, repo_path, configured="", sitemap_relative="sitemap.xml"):
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
        sitemap_path = self.find_sitemap(repo_path)
        if sitemap_path:
            locs = list(self._read_existing(sitemap_path))
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

        return self._github_pages_url(repo_path)

    def _github_pages_url(self, repo_path):
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

    # ======= Pages à indexer =======

    def _read_existing(self, sitemap_path):
        """Réglages (changefreq, priority) du sitemap existant, par URL"""
        try:
            root = ET.parse(sitemap_path).getroot()
        except Exception as e:
            self.logger.log(f"Sitemap existant illisible, il sera régénéré: {e}")
            return {}
        entries = {}
        for url in root.iter():
            if url.tag.rsplit("}", 1)[-1] != "url":
                continue
            fields = {child.tag.rsplit("}", 1)[-1]: (child.text or "").strip() for child in url}
            if fields.get("loc"):
                entries[fields["loc"]] = fields
        return entries

    def _robots_rules(self, repo_path):
        """Règles Allow/Disallow du groupe 'User-agent: *' du robots.txt"""
        robots_path = Path(repo_path) / "robots.txt"
        if not robots_path.exists():
            return []
        rules = []
        in_star_group = False
        previous_was_agent = False
        for line in robots_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            field, value = (part.strip() for part in line.split(":", 1))
            field = field.lower()
            if field == "user-agent":
                # Plusieurs User-agent consécutifs partagent le même groupe
                in_star_group = (in_star_group and previous_was_agent) or value == "*"
                previous_was_agent = True
                continue
            previous_was_agent = False
            if in_star_group and field in ("allow", "disallow") and value:
                rules.append((field == "allow", value))
        return rules

    @staticmethod
    def _robots_allows(rules, path):
        """La règle la plus longue qui correspond l'emporte, Allow en cas d'égalité (comme Google)"""
        best_len, allowed = -1, True
        for is_allow, pattern in rules:
            regex = "^" + re.escape(pattern).replace(r"\*", ".*")
            if regex.endswith(r"\$"):
                regex = regex[:-2] + "$"
            if re.match(regex, path) and (len(pattern) > best_len or (len(pattern) == best_len and is_allow)):
                best_len, allowed = len(pattern), is_allow
        return allowed

    @staticmethod
    def _has_noindex(file_path):
        """La page contient-elle <meta name="robots" content="...noindex...">"""
        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return False
        for tag in re.findall(r"<meta\b[^>]*>", content, re.I):
            if re.search(r"name\s*=\s*[\"']?robots", tag, re.I) and "noindex" in tag.lower():
                return True
        return False

    def get_file_modification_date(self, file_path):
        """Obtenir la date de dernière modification d'un fichier"""
        try:
            return datetime.fromtimestamp(Path(file_path).stat().st_mtime).strftime('%Y-%m-%d')
        except Exception as e:
            self.logger.log(
                f"Erreur lors de la lecture de la date du fichier {file_path}: {str(e)}")
            return datetime.now().strftime('%Y-%m-%d')

    # ======= Génération =======

    def generate_sitemap(self, repo_path, base_url="", sitemap_relative="sitemap.xml"):
        """Générer le sitemap.xml à partir des pages HTML trouvées dans le projet"""
        try:
            repo_path = Path(repo_path)
            base_url = self.detect_base_url(repo_path, base_url, sitemap_relative)
            if not base_url:
                return {"success": False, "error": "URL du site introuvable : renseignez-la dans les paramètres"}

            sitemap_path = self.find_sitemap(repo_path)
            existing = self._read_existing(sitemap_path) if sitemap_path else {}
            rules = self._robots_rules(repo_path)

            urlset = ET.Element('urlset')
            urlset.set('xmlns', SITEMAP_NS)
            urlset.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            urlset.set('xsi:schemaLocation',
                       'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd')

            included, excluded = [], []
            for relative_path in find_html_pages(repo_path):
                url_path = "/" if relative_path == "index.html" else "/" + relative_path
                if not self._robots_allows(rules, url_path) or self._has_noindex(repo_path / relative_path):
                    excluded.append(relative_path)
                    continue
                included.append(relative_path)

                loc_text = base_url + url_path
                # Conserver les réglages déjà présents dans le sitemap pour cette page
                previous = existing.get(loc_text, {})
                default_priority = self.HOME_PRIORITY if relative_path == "index.html" else self.DEFAULT_PRIORITY

                url = ET.SubElement(urlset, 'url')
                ET.SubElement(url, 'loc').text = loc_text
                ET.SubElement(url, 'lastmod').text = self.get_file_modification_date(repo_path / relative_path)
                ET.SubElement(url, 'changefreq').text = previous.get('changefreq') or self.DEFAULT_CHANGEFREQ
                ET.SubElement(url, 'priority').text = previous.get('priority') or str(default_priority)

            # Formater le XML
            xml_str = minidom.parseString(
                ET.tostring(urlset)).toprettyxml(indent="    ")
            # Supprimer la ligne XML en double
            xml_str = '\n'.join(xml_str.split('\n')[1:])

            self.logger.log(f"Sitemap généré: {len(included)} pages ({len(excluded)} exclues)")
            return {"success": True, "content": xml_str, "base_url": base_url,
                    "included": included, "excluded": excluded}
        except Exception as e:
            error_msg = f"Erreur lors de la génération du sitemap: {str(e)}"
            self.logger.log(error_msg)
            return {"success": False, "error": error_msg}

    def save_sitemap(self, repo_path, sitemap_content):
        """Sauvegarder le sitemap.xml"""
        try:
            sitemap_path = Path(repo_path) / "sitemap.xml"
            with open(sitemap_path, 'w', encoding='utf-8') as f:
                f.write(sitemap_content)
            self.logger.log(f"Sitemap sauvegardé: {sitemap_path}")
            return {"success": True, "path": str(sitemap_path)}
        except Exception as e:
            error_msg = f"Erreur lors de la sauvegarde du sitemap: {str(e)}"
            self.logger.log(error_msg)
            return {"success": False, "error": error_msg}

    def update_sitemap(self, repo_path, base_url=""):
        """Ramener le sitemap à la racine (ou le créer), puis le régénérer"""
        try:
            created = self.find_sitemap(repo_path) is None
            moved_from = self.ensure_sitemap_at_root(repo_path)

            # Après un déplacement, le robots.txt référence encore l'ancien emplacement
            result = self.generate_sitemap(repo_path, base_url, moved_from or "sitemap.xml")
            if not result['success']:
                return result

            save_result = self.save_sitemap(repo_path, result['content'])
            if not save_result['success']:
                return save_result
            if moved_from:
                self._update_robots_sitemap_line(repo_path, result["base_url"])
            return {**save_result, "created": created, "moved_from": moved_from,
                    "base_url": result["base_url"], "included": result["included"],
                    "excluded": result["excluded"]}
        except Exception as e:
            error_msg = f"Erreur lors de la mise à jour du sitemap: {str(e)}"
            self.logger.log(error_msg)
            return {"success": False, "error": error_msg}
