"""Pagine dell'applicazione Streamlit."""
import os
import io
import json
import csv as csv_module
from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st

from config import (
    DEMO_MODE, RICORRENZE, CANALI_PRENOTAZIONE, STATI_PRENOTAZIONE,
    APP_VERSION, APP_NOME, APP_SOTTOTITOLO, BACKUP_DIR,
)

from payment_methods import METODI_PAGAMENTO
from database import (
    aggiungi_transazione, ottieni_transazioni, elimina_transazione,
    ottieni_categorie, aggiungi_categoria,
    ottieni_prenotazioni, aggiungi_prenotazione, aggiorna_stato_prenotazione,
    elimina_prenotazione, registra_prenotazione_contabilita,
    ottieni_scadenze, aggiungi_scadenza, elimina_scadenza,
    registra_pagamento_scadenza, auto_categorizza, genera_testo_resoconto,
    esegui_backup, elenca_backup, ripristina_backup,
    ottieni_operatori, aggiungi_operatore, elimina_operatore, aggiorna_operatore,
    crea_azienda, ottieni_aziende,
)

from storage import scarica_ricevuta


# ═══════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════
def mostra_sidebar():
    """Mostra la sidebar con navigazione e logout."""
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; padding: 0.5rem 0;'>
                <div style='font-size: 2.5rem;'>💶</div>
                <div style='font-weight: 600; font-size: 1.1rem; color: #F8FAFC;'>Contabilità</div>
                <div style='font-size: 0.85rem; color: #94A3B8;'>Francesco</div>
            </div>
        """, unsafe_allow_html=True)
        st.space("small")

        if DEMO_MODE:
            st.info("🔍 **DEMO**")

        pagina = st.radio(
            "Navigazione",
            ["Nuova registrazione", "Carica Estratto Conto", "Prenotazioni & Ospiti", "Scadenzario & Promemoria", "Resoconto & analisi", "Archivio ricevute", "Archivio pagamenti", "Gestione categorie", "Gestione operatori", "Backup & Ripristino", "Guida"],
            captions=["Aggiungi un movimento", "Analizza ed importa da Excel", "Gestisci prenotazioni e ospiti", "Gestisci scadenze e promemoria", "Vedi entrate/uscite/grafici", "Visualizza e cerca ricevute", "Storico completo pagamenti", "Modifica le voci contabili", "Gestisci utenti e accessi", "Salva e ripristina i dati", "Manuale d'uso dell'app"],
            label_visibility="collapsed",
            key="nav"
        )

        st.space("large")
        if st.button(":material/logout: Esci", use_container_width=True):
            st.session_state.autenticato = False
            st.rerun()
        st.caption(f"App v{APP_VERSION} • {datetime.now().year}")
        if DEMO_MODE:
            st.caption("Modalità DEMO 🎬")
        else:
            st.caption("Dati su Supabase ☁️")

    return pagina


# ═══════════════════════════════════════════════════════════
#  HEADER & PROMEMORIA
# ═══════════════════════════════════════════════════════════
def mostra_header():
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


def mostra_promemoria_scadenze():
    """Mostra il banner globale con le scadenze imminenti/scadute."""
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


# ═══════════════════════════════════════════════════════════
#  PAGINA: NUOVA REGISTRAZIONE
# ═══════════════════════════════════════════════════════════
def pagina_nuova_registrazione():
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


# ═══════════════════════════════════════════════════════════
#  PAGINA: CARICA ESTRATTO CONTO
# ═══════════════════════════════════════════════════════════
def pagina_estratto_conto():
    st.markdown("### :material/upload_file: Carica & Analizza Estratto Conto")
    st.caption("Carica il tuo estratto conto bancario in formato **Excel (.xlsx, .xls)** o **CSV (.csv)** per analizzare, categorizzare automaticamente e importare le transazioni nel database.")
    st.caption("💡 **Nota:** Se hai un file PDF, esportalo come Excel o CSV dal tuo home banking, oppure usa la pagina *Nuova registrazione* per inserire manualmente le transazioni.")

    file_caricato = st.file_uploader("Seleziona il file dell'estratto conto", type=["xlsx", "xls", "csv"])
    if file_caricato is not None:
        try:
            nome_file = file_caricato.name.lower()
            estensione = nome_file.split('.')[-1] if '.' in nome_file else ''

            if estensione == 'csv':
                contenuto = file_caricato.getvalue().decode('utf-8', errors='replace')
                try:
                    dialetto = csv_module.Sniffer().sniff(contenuto[:2048], delimiters=',;\t')
                    separatore = dialetto.delimiter
                except Exception:
                    separatore = ';'
                df_excel = pd.read_csv(io.BytesIO(file_caricato.getvalue()), sep=separatore, encoding='utf-8', on_bad_lines='skip')
                foglio_selezionato = "CSV"
            else:
                excel_file = pd.ExcelFile(file_caricato)
                nomi_fogli = excel_file.sheet_names
                if len(nomi_fogli) > 1:
                    foglio_selezionato = st.selectbox("Seleziona il foglio di lavoro:", nomi_fogli)
                else:
                    foglio_selezionato = nomi_fogli[0]
                df_excel = pd.read_excel(file_caricato, sheet_name=foglio_selezionato)

            st.markdown("#### :material/preview: Anteprima del file caricato")
            st.caption("Ecco le prime 10 righe del file. Seleziona le colonne corrispondenti qui sotto.")
            st.dataframe(df_excel.head(10), width='stretch')

            col_sc1, col_sc2, col_sc3 = st.columns(3)
            colonne_disponibili = [""] + list(df_excel.columns)

            def trova_colonna(nomi_possibili, colonne, escludi=None):
                for col in colonne:
                    col_lower = str(col).lower()
                    if escludi and any(e in col_lower for e in escludi):
                        continue
                    if any(p in col_lower for p in nomi_possibili):
                        return col
                return ""

            col_data_prev = trova_colonna(["data contabile", "data operazione", "data"], df_excel.columns, escludi=["valuta"])
            if not col_data_prev:
                col_data_prev = trova_colonna(["data", "date"], df_excel.columns)

            col_desc_prev = trova_colonna(
                ["operazione", "descrizione", "causale", "desc", "dettaglio", "movimento", "beneficiario", "note"],
                df_excel.columns,
                escludi=["data", "valuta", "caus. abi", "abi"]
            )

            col_imp_prev = trova_colonna(
                ["importo", "valore", "ammontare", "quantità", "euro", "eur", "cifra", "dare", "avere"],
                df_excel.columns,
                escludi=["uscita", "entrata"]
            )

            col_imp_ent_prev = trova_colonna(["entrata", "entrate", "avere", "accredito", "accrediti"], df_excel.columns)
            col_imp_usc_prev = trova_colonna(["uscita", "uscite", "dare", "spesa", "spese", "addebito", "addebiti"], df_excel.columns)

            if col_imp_ent_prev and col_imp_usc_prev:
                tipo_importo_default = "Due colonne separate (Entrate e Uscite)"
            else:
                tipo_importo_default = "Colonna singola (segno +/-)"

            with col_sc1:
                col_data = st.selectbox("Colonna Data:", colonne_disponibili, index=colonne_disponibili.index(col_data_prev) if col_data_prev in colonne_disponibili else 0)
            with col_sc2:
                col_desc = st.selectbox("Colonna Descrizione:", colonne_disponibili, index=colonne_disponibili.index(col_desc_prev) if col_desc_prev in colonne_disponibili else 0)
            with col_sc3:
                tipo_importo = st.radio("Struttura importo:", ["Colonna singola (segno +/-)", "Due colonne separate (Entrate e Uscite)"], horizontal=True)

            col_sc4, col_sc5 = st.columns(2)
            if tipo_importo == "Colonna singola (segno +/-)":
                with col_sc4:
                    col_importo = st.selectbox("Colonna Importo:", colonne_disponibili, index=colonne_disponibili.index(col_imp_prev) if col_imp_prev in colonne_disponibili else 0)
                col_importo_entrata = ""
                col_importo_uscita = ""
            else:
                col_imp_ent_prev = trova_colonna(["entrata", "entrate", "avere", "accredito", "accrediti"], df_excel.columns)
                col_imp_usc_prev = trova_colonna(["uscita", "uscite", "dare", "spesa", "spese", "addebito", "addebiti"], df_excel.columns)
                with col_sc4:
                    col_importo_entrata = st.selectbox("Colonna Entrate:", colonne_disponibili, index=colonne_disponibili.index(col_imp_ent_prev) if col_imp_ent_prev in colonne_disponibili else 0)
                with col_sc5:
                    col_importo_uscita = st.selectbox("Colonna Uscite:", colonne_disponibili, index=colonne_disponibili.index(col_imp_usc_prev) if col_imp_usc_prev in colonne_disponibili else 0)
                col_importo = ""

            col_met_def, col_pers_def = st.columns(2)
            with col_met_def:
                metodo_predefinito = st.selectbox("Metodo di pagamento predefinito:", METODI_PAGAMENTO, index=METODI_PAGAMENTO.index("Bonifico") if "Bonifico" in METODI_PAGAMENTO else 0)
            with col_pers_def:
                persona_predefinita = st.text_input("Persona / Ente predefinito (opzionale):", placeholder="Es. Banca, Fornitore...")

            mappatura_ok = False
            if col_data and col_desc:
                if tipo_importo == "Colonna singola (segno +/-)" and col_importo:
                    mappatura_ok = True
                elif tipo_importo == "Due colonne separate (Entrate e Uscite)" and col_importo_entrata and col_importo_uscita:
                    mappatura_ok = True

            if not mappatura_ok:
                st.warning("⚠️ Seleziona le colonne corrette per procedere con l'analisi.")
            else:
                transazioni_elaborate = []

                for idx, row in df_excel.iterrows():
                    val_data = row[col_data]
                    val_desc = row[col_desc]
                    if pd.isna(val_data) or pd.isna(val_desc):
                        continue

                    try:
                        if isinstance(val_data, datetime):
                            data_parsed = val_data.date()
                        elif isinstance(val_data, date):
                            data_parsed = val_data
                        else:
                            data_parsed = pd.to_datetime(val_data).date()
                    except Exception:
                        continue

                    importo_val = 0.0
                    tipo_val = "Uscita"

                    if tipo_importo == "Colonna singola (segno +/-)":
                        val_imp = row[col_importo]
                        if pd.isna(val_imp):
                            continue
                        try:
                            if isinstance(val_imp, str):
                                val_imp_cleaned = val_imp.strip().replace('.', '').replace(',', '.')
                                importo_val = float(val_imp_cleaned)
                            else:
                                importo_val = float(val_imp)
                        except Exception:
                            continue

                        if importo_val == 0:
                            continue

                        if importo_val > 0:
                            tipo_val = "Entrata"
                        else:
                            tipo_val = "Uscita"
                            importo_val = abs(importo_val)
                    else:
                        val_ent = row[col_importo_entrata]
                        val_usc = row[col_importo_uscita]

                        ent_valida = False
                        usc_valida = False

                        try:
                            if not pd.isna(val_ent) and str(val_ent).strip() != "":
                                f_ent = float(str(val_ent).replace('.', '').replace(',', '.')) if isinstance(val_ent, str) else float(val_ent)
                                if f_ent != 0:
                                    ent_valida = True
                                    importo_val = abs(f_ent)
                        except Exception:
                            pass

                        try:
                            if not ent_valida and not pd.isna(val_usc) and str(val_usc).strip() != "":
                                f_usc = float(str(val_usc).replace('.', '').replace(',', '.')) if isinstance(val_usc, str) else float(val_usc)
                                if f_usc != 0:
                                    usc_valida = True
                                    importo_val = abs(f_usc)
                        except Exception:
                            pass

                        if ent_valida:
                            tipo_val = "Entrata"
                        elif usc_valida:
                            tipo_val = "Uscita"
                        else:
                            continue

                    desc_str = str(val_desc).strip()
                    voce_automatica = auto_categorizza(desc_str, tipo_val)

                    transazioni_elaborate.append({
                        "Importa": True,
                        "Data": data_parsed,
                        "Tipo": tipo_val,
                        "Voce": voce_automatica,
                        "Importo": importo_val,
                        "Metodo": metodo_predefinito,
                        "Persona": persona_predefinita if persona_predefinita else "",
                        "Descrizione": desc_str
                    })

                if not transazioni_elaborate:
                    st.error("Nessuna riga valida trovata nel file Excel con i criteri selezionati.")
                else:
                    df_elaborato = pd.DataFrame(transazioni_elaborate)

                    st.markdown("#### :material/analytics: Analisi e Categorizzazione Automatica")

                    min_date = df_elaborato['Data'].min()
                    max_date = df_elaborato['Data'].max()
                    try:
                        df_esistenti = ottieni_transazioni(min_date.strftime("%Y-%m-%d"), max_date.strftime("%Y-%m-%d"))
                    except Exception:
                        df_esistenti = pd.DataFrame()

                    if not df_esistenti.empty:
                        df_esistenti['data_str'] = df_esistenti['data'].astype(str)
                        df_elaborato['data_str'] = df_elaborato['Data'].astype(str)

                        possibili_duplicati = 0
                        for idx_el, row_el in df_elaborato.iterrows():
                            match = df_esistenti[
                                (df_esistenti['data_str'] == row_el['data_str']) &
                                (df_esistenti['importo'].round(2) == round(row_el['Importo'], 2))
                            ]
                            if not match.empty:
                                df_elaborato.at[idx_el, 'Importa'] = False
                                possibili_duplicati += 1

                        if possibili_duplicati > 0:
                            st.warning(f"⚠️ Rilevati {possibili_duplicati} possibili duplicati già presenti nel database! Queste righe sono state deselezionate automaticamente nella tabella sottostante.")

                        df_elaborato.drop(columns=['data_str'], inplace=True)

                    df_filtrato_importa = df_elaborato[df_elaborato['Importa'] == True]

                    tot_ent = df_filtrato_importa[df_filtrato_importa['Tipo'] == 'Entrata']['Importo'].sum()
                    tot_usc = df_filtrato_importa[df_filtrato_importa['Tipo'] == 'Uscita']['Importo'].sum()

                    st.markdown("##### :material/dashboard: Resoconto dell'Estratto Conto (Selezionati per l'importazione)")
                    col_rep1, col_rep2, col_rep3 = st.columns(3)
                    with col_rep1:
                        st.metric("Totale Entrate", f"{tot_ent:,.2f} EUR")
                    with col_rep2:
                        st.metric("Totale Uscite", f"{tot_usc:,.2f} EUR")
                    with col_rep3:
                        st.metric("Saldo Netto", f"{tot_ent - tot_usc:,.2f} EUR")

                    st.markdown("##### :material/account_balance: Saldo iniziale e finale")
                    col_saldo1, col_saldo2, col_saldo3 = st.columns(3)
                    with col_saldo1:
                        saldo_iniziale = st.number_input(
                            "Saldo iniziale (EUR)", min_value=0.0, value=0.0, step=100.00, format="%.2f",
                            help="Inserisci il saldo del conto all'inizio del periodo dell'estratto conto.",
                            key="saldo_iniziale_ec"
                        )
                    with col_saldo2:
                        saldo_finale = st.number_input(
                            "Saldo finale (EUR)", min_value=0.0, value=0.0, step=100.00, format="%.2f",
                            help="Inserisci il saldo del conto alla fine del periodo dell'estratto conto.",
                            key="saldo_finale_ec"
                        )
                    with col_saldo3:
                        saldo_calcolato = saldo_iniziale + tot_ent - tot_usc
                        st.metric(
                            "Saldo calcolato",
                            f"{saldo_calcolato:,.2f} EUR",
                            delta=f"{saldo_finale - saldo_calcolato:,.2f} EUR",
                            delta_color="normal" if abs(saldo_finale - saldo_calcolato) < 0.01 else "inverse",
                            help="Saldo iniziale + entrate - uscite. Confrontalo con il saldo finale dichiarato dalla banca."
                        )
                        if abs(saldo_finale - saldo_calcolato) >= 0.01 and saldo_finale > 0:
                            st.warning(f"⚠️ Differenza di {abs(saldo_finale - saldo_calcolato):,.2f} EUR tra il saldo calcolato e quello dichiarato. Verifica che tutte le transazioni siano state incluse.")

                    st.markdown("##### :material/table_chart: Totali per singola voce")
                    df_tot_voci = df_filtrato_importa.groupby(['Tipo', 'Voce'])['Importo'].sum().reset_index()
                    df_tot_voci.columns = ['Tipo', 'Voce', 'Totale (EUR)']
                    df_tot_voci = df_tot_voci.sort_values(['Tipo', 'Totale (EUR)'], ascending=[True, False])

                    col_tv1, col_tv2 = st.columns(2)
                    with col_tv1:
                        with st.container(border=True):
                            st.markdown("**:material/trending_up: Entrate per voce**")
                            df_tot_ent_voci = df_tot_voci[df_tot_voci['Tipo'] == 'Entrata']
                            if not df_tot_ent_voci.empty:
                                st.dataframe(
                                    df_tot_ent_voci[['Voce', 'Totale (EUR)']].style.format({'Totale (EUR)': '{:,.2f}'}),
                                    hide_index=True, width='stretch'
                                )
                            else:
                                st.info("Nessuna entrata selezionata.")
                    with col_tv2:
                        with st.container(border=True):
                            st.markdown("**:material/trending_down: Uscite per voce**")
                            df_tot_usc_voci = df_tot_voci[df_tot_voci['Tipo'] == 'Uscita']
                            if not df_tot_usc_voci.empty:
                                st.dataframe(
                                    df_tot_usc_voci[['Voce', 'Totale (EUR)']].style.format({'Totale (EUR)': '{:,.2f}'}),
                                    hide_index=True, width='stretch'
                                )
                            else:
                                st.info("Nessuna uscita selezionata.")

                    col_gr1, col_gr2 = st.columns(2)
                    with col_gr1:
                        st.markdown("**Suddivisione Spese per Tipologia/Categoria**")
                        df_spese = df_filtrato_importa[df_filtrato_importa['Tipo'] == 'Uscita']
                        if not df_spese.empty:
                            spese_raggruppate = df_spese.groupby('Voce')['Importo'].sum().reset_index()
                            st.bar_chart(data=spese_raggruppate, x='Voce', y='Importo', use_container_width=True)
                        else:
                            st.info("Nessuna spesa selezionata.")

                    with col_gr2:
                        st.markdown("**Dettaglio Utenze (Bollette luce, gas, internet ecc.)**")
                        df_utenze = df_filtrato_importa[
                            (df_filtrato_importa['Tipo'] == 'Uscita') &
                            (df_filtrato_importa['Voce'].isin(['Bollette luce gas appartamenti', 'Internet']))
                        ]
                        if not df_utenze.empty:
                            utenze_raggruppate = df_utenze.groupby('Voce')['Importo'].sum().reset_index()
                            st.bar_chart(data=utenze_raggruppate, x='Voce', y='Importo', use_container_width=True)
                            st.dataframe(df_utenze[['Data', 'Voce', 'Importo', 'Descrizione']], hide_index=True)
                        else:
                            st.info("Nessuna utenza o bolletta rilevata tra le transazioni selezionate.")

                    st.markdown("#### :material/edit: Modifica e Valida le Transazioni prima del Salvataggio")
                    st.caption("Puoi modificare le categorie, i metodi di pagamento, la descrizione o deselezionare le righe che non desideri importare.")

                    tutte_categorie_db = list(set(ottieni_categorie('Entrata') + ottieni_categorie('Uscita')))
                    if not tutte_categorie_db:
                        tutte_categorie_db = ['Accredito', 'Fatturato / Vendite', 'Prestazione Servizi', 'Altro (Entrata)', 'Addebito', 'Cassa', 'Affitto', 'Stipendi', 'Bollette luce gas appartamenti', 'Internet', 'Tasse di soggiorno', 'Altro (Uscita)']

                    edited_df = st.data_editor(
                        df_elaborato,
                        column_config={
                            "Importa": st.column_config.CheckboxColumn("Importa?", default=True),
                            "Data": st.column_config.DateColumn("Data", disabled=True),
                            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrata", "Uscita"]),
                            "Voce": st.column_config.SelectboxColumn("Voce (Categoria)", options=tutte_categorie_db),
                            "Importo": st.column_config.NumberColumn("Importo (EUR)", format="%.2f"),
                            "Metodo": st.column_config.SelectboxColumn("Metodo", options=METODI_PAGAMENTO),
                            "Persona": st.column_config.TextColumn("Persona / Fornitore"),
                            "Descrizione": st.column_config.TextColumn("Descrizione / Causale", width="large")
                        },
                        hide_index=True,
                        use_container_width=True,
                        key="editor_estratto_conto"
                    )

                    if st.button("🚀 Importa Transazioni Selezionate nel Database", type="primary", use_container_width=True):
                        df_da_importare = edited_df[edited_df['Importa'] == True]
                        if df_da_importare.empty:
                            st.warning("Nessuna transazione selezionata per l'importazione.")
                        else:
                            success_count = 0
                            progress_text = "Salvataggio nel database in corso..."
                            my_bar = st.progress(0, text=progress_text)

                            tot_righe = len(df_da_importare)
                            for i, (_, row_imp) in enumerate(df_da_importare.iterrows()):
                                data_str = row_imp['Data'].strftime("%Y-%m-%d") if isinstance(row_imp['Data'], (date, datetime)) else str(row_imp['Data'])
                                ok = aggiungi_transazione(
                                    data_str, row_imp['Tipo'], row_imp['Voce'], float(row_imp['Importo']),
                                    row_imp['Metodo'], row_imp['Persona'], row_imp['Descrizione'], None
                                )
                                if ok:
                                    success_count += 1
                                my_bar.progress((i + 1) / tot_righe, text=f"Importati {i+1}/{tot_righe} movimenti...")

                            my_bar.empty()
                            st.success(f"✅ Importazione completata! {success_count} su {tot_righe} transazioni sono state caricate con successo nel database.")
                            st.balloons()
                            st.button("Pulisci ed esegui un nuovo caricamento", on_click=lambda: st.rerun())
        except Exception as e:
            st.error(f"Errore durante la lettura del file Excel: {str(e)}")


# ═══════════════════════════════════════════════════════════
#  PAGINA: PRENOTAZIONI & OSPITI
# ═══════════════════════════════════════════════════════════
def pagina_prenotazioni():
    st.markdown("### :material/bed: Prenotazioni & Ospiti")
    st.caption("Gestisci le prenotazioni del B&B, gli ospiti e registra i soggiorni in contabilità.")

    df_tutte_pren = ottieni_prenotazioni()
    oggi_p = date.today()

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
                pn_canale = st.selectbox("Canale *", CANALI_PRENOTAZIONE, key="pn_canale")
                pn_importo = st.number_input("Importo soggiorno (EUR) *", min_value=0.0, value=100.00, step=10.00, format="%.2f", key="pn_importo")
                pn_commissione = st.number_input("Commissione canale (EUR)", min_value=0.0, value=0.00, step=5.00, format="%.2f", key="pn_commissione")
                pn_tassa = st.number_input("Tassa di soggiorno (EUR)", min_value=0.0, value=0.00, step=1.00, format="%.2f", key="pn_tassa")
            pn_note = st.text_area("Note", placeholder="Dettagli aggiuntivi...", height=68, key="pn_note")

            if st.button(":material/save: Salva prenotazione", use_container_width=True, type="primary"):
                ok, msg = aggiungi_prenotazione(
                    pn_ospite, pn_check_in, pn_check_out, pn_camera, pn_canale,
                    pn_importo, pn_commissione, pn_tassa, pn_note
                )
                if ok:
                    st.success(f"✅ {msg}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)

    with tab_pren:
        if df_tutte_pren.empty:
            st.info("Nessuna prenotazione registrata.")
        else:
            filtro_stato = st.segmented_control(
                "Filtra per stato",
                ["Tutte", "Confermata", "In corso", "Completata", "Cancellata"],
                default="Tutte",
                selection_mode="single",
                key="filtro_stato_pren"
            )
            df_display_pren = df_tutte_pren.copy()
            if filtro_stato != "Tutte":
                df_display_pren = df_display_pren[df_display_pren['stato'] == filtro_stato]

            if df_display_pren.empty:
                st.info("Nessuna prenotazione con questo stato.")
            else:
                for _, pren in df_display_pren.iterrows():
                    stato = pren['stato']
                    if stato == "Confermata":
                        colore_stato = "#3B82F6"
                        icona_stato = "🟦"
                    elif stato == "In corso":
                        colore_stato = "#F59E0B"
                        icona_stato = "🟧"
                    elif stato == "Completata":
                        colore_stato = "#16A34A"
                        icona_stato = "🟩"
                    else:
                        colore_stato = "#DC2626"
                        icona_stato = "🟥"

                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{pren['ospite']}** {icona_stato}")
                            st.caption(f"📅 {pren['check_in']} → {pren['check_out']} • {pren['pernottamenti']} notti • {pren['camera']}")
                            st.caption(f"🏨 Canale: {pren['canale']} • 💶 {pren['importo']:,.2f} EUR")
                            if pren.get('commissione', 0) > 0:
                                st.caption(f"📉 Commissione: {pren['commissione']:,.2f} EUR")
                            if pren.get('tassa_soggiorno', 0) > 0:
                                st.caption(f"🏛️ Tassa soggiorno: {pren['tassa_soggiorno']:,.2f} EUR")
                            if pren.get('note'):
                                st.caption(f"📝 {pren['note']}")
                        with c2:
                            st.markdown(f"<span style='color:{colore_stato}; font-weight:600;'>{stato}</span>", unsafe_allow_html=True)
                            st.space("small")
                            if stato in ["Confermata", "Completata"]:
                                if st.button(":material/play_arrow: In corso", key=f"in_corso_{pren['id']}", use_container_width=True):
                                    aggiorna_stato_prenotazione(pren['id'], "In corso")
                                    st.rerun()
                            if stato in ["Confermata", "In corso"]:
                                if st.button(":material/check: Completata", key=f"completata_{pren['id']}", use_container_width=True):
                                    aggiorna_stato_prenotazione(pren['id'], "Completata")
                                    st.rerun()
                            if stato == "Completata" and not pren.get('registrata_contabilita', False):
                                if st.button(":material/account_balance: Registra in contabilità", key=f"reg_cont_{pren['id']}", use_container_width=True, type="primary"):
                                    with st.form(key=f"form_reg_cont_{pren['id']}"):
                                        data_pag = st.date_input("Data pagamento", value=date.today(), key=f"data_pag_{pren['id']}")
                                        metodo_pag = st.selectbox("Metodo", METODI_PAGAMENTO, key=f"metodo_pag_{pren['id']}")
                                        if st.form_submit_button(":material/check: Conferma registrazione"):
                                            ok_reg, msg_reg = registra_prenotazione_contabilita(pren, data_pag, metodo_pag)
                                            if ok_reg:
                                                st.success(f"✅ {msg_reg}")
                                                st.rerun()
                                            else:
                                                st.error(msg_reg)
                            if stato == "Cancellata":
                                if st.button(":material/delete: Elimina", key=f"elim_pren_{pren['id']}", use_container_width=True):
                                    elimina_prenotazione(pren['id'])
                                    st.rerun()


# ═══════════════════════════════════════════════════════════
#  PAGINA: SCADENZARIO & PROMEMORIA
# ═══════════════════════════════════════════════════════════
def pagina_scadenzario():
    st.markdown("### :material/calendar_clock: Scadenzario & Promemoria")
    st.caption("Gestisci le scadenze (bollette, rate, F24, affitti...) e registra i pagamenti in contabilità.")

    df_scadenze = ottieni_scadenze()
    oggi_s = date.today()

    if not df_scadenze.empty:
        df_scadenze['dt_scad'] = pd.to_datetime(df_scadenze['data_scadenza']).dt.date
        df_scadute = df_scadenze[(df_scadenze['stato'] == 'In attesa') & (df_scadenze['dt_scad'] < oggi_s)]
        df_imminenti = df_scadenze[(df_scadenze['stato'] == 'In attesa') & (df_scadenze['dt_scad'] >= oggi_s) & (df_scadenze['dt_scad'] <= oggi_s + timedelta(days=7))]
        df_future = df_scadenze[(df_scadenze['stato'] == 'In attesa') & (df_scadenze['dt_scad'] > oggi_s + timedelta(days=7))]
        df_pagate = df_scadenze[df_scadenze['stato'] == 'Pagato']

        col_sm1, col_sm2, col_sm3, col_sm4 = st.columns(4)
        with col_sm1:
            st.metric(":material/error: Scadute", f"{len(df_scadute)}", border=True)
        with col_sm2:
            st.metric(":material/schedule: In arrivo (7gg)", f"{len(df_imminenti)}", border=True)
        with col_sm3:
            st.metric(":material/event: Future", f"{len(df_future)}", border=True)
        with col_sm4:
            st.metric(":material/check_circle: Pagate", f"{len(df_pagate)}", border=True)

        st.space("small")

    tab_scad, tab_nuova_scad = st.tabs([
        ":material/format_list_bulleted: Elenco scadenze",
        ":material/add_circle: Nuova scadenza"
    ])

    with tab_nuova_scad:
        st.markdown("#### :material/add_circle: Registra una nuova scadenza")
        with st.container(border=True):
            col_sn1, col_sn2 = st.columns(2)
            with col_sn1:
                sn_descrizione = st.text_input("Descrizione *", placeholder="Es. Affitto appartamento", key="sn_descrizione")
                sn_tipo = st.segmented_control("Tipo", ["Uscita", "Entrata"], default="Uscita", selection_mode="single", key="sn_tipo")
                sn_voce = st.selectbox("Voce *", ottieni_categorie(sn_tipo), key="sn_voce")
                sn_importo = st.number_input("Importo (EUR) *", min_value=0.01, value=100.00, step=10.00, format="%.2f", key="sn_importo")
            with col_sn2:
                sn_data = st.date_input("Data scadenza *", value=oggi_s + timedelta(days=30), key="sn_data")
                sn_ricorrenza = st.selectbox("Ricorrenza", RICORRENZE, key="sn_ricorrenza")
                sn_metodo = st.selectbox("Metodo di pagamento", METODI_PAGAMENTO, key="sn_metodo")
                sn_persona = st.text_input("Persona / Ente", placeholder="Es. Enel, Agenzia Entrate...", key="sn_persona")
            sn_note = st.text_area("Note", placeholder="Dettagli aggiuntivi...", height=68, key="sn_note")

            if st.button(":material/save: Salva Scadenza", use_container_width=True, type="primary"):
                ok, msg = aggiungi_scadenza(
                    sn_descrizione, sn_tipo, sn_voce, sn_importo, sn_data,
                    sn_ricorrenza, sn_metodo, sn_persona, sn_note
                )
                if ok:
                    st.success(f"✅ {msg}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)

    with tab_scad:
        if df_scadenze.empty:
            st.info("Nessuna scadenza registrata.")
        else:
            filtro_stato_scad = st.segmented_control(
                "Filtra per stato",
                ["Tutte", "In attesa", "Pagato"],
                default="Tutte",
                selection_mode="single",
                key="filtro_stato_scad"
            )
            df_display_scad = df_scadenze.copy()
            if filtro_stato_scad != "Tutte":
                df_display_scad = df_display_scad[df_display_scad['stato'] == filtro_stato_scad]

            if df_display_scad.empty:
                st.info("Nessuna scadenza con questo stato.")
            else:
                for _, scad in df_display_scad.iterrows():
                    stato_scad = scad['stato']
                    dt_scad = pd.to_datetime(scad['data_scadenza']).date()

                    if stato_scad == "Pagato":
                        colore_scad = "#16A34A"
                        icona_scad = "🟢"
                    elif dt_scad < oggi_s:
                        colore_scad = "#DC2626"
                        icona_scad = "🚨"
                    elif dt_scad <= oggi_s + timedelta(days=7):
                        colore_scad = "#F59E0B"
                        icona_scad = "⏰"
                    else:
                        colore_scad = "#16A34A"
                        icona_scad = "🟢"

                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{scad['descrizione']}** {icona_scad}")
                            st.caption(f"📅 Scadenza: {scad['data_scadenza']} • 💶 {scad['importo']:,.2f EUR} • {scad['tipo']}")
                            st.caption(f"🏷️ Voce: {scad['voce']} • 🔄 Ricorrenza: {scad['ricorrenza']}")
                            if scad.get('persona'):
                                st.caption(f"👤 {scad['persona']}")
                            if scad.get('note'):
                                st.caption(f"📝 {scad['note']}")
                        with c2:
                            st.markdown(f"<span style='color:{colore_scad}; font-weight:600;'>{stato_scad}</span>", unsafe_allow_html=True)
                            st.space("small")
                            if stato_scad == "In attesa":
                                if st.button(":material/payments: Segna come Pagato", key=f"paga_scad_{scad['id']}", use_container_width=True, type="primary"):
                                    with st.form(key=f"form_paga_scad_{scad['id']}"):
                                        data_pag_scad = st.date_input("Data pagamento", value=date.today(), key=f"data_pag_scad_{scad['id']}")
                                        metodo_pag_scad = st.selectbox("Metodo", METODI_PAGAMENTO, key=f"metodo_pag_scad_{scad['id']}")
                                        if st.form_submit_button(":material/check: Conferma pagamento"):
                                            ok_pag, msg_pag = registra_pagamento_scadenza(scad, data_pag_scad, metodo_pag_scad)
                                            if ok_pag:
                                                st.success(f"✅ {msg_pag}")
                                                st.rerun()
                                            else:
                                                st.error(msg_pag)
                            if st.button(":material/delete: Elimina", key=f"elim_scad_{scad['id']}", use_container_width=True):
                                elimina_scadenza(scad['id'])
                                st.rerun()


# ═══════════════════════════════════════════════════════════
#  PAGINA: RESOCONTO & ANALISI
# ═══════════════════════════════════════════════════════════
def pagina_resoconto():
    st.markdown("### :material/analytics: Resoconto & analisi")
    st.caption("Visualizza il quadro completo della tua contabilità nel periodo selezionato.")

    oggi_r = date.today()
    inizio_mese = oggi_r.replace(day=1)

    col_per1, col_per2 = st.columns(2)
    with col_per1:
        data_inizio = st.date_input("Data inizio", value=inizio_mese, key="data_inizio_res")
    with col_per2:
        data_fine = st.date_input("Data fine", value=oggi_r, key="data_fine_res")

    if data_inizio > data_fine:
        st.error("La data di inizio non può essere successiva alla data di fine.")
        return

    df_tutte = ottieni_transazioni(data_inizio, data_fine)

    if df_tutte.empty:
        st.info("Nessuna transazione nel periodo selezionato.")
        return

    df_entrate = df_tutte[df_tutte['tipo'] == 'Entrata']
    df_uscite = df_tutte[df_tutte['tipo'] == 'Uscita']
    tot_entrate = df_entrate['importo'].sum()
    tot_uscite = df_uscite['importo'].sum()
    saldo = tot_entrate - tot_uscite

    col_riep1, col_riep2, col_riep3 = st.columns(3)
    with col_riep1:
        st.metric(":material/trending_up: Entrate", f"{tot_entrate:,.2f} EUR", border=True)
    with col_riep2:
        st.metric(":material/trending_down: Uscite", f"{tot_uscite:,.2f} EUR", border=True)
    with col_riep3:
        st.metric(":material/balance: Saldo", f"{saldo:,.2f} EUR", border=True)

    st.space("small")

    tab_res, tab_analisi, tab_fiscale = st.tabs([
        ":material/table: Transazioni",
        ":material/pie_chart: Analisi",
        ":material/description: Report fiscali"
    ])

    with tab_res:
        st.markdown(f"**{len(df_tutte)} transazioni nel periodo**")
        df_display = df_tutte[['data', 'tipo', 'voce', 'importo', 'metodo_pagamento', 'persona', 'descrizione']].copy()
        df_display.columns = ['Data', 'Tipo', 'Voce', 'Importo (EUR)', 'Metodo', 'Persona', 'Descrizione']

        def color_tipo(val):
            if val == 'Entrata':
                return 'color: #16A34A; font-weight: 600;'
            return 'color: #DC2626; font-weight: 600;'

        styled = df_display.style.map(color_tipo, subset=['Tipo']).format({'Importo (EUR)': '{:,.2f}'})
        st.dataframe(styled, width='stretch', hide_index=True)

        testo_resoconto = genera_testo_resoconto(df_tutte, data_inizio, data_fine)
        st.download_button(
            ":material/download: Scarica resoconto",
            data=testo_resoconto.encode('utf-8'),
            file_name=f"resoconto_{data_inizio}_{data_fine}.txt",
            mime="text/plain",
            use_container_width=True
        )

    with tab_analisi:
        col_an1, col_an2 = st.columns(2)
        with col_an1:
            st.markdown("##### :material/trending_up: Entrate per voce")
            df_ent_voci = df_entrate.groupby('voce')['importo'].sum().reset_index().sort_values('importo', ascending=False)
            if not df_ent_voci.empty:
                st.dataframe(df_ent_voci.style.format({'importo': '{:,.2f}'}), hide_index=True, width='stretch')
                st.bar_chart(data=df_ent_voci, x='voce', y='importo', use_container_width=True)
            else:
                st.info("Nessuna entrata nel periodo.")
        with col_an2:
            st.markdown("##### :material/trending_down: Uscite per voce")
            df_usc_voci = df_uscite.groupby('voce')['importo'].sum().reset_index().sort_values('importo', ascending=False)
            if not df_usc_voci.empty:
                st.dataframe(df_usc_voci.style.format({'importo': '{:,.2f}'}), hide_index=True, width='stretch')
                st.bar_chart(data=df_usc_voci, x='voce', y='importo', use_container_width=True)
            else:
                st.info("Nessuna uscita nel periodo.")

        st.markdown("##### :material/payments: Analisi per metodo di pagamento")
        df_metodo = df_tutte.groupby('metodo_pagamento')['importo'].sum().reset_index().sort_values('importo', ascending=False)
        if not df_metodo.empty:
            st.dataframe(df_metodo.style.format({'importo': '{:,.2f}'}), hide_index=True, width='stretch')
            st.bar_chart(data=df_metodo, x='metodo_pagamento', y='importo', use_container_width=True)

    with tab_fiscale:
        st.markdown("##### :material/description: Report fiscale")
        st.caption("Riepilogo mensile e trimestrale per la dichiarazione fiscale.")

        df_tutte['mese'] = pd.to_datetime(df_tutte['data']).dt.to_period('M')
        df_tutte['trimestre'] = pd.to_datetime(df_tutte['data']).dt.to_period('Q')

        df_mensile = df_tutte.groupby(['mese', 'tipo'])['importo'].sum().unstack(fill_value=0)
        df_mensile['Saldo'] = df_mensile.get('Entrata', 0) - df_mensile.get('Uscita', 0)
        df_mensile.columns = ['Entrate', 'Uscite', 'Saldo']
        st.markdown("**Riepilogo mensile**")
        st.dataframe(df_mensile.style.format('{:,.2f}'), width='stretch')

        df_trimestrale = df_tutte.groupby(['trimestre', 'tipo'])['importo'].sum().unstack(fill_value=0)
        df_trimestrale['Saldo'] = df_trimestrale.get('Entrata', 0) - df_trimestrale.get('Uscita', 0)
        df_trimestrale.columns = ['Entrate', 'Uscite', 'Saldo']
        st.markdown("**Riepilogo trimestrale**")
        st.dataframe(df_trimestrale.style.format('{:,.2f}'), width='stretch')

        testo_fiscale = f"""
