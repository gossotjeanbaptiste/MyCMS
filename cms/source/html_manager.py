#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire HTML - Édition et manipulation des fichiers HTML
"""

from bs4 import BeautifulSoup
import html
import re
from pathlib import Path
import datetime

from html_source import HybridSaver, editable_sources, parse, set_attribute


class HTMLManager:
    """Gère la lecture et modification des fichiers HTML"""

    def __init__(self, logger):
        self.logger = logger

    def read_file(self, file_path):
        """Lire un fichier HTML"""
        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
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
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
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

    def apply_editable_texts(self, content, values):
        """Appliquer du texte brut aux éléments éditables (par index), pour l'ancienne interface CTk.
        Seuls les éléments dont la valeur a changé sont réécrits, directement dans le texte
        source : le reste du fichier (indentation, attributs, fins de ligne) reste identique."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            editable_elements = soup.find_all(class_='editable')
            line_starts = [0] + [m.end() for m in re.finditer('\n', content)]

            edits = []  # (début, fin, remplacement) dans content
            for elem_index, new_value in values.items():
                if not 0 <= elem_index < len(editable_elements):
                    continue
                element = editable_elements[elem_index]
                is_iframe = element.name == 'iframe'
                current = element.get('src', '') if is_iframe else element.get_text().strip()
                if new_value == current:
                    continue

                start = line_starts[element.sourceline - 1] + element.sourcepos
                if content[start:start + len(element.name) + 1].lower() != f"<{element.name}":
                    return {"success": False, "error": f"Position introuvable pour l'élément [{elem_index}]"}
                start_tag_end = self._start_tag_end(content, start)

                if is_iframe:
                    start_tag = content[start:start_tag_end]
                    edits.append((start, start_tag_end, set_attribute(start_tag, 'src', new_value)))
                    continue

                end_tag_start = self._find_end_tag(content, element.name, start_tag_end)
                if end_tag_start is None:
                    return {"success": False, "error": f"Balise fermante </{element.name}> introuvable pour l'élément [{elem_index}]"}

                # Garder les espaces / retours à la ligne autour du texte
                inner = content[start_tag_end:end_tag_start]
                stripped = inner.strip()
                leading = inner[:inner.index(stripped)] if stripped else inner
                trailing = inner[inner.index(stripped) + len(stripped):] if stripped else ""
                edits.append((start_tag_end, end_tag_start,
                              leading + html.escape(new_value, quote=False) + trailing))

            edits.sort()
            for (_, previous_end, _), (next_start, _, _) in zip(edits, edits[1:]):
                if previous_end > next_start:
                    return {"success": False, "error": "Deux éléments éditables imbriqués ont été modifiés en même temps"}

            # Appliquer de la fin vers le début pour que les positions restent valides
            for start, end, replacement in reversed(edits):
                content = content[:start] + replacement + content[end:]
            return {"success": True, "content": content, "changed": len(edits)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _start_tag_end(content, start):
        """Position juste après le '>' de la balise ouvrante qui commence à start"""
        quote = None
        for i in range(start + 1, len(content)):
            char = content[i]
            if quote:
                if char == quote:
                    quote = None
            elif char in '"\'':
                quote = char
            elif char == '>':
                return i + 1
        raise ValueError("Balise ouvrante non terminée")

    @staticmethod
    def _find_end_tag(content, tag, position):
        """Début de la balise fermante correspondante, en tenant compte des balises de même nom imbriquées"""
        depth = 1
        for match in re.finditer(rf'<(/?){re.escape(tag)}(?=[\s/>])', content[position:], re.I):
            depth += -1 if match.group(1) else 1
            if depth == 0:
                return position + match.start()
        return None

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
