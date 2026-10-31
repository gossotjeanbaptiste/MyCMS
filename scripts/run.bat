@echo off
REM Script de lancement pour Windows - MyCMS
setlocal enabledelayedexpansion
REM Racine du depot : le dossier du script, ou son parent (script range dans scripts\ ou remis a la racine)
cd /d "%~dp0"
if not exist "cms\web\server.py" cd ..
if not exist "cms\web\server.py" (
    echo Erreur: racine de MyCMS introuvable. Placez ce script a la racine du depot ou dans scripts\
    pause
    exit /b 1
)

echo.
echo MyCMS
echo =====
echo.

REM Verifier si Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo Erreur: Python n'est pas trouve
    echo Installez Python 3.9+ depuis https://www.python.org
    pause
    exit /b 1
)

echo OK - Python trouve

REM Verifier si les dependances sont installees : toutes, pas seulement Flask
REM (une dependance ajoutee plus tard, comme pystray pour l'icone de notification, serait sinon oubliee)
python -c "import importlib.util as u, sys; sys.exit(any(u.find_spec(m) is None for m in ('flask', 'waitress', 'bs4', 'git', 'pystray', 'PIL')))" >nul 2>&1
if errorlevel 1 (
    echo Installation des dependances...
    python -m pip install -r cms\requirements.txt
    if errorlevel 1 (
        echo Erreur lors de l'installation
        pause
        exit /b 1
    )
)

echo OK - Dependances pres
echo.
echo Lancement de l'application...
echo.

python cms/web/server.py

if errorlevel 1 (
    echo L'application s'est terminee avec une erreur
    pause
)
