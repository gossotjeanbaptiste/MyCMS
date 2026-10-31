@echo off
REM Tests de MyCMS : Python (pytest) puis interface (node --test)
REM Double-clic, ou depuis un terminal : scripts\run_tests.bat [options de pytest, ex. -k editor]
REM Pour inclure une copie du vrai site : set MYCMS_SITE=C:\chemin\du\site avant de lancer
setlocal
REM Racine du depot : le dossier du script, ou son parent (script range dans scripts\ ou remis a la racine)
cd /d "%~dp0"
if not exist "cms\web\server.py" cd ..
if not exist "cms\web\server.py" (
    echo Erreur: racine de MyCMS introuvable. Placez ce script a la racine du depot ou dans scripts\
    pause
    exit /b 1
)

REM Lancé par un double-clic : la fenêtre reste ouverte à la fin pour lire le résultat
set "DOUBLE_CLICK="
echo %cmdcmdline% | find /i "%~0" >nul && set "DOUBLE_CLICK=1"

python -c "import pytest" >nul 2>&1 || python -m pip install -r cms\requirements-dev.txt || goto :error
if not exist cms\web\node_modules\jsdom (
    pushd cms\web
    call npm install || (popd & goto :error)
    popd
)

echo.
echo === Tests Python ===
python -m pytest -v %* || goto :error

echo.
echo === Tests de l'interface ===
pushd cms\web
call npm test || (popd & goto :error)
popd

echo.
echo Tous les tests sont passes.
if defined DOUBLE_CLICK pause
exit /b 0

:error
echo.
echo Des tests ont echoue.
if defined DOUBLE_CLICK pause
exit /b 1
