#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour compiler l'installeur Windows (.msi) de MyCMS :
l'exécutable PyInstaller et un Git portable (MinGit), pour un poste sans rien d'installé.
Nécessite le SDK .NET (https://dotnet.microsoft.com/download) : WiX est récupéré par dotnet build.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from build_exe import compile_to_exe

# Git portable embarqué : version fixée et vérifiée par son empreinte SHA-256 (publiée par Git for Windows)
MINGIT_VERSION = "2.56.0.2"
MINGIT_URL = ("https://github.com/git-for-windows/git/releases/download/"
              "v2.56.0.windows.2/MinGit-2.56.0.2-64-bit.zip")
MINGIT_SHA256 = "da35e72aa21c005a5a0d298cfbae110bc1609a815730ea0dde84b01a1b3cd3be"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INSTALLER_DIR = PROJECT_ROOT / "cms" / "installer"
CACHE_DIR = INSTALLER_DIR / "cache"


def product_version():
    """Version de l'application (celle de cms/web/package.json)"""
    with open(PROJECT_ROOT / "cms" / "web" / "package.json", encoding="utf-8") as f:
        return json.load(f)["version"]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_mingit():
    """Télécharger MinGit (une seule fois, gardé dans cms/installer/cache) et l'extraire"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    archive = CACHE_DIR / f"MinGit-{MINGIT_VERSION}-64-bit.zip"
    if not archive.exists() or sha256(archive) != MINGIT_SHA256:
        print(f"📥 Téléchargement de MinGit {MINGIT_VERSION}...")
        partial = archive.with_suffix(".part")
        urllib.request.urlretrieve(MINGIT_URL, partial)
        if sha256(partial) != MINGIT_SHA256:
            partial.unlink()
            raise RuntimeError("Empreinte SHA-256 de MinGit incorrecte : téléchargement refusé")
        partial.replace(archive)
    else:
        print(f"✅ MinGit {MINGIT_VERSION} déjà téléchargé")

    git_dir = CACHE_DIR / f"MinGit-{MINGIT_VERSION}"
    if git_dir.exists():
        shutil.rmtree(git_dir)
    with zipfile.ZipFile(archive) as z:
        z.extractall(git_dir)
    return git_dir


def compile_to_msi():
    """Compiler l'exécutable puis l'installeur .msi"""
    dotnet = shutil.which("dotnet")
    if not dotnet:
        print("❌ Le SDK .NET est introuvable (commande dotnet)")
        print("Installez-le depuis https://dotnet.microsoft.com/download puis relancez")
        return False

    # L'exécutable n'est qu'une étape : compilé dans un dossier temporaire, seul le .msi va dans dist/
    exe_path = compile_to_exe(INSTALLER_DIR / "obj" / "exe")
    if not exe_path:
        return False

    try:
        git_dir = prepare_mingit()
    except Exception as e:
        print(f"\n❌ Impossible de préparer MinGit: {e}")
        return False

    version = product_version()
    print(f"\n📦 Compilation de l'installeur MyCMS {version}...\n")
    try:
        subprocess.check_call([
            dotnet, "build", str(INSTALLER_DIR / "MyCMS.wixproj"),
            "-c", "Release",
            f"-p:ProductVersion={version}",
            f"-p:ExeFile={exe_path}",
            f"-p:GitDir={git_dir}",
            f"-p:IconFile={PROJECT_ROOT / 'cms' / 'icon' / 'logo.ico'}",
        ])
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors de la compilation de l'installeur: {e}")
        return False

    built = next((INSTALLER_DIR / "bin").rglob("MyCMS.msi"))
    dist_dir = PROJECT_ROOT / "dist"
    shutil.rmtree(dist_dir, ignore_errors=True)  # Anciens .exe et .msi
    dist_dir.mkdir()
    msi_path = dist_dir / f"MyCMS-{version}.msi"
    shutil.copy2(built, msi_path)
    for folder in ("bin", "obj"):
        shutil.rmtree(INSTALLER_DIR / folder, ignore_errors=True)

    print("\n✅ Installeur créé!")
    print(f"\n📦 L'installeur se trouve dans: {msi_path}")
    print("\n🎉 Il installe MyCMS et Git : rien d'autre à installer sur le poste.")
    return True


if __name__ == "__main__":
    # Sortie redirigée ou console non UTF-8 : remplacer les emojis au lieu de planter
    sys.stdout.reconfigure(errors="replace")
    success = compile_to_msi()
    sys.exit(0 if success else 1)
