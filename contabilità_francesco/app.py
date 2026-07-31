import streamlit as st
import pandas as pd
import os
import shutil
import json
import io
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from supabase import create_client, Client
from dotenv import load_dotenv
from payment_methods import METODI_PAGAMENTO, normalizza_metodo_pagamento

load_dotenv()

def get_secret(key):
    """Legge un segreto da st.secrets senza sollevare errori se il file non esiste."""
    try:
        return st.secrets.get(key)
    except Exception:
        return None

SUPABASE_URL = get_secret("SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Credenziali Supabase non trovate! Crea un file .env o configura i secrets.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="Contabilità Francesco",
    page_icon=":material/euro_symbol:",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "ricevute_uploads")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

RICORRENZE = ["Nessuna", "Settimanale", "Quindicinale", "Mensile", "Bimestrale", "Trimestrale", "Semestrale", "Annuale"]

# ─── Supabase Storage ──────────────────────────────────────
STORAGE_BUCKET = "ricevute"
SUPABASE_STORAGE_URL = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}"

def upload_ricevuta_storage(file_obj, nome_file):
    """Carica una ricevuta su Supabase Storage e restituisce il nome salvato."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_pulito = "".join([c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in nome_file])
    nome_salvato = f"{timestamp}_{nome_pulito}"
    try:
        supabase.storage.from_(STORAGE_BUCKET).upload(
            nome_salvato,
            file_obj.read(),
            {"content-type": "application/octet-stream"}
        )
        return nome_salvato
    except Exception as e:
        # Create subdirectories based on date
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_part = timestamp[:8]  # YYYYMMDD
        year = date_part[:4]
        month = date_part[4:6]
        local_dir = os.path.join(UPLOAD_DIR, year, month)
        os.makedirs(local_dir, exist_ok=True)
        percorso = os.path.join(local_dir, nome_salvato)
        with open(percorso, "wb") as f:
            f.write(file_obj.getvalue() if hasattr(file_obj, 'getvalue') else file_obj.read())
        return nome_salvato

def get_ricevuta_url(nome_file):
    if not nome_file:
        return None
    return f"{SUPABASE_STORAGE_URL}/{nome_file}"

def scarica_ricevuta(nome_file):
    try:
        resp = supabase.storage.from_(STORAGE_BUCKET).download(nome_file)
        return resp
    except Exception:
        percorso = os.path.join(UPLOAD_DIR, nome_file)
        if os.path.exists(percorso):
            with open(percorso, "rb") as f:
                return f.read()
        return None

# ─── LOGIN (automatico: legge tutti i LOGIN_USERNAME* dai secrets) ──
UTENTI = {}
try:
    for key, value in st.secrets.items():
        if key.startswith("LOGIN_USERNAME"):
            suffix = key.replace("LOGIN_USERNAME", "")
            password_key = f"LOGIN_PASSWORD{suffix}"
            password = st.secrets.get(password_key, "")
            if value and password:
                UTENTI[value] = password
except Exception:
    pass
if not UTENTI:
    UTENTI = {"admin": "admin"}

if "autenticato" not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.utente = ""

def mostra_login():
    st.markdown("""
        <div style='text-align: center; padding: 3rem 0 1rem 0;'>
            <div style='font-size: 4rem;'>💶</div>
            <h1 style='color: #1E40AF; margin: 0.5rem 0; font-size: 1.8rem; font-weight: 700;'>
                Gestionale Contabilità
            </h1>
            <p style='color: #64748B; margin: 0 0 1.5rem 0; font-size: 1rem;'>
                Francesco
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True, width="content"):
        st.markdown("#### :material/lock: Accesso riservato")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Inserisci username...")
            password = st.text_input("Password", type="password", placeholder="Inserisci password...")
            if st.form_submit_button(":material/login: Accedi", use_container_width=True, type="primary"):
                if username in UTENTI and UTENTI[username] == password:
                    st.session_state.autenticato = True
                    st.session_state.utente = username
                    st.rerun()
                else:
                    st.error(":material/error: Username o password errati!")
    
    st.caption("Contabilità Francesco v2.0")

if not st.session_state.autenticato:
    mostra_login()
    st.stop()

