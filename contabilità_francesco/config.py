"""Configurazione dell'applicazione: secrets, ambiente, costanti e modalità DEMO."""
import os
import tomllib
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─── Modalità DEMO ─────────────────────────────────────────
# Se APP_DEMO=1 (o "true"/"yes") l'app usa dati fittizi in memoria
# e NON tocca il database reale. Utile per demo di vendita.
DEMO_MODE = os.getenv("APP_DEMO", "").strip().lower() in ("1", "true", "yes", "demo")


def get_secret(key):
    """Legge un segreto da st.secrets senza sollevare errori se il file non esiste."""
    try:
        return st.secrets.get(key)
    except Exception:
        return None


def carica_secrets_ambiente():
    """
    Carica le credenziali in base all'ambiente.
    - APP_ENV=dev  -> usa dev_secrets.toml (dati reali)
    - default      -> usa .streamlit/secrets.toml (se presente) oppure .env
    """
    ambiente = os.getenv("APP_ENV", "").strip().lower()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if ambiente == "dev":
        percorso = os.path.join(os.path.dirname(base_dir), "dev_secrets.toml")
        if os.path.exists(percorso):
            with open(percorso, "rb") as f:
                return tomllib.load(f)

    # Fallback: usa st.secrets (da .streamlit/secrets.toml) o .env
    return {}


secrets_ambiente = carica_secrets_ambiente()

SUPABASE_URL = (
    secrets_ambiente.get("SUPABASE_URL")
    or get_secret("SUPABASE_URL")
    or os.getenv("SUPABASE_URL")
)
SUPABASE_KEY = (
    secrets_ambiente.get("SUPABASE_KEY")
    or get_secret("SUPABASE_KEY")
    or os.getenv("SUPABASE_KEY")
)

# ─── Percorsi ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "ricevute_uploads")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# ─── Costanti ──────────────────────────────────────────────
RICORRENZE = ["Nessuna", "Settimanale", "Quindicinale", "Mensile", "Bimestrale", "Trimestrale", "Semestrale", "Annuale"]
CANALI_PRENOTAZIONE = ["Diretto", "Booking", "Airbnb", "Expedia", "Altro"]
STATI_PRENOTAZIONE = ["Confermata", "In corso", "Completata", "Cancellata"]
STORAGE_BUCKET = "ricevute"

APP_VERSION = "3.1"
APP_NOME = "Gestionale Contabilità"
APP_SOTTOTITOLO = "Francesco"

# ─── Backup automatico ─────────────────────────────────────
BACKUP_INTERVAL_GIORNI = 7  # Backup automatico ogni 7 giorni


