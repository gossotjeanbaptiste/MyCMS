#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de desktop : mise à jour automatique au démarrage (active par défaut, une tentative par version)"""

import pytest

from core import updates
from desktop import auto_update, installer

MSI = {"name": "MyCMS-99.0.0.msi", "url": "https://github.com/r/MyCMS-99.0.0.msi", "size": 3, "sha256": None}


@pytest.fixture
def mycms(services, monkeypatch, tmp_path):
    """Services de l'application, avec une version 99.0.0 publiée ; renvoie (services, installeurs lancés)"""
    launched = []
    monkeypatch.setattr(updates, "fetch_latest", lambda: {"tag": "v99.0.0", "url": "https://r", "installer": MSI})
    monkeypatch.setattr(updates, "download", lambda msi, folder: tmp_path / msi["name"])
    monkeypatch.setattr(installer, "launch_installer", launched.append)
    return services, launched


def test_active_by_default(services):
    assert services.config.get_auto_update() is True and services.config.get_update_tried() == ""


def test_installs_the_new_version(mycms, tmp_path):
    services, launched = mycms
    assert auto_update.install_at_startup(services, "2.2.5", frozen=True) is True
    assert launched == [tmp_path / "MyCMS-99.0.0.msi"]
    assert services.config.get_update_tried() == "99.0.0" and services.update["latest"] == "99.0.0"


def test_one_attempt_per_version(mycms):
    """Installation refusée (autorisation d'administrateur) : au lancement suivant, MyCMS démarre normalement"""
    services, launched = mycms
    services.config.set_update_tried("99.0.0")
    assert auto_update.install_at_startup(services, "2.2.5", frozen=True) is False and launched == []
    assert services.update["available"]  # Le bouton « Nouvelle version » reste proposé


@pytest.mark.parametrize("frozen, enabled, current", [(False, True, "2.2.5"),  # Depuis les sources
                                                      (True, False, "2.2.5"),  # Réglage désactivé
                                                      (True, True, "99.0.0")])  # Déjà à jour
def test_nothing_to_install(mycms, frozen, enabled, current):
    services, launched = mycms
    services.config.set_auto_update(enabled)
    assert auto_update.install_at_startup(services, current, frozen) is False and launched == []
    assert services.config.get_update_tried() == ""


def test_failed_download_starts_mycms(mycms, monkeypatch):
    services, launched = mycms

    def broken(msi, folder):
        raise OSError("pas de réseau")

    monkeypatch.setattr(updates, "download", broken)
    assert auto_update.install_at_startup(services, "2.2.5", frozen=True) is False and launched == []
    assert services.config.get_update_tried() == ""  # Nouvelle tentative au prochain lancement


def test_setting_saved_from_the_interface(client):
    response = client.post("/api/config", json={"auto_update": False})
    assert response.get_json()["config"]["auto_update"] is False