REPORT FISCALE
Periodo: {data_inizio} -> {data_fine}
Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}

RIEPILOGO MENSILE:
{df_mensile.to_string()}

RIEPILOGO TRIMESTRALE:
{df_trimestrale.to_string()}

TOTALE ENTRATE: {tot_entrate:,.2f} EUR
TOTALE USCITE: {tot_uscite:,.2f} EUR
SALDO: {saldo:,.2f} EUR
"""
        st.download_button(
            ":material/download: Scarica report fiscale",
            data=testo_fiscale.encode('utf-8'),
            file_name=f"report_fiscale_{data_inizio}_{data_fine}.txt",
            mime="text/plain",
            use_container_width=True
        )


# ═══════════════════════════════════════════════════════════
#  PAGINA: ARCHIVIO RICEVUTE
# ═══════════════════════════════════════════════════════════
def pagina_archivio_ricevute():
    st.markdown("### :material/folder: Archivio ricevute")
    st.caption("Visualizza, cerca e scarica tutte le ricevute caricate con i movimenti.")

    df_tutte_ricevute = ottieni_transazioni()
    df_con_ricevute = df_tutte_ricevute[df_tutte_ricevute['ricevuta_nome'].notna()] if not df_tutte_ricevute.empty else pd.DataFrame()

    if df_con_ricevute.empty:
        st.info("Nessuna ricevuta caricata.")
        return

    col_fr1, col_fr2, col_fr3 = st.columns(3)
    with col_fr1:
        filtro_tipo_r = st.selectbox("Tipo", ["Tutti", "Entrata", "Uscita"], key="filtro_tipo_ricevute")
    with col_fr2:
        df_con_ricevute['anno_r'] = pd.to_datetime(df_con_ricevute['data']).dt.year
        anni_r = sorted(df_con_ricevute['anno_r'].unique(), reverse=True)
        filtro_anno_r = st.selectbox("Anno", ["Tutti"] + [str(a) for a in anni_r], key="filtro_anno_ricevute")
    with col_fr3:
        filtro_desc_r = st.text_input(":material/search: Cerca", placeholder="Descrizione...", key="filtro_desc_ricevute")

    df_ricevute_filtrate = df_con_ricevute.copy()
    if filtro_tipo_r != "Tutti":
        df_ricevute_filtrate = df_ricevute_filtrate[df_ricevute_filtrate['tipo'] == filtro_tipo_r]
    if filtro_anno_r != "Tutti":
        df_ricevute_filtrate = df_ricevute_filtrate[df_ricevute_filtrate['anno_r'] == int(filtro_anno_r)]
    if filtro_desc_r:
        df_ricevute_filtrate = df_ricevute_filtrate[df_ricevute_filtrate['descrizione'].str.contains(filtro_desc_r, case=False, na=False)]

    st.markdown(f"**{len(df_ricevute_filtrate)} ricevute trovate**")

    for _, row in df_ricevute_filtrate.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{row['voce']}**")
                st.caption(f"📅 {row['data']} • 💶 {row['importo']:,.2f} EUR • {row['tipo']}")
                if row.get('descrizione'):
                    st.caption(f"📝 {row['descrizione']}")
            with c2:
                nome_file = row['ricevuta_nome']
                dati_file = scarica_ricevuta(row['ricevuta_percorso'] or row['ricevuta_nome'])
                if dati_file:
                    st.download_button(
                        ":material/download: Scarica",
                        data=dati_file,
                        file_name=nome_file,
                        mime="application/octet-stream",
                        key=f"dl_ricevuta_{row['id']}",
                        use_container_width=True
                    )


# ═══════════════════════════════════════════════════════════
#  PAGINA: ARCHIVIO PAGAMENTI
# ═══════════════════════════════════════════════════════════
def pagina_archivio_pagamenti():
    st.markdown("### :material/payments: Archivio pagamenti")
    st.caption("Storico completo di tutti i pagamenti registrati.")

    df_tutte_pag = ottieni_transazioni()

    if df_tutte_pag.empty:
        st.info(":material/info: Nessun pagamento registrato.")
    else:
        col_filtri_p1, col_filtri_p2, col_filtri_p3, col_filtri_p4 = st.columns(4)
        with col_filtri_p1:
            filtro_tipo_p = st.selectbox("Tipo", ["Tutti", "Entrata", "Uscita"], key="filtro_tipo_pag")
        with col_filtri_p2:
            filtro_metodo_p = st.selectbox("Metodo", ["Tutti"] + METODI_PAGAMENTO, key="filtro_metodo_pag")
        with col_filtri_p3:
            df_tutte_pag['anno_p'] = pd.to_datetime(df_tutte_pag['data']).dt.year
            anni_p = sorted(df_tutte_pag['anno_p'].unique(), reverse=True)
            filtro_anno_p = st.selectbox("Anno", ["Tutti"] + [str(a) for a in anni_p], key="filtro_anno_pag")
        with col_filtri_p4:
            filtro_persona_p = st.text_input(":material/person: Persona", placeholder="Cerca...", key="filtro_persona_pag")

        df_pag_filtrate = df_tutte_pag.copy()
        if filtro_tipo_p != "Tutti":
            df_pag_filtrate = df_pag_filtrate[df_pag_filtrate['tipo'] == filtro_tipo_p]
        if filtro_metodo_p != "Tutti":
            df_pag_filtrate = df_pag_filtrate[df_pag_filtrate['metodo_pagamento'] == filtro_metodo_p]
        if filtro_anno_p != "Tutti":
            df_pag_filtrate = df_pag_filtrate[df_pag_filtrate['anno_p'] == int(filtro_anno_p)]
        if filtro_persona_p:
            df_pag_filtrate = df_pag_filtrate[df_pag_filtrate['persona'].str.contains(filtro_persona_p, case=False, na=False)]

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

        df_display_p = df_pag_filtrate[['data', 'tipo', 'voce', 'importo', 'metodo_pagamento', 'persona', 'descrizione']].copy()
        df_display_p.columns = ['Data', 'Tipo', 'Voce', 'Importo (EUR)', 'Metodo', 'Persona', 'Descrizione']

        def color_tipo_p(val):
            if val == 'Entrata':
                return 'color: #16A34A; font-weight: 600;'
            return 'color: #DC2626; font-weight: 600;'

        styled_p = df_display_p.style.map(color_tipo_p, subset=['Tipo']).format({'Importo (EUR)': '{:,.2f}'})
        st.dataframe(styled_p, width='stretch', hide_index=True)

        csv_data = df_display_p.to_csv(index=False).encode('utf-8')
        st.download_button(
            ":material/download: Scarica CSV",
            data=csv_data,
            file_name=f"pagamenti_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )


# ═══════════════════════════════════════════════════════════
#  PAGINA: GESTIONE CATEGORIE
# ═══════════════════════════════════════════════════════════
def pagina_gestione_categorie():
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


# ═══════════════════════════════════════════════════════════
#  PAGINA: GESTIONE OPERATORI
# ═══════════════════════════════════════════════════════════
def pagina_gestione_operatori():
    st.markdown("### :material/group: Gestione operatori")
    st.caption("Gestisci gli utenti che possono accedere all'applicazione.")

    if DEMO_MODE:
        st.info("🔍 In modalità DEMO la gestione operatori è disabilitata. Attiva la modalità reale per gestire gli operatori.")

    # Mostra l'azienda corrente
    azienda_nome = st.session_state.get('azienda_nome', '')
    if azienda_nome:
        st.info(f"🏢 **Azienda corrente:** {azienda_nome}")

    df_op = ottieni_operatori()

    col_op1, col_op2 = st.columns(2)
    with col_op1:
        with st.container(border=True):
            st.markdown("##### :material/person_add: Aggiungi operatore")
            with st.form("form_aggiungi_operatore", clear_on_submit=False):
                op_username = st.text_input("Username *", placeholder="Es. mario")
                op_password = st.text_input("Password *", type="password", placeholder="Inserisci password...")
                op_nome = st.text_input("Nome completo", placeholder="Es. Mario Rossi")
                op_ruolo = st.selectbox("Ruolo", ["operatore", "admin"])
                submitted_op = st.form_submit_button(":material/add: Aggiungi operatore", use_container_width=True, type="primary", disabled=DEMO_MODE)
            if submitted_op:
                ok_op, msg_op = aggiungi_operatore(op_username, op_password, op_nome, op_ruolo)
                if ok_op:
                    st.success(f"✅ {msg_op}")
                    st.rerun()
                else:
                    st.error(msg_op)


    with col_op2:
        with st.container(border=True):
            st.markdown("##### :material/group: Operatori esistenti")
            if df_op.empty:
                st.info("Nessun operatore registrato.")
            else:
                for _, op in df_op.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{op.get('nome', op['username'])}**")
                            st.caption(f"👤 Username: {op['username']} • 🎖️ Ruolo: {op.get('ruolo', 'operatore')}")
                            st.caption(f"✅ Attivo: {'Sì' if op.get('attivo', True) else 'No'}")
                            if op.get('azienda_nome'):
                                st.caption(f"🏢 Azienda: {op['azienda_nome']}")
                        with c2:
                            if not DEMO_MODE and op['username'] != st.session_state.get('utente', ''):
                                if st.button(":material/delete: Elimina", key=f"elim_op_{op['id']}", use_container_width=True):
                                    elimina_operatore(op['id'])
                                    st.rerun()

    # Sezione gestione aziende (solo per admin)
    if not DEMO_MODE and st.session_state.get('ruolo', '') == 'admin':
        st.space("medium")
        st.markdown("---")
        st.markdown("### :material/business: Gestione aziende")
        st.caption("Crea nuove aziende (clienti) per l'architettura multi-tenant.")

        col_az1, col_az2 = st.columns(2)
        with col_az1:
            with st.container(border=True):
                st.markdown("##### :material/add_business: Crea nuova azienda")
                az_nome = st.text_input("Nome azienda", placeholder="Es. B&B La Casa di Maria", key="az_nome")
                if st.button(":material/add: Crea azienda", use_container_width=True, type="primary"):
                    ok_az, msg_az = crea_azienda(az_nome)
                    if ok_az:
                        st.success(f"✅ Azienda creata con ID {msg_az}!")
                        st.rerun()
                    else:
                        st.error(msg_az)
        with col_az2:
            with st.container(border=True):
                st.markdown("##### :material/business: Aziende esistenti")
                df_az = ottieni_aziende()
                if df_az.empty:
                    st.info("Nessuna azienda registrata.")
                else:
                    st.dataframe(df_az[['id', 'nome']], width='stretch', hide_index=True)



# ═══════════════════════════════════════════════════════════
#  PAGINA: BACKUP & RIPRISTINO
# ═══════════════════════════════════════════════════════════
def pagina_backup():
    st.markdown("### :material/save: Backup & Ripristino")
    st.caption("Crea backup manuali dei dati, scaricali e ripristina quando necessario.")

    if DEMO_MODE:
        st.info("🔍 In modalità DEMO il backup è disabilitato perché i dati sono dimostrativi.")

    tab_backup, tab_ripristino = st.tabs([
        ":material/save: Crea Backup",
        ":material/restore: Ripristina"
    ])

    with tab_backup:
        st.markdown("#### :material/save: Crea un nuovo backup")
        st.info("Il backup salva tutte le **transazioni**, le **categorie**, le **scadenze**, le **prenotazioni**, gli **operatori** e le **aziende** in un file JSON scaricabile.")
        st.caption("💡 Il backup automatico viene eseguito ogni **7 giorni** in background.")

        if st.button(":material/backup: Crea backup ora", type="primary", use_container_width=True, disabled=DEMO_MODE):
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
                    with open(percorso, "r", encoding="utf-8") as f_text:
                        dati = json.load(f_text)
                    data_creazione = dati.get("creato_il", "N/D")
                    n_tx = len(dati.get("transazioni", []))
                    n_cat = len(dati.get("categorie", []))
                    n_sc = len(dati.get("scadenze", []))
                    n_pr = len(dati.get("prenotazioni", []))
                    n_op = len(dati.get("operatori", []))
                    n_az = len(dati.get("aziende", []))
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{nome}**")
                            st.caption(f"Creato il: {data_creazione} • {dimensione:.1f} KB")
                            st.caption(f"📊 {n_tx} transazioni • {n_cat} categorie • {n_sc} scadenze • {n_pr} prenotazioni • {n_op} operatori • {n_az} aziende")
                        with c2:
                            with open(percorso, "rb") as f_bin:
                                dati_file = f_bin.read()
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
                    with open(percorso, "r", encoding="utf-8") as f_text:
                        dati = json.load(f_text)
                    data_creazione = dati.get("creato_il", "N/D")
                    n_tx = len(dati.get("transazioni", []))
                    n_cat = len(dati.get("categorie", []))
                    n_sc = len(dati.get("scadenze", []))
                    st.caption(f"Backup del {data_creazione} • {n_tx} transazioni • {n_cat} categorie • {n_sc} scadenze")

                    conferma = st.checkbox("Ho letto l'avviso e voglio procedere con il ripristino.", key="conferma_ripristino")
                    if st.button(":material/restore: Ripristina ora", type="primary", use_container_width=True, disabled=not conferma or DEMO_MODE):
                        with st.spinner("Ripristino in corso..."):
                            ok_r, msg_r = ripristina_backup(percorso)
                            if ok_r:
                                st.success(f"✅ {msg_r}")
                                st.balloons()
                            else:
                                st.error(msg_r)
                except Exception as e:
                    st.error(f"Errore lettura backup: {str(e)}")


# ═══════════════════════════════════════════════════════════
#  PAGINA: GUIDA
# ═══════════════════════════════════════════════════════════
def pagina_guida():
    st.markdown("### :material/menu_book: Guida all'uso")
    st.caption("Manuale completo del Gestionale Contabilità Francesco. Seleziona un argomento per scoprire come usare ogni funzione.")

    guida_tab = st.tabs([
        ":material/rocket_launch: Introduzione",
        ":material/add_circle: Registrazione movimenti",
        ":material/upload_file: Estratto conto",
        ":material/bed: Prenotazioni & Ospiti",
        ":material/calendar_clock: Scadenzario",
        ":material/analytics: Resoconto & Analisi",
        ":material/folder: Ricevute & Pagamenti",
        ":material/settings: Categorie",
        ":material/group: Operatori",
        ":material/save: Backup & Ripristino",
        ":material/help: FAQ & Suggerimenti"
    ])

    with guida_tab[0]:
        st.markdown("#### :material/rocket_launch: Benvenuto nel Gestionale Contabilità")
        st.write("""