# ─── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 0.5rem 0;'>
            <div style='font-size: 2.5rem;'>💶</div>
            <div style='font-weight: 600; font-size: 1.1rem; color: #F8FAFC;'>Contabilità</div>
            <div style='font-size: 0.85rem; color: #94A3B8;'>Francesco</div>
        </div>
    """, unsafe_allow_html=True)
    st.space("small")
    
    pagina = st.radio(
        "Navigazione",
        ["Nuova registrazione", "Prenotazioni & Ospiti", "Scadenzario & Promemoria", "Resoconto & analisi", "Archivio ricevute", "Archivio pagamenti", "Gestione categorie", "Backup & Ripristino"],
        captions=["Aggiungi un movimento", "Gestisci prenotazioni e ospiti", "Gestisci scadenze e promemoria", "Vedi entrate/uscite/grafici", "Visualizza e cerca ricevute", "Storico completo pagamenti", "Modifica le voci contabili", "Salva e ripristina i dati"],
        label_visibility="collapsed",
        key="nav"
    )
    
    st.space("large")
    if st.button(":material/logout: Esci", use_container_width=True):
        st.session_state.autenticato = False
        st.rerun()
    st.caption(f"App v2.0 • {datetime.now().year}")
    st.caption("Dati su Supabase ☁️")

# ─── Funzioni DB ───────────────────────────────────────────
def init_db():
    anno_corrente = datetime.now().year
    categorie_iniziali = [
        ('Entrata', 'Fatturato / Vendite'),
        ('Entrata', 'Prestazione Servizi'),
        ('Entrata', 'Altro (Entrata)'),
        ('Uscita', 'Affitto'),
        ('Uscita', 'Stipendi'),
        ('Uscita', 'Bollette luce gas appartamenti'),
        ('Uscita', 'ufficio'),
        ('Uscita', 'casa'),
        ('Uscita', 'f24 : rateizzazione tasse 2025'),
        ('Uscita', 'f24 : rateizzazione tasse 2026'),
        ('Uscita', f'f24 : rateizzazione tasse {anno_corrente}'),
        ('Uscita', f'f24 : rateizzazione tasse {anno_corrente + 1}'),
        ('Uscita', 'Tasse di soggiorno'),
        ('Uscita', 'Internet'),
        ('Uscita', 'Booking - idealista - segreteria.it - immobiliare.it'),
        ('Uscita', 'pulizia nolmar / tutto igiene / Verona lux / Albanese group'),
        ('Uscita', 'Commercialista a tempora'),
        ('Uscita', 'Altro (Uscita)')
    ]
    for tipo, nome in categorie_iniziali:
        try:
            existing = supabase.table("categorie").select("id").eq("nome", nome).execute()
            if not existing.data:
                supabase.table("categorie").insert({"tipo": tipo, "nome": nome}).execute()
        except Exception:
            pass

try:
    init_db()
except Exception:
    pass

def aggiungi_transazione(data, tipo, voce, importo, metodo_pagamento, persona, descrizione, ricevuta_file):
    ricevuta_nome = None
    ricevuta_percorso = None
    if ricevuta_file is not None:
        nome_salvato = upload_ricevuta_storage(ricevuta_file, ricevuta_file.name)
        ricevuta_nome = ricevuta_file.name
        ricevuta_percorso = nome_salvato
    metodo_pagamento = normalizza_metodo_pagamento(metodo_pagamento)
    data_inserimento = {
        "data": data, "tipo": tipo, "voce": voce, "importo": importo,
        "metodo_pagamento": metodo_pagamento,
        "persona": persona if persona else None,
        "descrizione": descrizione if descrizione else None,
        "ricevuta_nome": ricevuta_nome, "ricevuta_percorso": ricevuta_percorso
    }
    response = supabase.table("transazioni").insert(data_inserimento).execute()
    if hasattr(response, 'error') and response.error:
        st.error(f"Errore: {response.error}")
        return False
    return True

def ottieni_transazioni(data_inizio=None, data_fine=None):
    query = supabase.table("transazioni").select("*")
    if data_inizio and data_fine:
        query = query.gte("data", data_inizio).lte("data", data_fine)
    elif data_inizio:
        query = query.gte("data", data_inizio)
    elif data_fine:
        query = query.lte("data", data_fine)
    query = query.order("data", desc=True).order("id", desc=True)
    response = query.execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame()

def elimina_transazione(id_transazione, percorso_ricevuta):
    if percorso_ricevuta:
        try:
            supabase.storage.from_(STORAGE_BUCKET).remove([percorso_ricevuta])
        except Exception:
            pass
        percorso_locale = os.path.join(UPLOAD_DIR, percorso_ricevuta)
        if os.path.exists(percorso_locale):
            try:
                os.remove(percorso_locale)
            except Exception:
                pass
    supabase.table("transazioni").delete().eq("id", id_transazione).execute()

def ottieni_categorie(tipo=None):
    query = supabase.table("categorie").select("nome")
    if tipo:
        query = query.eq("tipo", tipo)
    query = query.order("nome")
    response = query.execute()
    if response.data:
        return [row['nome'] for row in response.data]
    return []

def aggiungi_categoria(tipo, nome):
    nome = nome.strip()
    if not nome:
        return False, "Il nome non può essere vuoto"
    try:
        existing = supabase.table("categorie").select("id").eq("nome", nome).execute()
        if existing.data:
            return False, "Categoria già esistente."
        supabase.table("categorie").insert({"tipo": tipo, "nome": nome}).execute()
        return True, f"Categoria '{nome}' aggiunta!"
    except Exception as e:
        return False, f"Errore: {str(e)}"

# ─── Funzioni Prenotazioni & Ospiti ────────────────────────
CANALI_PRENOTAZIONE = ["Diretto", "Booking", "Airbnb", "Expedia", "Altro"]
STATI_PRENOTAZIONE = ["Confermata", "In corso", "Completata", "Cancellata"]

def ottieni_prenotazioni(stato=None):
    try:
        query = supabase.table("prenotazioni").select("*")
        if stato:
            query = query.eq("stato", stato)
        query = query.order("check_in", desc=False)
        response = query.execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception:
        pass
    return pd.DataFrame()

def aggiungi_prenotazione(ospite, check_in, check_out, camera, canale, importo, commissione, tassa_soggiorno, note):
    ospite = ospite.strip()
    if not ospite:
        return False, "Il nome dell'ospite è obbligatorio."
    if check_out <= check_in:
        return False, "La data di check-out deve essere successiva al check-in."
    
    pernottamenti = (check_out - check_in).days
    if pernottamenti <= 0:
        return False, "Il numero di pernottamenti deve essere almeno 1."
    
    data_inserimento = {
        "ospite": ospite,
        "check_in": str(check_in),
        "check_out": str(check_out),
        "pernottamenti": pernottamenti,
        "camera": camera.strip() if camera else "",
        "canale": canale,
        "importo": importo,
        "commissione": commissione,
        "tassa_soggiorno": tassa_soggiorno,
        "stato": "Confermata",
        "note": note.strip() if note else "",
        "registrata_contabilita": False
    }
    try:
        response = supabase.table("prenotazioni").insert(data_inserimento).execute()
        return True, f"Prenotazione registrata per {ospite} ({pernottamenti} notti)!"
    except Exception as e:
        return False, f"Errore durante l'inserimento: {str(e)}"

def aggiorna_stato_prenotazione(id_prenotazione, nuovo_stato):
    try:
        supabase.table("prenotazioni").update({"stato": nuovo_stato}).eq("id", id_prenotazione).execute()
        return True
    except Exception:
        return False

def elimina_prenotazione(id_prenotazione):
    try:
        supabase.table("prenotazioni").delete().eq("id", id_prenotazione).execute()
        return True
    except Exception:
        return False

def registra_prenotazione_contabilita(prenotazione_row, data_pagamento, metodo_pagamento):
    """
    Registra l'importo della prenotazione come entrata in 'transazioni'.
    Se la prenotazione ha una tassa di soggiorno, la registra come uscita separata.
    """
    data_str = str(data_pagamento)
    metodo = normalizza_metodo_pagamento(metodo_pagamento)
    ospite = prenotazione_row.get("ospite", "")
    canale = prenotazione_row.get("canale", "Diretto")
    importo = float(prenotazione_row.get("importo", 0))
    commissione = float(prenotazione_row.get("commissione", 0))
    tassa = float(prenotazione_row.get("tassa_soggiorno", 0))
    
    # Registra l'entrata (soggiorno)
    descrizione_entrata = f"Soggiorno {ospite} ({canale}) - {prenotazione_row.get('pernottamenti', 0)} notti"
    data_entrata = {
        "data": data_str,
        "tipo": "Entrata",
        "voce": "Fatturato / Vendite",
        "importo": importo,
        "metodo_pagamento": metodo,
        "persona": ospite,
        "descrizione": descrizione_entrata
    }
    try:
        response = supabase.table("transazioni").insert(data_entrata).execute()
        if hasattr(response, 'error') and response.error:
            return False, f"Errore registrazione entrata: {response.error}"
    except Exception as e:
        return False, f"Errore registrazione entrata: {str(e)}"
    
    # Registra l'uscita (commissione canale OTA) se presente
    if commissione > 0:
        descrizione_commissione = f"Commissione {canale} - {ospite}"
        data_commissione = {
            "data": data_str,
            "tipo": "Uscita",
            "voce": "Booking - idealista - segreteria.it - immobiliare.it",
            "importo": commissione,
            "metodo_pagamento": metodo,
            "persona": ospite,
            "descrizione": descrizione_commissione
        }
        try:
            response = supabase.table("transazioni").insert(data_commissione).execute()
            if hasattr(response, 'error') and response.error:
                return False, f"Entrata registrata ma errore commissione: {response.error}"
        except Exception as e:
            return False, f"Entrata registrata ma errore commissione: {str(e)}"
    
    # Registra l'uscita (tassa di soggiorno) se presente
    if tassa > 0:
        descrizione_tassa = f"Tassa di soggiorno - {ospite} ({canale})"
        data_tassa = {
            "data": data_str,
            "tipo": "Uscita",
            "voce": "Tasse di soggiorno",
            "importo": tassa,
            "metodo_pagamento": metodo,
            "persona": ospite,
            "descrizione": descrizione_tassa
        }
        try:
            response = supabase.table("transazioni").insert(data_tassa).execute()
            if hasattr(response, 'error') and response.error:
                return False, f"Entrata registrata ma errore tassa: {response.error}"
        except Exception as e:
            return False, f"Entrata registrata ma errore tassa: {str(e)}"
    
    # Aggiorna la prenotazione come registrata in contabilità
    try:
        supabase.table("prenotazioni").update({
            "stato": "Completata",
            "registrata_contabilita": True
        }).eq("id", int(prenotazione_row["id"])).execute()
    except Exception:
        pass
    
    return True, "Soggiorno registrato in contabilità (entrata + commissione + eventuale tassa di soggiorno)!"

# ─── Funzioni Scadenzario & Promemoria ─────────────────────
def calcola_prossima_data(data_scadenza_input, ricorrenza):
    if isinstance(data_scadenza_input, str):
        data_base = datetime.strptime(data_scadenza_input, "%Y-%m-%d").date()
    else:
        data_base = data_scadenza_input

    if ricorrenza == "Settimanale":
        nuova_data = data_base + timedelta(days=7)
    elif ricorrenza == "Quindicinale":
        nuova_data = data_base + timedelta(days=15)
    elif ricorrenza == "Mensile":
        nuova_data = data_base + relativedelta(months=1)
    elif ricorrenza == "Bimestrale":
        nuova_data = data_base + relativedelta(months=2)
    elif ricorrenza == "Trimestrale":
        nuova_data = data_base + relativedelta(months=3)
    elif ricorrenza == "Semestrale":
        nuova_data = data_base + relativedelta(months=6)
    elif ricorrenza == "Annuale":
        nuova_data = data_base + relativedelta(years=1)
    else:
        nuova_data = data_base

    return nuova_data.strftime("%Y-%m-%d")

def ottieni_scadenze(stato=None):
    try:
        query = supabase.table("scadenze").select("*")
        if stato:
            query = query.eq("stato", stato)
        query = query.order("data_scadenza", desc=False)
        response = query.execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception:
        pass
    return pd.DataFrame()

def aggiungi_scadenza(descrizione, tipo, voce, importo, data_scadenza, ricorrenza, metodo_pagamento, persona, note):
    descrizione = descrizione.strip()
    if not descrizione:
        return False, "La descrizione è obbligatoria."
    if importo <= 0:
        return False, "L'importo deve essere maggiore di zero."
        
    metodo_pagamento = normalizza_metodo_pagamento(metodo_pagamento)
    data_inserimento = {
        "descrizione": descrizione,
        "tipo": tipo,
        "voce": voce,
        "importo": importo,
        "data_scadenza": str(data_scadenza),
        "ricorrenza": ricorrenza,
        "metodo_pagamento": metodo_pagamento,
        "persona": persona.strip() if persona else "",
        "stato": "In attesa",
        "note": note.strip() if note else ""
    }
    try:
        response = supabase.table("scadenze").insert(data_inserimento).execute()
        return True, "Scadenza registrata con successo!"
    except Exception as e:
        return False, f"Errore durante l'inserimento: {str(e)}"

def elimina_scadenza(id_scadenza):
    try:
        supabase.table("scadenze").delete().eq("id", id_scadenza).execute()
        return True
    except Exception:
        return False

def registra_pagamento_scadenza(scadenza_row, data_pagamento, metodo_pagamento):
    """
    Registra il pagamento di una scadenza:
    1. Crea un movimento in 'transazioni' (importo, voce, tipo, metodo, persona, descrizione).
    2. Se ricorrenza == 'Nessuna' -> stato = 'Pagato'
    3. Se ricorrenza != 'Nessuna' -> calcola la nuova data_scadenza e la aggiorna nel DB mantenendo stato = 'In attesa'
    """
    data_str = str(data_pagamento)
    metodo = normalizza_metodo_pagamento(metodo_pagamento if metodo_pagamento else scadenza_row.get("metodo_pagamento", "Bonifico"))
    persona = scadenza_row.get("persona", "")
    descrizione_tx = f"Pagamento scadenza: {scadenza_row.get('descrizione', '')}"
    
    data_transazione = {
        "data": data_str,
        "tipo": scadenza_row["tipo"],
        "voce": scadenza_row["voce"],
        "importo": float(scadenza_row["importo"]),
        "metodo_pagamento": metodo,
        "persona": persona if persona else None,
        "descrizione": descrizione_tx
    }
    
    try:
        response = supabase.table("transazioni").insert(data_transazione).execute()
        if hasattr(response, 'error') and response.error:
            return False, f"Errore registrazione transazione: {response.error}"
    except Exception as e:
        return False, f"Errore registrazione transazione: {str(e)}"
        
    ricorrenza = scadenza_row.get("ricorrenza", "Nessuna")
    id_scadenza = int(scadenza_row["id"])
    
    if ricorrenza == "Nessuna":
        update_data = {
            "stato": "Pagato",
            "ultimo_pagamento": data_str
        }
    else:
        prossima_data = calcola_prossima_data(scadenza_row["data_scadenza"], ricorrenza)
        update_data = {
            "data_scadenza": prossima_data,
            "ultimo_pagamento": data_str,
            "stato": "In attesa"
        }
        
    try:
        supabase.table("scadenze").update(update_data).eq("id", id_scadenza).execute()
        return True, "Pagamento registrato nelle transazioni e scadenza aggiornata!"
    except Exception as e:
        return False, f"Transazione creata ma errore aggiornamento scadenza: {str(e)}"

def genera_testo_resoconto(df, data_inizio, data_fine):
    df_entrate = df[df['tipo'] == 'Entrata']
    df_uscite = df[df['tipo'] == 'Uscita']
    totale_entrate = df_entrate['importo'].sum()
    totale_uscite = df_uscite['importo'].sum()
    saldo = totale_entrate - totale_uscite
    ha_metodo = 'metodo_pagamento' in df.columns
    
    testo = f"""
