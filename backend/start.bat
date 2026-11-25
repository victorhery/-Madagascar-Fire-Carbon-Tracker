@echo off
REM Double-clic pour démarrer toute la plateforme : API + polling FIRMS +
REM estimations MODIS/Sentinel-2 + alertes. Tout tourne dans ce seul
REM processus (voir app/core/scheduling.py) -> pas d'autre terminal requis.
REM Pour arrêter : fermer cette fenêtre, ou Ctrl+C.

cd /d "%~dp0"

if not exist venv (
    echo [ERREUR] Environnement virtuel introuvable ^(dossier venv^).
    echo Lancer d'abord : python -m venv venv puis venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Démarrage de la plateforme Madagascar FireCarbon Tracker...
echo Dashboard backend accessible sur http://127.0.0.1:8000
echo Documentation API : http://127.0.0.1:8000/docs
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