Questo gestionale ti permette di **monitorare entrate e uscite**, gestire le **prenotazioni del B&B**,
tenere sotto controllo le **scadenze** e **archiviare le ricevute** fiscali, il tutto con i dati salvati
in modo sicuro su **Supabase** (cloud).

**Cosa puoi fare con l'app:**
- 📥 Registrare manualmente entrate e uscite
- 📊 Importare automaticamente gli estratti conto bancari (Excel/CSV)
- 🛏️ Gestire prenotazioni, ospiti, commissioni OTA e tasse di soggiorno
- ⏰ Tenere traccia delle scadenze con promemoria automatici
- 📈 Analizzare i dati con grafici e report fiscali
- 🗂️ Archiviare e cercare le ricevute
- 👥 Gestire più operatori con accessi separati
- 💾 Creare backup e ripristinare i dati
""")
        st.info("💡 **Suggerimento:** usa la barra laterale a sinistra per navigare tra le diverse sezioni dell'app.")

    with guida_tab[1]:
        st.markdown("#### :material/add_circle: Nuova registrazione")
        st.write("""
Questa pagina ti permette di **inserire manualmente** un movimento contabile (entrata o uscita).

**Campi da compilare:**
- **Tipo** — scegli se è un'*Entrata* (denaro che entra) o un'*Uscita* (denaro che esce)
- **Voce** — la categoria contabile (es. Fatturato, Affitto, Bollette...)
- **Data** — la data del movimento
- **Da chi** — il cliente o fornitore (opzionale)
- **Importo** — l'importo in euro
- **Metodo di pagamento** — Contanti, POS, Bonifico, Carta, Assegno o Altro
- **Note** — eventuali dettagli aggiuntivi
- **Ricevuta** — puoi allegare un PDF o un'immagine della ricevuta

