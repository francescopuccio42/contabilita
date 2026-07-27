import streamlit as st
import pandas as pd
import sqlite3
import os
import shutil
from datetime import datetime, date

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Contabilità Francesco - WebApp",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definizione dei percorsi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "contabilita.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "ricevute_uploads")

# Creazione delle cartelle necessarie
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Funzioni di connessione e gestione Database SQLite
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        # Tabella transazioni
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transazioni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                tipo TEXT NOT NULL,          -- 'Entrata' o 'Uscita'
                voce TEXT NOT NULL,          -- Categoria/Voce di bilancio
                importo REAL NOT NULL,
                descrizione TEXT,
                ricevuta_nome TEXT,          -- Nome file originale
                ricevuta_percorso TEXT       -- Percorso locale del file salvato
            )
        """)
        # Tabella categorie predefinite / personalizzate
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,          -- 'Entrata' o 'Uscita'
                nome TEXT NOT NULL UNIQUE
            )
        """)
        
        # Inserimento o aggiornamento delle categorie richieste dall'utente (con supporto incrementale per gli anni tasse f24)
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
        cursor.executemany("INSERT OR IGNORE INTO categorie (tipo, nome) VALUES (?, ?)", categorie_iniziali)
        conn.commit()

init_db()

# Funzioni CRUD per database
def aggiungi_transazione(data, tipo, voce, importo, descrizione, ricevuta_file):
    ricevuta_nome = None
    ricevuta_percorso = None
    
    if ricevuta_file is not None:
        # Crea un nome file sicuro ed unico usando timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_file_pulito = "".join([c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in ricevuta_file.name])
        ricevuta_nome = ricevuta_file.name
        nome_salvataggio = f"{timestamp}_{nome_file_pulito}"
        ricevuta_percorso = os.path.join(UPLOAD_DIR, nome_salvataggio)
        
        with open(ricevuta_percorso, "wb") as f:
            shutil.copyfileobj(ricevuta_file, f)
            
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transazioni (data, tipo, voce, importo, descrizione, ricevuta_nome, ricevuta_percorso)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data, tipo, voce, importo, descrizione, ricevuta_nome, ricevuta_percorso))
        conn.commit()

def ottieni_transazioni(data_inizio=None, data_fine=None):
    query = "SELECT * FROM transazioni"
    parametri = []
    
    if data_inizio and data_fine:
        query += " WHERE data BETWEEN ? AND ?"
        parametri.extend([data_inizio, data_fine])
    elif data_inizio:
        query += " WHERE data >= ?"
        parametri.append(data_inizio)
    elif data_fine:
        query += " WHERE data <= ?"
        parametri.append(data_fine)
        
    query += " ORDER BY data DESC, id DESC"
    
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=parametri)
    return df

def elimina_transazione(id_transazione, percorso_ricevuta):
    if percorso_ricevuta and os.path.exists(percorso_ricevuta):
        try:
            os.remove(percorso_ricevuta)
        except Exception as e:
            st.error(f"Errore nell'eliminazione del file della ricevuta: {e}")
            
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transazioni WHERE id = ?", (id_transazione,))
        conn.commit()

