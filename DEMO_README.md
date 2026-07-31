# 🎯 Guida alla DEMO — Gestionale Contabilità B&B

Questa guida ti spiega come creare una **versione demo** dell'app da mostrare ai potenziali clienti, **senza esporre i dati reali** del cliente.

La demo usa un **progetto Supabase separato** con dati di esempio realistici (movimenti, prenotazioni B&B, scadenze) e credenziali di accesso dedicate.

---

## 📋 Cosa serve

- Un account **Supabase** (gratuito) — usa il tuo account personale, non quello del cliente
- Un account **Streamlit Cloud** (gratuito) per pubblicare la demo online

---

## 🚀 Passo 1 — Crea il progetto Supabase demo

1. Vai su [https://supabase.com](https://supabase.com) e accedi con il **tuo** account
2. Clicca **"New project"**
3. Dai un nome (es. `contabilita-demo`)
4. Scegli una password per il database (salvala!)
5. Scegli la regione più vicina a te
6. Clicca **"Create new project"** e attendi il completamento (1-2 minuti)

---

## 🚀 Passo 2 — Crea le tabelle e i dati di esempio

1. Nel progetto appena creato, vai su **SQL Editor** (menu a sinistra)
2. Clicca **"New query"**
3. Apri il file **`demo_setup.sql`** di questo progetto e copia tutto il contenuto
4. Incollalo nell'editor SQL
5. Clicca **"Run"** (▶️)

Questo crea le tabelle (`transazioni`, `categorie`, `scadenze`, `prenotazioni`) e inserisce **dati di esempio realistici**:
- 📈 Movimenti di entrata/uscita degli ultimi 3 mesi
- 🏨 Prenotazioni B&B con ospiti, camere e canali
- 📅 Scadenze ricorrenti (affitto, bollette, ecc.)

---

## 🚀 Passo 3 — Prendi le chiavi del progetto demo

1. Nel progetto Supabase, vai su **Settings** (ingranaggio) → **API**
2. Copia il **Project URL** (es. `https://xxxx.supabase.co`)
3. Copia la **anon public key** (la chiave `anon`)

---

## 🚀 Passo 4 — Configura le credenziali demo

Apri il file **`demo_secrets.toml`** di questo progetto e sostituisci i valori segnaposto:

```toml
SUPABASE_URL = "https://IL_TUO_PROGETTO_DEMO.supabase.co"
SUPABASE_KEY = "la_tua_chiave_anon_demo"
```

### Per la demo locale (sul tuo PC)
Copia il contenuto di `demo_secrets.toml` in **`.streamlit/secrets.toml`** (sostituendo il contenuto attuale).

### Per la demo online (Streamlit Cloud)
1. Vai su [https://share.streamlit.io](https://share.streamlit.io)
2. Collega il repository `grazialarocca1976-maker/progetto-b-b`
3. In **Settings → Secrets**, incolla il contenuto di `demo_secrets.toml`
4. Imposta il file principale su `contabilità_francesco/app.py`
5. Clicca **"Deploy"**

---

## 🔑 Credenziali di accesso alla demo

| Utente | Password |
|--------|----------|
| `demo` | `demo2024` |
| `ospite` | `ospite2024` |

> 💡 Puoi cambiare queste credenziali nel file `demo_secrets.toml`.

---

## ✅ Riepilogo

| Cosa | Dove |
|------|------|
| Tabelle + dati di esempio | `demo_setup.sql` (esegui nel SQL Editor) |
| Credenziali demo | `demo_secrets.toml` |
| App principale | `contabilità_francesco/app.py` |

---

## ⚠️ Importante

- **Non condividere** `demo_secrets.toml` né `.streamlit/secrets.toml` (contengono le chiavi)
- La demo usa dati **fittizi** — non tocca i dati reali del cliente
- Se vuoi mostrare la demo senza login, puoi rimuovere le righe `LOGIN_*` da `demo_secrets.toml` (l'app userà `admin`/`admin` di default)