Dopo aver compilato i campi, premi **"Registra movimento"** per salvare.
""")
        st.success("✅ Il movimento viene salvato immediatamente su Supabase e sarà visibile in *Resoconto & analisi*.")

    with guida_tab[2]:
        st.markdown("#### :material/upload_file: Carica & Analizza Estratto Conto")
        st.write("""
Questa funzione ti permette di **importare automaticamente** le transazioni dal tuo estratto conto bancario.

**Formati supportati:** Excel (`.xlsx`, `.xls`) e CSV (`.csv`).

**Come funziona:**
1. **Carica il file** dell'estratto conto
2. **Seleziona le colonne** corrispondenti (Data, Descrizione, Importo)
3. **Imposta il metodo di pagamento** predefinito e la persona/ente
4. **L'app analizza e categorizza** automaticamente ogni transazione
5. **Controlla il riepilogo** (totali entrate/uscite, saldo iniziale/finale)
6. **Modifica le transazioni** se necessario (categoria, metodo, descrizione)
7. **Importa** le transazioni selezionate nel database

**Funzioni automatiche:**
- 🔍 **Rilevamento duplicati** — le transazioni già presenti vengono deselezionate automaticamente
- 🏷️ **Categorizzazione automatica** — l'app riconosce bollette, affitti, stipendi, F24, ecc.
- 📊 **Grafici** — suddivisione spese per categoria e dettaglio utenze
""")
        st.warning("💡 **Nota:** Se hai un file PDF, esportalo come Excel o CSV dal tuo home banking prima di caricarlo.")

    with guida_tab[3]:
        st.markdown("#### :material/bed: Prenotazioni & Ospiti")
        st.write("""