def ottieni_categorie(tipo=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if tipo:
            cursor.execute("SELECT nome FROM categorie WHERE tipo = ? ORDER BY nome ASC", (tipo,))
        else:
            cursor.execute("SELECT nome FROM categorie ORDER BY nome ASC")
        return [row['nome'] for row in cursor.fetchall()]

def aggiungi_categoria(tipo, nome):
    nome = nome.strip()
    if not nome:
        return False, "Il nome della categoria non può essere vuoto"
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categorie (tipo, nome) VALUES (?, ?)", (tipo, nome))
            conn.commit()
        return True, f"Categoria '{nome}' aggiunta con successo!"
    except sqlite3.IntegrityError:
        return False, "Questa categoria esiste già."

# --- INTERFACCIA UTENTE ---

# Header principale dell'applicazione
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📈 Gestionale Contabilità Francesco</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555;'>La webapp semplice e moderna per monitorare entrate, uscite e archiviare ricevute.</p>", unsafe_allow_html=True)
st.markdown("---")

# Layout principale a Tab
tab_inserimento, tab_resoconto, tab_categorie = st.tabs([
    "📥 Nuova Registrazione", 
    "📊 Resoconto & Analisi", 
    "⚙️ Gestione Categorie"
])

# --- TAB 1: NUOVA REGISTRAZIONE ---
with tab_inserimento:
    st.subheader("Registra un movimento finanziario")
    
    # Grid layout per un inserimento compatto ed elegante
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_movimento = st.radio(
            "Tipo di Movimento *",
            options=["Entrata", "Uscita"],
            horizontal=True,
            help="Scegli se stai registrando un ricavo (Entrata) o una spesa (Uscita)."
        )
        
        # Filtra le categorie in base al tipo selezionato
        categorie_disponibili = ottieni_categorie(tipo_movimento)
        
        voce_selezionata = st.selectbox(
            "Voce di Contabilità (Categoria) *",
            options=categorie_disponibili,
            help="Seleziona la categoria corrispondente. Puoi aggiungerne di nuove nel tab 'Gestione Categorie'."
        )
        
        data_movimento = st.date_input(
            "Data Movimento *",
            value=date.today(),
            help="Seleziona la data in cui è avvenuto il movimento."
        ).strftime("%Y-%m-%d")
        
    with col2:
        importo_movimento = st.number_input(
            "Importo (€) *",
            min_value=0.01,
            value=10.00,
            step=0.01,
            format="%.2f",
            help="Inserisci la cifra esatta del movimento."
        )
        
        descrizione_movimento = st.text_area(
            "Descrizione / Note",
            placeholder="Es. Pagamento fattura n. 45, Spesa cancelleria uffici...",
            height=68,
            help="Inserisci dettagli aggiuntivi facoltativi."
        )
        
        scansione_ricevuta = st.file_uploader(
            "Carica Scansione Ricevuta (PDF, PNG, JPG, JPEG)",
            type=["pdf", "png", "jpg", "jpeg"],
            help="Puoi caricare un file PDF o un'immagine della fattura/ricevuta fiscale."
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Pulsante di inserimento
    if st.button("💾 Registra Movimento", use_container_width=True):
        if not voce_selezionata:
            st.error("Per favore, seleziona una voce di contabilità.")
        else:
            aggiungi_transazione(
                data=data_movimento,
                tipo=tipo_movimento,
                voce=voce_selezionata,
                importo=importo_movimento,
                descrizione=descrizione_movimento,
                ricevuta_file=scansione_ricevuta
            )
            st.success(f"Movimento registrato con successo: {tipo_movimento} di {importo_movimento:.2f} € sotto la voce '{voce_selezionata}'!")
            st.balloons()
            # Ricarica per aggiornare i dati
            st.rerun()


# --- TAB 2: RESOCONTO & ANALISI ---
with tab_resoconto:
    st.subheader("Filtra e analizza i tuoi dati")
    
    # Filtro data da data a data
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        # Data inizio impostata di default a inizio anno corrente
        inizio_anno = date(date.today().year, 1, 1)
        data_inizio_filtro = st.date_input("Dalla data:", value=inizio_anno)
    with col_f2:
        data_fine_filtro = st.date_input("Alla data:", value=date.today())
        
    if data_inizio_filtro > data_fine_filtro:
        st.warning("La data di inizio non può essere successiva alla data di fine!")
        
    # Ottieni i dati filtrati
    df_transazioni = ottieni_transazioni(
        data_inizio=data_inizio_filtro.strftime("%Y-%m-%d"),
        data_fine=data_fine_filtro.strftime("%Y-%m-%d")
    )
    
    if df_transazioni.empty:
        st.info("Nessun movimento registrato nel periodo selezionato.")
    else:
        # Calcolo dei totali
        df_entrate = df_transazioni[df_transazioni['tipo'] == 'Entrata']
        df_uscite = df_transazioni[df_transazioni['tipo'] == 'Uscita']
        
        totale_entrate = df_entrate['importo'].sum()
        totale_uscite = df_uscite['importo'].sum()
        saldo = totale_entrate - totale_uscite
        
        # Visualizzazione metriche in colonne ben leggibili
        st.markdown("### Totale Somme Periodo Selezionato")
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.metric(
                label="🟢 Totale Entrate", 
                value=f"+ {totale_entrate:,.2f} €"
            )
        with col_m2:
            st.metric(
                label="🔴 Totale Uscite", 
                value=f"- {totale_uscite:,.2f} €"
            )
        with col_m3:
            # Colore diverso se saldo positivo o negativo
            colore_saldo = "green" if saldo >= 0 else "red"
            st.metric(
                label="⚖️ Saldo Netto", 
                value=f"{saldo:,.2f} €",
                delta=f"{saldo:,.2f} €"
            )
            
        st.markdown("---")
        
        # Suddivisione in tab interne per visualizzazioni grafiche vs lista
        tab_lista, tab_grafici = st.tabs(["📝 Lista Movimenti", "📊 Analisi per Voci (Categorie)"])
        
        with tab_lista:
            st.subheader("Elenco dettagliato delle transazioni")
            
            # Formattazione colonne per visualizzazione ottimale
            df_display = df_transazioni.copy()
            df_display.columns = ['ID', 'Data', 'Tipo', 'Voce / Categoria', 'Importo (€)', 'Descrizione', 'Ricevuta Originale', 'Percorso Ricevuta']
            
            # Mostriamo la tabella interattiva
            st.dataframe(
                df_display[['Data', 'Tipo', 'Voce / Categoria', 'Importo (€)', 'Descrizione', 'Ricevuta Originale']],
                use_container_width=True
            )
            
            # Sezione per Azioni Rapide (Visualizzare ricevute ed Eliminare elementi)
            st.markdown("### 🔍 Azioni Rapide su Singolo Movimento")
            
            # Crea un selettore per ID movimento per visualizzare o eliminare
            opzioni_selezione = [
                f"ID {row['id']} - {row['data']} | {row['tipo']} | {row['voce']} | {row['importo']:.2f} €" 
                for _, row in df_transazioni.iterrows()
            ]
            
            movimento_selezionato = st.selectbox(
                "Seleziona un movimento per vederne la ricevuta o per eliminarlo:",
                options=opzioni_selezione
            )
            
            if movimento_selezionato:
                # Recupera l'id corretto dal testo del selettore
                id_sel = int(movimento_selezionato.split(" - ")[0].replace("ID ", ""))
                mov_dati = df_transazioni[df_transazioni['id'] == id_sel].iloc[0]
                
                col_azione1, col_azione2 = st.columns([2, 1])
                
                with col_azione1:
                    st.write("**Dettagli Movimento Selezionato:**")
                    st.write(f"- **Data:** {mov_dati['data']}")
                    st.write(f"- **Tipo:** {mov_dati['tipo']}")
                    st.write(f"- **Voce:** {mov_dati['voce']}")
                    st.write(f"- **Importo:** {mov_dati['importo']:.2f} €")
                    st.write(f"- **Descrizione:** {mov_dati['descrizione'] if mov_dati['descrizione'] else 'Nessuna nota'}")
                    
                    if mov_dati['ricevuta_nome']:
                        st.write(f"- 📄 **Ricevuta:** {mov_dati['ricevuta_nome']}")
                        percorso = mov_dati['ricevuta_percorso']
                        if percorso and os.path.exists(percorso):
                            with open(percorso, "rb") as f:
                                dati_file = f.read()
                            
                            # Bottone per scaricare la ricevuta
                            st.download_button(
                                label="⬇️ Scarica / Apri Ricevuta",
                                data=dati_file,
                                file_name=mov_dati['ricevuta_nome'],
                                mime="application/octet-stream"
                            )
                            
                            # Se è un'immagine, mostrala direttamente nell'app!
                            estensione = os.path.splitext(mov_dati['ricevuta_nome'])[1].lower()
                            if estensione in ['.png', '.jpg', '.jpeg']:
                                st.image(percorso, caption="Anteprima Ricevuta", width=400)
                            elif estensione == '.pdf':
                                st.info("La ricevuta è un PDF. Clicca sul pulsante sopra per scaricarla o visualizzarla.")
                        else:
                            st.error("Il file della ricevuta risulta rimosso o non trovato sul server.")
                    else:
                        st.info("Nessuna ricevuta caricata per questo movimento.")
                        
                with col_azione2:
                    st.write("**Elimina Movimento:**")
                    st.warning("L'eliminazione è permanente e rimuoverà anche l'eventuale file di ricevuta associato.")
                    
                    # Pulsante conferma eliminazione
                    if st.button("🗑️ Elimina Definitivamente", type="secondary"):
                        elimina_transazione(mov_dati['id'], mov_dati['ricevuta_percorso'])
                        st.success("Movimento eliminato con successo!")
                        st.rerun()
                        
        with tab_grafici:
            st.subheader("Somma delle cifre per categoria (Voci)")
            
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.markdown("#### 🟢 Entrate suddivise per voce")
                if df_entrate.empty:
                    st.write("Nessuna entrata registrata in questo intervallo.")
                else:
                    sum_entrate_voci = df_entrate.groupby('voce')['importo'].sum().reset_index()
                    sum_entrate_voci.columns = ['Voce', 'Totale (€)']
                    st.dataframe(sum_entrate_voci, use_container_width=True, hide_index=True)
                    
                    # Grafico a barre
                    st.bar_chart(data=sum_entrate_voci, x='Voce', y='Totale (€)', use_container_width=True)
                    
            with col_g2:
                st.markdown("#### 🔴 Uscite suddivise per voce")
                if df_uscite.empty:
                    st.write("Nessuna uscita registrata in questo intervallo.")
                else:
                    sum_uscite_voci = df_uscite.groupby('voce')['importo'].sum().reset_index()
                    sum_uscite_voci.columns = ['Voce', 'Totale (€)']
                    st.dataframe(sum_uscite_voci, use_container_width=True, hide_index=True)
                    
                    # Grafico a barre
                    st.bar_chart(data=sum_uscite_voci, x='Voce', y='Totale (€)', use_container_width=True)


# --- TAB 3: GESTIONE CATEGORIE ---
with tab_categorie:
    st.subheader("Gestisci le categorie (Voci di Bilancio)")
    st.write("Personalizza le voci di spesa e di entrata in base alle tue esigenze aziendali o personali.")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("### Aggiungi Nuova Categoria")
        tipo_nuova_cat = st.selectbox(
            "Seleziona tipo per nuova categoria",
            options=["Entrata", "Uscita"],
            key="tipo_cat"
        )
        nome_nuova_cat = st.text_input(
            "Nome Categoria",
            placeholder="Es. Abbonamento Palestra, Servizio Cloud...",
            key="nome_cat"
        )
        
        if st.button("➕ Aggiungi Categoria", use_container_width=True):
            successo, msg = aggiungi_categoria(tipo_nuova_cat, nome_nuova_cat)
            if successo:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
                
    with col_c2:
        st.markdown("### Categorie Esistenti")
        tipo_filtro_cat = st.radio(
            "Visualizza Categorie di Tipo:",
            options=["Entrata", "Uscita"],
            horizontal=True,
            key="filtro_cat"
        )
        
        lista_cat_correnti = ottieni_categorie(tipo_filtro_cat)
        
        # Mostriamo l'elenco come una comoda tabella
        df_cat = pd.DataFrame(lista_cat_correnti, columns=["Nome Categoria"])
        st.dataframe(df_cat, use_container_width=True, hide_index=True)
