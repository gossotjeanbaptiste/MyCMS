#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire HTML - Édition et manipulation des fichiers HTML
"""

from bs4 import BeautifulSoup
from pathlib import Path

from content.html_tree import SRC_TAGS, editable_sources, parse
from content.hybrid_saver import HybridSaver


class HTMLManager:
    """Gère la lecture et modification des fichiers HTML"""

    def __init__(self, logger):
        self.logger = logger

    def write_file(self, file_path, content):
        """Écrire un fichier HTML"""
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            self.logger.log(f"Fichier écrit: {Path(file_path).name}")
            return {"success": True, "message": f"Fichier sauvegardé: {Path(file_path).name}"}
        except Exception as e:
            error_msg = f"Erreur lors de l'écriture: {str(e)}"
            self.logger.log(error_msg)
            return {"success": False, "error": error_msg}

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
                if elem_tag in SRC_TAGS:  # iframe ou image : on modifie l'adresse
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
                    "is_image": elem_tag == 'img',
                    "editable_value": editable_value
                })
            return {"success": True, "count": len(elements_data), "elements": elements_data}
        except Exception as e:
            return {"success": False, "error": str(e), "elements": []}
    
    def apply_editable_html(self, content, values):
        """Appliquer le HTML saisi dans l'éditeur web aux éléments éditables (par index).
        Les nœuds inchangés sont recopiés depuis le fichier, seuls les écarts sont réécrits."""
        try:
            new_content, changed = HybridSaver(content, values).apply()
            return {"success": True, "content": new_content, "changed": changed}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def editable_snippet(self, content, index, context=10):
        """Lignes de code source d'un élément éditable, avec quelques lignes autour"""
        _, editables = parse(content)
        if not 0 <= index < len(editables):
            return None
        node = editables[index]
        lines = [line.rstrip("\r") for line in content.split("\n")]
        first = content.count("\n", 0, node.start)
        last = content.count("\n", 0, max(node.start, node.end - 1))
        begin = max(0, first - context)
        return {
            "lines": lines[begin:last + context + 1],
            "first_line": begin + 1,
            "start_line": first + 1,
            "end_line": last + 1,
        }

    def extract_editable_sources(self, content):
        """Contenu source exact de chaque élément éditable et index de ses éléments éditables imbriqués"""
        return editable_sources(content)
