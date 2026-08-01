@echo off
chcp 65001 >nul
title Gestionale Contabilita Francesco
color 0A

echo ============================================================
echo    GESTIONALE CONTABILITA FRANCESCO - Avvio locale
echo ============================================================
echo.

REM --- Imposta ambiente ---
set APP_ENV=dev

REM --- Avvia l'app tramite run_local.py (gestisce encoding e dipendenze) ---
python run_local.py

echo.
echo App terminata.
pause
