"""
Avvio locale del Gestionale Contabilità Francesco.

Questo script:
  1. Verifica che le dipendenze siano installate (e le installa se mancano).
  2. Verifica la presenza delle credenziali Supabase (.env o .streamlit/secrets.toml).
  3. Avvia l'app Streamlit in locale.

Uso:
    python run_local.py
"""

import os
import subprocess
import sys
import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_PATH = BASE_DIR / "contabilita_francesco" / "app.py"
ENV_PATH = BASE_DIR / ".env"
SECRETS_PATH = BASE_DIR / ".streamlit" / "secrets.toml"

REQUIRED_PACKAGES = ["streamlit", "supabase", "python-dotenv", "pandas", "httpx", "python-dateutil"]


def check_dependencies():
    """Verifica che i pacchetti richiesti siano installati."""
    mancanti = []
    for pkg in REQUIRED_PACKAGES:
        if importlib.util.find_spec(pkg) is None:
            mancanti.append(pkg)
    return mancanti


def install_dependencies(pacchetti):
    """Installa i pacchetti mancanti tramite pip."""
    print("📦 Installazione delle dipendenze mancanti...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(BASE_DIR / "requirements.txt")])


def check_credentials():
    """Verifica la presenza delle credenziali Supabase."""
    if ENV_PATH.exists():
        return True, "env"
    if SECRETS_PATH.exists():
        return True, "secrets"
    return False, None


def create_env_template():
    """Crea un file .env.example come riferimento."""
    example = BASE_DIR / ".env.example"
    if not example.exists():
        example.write_text(
            "# Credenziali Supabase\n"
            "# Copia questo file in '.env' e inserisci i tuoi valori.\n"
            "SUPABASE_URL=https://TUO_PROGETTO.supabase.co\n"
            "SUPABASE_KEY=la_tua_chiave_anon\n",
            encoding="utf-8",
        )
        print("ℹ️  Creato il file di esempio '.env.example'.")


def main():
    print("=" * 55)
    print("   💶 GESTIONALE CONTABILITÀ FRANCESCO — Avvio locale")
    print("=" * 55)

    # 1. Verifica dipendenze
    print("\n[1/3] Verifica dipendenze...")
    mancanti = check_dependencies()
    if mancanti:
        print(f"   ⚠️  Pacchetti mancanti: {', '.join(mancanti)}")
        try:
            install_dependencies(mancanti)
            print("   ✅ Dipendenze installate.")
        except Exception as e:
            print(f"   ❌ Errore durante l'installazione: {e}")
            print("   Prova manualmente: pip install -r requirements.txt")
            sys.exit(1)
    else:
        print("   ✅ Tutte le dipendenze sono presenti.")

    # 2. Verifica credenziali
    print("\n[2/3] Verifica credenziali Supabase...")
    ok, tipo = check_credentials()
    if not ok:
        print("   ❌ Credenziali Supabase non trovate!")
        print("   Per avviare l'app devi configurare le credenziali.")
        print()
        print("   Opzione A — File .env (consigliato):")
        print("     1. Crea un file '.env' nella root del progetto")
        print("     2. Inserisci:")
        print("        SUPABASE_URL=https://TUO_PROGETTO.supabase.co")
        print("        SUPABASE_KEY=la_tua_chiave_anon")
        print()
        print("   Opzione B — Streamlit secrets:")
        print("     1. Crea il file '.streamlit/secrets.toml'")
        print("     2. Inserisci:")
        print("        SUPABASE_URL = \"https://TUO_PROGETTO.supabase.co\"")
        print("        SUPABASE_KEY = \"la_tua_chiave_anon\"")
        print()
        create_env_template()
        sys.exit(1)
    print(f"   ✅ Credenziali trovate ({tipo}).")

    # 3. Avvia l'app
    print("\n[3/3] Avvio dell'app Streamlit...")
    print("   🌐 Apri il browser all'indirizzo mostrato (di solito http://localhost:8501)")
    print("   Premi Ctrl+C per fermare l'app.\n")

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(APP_PATH),
        "--server.headless", "true",
    ]
    try:
        subprocess.run(cmd, cwd=str(BASE_DIR))
    except KeyboardInterrupt:
        print("\n👋 App fermata.")


if __name__ == "__main__":
    main()
