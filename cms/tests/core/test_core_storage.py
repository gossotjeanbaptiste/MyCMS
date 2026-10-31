#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de core : dossier de données (~/.mycms), configuration et journal"""

import json
import os

import pytest

from core.storage import data_dir as data_dir_module
from core.storage.config_manager import ConfigManager
from core.storage.data_dir import data_dir, lock_file, unlock_file
from core.logs.logger import Logger


# ======= Dossier de données =======

def test_data_dir_created_in_home(isolated_home):
    path = data_dir()
    assert path == isolated_home / ".mycms" and path.is_dir()


@pytest.mark.skipif(os.name != "nt", reason="attribut « caché » de Windows")
def test_data_dir_is_hidden(isolated_home):
    import ctypes
    attributes = ctypes.windll.kernel32.GetFileAttributesW(str(data_dir()))
    assert attributes & data_dir_module.FILE_ATTRIBUTE_HIDDEN


def test_legacy_data_dir_is_renamed(isolated_home):
    legacy = isolated_home / ".rout_art_cms"
    legacy.mkdir()
    (legacy / "config.json").write_text("{}", encoding="utf-8")
    path = data_dir()
    assert (path / "config.json").exists() and not legacy.exists()


def test_lock_file_refuses_writes_but_allows_reading_and_deleting(tmp_path):
    target = tmp_path / "auth.json"
    target.write_text("secret", encoding="utf-8")
    assert lock_file(target)
    with pytest.raises(PermissionError):
        target.write_text("modifié", encoding="utf-8")
    assert target.read_text(encoding="utf-8") == "secret"
    unlock_file(target)
    target.write_text("modifié", encoding="utf-8")
    lock_file(target)
    target.unlink()  # Procédure en cas de mot de passe oublié
    assert not target.exists()


def test_lock_missing_file_is_harmless(tmp_path):
    assert lock_file(tmp_path / "absent.json") is False
    unlock_file(tmp_path / "absent.json")


# ======= Configuration =======

def test_first_launch_config_is_complete(isolated_home):
    """Corrigé en v2.0.7 : sans config.json, get_all_config() ne renvoyait que le premier réglage enregistré"""
    config = ConfigManager()
    config.set_repo_path(str(isolated_home / "site"))
    values = config.get_all_config()
    assert set(values) == {"repo_path", "site_url", "auto_pull", "show_guide", "default_port"}
    assert values["default_port"] == 8000 and values["repo_path"] == str(isolated_home / "site")


def test_config_is_saved_and_reloaded(isolated_home):
    config = ConfigManager()
    config.set_site_url("  https://exemple.fr/  ")
    config.set_auto_pull(True)
    config.set_show_guide(False)
    config.set_default_port(8123)
    reloaded = ConfigManager()
    assert reloaded.get_site_url() == "https://exemple.fr/"
    assert reloaded.get_auto_pull() is True and reloaded.get_show_guide() is False
    assert reloaded.get_default_port() == 8123


@pytest.mark.parametrize("port", [0, 70000])
def test_invalid_port_is_refused(isolated_home, port):
    with pytest.raises(ValueError):
        ConfigManager().set_default_port(port)


def test_invalid_and_obsolete_keys_are_dropped(isolated_home):
    config_file = data_dir() / "config.json"
    config_file.write_text(json.dumps({"default_port": "abc", "theme": "dark", "auto_pull": True}), encoding="utf-8")
    config = ConfigManager()
    assert config.get_default_port() == 8000 and config.get_auto_pull() is True
    assert "theme" not in json.loads(config_file.read_text(encoding="utf-8"))


def test_corrupted_config_falls_back_to_defaults(isolated_home):
    (data_dir() / "config.json").write_text("{pas du json", encoding="utf-8")
    assert ConfigManager().get_all_config()["default_port"] == 8000


def test_reset_to_defaults(isolated_home):
    config = ConfigManager()
    config.set_default_port(9000)
    config.reset_to_defaults()
    assert config.get_default_port() == 8000 and ConfigManager().get_default_port() == 8000


# ======= Journal =======

def test_logger_keeps_messages_and_writes_file(isolated_home):
    logger = Logger(max_logs=2)
    for message in ("un", "deux", "trois"):
        logger.log(message)
    logs = logger.get_logs()
    assert len(logs) == 2 and logs[-1].endswith("[INFO] trois")
    assert "un" in (data_dir() / "app.log").read_text(encoding="utf-8")
    logger.clear_logs()
    assert logger.get_logs() == []


def test_logger_survives_non_utf8_console(isolated_home, monkeypatch):
    """Les emojis plantaient sur une console non UTF-8 : le logger doit s'en protéger"""
    calls = []

    def fake_print(text):
        calls.append(text)
        if len(calls) == 1:
            raise UnicodeEncodeError("charmap", text, 0, 1, "console non UTF-8")

    monkeypatch.setattr("builtins.print", fake_print)
    Logger().log("✓ Push réussi 🎉")
    assert len(calls) == 2 and calls[1].isascii()
