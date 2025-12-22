#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de Sitemap - Génération automatique du sitemap.xml
Génère automatiquement le sitemap avec les vraies dates de modification des fichiers
"""

from pathlib import Path
from datetime import datetime
from xml.dom import minidom
import xml.etree.ElementTree as ET


class SitemapGenerator:
    """Génère le sitemap.xml en fonction des fichiers HTML du projet"""

    def __init__(self, logger):
        self.logger = logger
        self.base_url = "https://autoecoleroutart.github.io"
        self.pages_config = {
            "index.html": {"changefreq": "weekly", "priority": 1.0},
            "page/presse.html": {"changefreq": "weekly", "priority": 1.0},
            "page/remerciement.html": {"changefreq": "weekly", "priority": 1.0},
            "page/code_de_la_route.html": {"changefreq": "weekly", "priority": 0.8},
            "page/contact.html": {"changefreq": "weekly", "priority": 0.9},
            "page/equipe.html": {"changefreq": "weekly", "priority": 0.7},
            "page/financement.html": {"changefreq": "weekly", "priority": 0.8},
            "page/formations.html": {"changefreq": "weekly", "priority": 0.9},
            "page/garantie_financiere.html": {"changefreq": "weekly", "priority": 0.3},
            "page/positionnement.html": {"changefreq": "weekly", "priority": 0.4},
            "page/reclamation.html": {"changefreq": "weekly", "priority": 0.4},
            "page/reglement.html": {"changefreq": "weekly", "priority": 0.5},
            "page/resultat.html": {"changefreq": "weekly", "priority": 0.6},
            "page/satisfaction.html": {"changefreq": "weekly", "priority": 0.4},
            "page/tarifs.html": {"changefreq": "weekly", "priority": 0.9},
        }

    def get_file_modification_date(self, file_path):
        """Obtenir la date de dernière modification d'un fichier"""
        try:
            path = Path(file_path)
            if path.exists():
                # Obtenir la date de modification du fichier
                mtime = path.stat().st_mtime
                mod_date = datetime.fromtimestamp(mtime)
                return mod_date.strftime('%Y-%m-%d')
            else:
                return datetime.now().strftime('%Y-%m-%d')
        except Exception as e:
            self.logger.log(
                f"Erreur lors de la lecture de la date du fichier {file_path}: {str(e)}")
            return datetime.now().strftime('%Y-%m-%d')

    def generate_sitemap(self, repo_path):
        """Générer le sitemap.xml en fonction des fichiers du projet"""
        try:
            repo_path = Path(repo_path)

            # Créer l'élément root
            urlset = ET.Element('urlset')
            urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
            urlset.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            urlset.set('xsi:schemaLocation',
                       'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd')

            # Ajouter chaque page
            for relative_path, config in self.pages_config.items():
                file_path = repo_path / relative_path

                # Obtenir la date de modification réelle du fichier
                lastmod = self.get_file_modification_date(file_path)

                # Créer l'URL
                url = ET.SubElement(urlset, 'url')

                loc = ET.SubElement(url, 'loc')
                if relative_path == "index.html":
                    loc.text = self.base_url + "/"
                else:
                    loc.text = self.base_url + "/" + relative_path

                lastmod_elem = ET.SubElement(url, 'lastmod')
                lastmod_elem.text = lastmod

                changefreq = ET.SubElement(url, 'changefreq')
                changefreq.text = config['changefreq']

                priority = ET.SubElement(url, 'priority')
                priority.text = str(config['priority'])

            # Formater le XML
            xml_str = minidom.parseString(
                ET.tostring(urlset)).toprettyxml(indent="    ")
            # Supprimer la ligne XML en double
            xml_lines = xml_str.split('\n')
            xml_str = '\n'.join(xml_lines[1:])  # Ignorer la première ligne XML

            self.logger.log("Sitemap généré avec succès")
            return {"success": True, "content": xml_str}
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

    def update_sitemap(self, repo_path):
        """Générer et sauvegarder le sitemap en une seule opération"""
        try:
            result = self.generate_sitemap(repo_path)
            if not result['success']:
                return result

            save_result = self.save_sitemap(repo_path, result['content'])
            return save_result
        except Exception as e:
            error_msg = f"Erreur lors de la mise à jour du sitemap: {str(e)}"
            self.logger.log(error_msg)
            return {"success": False, "error": error_msg}
