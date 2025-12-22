#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire HTML - Édition et manipulation des fichiers HTML
"""

from bs4 import BeautifulSoup
from pathlib import Path
import datetime


class HTMLManager:
    """Gère la lecture et modification des fichiers HTML"""

    def __init__(self, logger):
        self.logger = logger

    def read_file(self, file_path):
        """Lire un fichier HTML"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.logger.log(f"Fichier lu: {Path(file_path).name}")
            return {"success": True, "content": content}
        except Exception as e:
            error_msg = f"Erreur lors de la lecture: {str(e)}"
            self.logger.log(error_msg)
            return {"success": False, "content": "", "error": error_msg}

    def write_file(self, file_path, content):
        """Écrire un fichier HTML"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.log(f"Fichier écrit: {Path(file_path).name}")
            return {"success": True, "message": f"Fichier sauvegardé: {Path(file_path).name}"}
        except Exception as e:
            error_msg = f"Erreur lors de l'écriture: {str(e)}"
            self.logger.log(error_msg)
            return {"success": False, "error": error_msg}

    def parse_html(self, content):
        """Parser le contenu HTML"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            return {"success": True, "soup": soup}
        except Exception as e:
            error_msg = f"Erreur lors du parsing: {str(e)}"
            self.logger.log(error_msg)
            return {"success": False, "error": error_msg}

    def find_element(self, content, selector):
        """Trouver un élément par sélecteur CSS"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            element = soup.select_one(selector)
            if element:
                return {"success": True, "element": str(element)}
            else:
                return {"success": False, "error": f"Élément non trouvé: {selector}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def replace_element(self, content, selector, new_content):
        """Remplacer un élément"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            element = soup.select_one(selector)

            if element:
                element.replace_with(BeautifulSoup(new_content, 'html.parser'))
                return {"success": True, "content": str(soup.prettify())}
            else:
                return {"success": False, "error": f"Élément non trouvé: {selector}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_all_elements(self, content, selector):
        """Trouver tous les éléments correspondant au sélecteur"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            elements = soup.select(selector)
            return {"success": True, "count": len(elements), "elements": [str(e) for e in elements]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_html(self, content):
        """Valider la structure HTML"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            issues = []
            if not soup.find('html'):
                issues.append("Balise <html> manquante")
            if not soup.find('head'):
                issues.append("Balise <head> manquante")
            if not soup.find('body'):
                issues.append("Balise <body> manquante")
            if content.count('<') != content.count('>'):
                issues.append("Nombre de balises ouvrantes/fermantes mismatch")
            if issues:
                return {"success": False, "valid": False, "issues": issues}
            else:
                return {"success": True, "valid": True, "message": "HTML valide"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_editable_elements(self, content):
        """Extraire uniquement les éléments avec la classe 'editable'"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            editable_elements = soup.find_all(class_='editable')
            if not editable_elements:
                return {"success": False, "error": "Aucun élément éditable trouvé (class='editable')", "elements": []}
            elements_data = []
            for index, elem in enumerate(editable_elements):
                elem_id = elem.get('id', None)
                elem_tag = elem.name
                elem_class = ' '.join(elem.get('class', []))
                elem_content = str(elem)
                editable_value = None
                is_iframe = elem_tag == 'iframe'
                if is_iframe:
                    editable_value = elem.get('src', '')
                else:
                    editable_value = elem.get_text().strip()
                elements_data.append({
                    "index": index,
                    "id": elem_id,
                    "tag": elem_tag,
                    "class": elem_class,
                    "content": elem_content,
                    "is_iframe": is_iframe,
                    "editable_value": editable_value
                })
            return {"success": True, "count": len(elements_data), "elements": elements_data}
        except Exception as e:
            return {"success": False, "error": str(e), "elements": []}
    
    def update_editable_element(self, content, element_id, new_content):
        """Mettre à jour un élément éditable spécifique"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            element = soup.find(id=element_id, class_='editable')
            if not element:
                return {"success": False, "error": f"Élément éditable non trouvé: {element_id}"}
            element.string = new_content
            return {"success": True, "content": str(soup.prettify())}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_file_info(self, file_path):
        """Obtenir les informations du fichier"""
        try:
            path = Path(file_path)
            if path.exists():
                stat = path.stat()
                info = {
                    "name": path.name,
                    "size": f"{stat.st_size} bytes",
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "path": str(path.absolute())
                }
                return {"success": True, "info": info}
            else:
                return {"success": False, "error": "Fichier non trouvé"}
        except Exception as e:
            return {"success": False, "error": str(e)}
