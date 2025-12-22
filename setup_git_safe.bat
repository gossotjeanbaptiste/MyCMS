@echo off
REM Script pour configurer le répertoire courant comme git safe directory
REM Fonctionne peu importe le répertoire où le script est exécuté

setlocal enabledelayedexpansion

REM Obtenir le répertoire complet du fichier batch
set "SCRIPT_DIR=%~dp0"
REM Supprimer le backslash final s'il existe
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

@echo.
@echo ========================================
@echo Git Safe Directory Configuration
@echo ========================================
@echo.
@echo Repertoire cible: %SCRIPT_DIR%
@echo.

REM Exécuter la commande git
git config --global --add safe.directory "%SCRIPT_DIR%"

if %errorlevel% equ 0 (
    @echo.
    @echo Repertoire ajoute avec succes comme safe directory
    @echo.
    REM Vérifier la configuration
    @echo Verification:
    git config --global --get safe.directory
    @echo.
) else (
    @echo.
    @echo  Erreur lors de l'ajout du répertoire
    @echo Code d'erreur: %errorlevel%
    @echo.
)

pause
