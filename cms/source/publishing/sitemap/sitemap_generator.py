#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de Sitemap - Génération automatique du sitemap.xml
Génère automatiquement le sitemap avec les vraies dates de modification des fichiers
"""

import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from xml.dom import minidom

from content.pages.page_finder import find_html_pages
from publishing.sitemap.robots import has_noindex, robots_allows, robots_rules, update_sitemap_line
from publishing.sitemap.site_url import detect_base_url
from publishing.sitemap.sitemap_files import find_sitemap, read_existing

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


class SitemapGenerator:
    """Génère le sitemap.xml en fonction des fichiers HTML du projet"""

    DEFAULT_CHANGEFREQ = "weekly"
    DEFAULT_PRIORITY = 0.5
    HOME_PRIORITY = 1.0

    def __init__(self, logger):
        self.logger = logger

    # ======= Emplacement et URL du site =======

    def find_sitemap(self, repo_path):
        """Chemin du sitemap.xml : à la racine en priorité, sinon le premier trouvé"""
        return find_sitemap(repo_path)

    def detect_base_url(self, repo_path, configured="", sitemap_relative="sitemap.xml"):
        """URL publique du site, sans '/' final, ou '' si introuvable (voir site_url.detect_base_url)"""
        return detect_base_url(repo_path, self.logger, configured, sitemap_relative)

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
            existing = read_existing(sitemap_path, self.logger) if sitemap_path else {}
            rules = robots_rules(repo_path)

            urlset = ET.Element('urlset')
            urlset.set('xmlns', SITEMAP_NS)
            urlset.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            urlset.set('xsi:schemaLocation',
                       'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd')

            included, excluded = [], []
            for relative_path in find_html_pages(repo_path):
                url_path = "/" if relative_path == "index.html" else "/" + relative_path
                if not robots_allows(rules, url_path) or has_noindex(repo_path / relative_path):
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
                update_sitemap_line(repo_path, result["base_url"], self.logger)
            return {**save_result, "created": created, "moved_from": moved_from,
                    "base_url": result["base_url"], "included": result["included"],
                    "excluded": result["excluded"]}
        except Exception as e:
            error_msg = f"Erreur lors de la mise à jour du sitemap: {str(e)}"
            self.logger.log(error_msg)
            return {"success": False, "error": error_msg}
