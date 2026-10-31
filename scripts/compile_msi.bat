@echo off
REM Installeur de MyCMS : exe puis .msi dans dist\ (necessite le SDK .NET)
setlocal
REM Racine du depot : le dossier du script, ou son parent (script range dans scripts\ ou remis a la racine)
cd /d "%~dp0"
if not exist "cms\web\server.py" cd ..
if not exist "cms\web\server.py" (
    echo Erreur: racine de MyCMS introuvable. Placez ce script a la racine du depot ou dans scripts\
    pause
    exit /b 1
)
python cms\installer\build_msi.py
echo Appuyez sur une touche pour fermer le terminal
pause
