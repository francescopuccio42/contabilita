# 📈 Gestionale Contabilità Francesco

Webapp Streamlit per monitorare entrate, uscite e archiviare ricevute fiscali, con backend su **Supabase**.

## 🚀 Funzionalità

- **Registrazione movimenti** — Inserisci entrate e uscite con categoria, importo, descrizione e ricevuta
- **Prenotazioni & Ospiti** — Gestisci prenotazioni del B&B con check-in/check-out, pernottamenti automatici, camere, canali OTA, commissioni e tasse di soggiorno
- **Scadenzario & Promemoria** — Gestisci scadenze ricorrenti con promemoria automatici 7 giorni prima
- **Resoconto & Analisi** — Filtra per periodo, visualizza totali, saldo netto, lista movimenti e grafici per categoria
- **Report Fiscali** — Riepilogo mensile e trimestrale di entrate/uscite/saldo per la dichiarazione fiscale
- **Gestione Categorie** — Aggiungi e visualizza voci di bilancio personalizzate
- **Archiviazione Ricevute** — Carica PDF o immagini, visualizza anteprime e scarica i file
- **Archivio Pagamenti** — Storico completo con filtri per tipo, metodo, anno e persona
- **Backup & Ripristino** — Crea backup manuali dei dati e ripristinali quando necessario

## 🛠️ Tecnologie

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Backend:** [Supabase](https://supabase.com/) (PostgreSQL + API REST)
- **Linguaggio:** Python 3.14

## 📋 Prerequisiti

- Python 3.14+
- Un account Supabase con un progetto attivo

## 🔧 Installazione

1. **Clona il repository**
   ```bash
   git clone https://github.com/francescopuccio42/contabilita.git
   cd contabilita
   ```

2. **Installa le dipendenze**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura Supabase**
   - Vai su [Supabase Dashboard](https://supabase.com/dashboard/project/xiqtlyotxufzivprxrzw)
   - Apri **SQL Editor**
   - Esegui il contenuto del file `supabase_setup.sql`

4. **Configura le credenziali**
   - Crea un file `.env` nella root del progetto (già presente se clonato con le credenziali)
   ```
   SUPABASE_URL=https://xiqtlyotxufzivprxrzw.supabase.co
   SUPABASE_KEY=la_tua_chiave_anon
   ```

5. **Avvia l'app in locale**
   - **Doppio clic su `avvia_app.bat`** (Windows) — verifica automaticamente il file `.env` e le dipendenze, poi avvia l'app su `http://localhost:8501`.
   - Oppure da terminale:
     ```bash
     python run_local.py
     ```
   - Oppure direttamente con Streamlit:
     ```bash
     streamlit run contabilità_francesco/app.py
     ```

## 📁 Struttura del Progetto

```
contabilità_francesco/
├── contabilità_francesco/
│   ├── app.py              # Applicazione Streamlit principale
│   └── payment_methods.py  # Metodi di pagamento (Contanti, POS, Bonifico...)
├── avvia_app.bat           # Avvio rapido su Windows (doppio clic)
├── run_local.py            # Script di avvio locale (verifica dipendenze e credenziali)
├── supabase_setup.sql      # Script SQL per creare le tabelle su Supabase
├── .env                    # Credenziali Supabase (NON committare)
├── .env.example            # Template delle credenziali
├── .gitignore              # File ignorati da Git
├── README.md               # Questo file
├── CHANGELOG.md            # Storico delle modifiche
├── ricevute_uploads/       # Cartella per i file delle ricevute caricate
└── backups/                # Cartella per i file di backup (creata automaticamente)
```

## 🗄️ Tabelle Supabase

### `transazioni`
| Colonna           | Tipo            | Descrizione                          |
|-------------------|-----------------|--------------------------------------|
| `id`              | BIGINT (PK)     | Identificativo univoco               |
| `data`            | DATE            | Data del movimento                   |
| `tipo`            | TEXT            | 'Entrata' o 'Uscita'                 |
| `voce`            | TEXT            | Categoria / Voce di bilancio         |
| `importo`         | DOUBLE PRECISION| Importo in euro                      |
| `descrizione`     | TEXT            | Note opzionali                       |
| `ricevuta_nome`   | TEXT            | Nome file originale della ricevuta   |
| `ricevuta_percorso`| TEXT           | Percorso locale del file             |
| `created_at`      | TIMESTAMPTZ     | Data di creazione record             |

### `categorie`
| Colonna           | Tipo            | Descrizione                          |
|-------------------|-----------------|--------------------------------------|
| `id`              | BIGINT (PK)     | Identificativo univoco               |
| `tipo`            | TEXT            | 'Entrata' o 'Uscita'                 |
| `nome`            | TEXT (UNIQUE)   | Nome della categoria                 |
| `created_at`      | TIMESTAMPTZ     | Data di creazione record             |

### `prenotazioni`
| Colonna                | Tipo            | Descrizione                          |
|------------------------|-----------------|--------------------------------------|
| `id`                   | BIGINT (PK)     | Identificativo univoco               |
| `ospite`               | TEXT            | Nome dell'ospite                     |
| `check_in`             | DATE            | Data di arrivo                       |
| `check_out`            | DATE            | Data di partenza                     |
| `pernottamenti`        | INTEGER         | Numero di notti (calcolato)          |
| `camera`               | TEXT            | Camera / Appartamento                |
| `canale`               | TEXT            | Canale (Diretto, Booking, Airbnb...) |
| `importo`              | DOUBLE PRECISION| Importo del soggiorno                |
| `commissione`          | DOUBLE PRECISION| Commissione canale OTA               |
| `tassa_soggiorno`      | DOUBLE PRECISION| Tassa di soggiorno                   |
| `stato`                | TEXT            | Confermata / In corso / Completata / Cancellata |
| `note`                 | TEXT            | Note aggiuntive                      |
| `registrata_contabilita`| BOOLEAN        | Se registrata in contabilità         |
| `created_at`           | TIMESTAMPTZ     | Data di creazione record             |

## 📄 Licenza

Progetto personale — Francesco Puccio
