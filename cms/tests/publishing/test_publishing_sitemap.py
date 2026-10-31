#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de publishing : sitemap, robots.txt et URL publique du site"""

import pytest

from conftest import git
from publishing.robots import has_noindex, robots_allows, robots_rules, update_sitemap_line
from publishing.site_url import detect_base_url, github_pages_url
from publishing.sitemap_files import find_sitemap, read_existing
from publishing.sitemap_generator import SitemapGenerator
from site_builder import read

BASE = "https://exemple.github.io"


@pytest.fixture
def generator(logger):
    return SitemapGenerator(logger)


def test_generate_excludes_robots_and_noindex(generator, site):
    result = generator.generate_sitemap(site)
    assert result["success"] and result["base_url"] == BASE
    assert result["included"] == ["index.html", "page/financement.html", "page/formations.html"]
    assert result["excluded"] == ["page/mentions.html", "page/prive/secret.html"]
    assert f"<loc>{BASE}/</loc>" in result["content"] and "<priority>1.0</priority>" in result["content"]
    assert "<priority>0.5</priority>" in result["content"]


def test_update_creates_sitemap_at_root(generator, site):
    result = generator.update_sitemap(site)
    assert result["success"] and result["created"] and result["moved_from"] is None
    assert f"<loc>{BASE}/page/formations.html</loc>" in (site / "sitemap.xml").read_text(encoding="utf-8")


def test_existing_settings_are_kept(generator, site):
    (site / "sitemap.xml").write_text(f"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>{BASE}/page/formations.html</loc><changefreq>monthly</changefreq><priority>0.9</priority></url>
</urlset>""", encoding="utf-8")
    content = generator.update_sitemap(site) and (site / "sitemap.xml").read_text(encoding="utf-8")
    assert "<changefreq>monthly</changefreq>" in content and "<priority>0.9</priority>" in content


def test_sitemap_is_moved_to_root_and_robots_updated(generator, site):
    (site / "robots.txt").write_bytes(b"User-agent: *\r\nSitemap: https://exemple.github.io/page/sitemap.xml\r\n")
    (site / "page" / "sitemap.xml").write_text("<urlset/>", encoding="utf-8")
    result = generator.update_sitemap(site)
    assert result["moved_from"] == "page/sitemap.xml" and result["base_url"] == BASE
    assert not (site / "page" / "sitemap.xml").exists() and (site / "sitemap.xml").exists()
    assert (site / "robots.txt").read_bytes() == b"User-agent: *\r\nSitemap: https://exemple.github.io/sitemap.xml\r\n"


def test_unknown_site_url(generator, site):
    (site / "robots.txt").unlink()
    result = generator.update_sitemap(site)
    assert not result["success"] and "URL du site introuvable" in result["error"]


def test_find_and_read_sitemap(site, logger):
    assert find_sitemap(site) is None
    (site / "page" / "sitemap.xml").write_text("pas du xml", encoding="utf-8")
    assert find_sitemap(site) == site / "page" / "sitemap.xml"
    assert read_existing(site / "page" / "sitemap.xml", logger) == {}
    (site / "sitemap.xml").write_text("<urlset/>", encoding="utf-8")
    assert find_sitemap(site) == site / "sitemap.xml"


def test_file_modification_date(generator, site):
    assert len(generator.get_file_modification_date(site / "index.html")) == 10
    assert len(generator.get_file_modification_date(site / "absent.html")) == 10


# ======= robots.txt =======

def test_robots_rules_of_the_star_group(tmp_path):
    (tmp_path / "robots.txt").write_text("User-agent: Googlebot\nDisallow: /\n\n"
                                         "User-agent: Bing\nUser-agent: *\nDisallow: /prive/  # commentaire\n"
                                         "Allow: /prive/public.html\nDisallow:\n", encoding="utf-8")
    assert robots_rules(tmp_path) == [(False, "/prive/"), (True, "/prive/public.html")]
    assert robots_rules(tmp_path / "absent") == []


@pytest.mark.parametrize("path, allowed", [
    ("/index.html", True), ("/prive/a.html", False), ("/prive/public.html", True),
    ("/page/x.pdf", False), ("/page/x.pdf?v=1", True), ("/brouillon-1.html", False),
])
def test_robots_allows(path, allowed):
    rules = [(False, "/prive/"), (True, "/prive/public.html"), (False, "/*.pdf$"), (False, "/brouillon")]
    assert robots_allows(rules, path) is allowed


def test_noindex(site):
    assert has_noindex(site / "page" / "mentions.html") and not has_noindex(site / "index.html")
    assert not has_noindex(site / "absent.html")


def test_update_sitemap_line_without_robots(tmp_path, logger):
    update_sitemap_line(tmp_path, BASE, logger)
    assert not (tmp_path / "robots.txt").exists()


# ======= URL du site =======

def test_base_url_sources_in_order(site, logger):
    assert detect_base_url(site, logger, configured=" https://perso.fr/ ") == "https://perso.fr"
    assert detect_base_url(site, logger) == BASE  # robots.txt
    (site / "robots.txt").unlink()
    (site / "sitemap.xml").write_text("""<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://depuis-sitemap.fr/page/a.html</loc></url><url><loc>https://depuis-sitemap.fr/</loc></url>
</urlset>""", encoding="utf-8")
    assert detect_base_url(site, logger) == "https://depuis-sitemap.fr"
    (site / "sitemap.xml").unlink()
    (site / "CNAME").write_text("www.rout-art.fr\n", encoding="utf-8")
    assert detect_base_url(site, logger) == "https://www.rout-art.fr"
    (site / "CNAME").unlink()
    assert detect_base_url(site, logger) == ""


@pytest.mark.parametrize("remote, url", [
    ("git@github.com:autoecoleroutart/autoecoleroutart.github.io", "https://autoecoleroutart.github.io"),
    ("https://github.com/Owner/MonSite.git", "https://owner.github.io/MonSite"),
    ("https://gitlab.com/owner/site.git", ""),
])
def test_github_pages_url(tmp_path, remote, url):
    git(tmp_path, "init", "-q")
    git(tmp_path, "remote", "add", "origin", remote)
    assert github_pages_url(tmp_path) == url


def test_sitemap_info_reads_site(site):
    assert read(site / "robots.txt").count("\r\n") == 3
