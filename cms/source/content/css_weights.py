#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graisse du texte - Quels éléments éditables sont en gras d'après le CSS du site
(feuilles <link>, @import, <style>, variables CSS, style en ligne) ou parce que ce sont des <strong>/<b>.
Les titres ne sont pas considérés en gras par défaut : seulement si le CSS le dit.
"""

import re
from pathlib import Path

from bs4 import BeautifulSoup

# Balises en gras sans règle CSS (feuille du navigateur) ; les titres h1-h6 en sont exclus volontairement
BOLD_BY_DEFAULT = {"strong", "b"}
# Pseudo-classes d'état : la règle ne s'applique pas au texte affiché normalement
STATEFUL = re.compile(r"::|:(hover|focus|focus-within|focus-visible|active|visited|target|checked)\b", re.I)
SIMPLE_COMPOUND = re.compile(r"[a-zA-Z][\w-]*(\.[\w-]+)*|(\.[\w-]+)+")


def _read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _inside(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _local(href):
    return href and not re.match(r"(?i)^([a-z][a-z0-9+.-]*:|//)", href)


def _collect_css(repo_path, page_path, soup):
    """Texte CSS de la page, dans l'ordre : <link rel=stylesheet> locaux (avec leurs @import) et <style>"""
    seen = set()

    def load(path, depth=0):
        if depth > 10 or path in seen or not path.is_file() or not _inside(path, repo_path):
            return ""
        seen.add(path)
        css = re.sub(r"/\*.*?\*/", "", _read(path), flags=re.S)
        imports = ""
        for match in re.finditer(r"""@import\s+(?:url\(\s*)?["']?([^"')\s;]+)["']?\s*\)?[^;]*;""", css):
            if _local(match.group(1)):
                imports += load((path.parent / match.group(1)).resolve(), depth + 1)
        return imports + css

    chunks = []
    for tag in soup.find_all(["link", "style"]):
        if tag.name == "link" and "stylesheet" in [r.lower() for r in tag.get("rel", [])]:
            href = tag.get("href", "").split("?")[0].split("#")[0]
            if _local(href):
                base = repo_path if href.startswith("/") else page_path.parent
                chunks.append(load((base / href.lstrip("/")).resolve()))
        elif tag.name == "style":
            chunks.append(re.sub(r"/\*.*?\*/", "", tag.get_text(), flags=re.S))
    return "\n".join(chunks)


def _is_bold(value, variables, depth=0):
    """True / False selon la valeur de font-weight, None si indéterminée (inherit, var inconnue...)"""
    value = value.replace("!important", "").strip().lower()
    match = re.fullmatch(r"var\(\s*(--[\w-]+)\s*(?:,\s*(.+))?\)", value)
    if match:
        if depth > 5:
            return None
        resolved = variables.get(match.group(1), match.group(2))
        return _is_bold(resolved, variables, depth + 1) if resolved else None
    if value in ("bold", "bolder"):
        return True
    if value in ("normal", "lighter"):
        return False
    if re.fullmatch(r"\d+", value):
        return int(value) >= 600
    return None


def _specificity(selector):
    selector = re.sub(r"\([^)]*\)", "", selector)  # contenu de :not(...) etc. ignoré
    ids = len(re.findall(r"#[\w-]+", selector))
    classes = len(re.findall(r"\.[\w-]+|\[[^\]]*\]|:[\w-]+", selector))
    tags = len(re.findall(r"(?:^|[\s>+~])([a-zA-Z][\w-]*)", selector))
    return (ids, classes, tags)


def bold_info(repo_path, page_relative, content):
    """(gras de chaque élément éditable dans l'ordre, sélecteurs simples en gras pour le contenu des éléments)"""
    repo_path = Path(repo_path)
    soup = BeautifulSoup(content, "html.parser")
    css = _collect_css(repo_path, repo_path / page_relative, soup)
    variables = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;{}]+)", css))

    decided = {}  # id(élément) -> (priorité, gras)
    inner_selectors = []
    for order, match in enumerate(re.finditer(r"([^{}@;]+)\{([^{}]*)\}", css)):
        weights = re.findall(r"(?:^|;)\s*font-weight\s*:\s*([^;]+)", match.group(2))
        if not weights:
            continue
        bold = _is_bold(weights[-1], variables)
        if bold is None:
            continue
        for selector in match.group(1).split(","):
            selector = selector.strip()
            if not selector or STATEFUL.search(selector):
                continue
            try:
                elements = soup.select(selector)
            except Exception:
                continue
            priority = (0,) + _specificity(selector) + (order,)
            for element in elements:
                if id(element) not in decided or decided[id(element)][0] <= priority:
                    decided[id(element)] = (priority, bold)
            last = re.split(r"[\s>+~]+", selector)[-1]
            if bold and SIMPLE_COMPOUND.fullmatch(last) and last not in inner_selectors:
                inner_selectors.append(last)

    # Style en ligne : prioritaire sur les feuilles de style
    for element in soup.find_all(style=re.compile(r"font-weight", re.I)):
        weights = re.findall(r"font-weight\s*:\s*([^;]+)", element["style"], re.I)
        bold = _is_bold(weights[-1], variables) if weights else None
        if bold is not None:
            decided[id(element)] = ((1,), bold)

    def element_bold(element):
        # font-weight s'hérite : le premier ancêtre qui a une règle décide
        while element is not None and element.name:
            if id(element) in decided:
                return decided[id(element)][1]
            if element.name in BOLD_BY_DEFAULT:
                return True
            element = element.parent
        return False

    flags = [element_bold(e) for e in soup.find_all(class_="editable")]
    return flags, inner_selectors