========================================
   RESOCONTO CONTABILITÀ FRANCESCO
========================================
   Periodo: {data_inizio} -> {data_fine}
   Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}
========================================

RIEPILOGO:
  Totale entrate: {totale_entrate:,.2f} EUR
  Totale uscite:  {totale_uscite:,.2f} EUR
  Saldo netto:    {saldo:,.2f} EUR

----------------------------------------
DETTAGLIO TRANSAZIONI:
----------------------------------------
"""
    for _, row in df.iterrows():
        if ha_metodo:
            testo += f"  [{row['data']}] {row['tipo']:7s} | {row['metodo_pagamento']:10s} | {row['voce']:35s} | {row['importo']:>8.2f} EUR"
        else:
            testo += f"  [{row['data']}] {row['tipo']:7s} | {row['voce']:35s} | {row['importo']:>8.2f} EUR"
        if row['descrizione']:
            testo += f" | {row['descrizione']}"
        testo += "\n"
    
    if not df_entrate.empty:
        testo += "\n--- ENTRATE PER VOCE ---\n"
        for _, row in df_entrate.groupby('voce')['importo'].sum().reset_index().iterrows():
            testo += f"  {row['voce']:40s} {row['importo']:>8.2f} EUR\n"
    if not df_uscite.empty:
        testo += "\n--- USCITE PER VOCE ---\n"
        for _, row in df_uscite.groupby('voce')['importo'].sum().reset_index().iterrows():
            testo += f"  {row['voce']:40s} {row['importo']:>8.2f} EUR\n"
    if ha_metodo:
        testo += "\n--- SUDDIVISIONE PER METODO DI PAGAMENTO ---\n"
        for metodo in METODI_PAGAMENTO:
            df_metodo = df[df['metodo_pagamento'] == metodo]
            if not df_metodo.empty:
                testo += f"  {metodo:10s} {df_metodo['importo'].sum():>8.2f} EUR\n"
    testo += "\n========================================\n"
    return testo

# ─── Funzioni Backup & Ripristino ──────────────────────────
def esegui_backup():
    """Crea un backup completo dei dati (transazioni, categorie, scadenze) e lo salva in locale."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"backup_{timestamp}.json"
    percorso = os.path.join(BACKUP_DIR, nome_file)
    
    dati_backup = {
        "tipo": "backup",
        "versione": "2.0",
        "creato_il": datetime.now().isoformat(),
        "transazioni": [],
        "categorie": [],
        "scadenze": []
    }
    
    # Transazioni
    try:
        resp = supabase.table("transazioni").select("*").order("id").execute()
        if resp.data:
            dati_backup["transazioni"] = resp.data
    except Exception as e:
        return False, f"Errore lettura transazioni: {str(e)}"
    
    # Categorie
    try:
        resp = supabase.table("categorie").select("*").order("id").execute()
        if resp.data:
            dati_backup["categorie"] = resp.data
    except Exception as e:
        return False, f"Errore lettura categorie: {str(e)}"
    
    # Scadenze
    try:
        resp = supabase.table("scadenze").select("*").order("id").execute()
        if resp.data:
            dati_backup["scadenze"] = resp.data
    except Exception:
        pass
    
    try:
        with open(percorso, "w", encoding="utf-8") as f:
            json.dump(dati_backup, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        return False, f"Errore salvataggio file: {str(e)}"
    
    return True, (nome_file, percorso)

def elenca_backup():
    """Restituisce la lista dei file di backup disponibili, ordinati dal più recente."""
    if not os.path.exists(BACKUP_DIR):
        return []
    file_backup = [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".json")]
    file_backup.sort(reverse=True)
    return file_backup

def ripristina_backup(percorso_file):
    """Ripristina i dati da un file di backup, sovrascrivendo le tabelle su Supabase."""
    try:
        with open(percorso_file, "r", encoding="utf-8") as f:
            dati = json.load(f)
    except Exception as e:
        return False, f"Errore lettura file backup: {str(e)}"
    
    if dati.get("tipo") != "backup":
        return False, "File non valido: non è un backup riconosciuto."
    
    # Ripristina transazioni
    try:
        supabase.table("transazioni").delete().neq("id", 0).execute()
        if dati.get("transazioni"):
            for tx in dati["transazioni"]:
                tx_clean = {k: v for k, v in tx.items() if k != "id"}
                supabase.table("transazioni").insert(tx_clean).execute()
    except Exception as e:
        return False, f"Errore ripristino transazioni: {str(e)}"
    
    # Ripristina categorie
    try:
        supabase.table("categorie").delete().neq("id", 0).execute()
        if dati.get("categorie"):
            for cat in dati["categorie"]:
                cat_clean = {k: v for k, v in cat.items() if k != "id"}
                supabase.table("categorie").insert(cat_clean).execute()
    except Exception as e:
        return False, f"Errore ripristino categorie: {str(e)}"
    
    # Ripristina scadenze
    try:
        supabase.table("scadenze").delete().neq("id", 0).execute()
        if dati.get("scadenze"):
            for sc in dati["scadenze"]:
                sc_clean = {k: v for k, v in sc.items() if k != "id"}
                supabase.table("scadenze").insert(sc_clean).execute()
    except Exception:
        pass
    
    return True, "Backup ripristinato con successo!"

# ─── HEADER ────────────────────────────────────────────────
st.markdown("""
    <div style='text-align: center; padding: 0.8rem 0 0.3rem 0;'>
        <h1 style='color: #1E40AF; margin: 0; font-size: 2rem; font-weight: 700;'>
            💶 Gestionale Contabilità Francesco
        </h1>
        <p style='color: #64748B; margin: 0.2rem 0 0 0; font-size: 0.95rem;'>
            Monitora entrate, uscite, scadenze e archivia ricevute
        </p>
    </div>
""", unsafe_allow_html=True)

# ─── PROMEMORIA SCADENZE GLOBAL BANNER ─────────────────────
try:
    df_scadenze_attesa_global = ottieni_scadenze(stato="In attesa")
    if not df_scadenze_attesa_global.empty:
        oggi_g = date.today()
        limite_7gg_g = oggi_g + timedelta(days=7)
        df_scadenze_attesa_global['dt_scad_g'] = pd.to_datetime(df_scadenze_attesa_global['data_scadenza']).dt.date
        
        df_scadute_g = df_scadenze_attesa_global[df_scadenze_attesa_global['dt_scad_g'] < oggi_g]
        df_imminenti_g = df_scadenze_attesa_global[(df_scadenze_attesa_global['dt_scad_g'] >= oggi_g) & (df_scadenze_attesa_global['dt_scad_g'] <= limite_7gg_g)]
        
        cnt_scad = len(df_scadute_g)
        cnt_imm = len(df_imminenti_g)
        tot_scad = df_scadute_g['importo'].sum() if not df_scadute_g.empty else 0.0
        tot_imm = df_imminenti_g['importo'].sum() if not df_imminenti_g.empty else 0.0

        if cnt_scad > 0 or cnt_imm > 0:
            st.space("small")
            with st.container(border=True):
                st.markdown("#### :material/notifications_active: Promemoria Scadenze")
                c_prom1, c_prom2 = st.columns(2)
                if cnt_scad > 0:
                    with c_prom1:
                        st.error(f"🚨 **{cnt_scad} scadenze SCADUTE** per un totale di **{tot_scad:,.2f} EUR**! Vai in *Scadenzario & Promemoria* per regolarizzarle.")
                if cnt_imm > 0:
                    with c_prom2:
                        st.warning(f"⏰ **{cnt_imm} scadenze in arrivo (entro 7 gg)** per **{tot_imm:,.2f} EUR**.")
except Exception:
    pass

st.space("small")

