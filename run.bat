@echo off
REM Script de lancement pour Windows - Rout'Art CMS
setlocal enabledelayedexpansion

echo.
echo Rout'Art CMS
echo ============
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

REM Verifier si les dependances sont installees
python -c "import flask" >nul 2>&1
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
