@echo off
chcp 65001 >nul
title Gestionale Contabilita Francesco
color 0A

echo ============================================================
echo    GESTIONALE CONTABILITA FRANCESCO - Avvio locale
echo ============================================================
echo.

REM --- 1. Verifica file secrets.toml ---
if exist ".streamlit\secrets.toml" (
    echo [1/3] File secrets.toml trovato.
) else (
    echo [1/3] ATTENZIONE: file .streamlit\secrets.toml non trovato.
    echo    L'app potrebbe non connettersi a Supabase.
    echo    Crea il file .streamlit\secrets.toml con SUPABASE_URL e SUPABASE_KEY.
    echo.
)

REM --- 2. Verifica dipendenze ---
echo [2/3] Verifica dipendenze Python...
python -c "import streamlit, supabase, dotenv, pandas" >nul 2>&1
if errorlevel 1 goto install_deps
echo    Dipendenze gia presenti.
goto deps_done

:install_deps
echo    Dipendenze mancanti. Installazione in corso...
python -m pip install -r requirements.txt
if errorlevel 1 goto install_error
echo    Dipendenze installate.
goto deps_done

:install_error
echo    Errore durante l'installazione delle dipendenze.
pause
exit /b 1

:deps_done

REM --- 3. Avvia l'app ---
echo [3/3] Avvio dell'app Streamlit...
echo.
echo    Apri il browser all'indirizzo: http://localhost:8501
echo    Premi Ctrl+C nella finestra per fermare l'app.
echo.
python -m streamlit run "contabilita_francesco\app.py" --server.headless true

echo.
echo App terminata.
pause