Questa sezione ti permette di **gestire le prenotazioni del B&B** e registrare i soggiorni in contabilità.

**Registrare una nuova prenotazione:**
1. Vai nel tab **"Nuova prenotazione"**
2. Inserisci il **nome dell'ospite**, le date di **check-in** e **check-out**
3. Seleziona la **camera**, il **canale** (Diretto, Booking, Airbnb, Expedia, Altro)
4. Inserisci l'**importo del soggiorno**, la **commissione** del canale e la **tassa di soggiorno**
5. Premi **"Salva prenotazione"**

**Stati delle prenotazioni:**
- 🟦 **Confermata** — prenotazione accettata, in attesa
- 🟧 **In corso** — l'ospite è in casa
- 🟩 **Completata** — soggiorno terminato e registrato in contabilità
- 🟥 **Cancellata** — prenotazione annullata

**Registrare in contabilità:**
Quando il soggiorno è completato, premi **"Registra in contabilità"**:
- L'**importo del soggiorno** viene registrato come *entrata* (voce "Fatturato / Vendite")
- La **commissione** del canale viene registrata come *uscita*
- La **tassa di soggiorno** viene registrata come *uscita* separata
""")

    with guida_tab[4]:
        st.markdown("#### :material/calendar_clock: Scadenzario & Promemoria")
        st.write("""
