#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour compiler l'application en .exe avec PyInstaller
À exécuter après avoir installé les dépendances de compilation : pip install -r cms/requirements-build.txt
"""

import subprocess
import sys
from pathlib import Path
import shutil
import os


def kill_exe_process():
    """Tuer les processus de l'exécutable CMS s'il est en cours d'exécution"""
    try:
        subprocess.run(
            ['taskkill', '/IM', "MyCMS.exe", '/F'],
            capture_output=True,
            timeout=5
        )
        print("🛑 Processus de l'application fermé")
    except Exception:  # Pas en cours d'utilisation
        pass


def check_pyinstaller():
    """Vérifier que PyInstaller est installé"""
    try:
        import PyInstaller
        print(f"✅ PyInstaller trouvé: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller n'est pas installé!")
        print("Installez-le avec: pip install -r cms/requirements-build.txt")
        return False


def build_css(project_root):
    """Recompiler le CSS Tailwind de l'interface web (sinon le style.css versionné est utilisé)"""
    web_dir = project_root / "cms" / "web"
    npm = shutil.which("npm")
    if not npm:
        print("⚠️  npm introuvable : le CSS déjà compilé (cms/web/static/style.css) sera utilisé")
        return
    try:
        if not (web_dir / "node_modules").exists():
            print("📦 Installation de Tailwind (npm install)...")
            subprocess.check_call([npm, "install"], cwd=web_dir)
        print("🎨 Compilation du CSS Tailwind...")
        subprocess.check_call([npm, "run", "build:css"], cwd=web_dir)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Compilation du CSS impossible ({e}) : le CSS déjà compilé sera utilisé")


def compile_to_exe(dist_dir=None):
    """Compiler l'application en .exe, dans dist/ ou dans dist_dir (dossier temporaire de l'installeur).
    Retourne le chemin de l'exécutable, ou False en cas d'erreur"""
    if not check_pyinstaller():
        return False
    build_css(Path(__file__).parent.parent.parent)
    print("\n🛑 Vérification de l'application en cours d'exécution...\n")
    kill_exe_process()
    print("\n🔨 Compilation en cours...\n")
    # Le répertoire parent du script est cms/installer, on doit remonter à la racine du projet
    source_dir = Path(__file__).parent
    project_root = source_dir.parent.parent
    spec_file = source_dir / "mycms.spec"
    try:
        # Nettoyer les anciens builds et dist à la racine du projet
        build_dir = project_root / "build"
        for_installer = dist_dir is not None
        dist_dir = Path(dist_dir) if for_installer else project_root / "dist"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            print("🗑️  Dossier build supprimé")
        if dist_dir.exists():
            try:
                shutil.rmtree(dist_dir)
                print("🗑️  Dossier dist supprimé")
            except Exception as e:
                print(f"⚠️  Impossible de supprimer dist: {e}")
        original_cwd = os.getcwd()
        os.chdir(project_root)
        try:
            # Compiler
            subprocess.check_call([
                sys.executable,
                "-m",
                "PyInstaller",
                str(spec_file),
                "--noconfirm",
                "--distpath", str(dist_dir),
            ])
        finally:
            os.chdir(original_cwd)
        if build_dir.exists():
            shutil.rmtree(build_dir)
            print("🧹 Dossier build supprimé")
        exe_path = dist_dir / "MyCMS.exe"
        print("\n✅ Compilation de l'exécutable réussie!")
        if not for_installer:
            print(f"\n📦 L'exécutable se trouve dans: {exe_path}")
            print("\n🎉 Vous pouvez maintenant distribuer ce fichier .exe!")
        return exe_path
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors de la compilation: {e}")
        return False


if __name__ == "__main__":
    # Sortie redirigée ou console non UTF-8 : remplacer les emojis au lieu de planter
    sys.stdout.reconfigure(errors="replace")
    success = compile_to_exe()
    sys.exit(0 if success else 1)
