# Changelog

Tutte le modifiche significative a questo progetto saranno documentate in questo file.

## [2.2.0] — 2026-07-28

### Aggiunto
- **Archivio ricevute**: nuova pagina dedicata per visualizzare, cercare e scaricare tutte le ricevute caricate, con filtri per tipo, anno e descrizione.
- **Archivio pagamenti**: nuova pagina con lo storico completo di tutti i pagamenti registrati, filtri avanzati (tipo, metodo, anno, persona), riepilogo entrate/uscite/saldo ed export CSV.
- **Salvataggio ricevute in sottocartelle**: le ricevute salvate localmente vengono ora organizzate in cartelle `anno/mese` per una migliore gestione.

### Modificato
- **Navigazione**: aggiornata la barra laterale con le nuove voci "Archivio ricevute" e "Archivio pagamenti".

## [2.1.0] — 2026-07-28

### Aggiunto
- **Modulo Scadenzario & Promemoria**: nuova sezione per la registrazione e gestione delle scadenze di entrate e uscite.
- **Promemoria automatici (7 giorni prima)**: banner di notifica globale nell'interfaccia dell'app che avvisa delle scadenze imminenti e scadute.
- **Supporto Scadenze Ricorrenti**: gestione della ripetizione (*Settimanale, Quindicinale, Mensile, Bimestrale, Trimestrale, Semestrale, Annuale*).
- **Automazione Saldo Contabile**: al click su "Segna come Pagato", registra automaticamente il movimento contabile in `transazioni` e aggiorna la scadenza successiva per le scadenze ripetute.
- **Tabella Supabase `scadenze`**: aggiornato lo script `supabase_setup.sql` per la creazione della nuova tabella nel database backend.

## [1.1.0] — 2026-07-27

### Aggiunto
- Migrazione da SQLite a **Supabase** come database backend
- File `.env` per la configurazione delle credenziali Supabase
- Script SQL `supabase_setup.sql` per creare le tabelle su Supabase
- Dipendenza `supabase-py` per l'integrazione con Supabase API REST
- Dipendenza `python-dotenv` per la gestione delle variabili d'ambiente
- File `CHANGELOG.md` per tracciare le modifiche
- File `README.md` con documentazione del progetto
- File `.gitignore` aggiornato per escludere `.env` e file sensibili

### Modificato
- `app.py` riscritto: tutte le funzioni CRUD ora comunicano con Supabase invece di SQLite
- Rimosse le dipendenze da `sqlite3` (non più necessario)
- Aggiunta colonna `created_at` nella visualizzazione della tabella transazioni

### Note
- I file delle ricevute rimangono salvati localmente in `ricevute_uploads/`
- Il database SQLite locale (`contabilita.db`) non viene più utilizzato
- Prima di avviare l'app, eseguire `supabase_setup.sql` nel SQL Editor di Supabase

## [1.0.0] — Versione iniziale

### Funzionalità
- App Streamlit per la gestione della contabilità personale
- Database SQLite locale
- Registrazione di entrate e uscite con categorie
- Caricamento e visualizzazione ricevute (PDF/immagini)
- Resoconto con filtri per data, totali e grafici
- Gestione categorie personalizzate
