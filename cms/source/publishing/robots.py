#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
robots.txt et balises meta robots - Pages exclues du sitemap, ligne Sitemap du robots.txt
"""

import re
from pathlib import Path


def update_sitemap_line(repo_path, base_url, logger):
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
        logger.log("robots.txt: ligne Sitemap mise à jour")


def robots_rules(repo_path):
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


def robots_allows(rules, path):
    """La règle la plus longue qui correspond l'emporte, Allow en cas d'égalité (comme Google)"""
    best_len, allowed = -1, True
    for is_allow, pattern in rules:
        regex = "^" + re.escape(pattern).replace(r"\*", ".*")
        if regex.endswith(r"\$"):
            regex = regex[:-2] + "$"
        if re.match(regex, path) and (len(pattern) > best_len or (len(pattern) == best_len and is_allow)):
            best_len, allowed = len(pattern), is_allow
    return allowed


def has_noindex(file_path):
    """La page contient-elle <meta name="robots" content="...noindex...">"""
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    for tag in re.findall(r"<meta\b[^>]*>", content, re.I):
        if re.search(r"name\s*=\s*[\"']?robots", tag, re.I) and "noindex" in tag.lower():
            return True
    return False