# ─── PAGINA: NUOVA REGISTRAZIONE ──────────────────────────
if pagina == "Nuova registrazione":
    st.markdown("### :material/add_circle: Nuova registrazione")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            tipo_movimento = st.segmented_control(
                "Tipo", ["Entrata", "Uscita"],
                default="Entrata",
                selection_mode="single",
                key="tipo_reg"
            )
            categorie_disponibili = ottieni_categorie(tipo_movimento)
            voce_selezionata = st.selectbox("Voce *", options=categorie_disponibili, key="voce_reg")
            data_movimento = st.date_input("Data *", value=date.today(), key="data_reg").strftime("%Y-%m-%d")
            persona_movimento = st.text_input(
                ":material/person: Da chi", placeholder="Nome cliente / fornitore...", key="persona_reg"
            )
        with col2:
            importo_movimento = st.number_input(
                "Importo (EUR) *", min_value=0.01, value=10.00, step=0.01, format="%.2f", key="importo_reg"
            )
            metodo_pagamento = st.selectbox(
                ":material/payments: Metodo di pagamento *", options=METODI_PAGAMENTO, key="metodo_reg"
            )
            descrizione_movimento = st.text_area(
                "Note", placeholder="Dettagli...", height=68, key="note_reg"
            )
            scansione_ricevuta = st.file_uploader(
                "Ricevuta (PDF/immagine)", type=["pdf", "png", "jpg", "jpeg"], key="ricevuta_reg"
            )
    
    st.space("small")
    if st.button(":material/save: Registra movimento", use_container_width=True, type="primary"):
        if not voce_selezionata:
            st.error("Seleziona una voce.")
        else:
            ok = aggiungi_transazione(
                data_movimento, tipo_movimento, voce_selezionata, importo_movimento,
                metodo_pagamento, persona_movimento, descrizione_movimento, scansione_ricevuta
            )
            if ok:
                st.success(f"✅ Registrato: {tipo_movimento} {importo_movimento:.2f} EUR ({metodo_pagamento})")
                st.balloons()
                st.rerun()

# ─── PAGINA: PRENOTAZIONI & OSPITI ─────────────────────────
elif pagina == "Prenotazioni & Ospiti":
    st.markdown("### :material/bed: Prenotazioni & Ospiti")
    st.caption("Gestisci le prenotazioni del B&B, gli ospiti e registra i soggiorni in contabilità.")
    
    # Verifica esistenza tabella prenotazioni su Supabase
    prenotazioni_table_ok = True
    try:
        supabase.table("prenotazioni").select("id").limit(1).execute()
    except Exception:
        prenotazioni_table_ok = False
        st.error("⚠️ **Tabella `prenotazioni` non trovata su Supabase!**")
        st.info("Per attivare il modulo Prenotazioni, apri l'Editor SQL della tua Dashboard di Supabase ed esegui lo script seguente:")
        with st.expander("📄 Script SQL per creare la tabella prenotazioni"):
            st.code("""
CREATE TABLE IF NOT EXISTS prenotazioni (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ospite TEXT NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    pernottamenti INTEGER NOT NULL,
    camera TEXT DEFAULT '',
    canale TEXT DEFAULT 'Diretto' CHECK (canale IN ('Diretto', 'Booking', 'Airbnb', 'Expedia', 'Altro')),
    importo DOUBLE PRECISION NOT NULL DEFAULT 0,
    commissione DOUBLE PRECISION NOT NULL DEFAULT 0,
    tassa_soggiorno DOUBLE PRECISION NOT NULL DEFAULT 0,
    stato TEXT NOT NULL DEFAULT 'Confermata' CHECK (stato IN ('Confermata', 'In corso', 'Completata', 'Cancellata')),
    note TEXT DEFAULT '',
    registrata_contabilita BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE prenotazioni DISABLE ROW LEVEL SECURITY;
            """, language="sql")

    if prenotazioni_table_ok:
        df_tutte_pren = ottieni_prenotazioni()
        oggi_p = date.today()
        
        # Metriche riepilogo
        df_attive = df_tutte_pren[df_tutte_pren['stato'].isin(['Confermata', 'In corso'])] if not df_tutte_pren.empty else pd.DataFrame()
        df_in_corso = df_tutte_pren[df_tutte_pren['stato'] == 'In corso'] if not df_tutte_pren.empty else pd.DataFrame()
        df_completate = df_tutte_pren[df_tutte_pren['stato'] == 'Completata'] if not df_tutte_pren.empty else pd.DataFrame()
        
        tot_attive = df_attive['importo'].sum() if not df_attive.empty else 0.0
        tot_completate = df_completate['importo'].sum() if not df_completate.empty else 0.0
        
        col_pm1, col_pm2, col_pm3, col_pm4 = st.columns(4)
        with col_pm1:
            st.metric(":material/bed: Prenotazioni attive", f"{len(df_attive)}", border=True)
        with col_pm2:
            st.metric(":material/hotel: Ospiti in casa", f"{len(df_in_corso)}", border=True)
        with col_pm3:
            st.metric(":material/trending_up: Valore attivo", f"{tot_attive:,.2f} EUR", border=True)
        with col_pm4:
            st.metric(":material/check_circle: Completate", f"{tot_completate:,.2f} EUR", border=True)
        
        st.space("small")
        
        tab_pren, tab_nuova_pren = st.tabs([
            ":material/format_list_bulleted: Elenco prenotazioni",
            ":material/add_circle: Nuova prenotazione"
        ])
        
        with tab_nuova_pren:
            st.markdown("#### :material/add_circle: Registra una nuova prenotazione")
            with st.container(border=True):
                col_pn1, col_pn2 = st.columns(2)
                with col_pn1:
                    pn_ospite = st.text_input("Nome ospite *", placeholder="Es. Mario Rossi", key="pn_ospite")
                    pn_check_in = st.date_input("Check-in *", value=oggi_p, key="pn_check_in")
                    pn_check_out = st.date_input("Check-out *", value=oggi_p + timedelta(days=1), key="pn_check_out")
                    pn_camera = st.text_input("Camera", placeholder="Es. Camera 1, Appartamento...", key="pn_camera")
                with col_pn2:
                    pn_canale = st.selectbox("Canale di prenotazione", options=CANALI_PRENOTAZIONE, key="pn_canale")
                    pn_importo = st.number_input("Importo soggiorno (EUR)", min_value=0.0, value=100.00, step=10.00, format="%.2f", key="pn_importo")
                    pn_commissione = st.number_input("Commissione canale (EUR)", min_value=0.0, value=0.0, step=1.00, format="%.2f", help="Commissione trattenuta dal canale OTA (Booking, Airbnb, ecc.).", key="pn_commissione")
                    pn_tassa = st.number_input("Tassa di soggiorno (EUR)", min_value=0.0, value=0.0, step=1.00, format="%.2f", help="Importo totale della tassa di soggiorno per il soggiorno.", key="pn_tassa")
                    pn_note = st.text_area("Note", placeholder="Dettagli aggiuntivi...", height=68, key="pn_note")
            
            # Anteprima pernottamenti
            if pn_check_out > pn_check_in:
                pn_notti = (pn_check_out - pn_check_in).days
                st.info(f"📅 **{pn_notti} pernottamenti** calcolati automaticamente (dal {pn_check_in} al {pn_check_out}).")
            else:
                st.warning("⚠️ Il check-out deve essere successivo al check-in.")
            
            if st.button(":material/save: Salva prenotazione", type="primary", use_container_width=True):
                if not pn_ospite:
                    st.error("Inserisci il nome dell'ospite.")
                elif pn_check_out <= pn_check_in:
                    st.error("Il check-out deve essere successivo al check-in.")
                else:
                    ok_pn, msg_pn = aggiungi_prenotazione(
                        pn_ospite, pn_check_in, pn_check_out, pn_camera,
                        pn_canale, pn_importo, pn_commissione, pn_tassa, pn_note
                    )
                    if ok_pn:
                        st.success(f"✅ {msg_pn}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg_pn)
        
        with tab_pren:
            if df_tutte_pren.empty:
                st.info(":material/info: Nessuna prenotazione registrata.")
            else:
                # Filtri
                col_fp1, col_fp2, col_fp3 = st.columns(3)
                with col_fp1:
                    filtro_stato_pren = st.selectbox("Filtra per stato", ["Tutti"] + STATI_PRENOTAZIONE, key="filtro_stato_pren")
                with col_fp2:
                    filtro_canale_pren = st.selectbox("Filtra per canale", ["Tutti"] + CANALI_PRENOTAZIONE, key="filtro_canale_pren")
                with col_fp3:
                    filtro_ospite_pren = st.text_input(":material/search: Cerca ospite", placeholder="Nome...", key="filtro_ospite_pren")
                
                df_pren_filtrate = df_tutte_pren.copy()
                if filtro_stato_pren != "Tutti":
                    df_pren_filtrate = df_pren_filtrate[df_pren_filtrate['stato'] == filtro_stato_pren]
                if filtro_canale_pren != "Tutti":
                    df_pren_filtrate = df_pren_filtrate[df_pren_filtrate['canale'] == filtro_canale_pren]
                if filtro_ospite_pren:
                    df_pren_filtrate = df_pren_filtrate[df_pren_filtrate['ospite'].str.contains(filtro_ospite_pren, case=False, na=False)]
                
                st.markdown(f"**{len(df_pren_filtrate)} prenotazioni trovate**")
                
                for idx, row in df_pren_filtrate.iterrows():
                    stato_badge = {
                        "Confermata": ":blue-badge[Confermata]",
                        "In corso": ":orange-badge[In corso]",
                        "Completata": ":green-badge[Completata]",
                        "Cancellata": ":red-badge[Cancellata]"
                    }.get(row['stato'], row['stato'])
                    
                    canale_badge = f":material/globe: {row['canale']}"
                    
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 2])
                        with c1:
                            st.markdown(f"### {row['ospite']} {stato_badge}")
                            st.markdown(f"**Check-in:** `{row['check_in']}` → **Check-out:** `{row['check_out']}` | **{row['pernottamenti']} notti**")
                            if row.get('camera'):
                                st.markdown(f"**Camera:** {row['camera']}")
                            st.markdown(f"**Canale:** {canale_badge}")
                            if row.get('note'):
                                st.caption(f"Note: {row['note']}")
                        with c2:
                            st.markdown(f"#### {row['importo']:,.2f} EUR")
                            if row.get('commissione', 0) > 0:
                                st.write(f"💸 **Commissione:** {row['commissione']:,.2f} EUR")
                            if row.get('tassa_soggiorno', 0) > 0:
                                st.write(f"🏛️ **Tassa soggiorno:** {row['tassa_soggiorno']:,.2f} EUR")
                            if row.get('registrata_contabilita'):
                                st.success("✅ Registrata in contabilità")
                            else:
                                st.caption("Non ancora in contabilità")
                        with c3:
                            st.space("small")
                            # Azioni
                            if row['stato'] == "Confermata":
                                if st.button(":material/hotel: In corso", key=f"in_corso_{row['id']}", use_container_width=True):
                                    aggiorna_stato_prenotazione(row['id'], "In corso")
                                    st.rerun()
                            if row['stato'] in ["Confermata", "In corso"]:
                                if not row.get('registrata_contabilita'):
                                    with st.popover(":material/check_circle: Registra in contabilità", use_container_width=True, type="primary"):
                                        st.markdown("##### Registra soggiorno in contabilità")
                                        st.caption(f"Registra {row['importo']:,.2f} EUR come entrata per {row['ospite']}.")
                                        with st.form(key=f"form_pren_{row['id']}"):
                                            pr_data = st.date_input("Data pagamento", value=oggi_p, key=f"prdata_{row['id']}")
                                            pr_metodo = st.selectbox("Metodo pagamento", options=METODI_PAGAMENTO, key=f"prmetodo_{row['id']}")
                                            if st.form_submit_button("Conferma e registra", type="primary", use_container_width=True):
                                                ok_pr, msg_pr = registra_prenotazione_contabilita(row, pr_data, pr_metodo)
                                                if ok_pr:
                                                    st.success(f"✅ {msg_pr}")
                                                    st.balloons()
                                                    st.rerun()
                                                else:
                                                    st.error(msg_pr)
                            if st.button(":material/delete: Elimina", key=f"del_pren_{row['id']}", use_container_width=True, type="secondary"):
                                if elimina_prenotazione(row['id']):
                                    st.success("Prenotazione eliminata!")
                                    st.rerun()