Questa sezione ti aiuta a **non dimenticare le scadenze** (bollette, rate, F24, affitti...).

**Registrare una nuova scadenza:**
1. Vai nel tab **"Nuova scadenza"**
2. Inserisci la **descrizione**, il **tipo** (Uscita/Entrata) e la **voce contabile**
3. Imposta l'**importo** e la **data di scadenza**
4. Scegli la **ricorrenza** (Nessuna, Settimanale, Mensile, Annuale...)
5. Premi **"Salva Scadenza"**

**Promemoria automatici:**
- 🚨 Le scadenze **scadute** vengono evidenziate in rosso
- ⏰ Le scadenze **entro 7 giorni** vengono evidenziate in arancione
- 🟢 Le scadenze **future** sono in verde
- Un **banner globale** in cima all'app ti avvisa delle scadenze imminenti

**Segnare come pagato:**
Quando saldi una scadenza, premi **"Segna come Pagato"**:
- Il movimento viene **registrato automaticamente in contabilità**
- Se la scadenza è **ricorrente**, viene calcolata e impostata la **prossima data**
""")

    with guida_tab[5]:
        st.markdown("#### :material/analytics: Resoconto & analisi")
        st.write("""
Questa pagina ti mostra il **quadro completo** della tua contabilità nel periodo selezionato.

