@echo off
title Echecs P2P Pro - Stockfish 19
chcp 65001 >nul
cls
echo ======================================================================
echo                  ÉCHECS P2P PRO — STOCKFISH 19 EDITION
echo ======================================================================
echo.

:: Vérifier si Python est présent
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ATTENTION] Python n'a pas été détecté sur votre système Windows !
    echo.
    echo Pour jouer, vous pouvez soit :
    echo 1. Installer Python 3 depuis : https://www.python.org/downloads/
    echo    (Cochez bien la case "Add python.exe to PATH" lors de l'installation)
    echo 2. Ou lancer directement EchecsP2P.exe
    echo.
    pause
    exit /b 1
)

:: Installation / vérification des dépendances nécessaires
echo [1/2] Vérification des modules Python requis...
pip install -r requirements.txt >nul 2>&1

:: Lancement du jeu
echo [2/2] Lancement du jeu d'échecs en cours...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [INFO] Le jeu s'est arrêté avec un code de retour.
    pause
)
