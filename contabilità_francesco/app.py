import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime, date
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

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
os.makedirs(UPLOAD_DIR, exist_ok=True)

METODI_PAGAMENTO = ["Contante", "Bonifico", "Carta", "Assegno", "Altro"]

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
        st.warning(f"Storage non disponibile, salvo in locale: {e}")
        percorso = os.path.join(UPLOAD_DIR, nome_salvato)
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
for key, value in st.secrets.items():
    if key.startswith("LOGIN_USERNAME"):
        suffix = key.replace("LOGIN_USERNAME", "")
        password_key = f"LOGIN_PASSWORD{suffix}"
        password = st.secrets.get(password_key, "")
        if value and password:
            UTENTI[value] = password
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
        ["Nuova registrazione", "Resoconto & analisi", "Gestione categorie"],
        captions=["Aggiungi un movimento", "Vedi entrate/uscite/grafici", "Modifica le voci contabili"],
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

# ─── HEADER ────────────────────────────────────────────────
st.markdown("""
    <div style='text-align: center; padding: 0.8rem 0 0.3rem 0;'>
        <h1 style='color: #1E40AF; margin: 0; font-size: 2rem; font-weight: 700;'>
            💶 Gestionale Contabilità Francesco
        </h1>
        <p style='color: #64748B; margin: 0.2rem 0 0 0; font-size: 0.95rem;'>
            Monitora entrate, uscite e archivia ricevute
        </p>
    </div>
""", unsafe_allow_html=True)

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
        
        tab_lista, tab_grafici, tab_metodi = st.tabs([
            ":material/format_list_bulleted: Lista transazioni",
            ":material/pie_chart: Analisi per voce",
            ":material/payments: Analisi per metodo"
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