**Funzioni principali:**
- **Riepilogo** — totali entrate, uscite e saldo netto
- **Lista transazioni** — tutte le transazioni del periodo con dettaglio
- **Analisi per voce** — totali e grafici per categoria (entrate e uscite)
- **Analisi per metodo** — totali per metodo di pagamento
- **Report fiscali** — riepilogo mensile e trimestrale per la dichiarazione fiscale

**Esportazioni:**
- 📄 **Scarica resoconto** — file di testo con il dettaglio completo
- 📄 **Scarica report fiscale** — riepilogo mensile/trimestrale per il commercialista
""")

    with guida_tab[6]:
        st.markdown("#### :material/folder: Archivio ricevute & Archivio pagamenti")

        st.markdown("##### :material/folder: Archivio ricevute")
        st.write("""
Visualizza, cerca e scarica tutte le **ricevute** caricate con i movimenti.

**Filtri disponibili:**
- Per **tipo** (Entrata/Uscita)
- Per **anno**
- Per **descrizione** (ricerca testuale)

Le ricevute vengono mostrate in una griglia con anteprima (per le immagini) e pulsante di download.
""")

        st.markdown("##### :material/payments: Archivio pagamenti")
        st.write("""
Storico completo di **tutti i pagamenti** registrati.

**Filtri disponibili:**
- Per **tipo** (Entrata/Uscita)
- Per **metodo** di pagamento
- Per **anno**
- Per **persona**

