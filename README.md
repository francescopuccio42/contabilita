# 📈 Gestionale Contabilità Francesco

Webapp Streamlit per monitorare entrate, uscite e archiviare ricevute fiscali, con backend su **Supabase**.

## 🚀 Funzionalità

- **Registrazione movimenti** — Inserisci entrate e uscite con categoria, importo, descrizione e ricevuta
- **Resoconto & Analisi** — Filtra per periodo, visualizza totali, saldo netto, lista movimenti e grafici per categoria
- **Gestione Categorie** — Aggiungi e visualizza voci di bilancio personalizzate
- **Archiviazione Ricevute** — Carica PDF o immagini, visualizza anteprime e scarica i file

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

5. **Avvia l'app**
   ```bash
   streamlit run app.py
   ```

## 📁 Struttura del Progetto

```
contabilità francesco/
├── app.py                  # Applicazione Streamlit principale
├── supabase_setup.sql      # Script SQL per creare le tabelle su Supabase
├── .env                    # Credenziali Supabase (NON committare)
├── .gitignore              # File ignorati da Git
├── README.md               # Questo file
├── CHANGELOG.md            # Storico delle modifiche
├── contabilita.db          # Database SQLite locale (sostituito da Supabase)
└── ricevute_uploads/       # Cartella per i file delle ricevute caricate
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

## 📄 Licenza

Progetto personale — Francesco Puccio