# ─── PAGINA: SCADENZARIO & PROMEMORIA ───────────────────────
elif pagina == "Scadenzario & Promemoria":
    st.markdown("### :material/calendar_clock: Scadenzario & Promemoria")
    st.caption("Gestisci le tue scadenze, imposta le frequenze di ripetizione e ricevi promemoria automatici 1 settimana prima.")
    
    # Verifica esistenza tabella scadenze su Supabase
    scadenze_table_ok = True
    try:
        supabase.table("scadenze").select("id").limit(1).execute()
    except Exception:
        scadenze_table_ok = False
        st.error("⚠️ **Tabella `scadenze` non trovata su Supabase!**")
        st.info("Per attivare il modulo Scadenzario, apri l'Editor SQL della tua Dashboard di Supabase ed esegui lo script seguente:")
        with st.expander("📄 Script SQL per creare la tabella scadenze"):
            st.code("""
CREATE TABLE IF NOT EXISTS scadenze (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    descrizione TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'Uscita' CHECK (tipo IN ('Entrata', 'Uscita')),
    voce TEXT NOT NULL,
    importo DOUBLE PRECISION NOT NULL,
    data_scadenza DATE NOT NULL,
    ricorrenza TEXT NOT NULL DEFAULT 'Nessuna' CHECK (ricorrenza IN ('Nessuna', 'Settimanale', 'Quindicinale', 'Mensile', 'Bimestrale', 'Trimestrale', 'Semestrale', 'Annuale')),
    metodo_pagamento TEXT DEFAULT 'Bonifico',
    persona TEXT DEFAULT '',
    stato TEXT NOT NULL DEFAULT 'In attesa' CHECK (stato IN ('In attesa', 'Pagato')),
    note TEXT DEFAULT '',
    ultimo_pagamento DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE scadenze DISABLE ROW LEVEL SECURITY;
            """, language="sql")

    if scadenze_table_ok:
        df_tutte_scadenze = ottieni_scadenze()
        oggi = date.today()
        limite_7gg = oggi + timedelta(days=7)
        
        df_attesa = df_tutte_scadenze[df_tutte_scadenze['stato'] == 'In attesa'].copy() if not df_tutte_scadenze.empty else pd.DataFrame()
        df_pagate = df_tutte_scadenze[df_tutte_scadenze['stato'] == 'Pagato'].copy() if not df_tutte_scadenze.empty else pd.DataFrame()
        
        if not df_attesa.empty:
            df_attesa['dt_scad'] = pd.to_datetime(df_attesa['data_scadenza']).dt.date
            df_scadute = df_attesa[df_attesa['dt_scad'] < oggi]
            df_imminenti = df_attesa[(df_attesa['dt_scad'] >= oggi) & (df_attesa['dt_scad'] <= limite_7gg)]
            df_future = df_attesa[df_attesa['dt_scad'] > limite_7gg]
        else:
            df_scadute = pd.DataFrame()
            df_imminenti = pd.DataFrame()
            df_future = pd.DataFrame()
            
        tot_scaduto = df_scadute['importo'].sum() if not df_scadute.empty else 0.0
        tot_imminente = df_imminenti['importo'].sum() if not df_imminenti.empty else 0.0
        tot_attesa = df_attesa['importo'].sum() if not df_attesa.empty else 0.0
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(":material/warning: Scadute", f"{tot_scaduto:,.2f} EUR", f"{len(df_scadute)} scadenze", delta_color="inverse", border=True)
        with col_m2:
            st.metric(":material/schedule: Prossimi 7 giorni", f"{tot_imminente:,.2f} EUR", f"{len(df_imminenti)} scadenze", border=True)
        with col_m3:
            st.metric(":material/pending_actions: Totale in attesa", f"{tot_attesa:,.2f} EUR", f"{len(df_attesa)} scadenze", border=True)
            
        st.space("small")
        
        tab_attesa, tab_nuova, tab_storico = st.tabs([
            ":material/format_list_bulleted: Scadenze in attesa",
            ":material/add_circle: Nuova scadenza",
            ":material/history: Storico pagamenti"
        ])
        
        with tab_attesa:
            if df_attesa.empty:
                st.info(":material/info: Nessuna scadenza in attesa registrata.")
            else:
                filtro_urg = st.segmented_control(
                    "Filtra urgenza",
                    ["Tutte", "🚨 Scadute", "⏰ Prossimi 7 giorni", "🟢 Future"],
                    default="Tutte",
                    key="filtro_urg"
                )
                
                if filtro_urg == "🚨 Scadute":
                    df_mostra = df_scadute
                elif filtro_urg == "⏰ Prossimi 7 giorni":
                    df_mostra = df_imminenti
                elif filtro_urg == "🟢 Future":
                    df_mostra = df_future
                else:
                    df_mostra = df_attesa
                    
                if df_mostra.empty:
                    st.info(f"Nessuna scadenza trovata per il filtro '{filtro_urg}'.")
                else:
                    for idx, row in df_mostra.iterrows():
                        dt_scad = pd.to_datetime(row['data_scadenza']).date()
                        is_scaduta = dt_scad < oggi
                        is_imminente = oggi <= dt_scad <= limite_7gg
                        
                        if is_scaduta:
                            badge_status = ":red-badge[🚨 SCADUTA]"
                        elif is_imminente:
                            badge_status = ":orange-badge[⏰ IN SCADENZA (7 GG)]"
                        else:
                            badge_status = ":green-badge[🟢 FUTURA]"
                            
                        tipo_badge = ":red-badge[Uscita]" if row['tipo'] == 'Uscita' else ":green-badge[Entrata]"
                        
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([3, 2, 2])
                            with c1:
                                st.markdown(f"### {row['descrizione']} {badge_status} {tipo_badge}")
                                st.markdown(f"**Voce:** {row['voce']} | **Data Scadenza:** `{row['data_scadenza']}`")
                                if row.get('persona'):
                                    st.markdown(f"**Da chi / Per chi:** {row['persona']}")
                                if row.get('note'):
                                    st.caption(f"Note: {row['note']}")
                            with c2:
                                st.markdown(f"#### {row['importo']:,.2f} EUR")
                                st.write(f"🔄 **Ricorrenza:** {row['ricorrenza']}")
                                st.write(f"💳 **Metodo prev.:** {row.get('metodo_pagamento', 'N/D')}")
                                if row.get('ultimo_pagamento'):
                                    st.caption(f"Ultimo pagamento: {row['ultimo_pagamento']}")
                            with c3:
                                st.space("small")
                                with st.popover(":material/check_circle: Segna come Pagato", use_container_width=True, type="primary"):
                                    st.markdown("##### Registra Pagamento")
                                    st.caption(f"Salda '{row['descrizione']}' ({row['importo']:.2f} EUR)")
                                    with st.form(key=f"form_paga_{row['id']}"):
                                        p_data = st.date_input("Data pagamento", value=oggi, key=f"pdata_{row['id']}")
                                        p_metodo = st.selectbox("Metodo pagamento", options=METODI_PAGAMENTO, index=METODI_PAGAMENTO.index(row.get('metodo_pagamento')) if row.get('metodo_pagamento') in METODI_PAGAMENTO else 0, key=f"pmetodo_{row['id']}")
                                        if st.form_submit_button("Conferma e Inserisci in Contabilità", type="primary", use_container_width=True):
                                            ok_p, msg_p = registra_pagamento_scadenza(row, p_data, p_metodo)
                                            if ok_p:
                                                st.success(f"✅ {msg_p}")
                                                st.balloons()
                                                st.rerun()
                                            else:
                                                st.error(msg_p)
                                
                                if st.button(":material/delete: Elimina", key=f"del_scad_{row['id']}", use_container_width=True, type="secondary"):
                                    if elimina_scadenza(row['id']):
                                        st.success("Scadenza eliminata!")
                                        st.rerun()

        with tab_nuova:
            st.markdown("#### :material/add_circle: Registra una nuova scadenza")
            with st.container(border=True):
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    n_desc = st.text_input("Descrizione *", placeholder="Es. Bolletta luce appartamenti, Rata affitto, F24...", key="n_desc")
                    n_tipo = st.segmented_control("Tipo *", options=["Uscita", "Entrata"], default="Uscita", key="n_tipo")
                    cats = ottieni_categorie(n_tipo)
                    n_voce = st.selectbox("Voce contabile *", options=cats if cats else [""], key="n_voce")
                    n_importo = st.number_input("Importo (EUR) *", min_value=0.01, value=100.00, step=0.01, format="%.2f", key="n_importo")
                with col_n2:
                    n_data = st.date_input("Data prima scadenza *", value=oggi, key="n_data")
                    n_ricorrenza = st.selectbox("Ricorrenza (Ripetizione) *", options=RICORRENZE, index=3, help="Se selezionata una frequenza, dopo il pagamento la scadenza verrà automaticamente spostata alla data successiva.", key="n_ricorrenza")
                    n_metodo = st.selectbox("Metodo di pagamento previsto", options=METODI_PAGAMENTO, index=1, key="n_metodo")
                    n_persona = st.text_input("Da chi / Persona (opzionale)", placeholder="Cliente o fornitore...", key="n_persona")
                    n_note = st.text_area("Note / Dettagli", placeholder="Annotazioni aggiuntive...", height=68, key="n_note")
            
            if st.button(":material/save: Salva Scadenza", type="primary", use_container_width=True):
                if not n_desc:
                    st.error("Inserisci la descrizione della scadenza.")
                elif not n_voce:
                    st.error("Seleziona la voce contabile.")
                else:
                    ok_s, msg_s = aggiungi_scadenza(
                        n_desc, n_tipo, n_voce, n_importo, n_data,
                        n_ricorrenza, n_metodo, n_persona, n_note
                    )
                    if ok_s:
                        st.success(f"✅ {msg_s}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg_s)

        with tab_storico:
            st.markdown("#### :material/history: Storico scadenze pagate (singole)")
            if df_pagate.empty:
                st.info(":material/info: Nessuna scadenza singola saldata nello storico.")
            else:
                df_pag_disp = df_pagate[['data_scadenza', 'ultimo_pagamento', 'tipo', 'descrizione', 'voce', 'importo', 'metodo_pagamento', 'persona']].copy()
                df_pag_disp.columns = ['Data Prevista', 'Data Saldo', 'Tipo', 'Descrizione', 'Voce', 'Importo (EUR)', 'Metodo', 'Persona']
                st.dataframe(df_pag_disp, width='stretch', hide_index=True)

# ─── PAGINA: RESOCONTO & ANALISI ──────────────────────────
elif pagina == "Resoconto & analisi":
    st.markdown("### :material/analytics: Resoconto & analisi")
    
    with st.container(border=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            data_inizio_filtro = st.date_input("Dal:", value=date(date.today().year, 1, 1), key="data_inizio")
        with col_f2:
            data_fine_filtro = st.date_input("Al:", value=date.today(), key="data_fine")
    
    if data_inizio_filtro > data_fine_filtro:
        st.warning(":material/warning: Data inizio successiva a data fine!")
    
    df_transazioni = ottieni_transazioni(
        data_inizio_filtro.strftime("%Y-%m-%d"), data_fine_filtro.strftime("%Y-%m-%d")
    )
    
    if df_transazioni.empty:
        st.info(":material/info: Nessun movimento nel periodo selezionato.")
    else:
        df_entrate = df_transazioni[df_transazioni['tipo'] == 'Entrata']
        df_uscite = df_transazioni[df_transazioni['tipo'] == 'Uscita']
        totale_entrate = df_entrate['importo'].sum()
        totale_uscite = df_uscite['importo'].sum()
        saldo = totale_entrate - totale_uscite
        
        st.markdown("#### :material/bar_chart: Riepilogo")
        with st.container(horizontal=True):
            st.metric(":material/trending_up: Entrate", f"{totale_entrate:,.2f} EUR", border=True)
            st.metric(":material/trending_down: Uscite", f"{totale_uscite:,.2f} EUR", border=True)
            st.metric(
                ":material/balance: Saldo", f"{saldo:,.2f} EUR",
                delta=f"{saldo:,.2f} EUR",
                delta_color="normal" if saldo >= 0 else "inverse",
                border=True
            )
        
        testo_resoconto = genera_testo_resoconto(
            df_transazioni,
            data_inizio_filtro.strftime("%d/%m/%Y"),
            data_fine_filtro.strftime("%d/%m/%Y")
        )
        col_s1, col_s2 = st.columns([1, 3])
        with col_s1:
            st.download_button(
                ":material/print: Scarica resoconto",
                data=testo_resoconto,
                file_name=f"resoconto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_s2:
            st.caption("Scarica il resoconto completo in formato testo.")
        
        st.space("small")
        
        tab_lista, tab_grafici, tab_metodi, tab_fiscali = st.tabs([
            ":material/format_list_bulleted: Lista transazioni",
            ":material/pie_chart: Analisi per voce",
            ":material/payments: Analisi per metodo",
            ":material/account_balance: Report fiscali"
        ])
        
        with tab_lista:
            st.markdown("#### Transazioni del periodo")
            df_display = df_transazioni.copy()
            df_display.columns = ['ID', 'Data', 'Tipo', 'Voce', 'Importo (EUR)', 'Metodo', 'Persona', 'Descrizione', 'Ricevuta', 'Percorso', 'Creato']
            
            def color_tipo(val):
                if val == 'Entrata':
                    return 'color: #16A34A; font-weight: 600;'
                return 'color: #DC2626; font-weight: 600;'
            
            styled = df_display[['Data', 'Tipo', 'Voce', 'Importo (EUR)', 'Metodo', 'Persona', 'Descrizione', 'Ricevuta']].style.map(
                color_tipo, subset=['Tipo']
            ).format({'Importo (EUR)': '{:,.2f}'})
            
            st.dataframe(styled, width='stretch', hide_index=True)
            
            st.space("small")
            st.markdown("#### Dettaglio movimento")
            opzioni = [
                f"ID {r['id']} - {r['data']} | {r['tipo']} | {r['voce']} | {r['importo']:.2f} EUR | {r.get('metodo_pagamento', 'N/D')}"
                for _, r in df_transazioni.iterrows()
            ]
            movimento_sel = st.selectbox("Seleziona un movimento:", options=opzioni, key="sel_mov")
            if movimento_sel:
                id_sel = int(movimento_sel.split(" - ")[0].replace("ID ", ""))
                mov = df_transazioni[df_transazioni['id'] == id_sel].iloc[0]
                
                ca1, ca2 = st.columns([2, 1])
                with ca1:
                    with st.container(border=True):
                        badge_tipo = ":green-badge[Entrata]" if mov['tipo'] == 'Entrata' else ":red-badge[Uscita]"
                        st.markdown(f"**Dettagli** {badge_tipo}")
                        st.write(f"- **Data:** {mov['data']}")
                        st.write(f"- **Da chi:** {mov.get('persona') or 'N/D'}")
                        st.write(f"- **Voce:** {mov['voce']}")
                        st.write(f"- **Importo:** {mov['importo']:.2f} EUR")
                        st.write(f"- **Metodo:** {mov.get('metodo_pagamento', 'N/D')}")
                        st.write(f"- **Note:** {mov['descrizione'] or 'Nessuna'}")
                        if mov['ricevuta_nome']:
                            st.write(f"- **Ricevuta:** {mov['ricevuta_nome']}")
                            dati_ricevuta = scarica_ricevuta(mov['ricevuta_percorso'])
                            if dati_ricevuta:
                                st.download_button(
                                    ":material/download: Scarica ricevuta",
                                    data=dati_ricevuta,
                                    file_name=mov['ricevuta_nome']
                                )
                                ext = os.path.splitext(mov['ricevuta_nome'])[1].lower()
                                if ext in ['.png', '.jpg', '.jpeg']:
                                    st.image(dati_ricevuta, width=400)
                with ca2:
                    st.warning(":material/delete_forever: Eliminazione permanente")
                    if st.button(":material/delete: Elimina movimento", type="secondary", use_container_width=True):
                        elimina_transazione(mov['id'], mov['ricevuta_percorso'])
                        st.success("🗑️ Movimento eliminato!")
                        st.rerun()
        
        with tab_grafici:
            st.markdown("#### Totali per voce")
            cg1, cg2 = st.columns(2)
            with cg1:
                with st.container(border=True):
                    st.markdown("##### :material/trending_up: Entrate per voce")
                    if not df_entrate.empty:
                        se = df_entrate.groupby('voce')['importo'].sum().reset_index()
                        se.columns = ['Voce', 'Totale (EUR)']
                        st.dataframe(se, width='stretch', hide_index=True)
                        st.bar_chart(data=se, x='Voce', y='Totale (EUR)', color="#16A34A")
            with cg2:
                with st.container(border=True):
                    st.markdown("##### :material/trending_down: Uscite per voce")
                    if not df_uscite.empty:
                        su = df_uscite.groupby('voce')['importo'].sum().reset_index()
                        su.columns = ['Voce', 'Totale (EUR)']
                        st.dataframe(su, width='stretch', hide_index=True)
                        st.bar_chart(data=su, x='Voce', y='Totale (EUR)', color="#DC2626")
        
        with tab_metodi:
            st.markdown("#### Totali per metodo di pagamento")
            if 'metodo_pagamento' not in df_transazioni.columns:
                st.info(":material/info: Colonna 'metodo_pagamento' non presente nel database.")
            else:
                cm1, cm2 = st.columns(2)
                with cm1:
                    with st.container(border=True):
                        st.markdown("##### :material/trending_up: Entrate per metodo")
                        if not df_entrate.empty:
                            em = df_entrate.groupby('metodo_pagamento')['importo'].sum().reset_index()
                            em.columns = ['Metodo', 'Totale (EUR)']
                            st.dataframe(em, width='stretch', hide_index=True)
                            st.bar_chart(data=em, x='Metodo', y='Totale (EUR)', color="#16A34A")
                with cm2:
                    with st.container(border=True):
                        st.markdown("##### :material/trending_down: Uscite per metodo")
                        if not df_uscite.empty:
                            um = df_uscite.groupby('metodo_pagamento')['importo'].sum().reset_index()
                            um.columns = ['Metodo', 'Totale (EUR)']
                            st.dataframe(um, width='stretch', hide_index=True)
                            st.bar_chart(data=um, x='Metodo', y='Totale (EUR)', color="#DC2626")
        
        with tab_fiscali:
            st.markdown("#### :material/account_balance: Report fiscali")
            st.caption("Riepilogo mensile e trimestrale per la dichiarazione fiscale.")
            
            # Prepara dati con periodo
            df_fisc = df_transazioni.copy()
            df_fisc['data_dt'] = pd.to_datetime(df_fisc['data'])
            df_fisc['anno'] = df_fisc['data_dt'].dt.year
            df_fisc['mese'] = df_fisc['data_dt'].dt.month
            df_fisc['trimestre'] = ((df_fisc['mese'] - 1) // 3) + 1
            df_fisc['periodo_mese'] = df_fisc['data_dt'].dt.strftime('%Y-%m')
            df_fisc['periodo_trim'] = df_fisc['anno'].astype(str) + '-T' + df_fisc['trimestre'].astype(str)
            
            # Riepilogo mensile
            st.markdown("##### :material/calendar_month: Riepilogo mensile")
            df_mensile = df_fisc.groupby('periodo_mese').apply(
                lambda g: pd.Series({
                    'Entrate': g[g['tipo'] == 'Entrata']['importo'].sum(),
                    'Uscite': g[g['tipo'] == 'Uscita']['importo'].sum(),
                    'Saldo': g[g['tipo'] == 'Entrata']['importo'].sum() - g[g['tipo'] == 'Uscita']['importo'].sum()
                })
            ).reset_index()
            df_mensile.columns = ['Periodo', 'Entrate (EUR)', 'Uscite (EUR)', 'Saldo (EUR)']
            df_mensile = df_mensile.sort_values('Periodo')
            st.dataframe(df_mensile.style.format({
                'Entrate (EUR)': '{:,.2f}',
                'Uscite (EUR)': '{:,.2f}',
                'Saldo (EUR)': '{:,.2f}'
            }), width='stretch', hide_index=True)
            
            st.space("small")
            
            # Riepilogo trimestrale
            st.markdown("##### :material/calendar_view_week: Riepilogo trimestrale")
            df_trim = df_fisc.groupby('periodo_trim').apply(
                lambda g: pd.Series({
                    'Entrate': g[g['tipo'] == 'Entrata']['importo'].sum(),
                    'Uscite': g[g['tipo'] == 'Uscita']['importo'].sum(),
                    'Saldo': g[g['tipo'] == 'Entrata']['importo'].sum() - g[g['tipo'] == 'Uscita']['importo'].sum()
                })
            ).reset_index()
            df_trim.columns = ['Periodo', 'Entrate (EUR)', 'Uscite (EUR)', 'Saldo (EUR)']
            df_trim = df_trim.sort_values('Periodo')
            st.dataframe(df_trim.style.format({
                'Entrate (EUR)': '{:,.2f}',
                'Uscite (EUR)': '{:,.2f}',
                'Saldo (EUR)': '{:,.2f}'
            }), width='stretch', hide_index=True)
            
            st.space("small")
            
            # Grafico mensile
            st.markdown("##### :material/bar_chart: Andamento mensile")
            if not df_mensile.empty:
                st.bar_chart(data=df_mensile.set_index('Periodo')[['Entrate (EUR)', 'Uscite (EUR)']])
            
            # Export report fiscale
            st.space("small")
            testo_fiscale = f"""
   REPORT FISCALE — CONTABILITÀ FRANCESCO
   Periodo: {data_inizio_filtro.strftime('%d/%m/%Y')} -> {data_fine_filtro.strftime('%d/%m/%Y')}
   Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}

RIEPILOGO MENSILE:
{df_mensile.to_string(index=False)}

----------------------------------------
RIEPILOGO TRIMESTRALE:
{df_trim.to_string(index=False)}

----------------------------------------
TOTALI PERIODO:
  Totale entrate: {totale_entrate:,.2f} EUR
  Totale uscite:  {totale_uscite:,.2f} EUR
  Saldo netto:    {saldo:,.2f} EUR
"""
            st.download_button(
                ":material/download: Scarica report fiscale",
                data=testo_fiscale,
                file_name=f"report_fiscale_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# ─── PAGINA: ARCHIVIO RICEVUTE ────────────────────────────
elif pagina == "Archivio ricevute":
    st.markdown("### :material/folder: Archivio ricevute")
    st.caption("Visualizza, cerca e scarica tutte le ricevute caricate.")
    
    # Ottieni tutte le transazioni che hanno una ricevuta
    df_tutte = ottieni_transazioni()
    df_con_ricevute = df_tutte[df_tutte['ricevuta_nome'].notna() & (df_tutte['ricevuta_nome'] != '')].copy()
    
    if df_con_ricevute.empty:
        st.info(":material/info: Nessuna ricevuta caricata. Vai in *Nuova registrazione* per caricare una ricevuta.")
    else:
        # Filtri
        col_filtri_r1, col_filtri_r2, col_filtri_r3 = st.columns(3)
        with col_filtri_r1:
            filtro_tipo_r = st.selectbox("Filtra per tipo", ["Tutti", "Entrata", "Uscita"], key="filtro_tipo_ricevuta")
        with col_filtri_r2:
            # Estrai anni disponibili
            df_con_ricevute['anno'] = pd.to_datetime(df_con_ricevute['data']).dt.year
            anni_disponibili = sorted(df_con_ricevute['anno'].unique(), reverse=True)
            filtro_anno_r = st.selectbox("Filtra per anno", ["Tutti"] + [str(a) for a in anni_disponibili], key="filtro_anno_ricevuta")
        with col_filtri_r3:
            # Cerca per descrizione
            filtro_testo_r = st.text_input(":material/search: Cerca per descrizione", placeholder="Testo...", key="filtro_testo_ricevuta")
        
        # Applica filtri
        df_filtrate = df_con_ricevute.copy()
        if filtro_tipo_r != "Tutti":
            df_filtrate = df_filtrate[df_filtrate['tipo'] == filtro_tipo_r]
        if filtro_anno_r != "Tutti":
            df_filtrate = df_filtrate[df_filtrate['anno'] == int(filtro_anno_r)]
        if filtro_testo_r:
            df_filtrate = df_filtrate[df_filtrate['descrizione'].str.contains(filtro_testo_r, case=False, na=False)]
        
        st.markdown(f"**{len(df_filtrate)} ricevute trovate**")
        
        # Mostra ricevute in griglia
        cols_per_row = 3
        for i in range(0, len(df_filtrate), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, (idx, row) in enumerate(df_filtrate.iloc[i:i+cols_per_row].iterrows()):
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"**{row['ricevuta_nome']}**")
                        st.caption(f"{row['data']} | {row['tipo']} | {row['voce']}")
                        if row['descrizione']:
                            st.caption(f"📝 {row['descrizione']}")
                        if row.get('importo'):
                            st.markdown(f"**{row['importo']:.2f} EUR**")
                        
                        # Mostra anteprima e download
                        dati_ricevuta = scarica_ricevuta(row['ricevuta_percorso'])
                        if dati_ricevuta:
                            ext = os.path.splitext(row['ricevuta_nome'])[1].lower()
                            if ext in ['.png', '.jpg', '.jpeg']:
                                st.image(dati_ricevuta, width=250)
                            st.download_button(
                                ":material/download: Scarica",
                                data=dati_ricevuta,
                                file_name=row['ricevuta_nome'],
                                key=f"dl_ricevuta_{row['id']}",
                                use_container_width=True
                            )
                        else:
                            st.warning("File non disponibile")

# ─── PAGINA: ARCHIVIO PAGAMENTI ────────────────────────────
elif pagina == "Archivio pagamenti":
    st.markdown("### :material/payments: Archivio pagamenti")
    st.caption("Storico completo di tutti i pagamenti registrati.")
    
    # Ottieni tutte le transazioni
    df_tutte_pag = ottieni_transazioni()
    
    if df_tutte_pag.empty:
        st.info(":material/info: Nessun pagamento registrato.")
    else:
        # Filtri
        col_filtri_p1, col_filtri_p2, col_filtri_p3, col_filtri_p4 = st.columns(4)
        with col_filtri_p1:
            filtro_tipo_p = st.selectbox("Tipo", ["Tutti", "Entrata", "Uscita"], key="filtro_tipo_pag")
        with col_filtri_p2:
            filtro_metodo_p = st.selectbox("Metodo", ["Tutti"] + METODI_PAGAMENTO, key="filtro_metodo_pag")
        with col_filtri_p3:
            # Estrai anni
            df_tutte_pag['anno_p'] = pd.to_datetime(df_tutte_pag['data']).dt.year
            anni_p = sorted(df_tutte_pag['anno_p'].unique(), reverse=True)
            filtro_anno_p = st.selectbox("Anno", ["Tutti"] + [str(a) for a in anni_p], key="filtro_anno_pag")
        with col_filtri_p4:
            filtro_persona_p = st.text_input(":material/person: Persona", placeholder="Cerca...", key="filtro_persona_pag")
        
        # Applica filtri
        df_pag_filtrate = df_tutte_pag.copy()
        if filtro_tipo_p != "Tutti":
            df_pag_filtrate = df_pag_filtrate[df_pag_filtrate['tipo'] == filtro_tipo_p]
        if filtro_metodo_p != "Tutti":
            df_pag_filtrate = df_pag_filtrate[df_pag_filtrate['metodo_pagamento'] == filtro_metodo_p]
        if filtro_anno_p != "Tutti":
            df_pag_filtrate = df_pag_filtrate[df_pag_filtrate['anno_p'] == int(filtro_anno_p)]
        if filtro_persona_p:
            df_pag_filtrate = df_pag_filtrate[df_pag_filtrate['persona'].str.contains(filtro_persona_p, case=False, na=False)]
        
        # Riepilogo
        tot_entrate_p = df_pag_filtrate[df_pag_filtrate['tipo'] == 'Entrata']['importo'].sum()
        tot_uscite_p = df_pag_filtrate[df_pag_filtrate['tipo'] == 'Uscita']['importo'].sum()
        
        col_riep_p1, col_riep_p2, col_riep_p3 = st.columns(3)
        with col_riep_p1:
            st.metric(":material/trending_up: Entrate", f"{tot_entrate_p:,.2f} EUR", border=True)
        with col_riep_p2:
            st.metric(":material/trending_down: Uscite", f"{tot_uscite_p:,.2f} EUR", border=True)
        with col_riep_p3:
            st.metric(":material/balance: Saldo", f"{tot_entrate_p - tot_uscite_p:,.2f} EUR", border=True)
        
        st.markdown(f"**{len(df_pag_filtrate)} pagamenti trovati**")
        
        # Mostra tabella
        df_display_p = df_pag_filtrate[['data', 'tipo', 'voce', 'importo', 'metodo_pagamento', 'persona', 'descrizione']].copy()
        df_display_p.columns = ['Data', 'Tipo', 'Voce', 'Importo (EUR)', 'Metodo', 'Persona', 'Descrizione']
        
        def color_tipo_p(val):
            if val == 'Entrata':
                return 'color: #16A34A; font-weight: 600;'
            return 'color: #DC2626; font-weight: 600;'
        
        styled_p = df_display_p.style.map(color_tipo_p, subset=['Tipo']).format({'Importo (EUR)': '{:,.2f}'})
        st.dataframe(styled_p, width='stretch', hide_index=True)
        
        # Export CSV
        csv_data = df_display_p.to_csv(index=False).encode('utf-8')
        st.download_button(
            ":material/download: Scarica CSV",
            data=csv_data,
            file_name=f"pagamenti_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ─── PAGINA: GESTIONE CATEGORIE ────────────────────────────
elif pagina == "Gestione categorie":
    st.markdown("### :material/settings: Gestione categorie")
    
    cc1, cc2 = st.columns(2)
    with cc1:
        with st.container(border=True):
            st.markdown("##### :material/add_circle: Aggiungi categoria")
            tnc = st.selectbox("Tipo", ["Entrata", "Uscita"], key="tipo_cat")
            nnc = st.text_input("Nome", placeholder="Nuova categoria...", key="nome_cat")
            if st.button(":material/add: Aggiungi", use_container_width=True, type="primary"):
                ok, msg = aggiungi_categoria(tnc, nnc)
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(msg)
    with cc2:
        with st.container(border=True):
            st.markdown("##### :material/list: Categorie esistenti")
            tfc = st.segmented_control(
                "Filtra tipo", ["Entrata", "Uscita"],
                default="Entrata",
                selection_mode="single",
                key="filtro_cat"
            )
            df_cat = pd.DataFrame(ottieni_categorie(tfc), columns=["Nome categoria"])
            st.dataframe(df_cat, width='stretch', hide_index=True)

# ─── PAGINA: BACKUP & RIPRISTINO ──────────────────────────
elif pagina == "Backup & Ripristino":
    st.markdown("### :material/save: Backup & Ripristino")
    st.caption("Crea backup manuali dei dati, scaricali e ripristina quando necessario.")
    
    tab_backup, tab_ripristino = st.tabs([
        ":material/save: Crea Backup",
        ":material/restore: Ripristina"
    ])
    
    with tab_backup:
        st.markdown("#### :material/save: Crea un nuovo backup")
        st.info("Il backup salva tutte le **transazioni**, le **categorie** e le **scadenze** in un file JSON scaricabile.")
        
        if st.button(":material/backup: Crea backup ora", type="primary", use_container_width=True):
            with st.spinner("Creazione backup in corso..."):
                ok, risultato = esegui_backup()
                if ok:
                    nome_file, percorso = risultato
                    st.success(f"✅ Backup creato con successo!")
                    with open(percorso, "rb") as f:
                        dati_file = f.read()
                    st.download_button(
                        ":material/download: Scarica backup",
                        data=dati_file,
                        file_name=nome_file,
                        mime="application/json",
                        use_container_width=True
                    )
                else:
                    st.error(risultato)
        
        st.space("small")
        st.markdown("#### :material/history: Backup esistenti")
        backup_disponibili = elenca_backup()
        if not backup_disponibili:
            st.info("Nessun backup ancora creato.")
        else:
            for nome in backup_disponibili:
                percorso = os.path.join(BACKUP_DIR, nome)
                try:
                    dimensione = os.path.getsize(percorso) / 1024
                    with open(percorso, "r", encoding="utf-8") as f:
                        dati = json.load(f)
                    data_creazione = dati.get("creato_il", "N/D")
                    n_tx = len(dati.get("transazioni", []))
                    n_cat = len(dati.get("categorie", []))
                    n_sc = len(dati.get("scadenze", []))
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{nome}**")
                            st.caption(f"Creato il: {data_creazione} • {dimensione:.1f} KB")
                            st.caption(f"📊 {n_tx} transazioni • {n_cat} categorie • {n_sc} scadenze")
                        with c2:
                            with open(percorso, "rb") as f:
                                dati_file = f.read()
                            st.download_button(
                                ":material/download:",
                                data=dati_file,
                                file_name=nome,
                                mime="application/json",
                                key=f"dl_backup_{nome}",
                                use_container_width=True
                            )
                except Exception:
                    pass
    
    with tab_ripristino:
        st.markdown("#### :material/restore: Ripristina da backup")
        st.warning("⚠️ **Attenzione:** il ripristino sovrascriverà tutti i dati attuali su Supabase con quelli del backup selezionato. Questa operazione è irreversibile.")
        
        backup_disponibili = elenca_backup()
        if not backup_disponibili:
            st.info("Nessun backup disponibile per il ripristino.")
        else:
            backup_selezionato = st.selectbox("Seleziona un backup da ripristinare:", backup_disponibili, key="sel_ripristino")
            if backup_selezionato:
                percorso = os.path.join(BACKUP_DIR, backup_selezionato)
                try:
                    with open(percorso, "r", encoding="utf-8") as f:
                        dati = json.load(f)
                    data_creazione = dati.get("creato_il", "N/D")
                    n_tx = len(dati.get("transazioni", []))
                    n_cat = len(dati.get("categorie", []))
                    n_sc = len(dati.get("scadenze", []))
                    st.caption(f"Backup del {data_creazione} • {n_tx} transazioni • {n_cat} categorie • {n_sc} scadenze")
                    
                    conferma = st.checkbox("Ho letto l'avviso e voglio procedere con il ripristino.", key="conferma_ripristino")
                    if st.button(":material/restore: Ripristina ora", type="primary", use_container_width=True, disabled=not conferma):
                        with st.spinner("Ripristino in corso..."):
                            ok_r, msg_r = ripristina_backup(percorso)
                            if ok_r:
                                st.success(f"✅ {msg_r}")
                                st.balloons()
                            else:
                                st.error(msg_r)
                except Exception as e:
                    st.error(f"Errore lettura backup: {str(e)}")