Include riepilogo entrate/uscite/saldo ed **export CSV** dei dati filtrati.
""")

    with guida_tab[7]:
        st.markdown("#### :material/settings: Gestione categorie")
        st.write("""
Questa pagina ti permette di **gestire le voci contabili** (categorie) usate per classificare i movimenti.

**Aggiungere una categoria:**
1. Seleziona il **tipo** (Entrata o Uscita)
2. Inserisci il **nome** della nuova categoria
3. Premi **"Aggiungi"**

**Visualizzare le categorie:**
- Usa il filtro per tipo per vedere le categorie di entrata o uscita
- Le categorie vengono usate in *Nuova registrazione*, *Scadenzario* e *Estratto conto*
""")
        st.info("💡 Le categorie predefinite vengono create automaticamente al primo avvio dell'app.")

    with guida_tab[8]:
        st.markdown("#### :material/group: Gestione operatori")
        st.write("""
Questa sezione ti permette di **gestire gli operatori** (utenti) che possono accedere all'applicazione.

**Aggiungere un operatore:**
1. Inserisci **username** e **password**
2. Inserisci il **nome completo** (opzionale)
3. Scegli il **ruolo** (operatore o admin)
4. Premi **"Aggiungi operatore"**

**Ruoli:**
- **admin** — accesso completo a tutte le funzioni
- **operatore** — accesso alle funzioni operative

> 💡 Gli operatori vengono salvati nella tabella `operatori` su Supabase.
""")

    with guida_tab[9]:
        st.markdown("#### :material/save: Backup & Ripristino")
        st.write("""
Questa sezione ti permette di **proteggere i tuoi dati** creando backup e ripristinandoli quando necessario.

**Creare un backup:**
1. Vai nel tab **"Crea Backup"**
2. Premi **"Crea backup ora"**
3. Il backup salva **transazioni, categorie e scadenze** in un file JSON
4. Puoi **scaricare** il file per conservarlo in un luogo sicuro

**Ripristinare un backup:**
1. Vai nel tab **"Ripristina"**
2. Seleziona il backup da ripristinare
3. **Leggi attentamente l'avviso** e spunta la conferma
4. Premi **"Ripristina ora"**

> ⚠️ **Attenzione:** il ripristino **sovrascrive tutti i dati attuali** su Supabase con quelli del backup. Questa operazione è **irreversibile**.
""")
        st.success("💡 **Consiglio:** crea un backup regolarmente (es. una volta al mese) e conserva i file in un luogo sicuro.")

    with guida_tab[10]:
        st.markdown("#### :material/help: FAQ & Suggerimenti")

        with st.expander("🔐 Come accedo all'app?"):
            st.write("""
L'app richiede un **login**. Le credenziali vengono configurate nel file `dev_secrets.toml` (in locale)
o nei secrets di Streamlit Cloud. Se non configurato, le credenziali predefinite sono **admin/admin**.
""")

        with st.expander("☁️ Dove vengono salvati i dati?"):
            st.write("""
Tutti i dati (transazioni, categorie, scadenze, prenotazioni) vengono salvati su **Supabase**, un database cloud.
Le **ricevute** vengono caricate su Supabase Storage (con fallback locale). I **backup** vengono salvati in locale nella cartella `backups/`.
""")

        with st.expander("📥 Come importo un estratto conto in PDF?"):
            st.write("""
L'app non legge direttamente i PDF. **Esporta il PDF come Excel o CSV** dal tuo home banking,
poi carica il file nella pagina *Carica Estratto Conto*.
""")

        with st.expander("🔄 Come funzionano le scadenze ricorrenti?"):
            st.write("""
Quando registri una scadenza con una **ricorrenza** (es. Mensile), dopo averla segnata come pagata
l'app calcola automaticamente la **prossima data** e la imposta come nuova scadenza in attesa.
""")

        with st.expander("💾 Con quale frequenza dovrei fare un backup?"):
            st.write("""
È consigliabile creare un backup **almeno una volta al mese**, oppure dopo ogni modifica importante
dei dati. Conserva i file di backup in un luogo sicuro (es. cloud, disco esterno).
""")

        with st.expander("🛏️ Come registro una prenotazione in contabilità?"):
            st.write("""
Quando il soggiorno è completato, nella scheda della prenotazione premi **"Registra in contabilità"**.
L'app registrerà automaticamente l'entrata del soggiorno, la commissione del canale e la tassa di soggiorno.
""")

        with st.expander("📊 Come genero il report fiscale?"):
            st.write("""
Vai in *Resoconto & analisi*, seleziona il periodo desiderato e apri il tab **"Report fiscali"**.
Qui trovi il riepilogo mensile e trimestrale, il grafico andamento e il pulsante per **scaricare il report**.
""")

        with st.expander("👥 Come aggiungo un operatore?"):
            st.write("""
Vai in *Gestione operatori*, inserisci username, password, nome e ruolo, poi premi **"Aggiungi operatore"**.
L'operatore potrà accedere con le proprie credenziali.
""")

        with st.expander("❓ L'app non si avvia. Cosa faccio?"):
            st.write("""
1. Verifica che il file `dev_secrets.toml` o `.env` contenga le credenziali Supabase corrette
2. Verifica che le dipendenze siano installate: `pip install -r requirements.txt`
3. Su Windows, usa **`avvia_app.bat`** (doppio clic) che verifica tutto automaticamente
4. Controlla che le tabelle esistano su Supabase (esegui `supabase_setup.sql`)
""")

        st.space("small")
        st.markdown("---")
        st.caption("Gestionale Contabilità Francesco — Guida in linea v3.0")


