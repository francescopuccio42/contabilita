"""
Script per inserire i dati di esempio nel progetto Supabase DEMO.

COME USARE:
1. Crea un progetto Supabase (account tuo)
2. Esegui demo_setup.sql nel SQL Editor per creare le tabelle
   (oppure esegui prima questo script che crea le tabelle via SQL)
3. Imposta le credenziali:
   - Opzione A: crea un file .env con SUPABASE_URL e SUPABASE_KEY
   - Opzione B: passa le credenziali come variabili d'ambiente
4. Esegui: python seed_demo.py
"""

import os
import sys
from datetime import date

from dotenv import load_dotenv
from supabase import create_client

# Assicura che gli emoji vengano stampati correttamente su Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERRORE: mancano SUPABASE_URL e SUPABASE_KEY.")
    print("   Crea un file .env con:")
    print("   SUPABASE_URL=https://TUO_PROGETTO.supabase.co")
    print("   SUPABASE_KEY=la_tua_chiave_anon")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Categorie di esempio ───────────────────────────────────
CATEGORIE = [
    ("Entrata", "Fatturato / Vendite"),
    ("Entrata", "Prestazione Servizi"),
    ("Entrata", "Prenotazioni B&B"),
    ("Entrata", "Altro (Entrata)"),
    ("Uscita", "Affitto"),
    ("Uscita", "Stipendi"),
    ("Uscita", "Bollette luce gas"),
    ("Uscita", "Tasse di soggiorno"),
    ("Uscita", "Internet"),
    ("Uscita", "Commissioni OTA"),
    ("Uscita", "Pulizie"),
    ("Uscita", "Commercialista"),
    ("Uscita", "Manutenzione"),
    ("Uscita", "Altro (Uscita)"),
]

# ─── Transazioni di esempio ──────────────────────────────────
TRANS_AZIONI = [
    # (data, tipo, voce, importo, metodo, persona, descrizione)
    ("2026-05-02", "Entrata", "Prenotazioni B&B", 420.00, "Bonifico", "Mario Rossi", "Soggiorno 2 notti - Camera 1"),
    ("2026-05-10", "Entrata", "Prenotazioni B&B", 315.00, "Carta", "Anna Bianchi", "Soggiorno 1 notte - Camera 2"),
    ("2026-05-18", "Entrata", "Prenotazioni B&B", 680.00, "Bonifico", "Luca Verdi", "Soggiorno 3 notti - Appartamento"),
    ("2026-05-25", "Entrata", "Prenotazioni B&B", 210.00, "Contante", "Giulia Neri", "Soggiorno 1 notte - Camera 1"),
    ("2026-06-03", "Entrata", "Prenotazioni B&B", 520.00, "Bonifico", "Paolo Gialli", "Soggiorno 2 notti - Appartamento"),
    ("2026-06-12", "Entrata", "Prenotazioni B&B", 315.00, "Carta", "Sara Blu", "Soggiorno 1 notte - Camera 2"),
    ("2026-06-20", "Entrata", "Prenotazioni B&B", 840.00, "Bonifico", "Marco Rosa", "Soggiorno 4 notti - Appartamento"),
    ("2026-06-28", "Entrata", "Prenotazioni B&B", 210.00, "Contante", "Elena Viola", "Soggiorno 1 notte - Camera 1"),
    ("2026-07-05", "Entrata", "Prenotazioni B&B", 630.00, "Bonifico", "Davide Arancio", "Soggiorno 3 notti - Appartamento"),
    ("2026-07-11", "Entrata", "Prenotazioni B&B", 315.00, "Carta", "Chiara Grigi", "Soggiorno 1 notte - Camera 2"),
    ("2026-07-19", "Entrata", "Prenotazioni B&B", 420.00, "Bonifico", "Andrea Marroni", "Soggiorno 2 notti - Camera 1"),
    ("2026-07-26", "Entrata", "Prenotazioni B&B", 210.00, "Contante", "Francesca Indaco", "Soggiorno 1 notte - Camera 1"),
    ("2026-05-15", "Entrata", "Prestazione Servizi", 150.00, "Bonifico", "", "Consulenza"),
    ("2026-06-15", "Entrata", "Prestazione Servizi", 150.00, "Bonifico", "", "Consulenza"),
    ("2026-07-15", "Entrata", "Prestazione Servizi", 150.00, "Bonifico", "", "Consulenza"),
    ("2026-05-05", "Uscita", "Affitto", 800.00, "Bonifico", "", "Affitto mensile"),
    ("2026-06-05", "Uscita", "Affitto", 800.00, "Bonifico", "", "Affitto mensile"),
    ("2026-07-05", "Uscita", "Affitto", 800.00, "Bonifico", "", "Affitto mensile"),
    ("2026-05-08", "Uscita", "Bollette luce gas", 145.30, "Bonifico", "", "Bolletta luce"),
    ("2026-06-08", "Uscita", "Bollette luce gas", 132.80, "Bonifico", "", "Bolletta luce"),
    ("2026-07-08", "Uscita", "Bollette luce gas", 158.40, "Bonifico", "", "Bolletta luce"),
    ("2026-05-12", "Uscita", "Internet", 29.90, "Bonifico", "", "Fibra"),
    ("2026-06-12", "Uscita", "Internet", 29.90, "Bonifico", "", "Fibra"),
    ("2026-07-12", "Uscita", "Internet", 29.90, "Bonifico", "", "Fibra"),
    ("2026-05-20", "Uscita", "Commissioni OTA", 63.00, "Bonifico", "", "Commissione Booking"),
    ("2026-06-20", "Uscita", "Commissioni OTA", 78.00, "Bonifico", "", "Commissione Booking"),
    ("2026-07-20", "Uscita", "Commissioni OTA", 52.50, "Bonifico", "", "Commissione Booking"),
    ("2026-05-22", "Uscita", "Pulizie", 90.00, "Contante", "", "Pulizia appartamento"),
    ("2026-06-22", "Uscita", "Pulizie", 90.00, "Contante", "", "Pulizia appartamento"),
    ("2026-07-22", "Uscita", "Pulizie", 90.00, "Contante", "", "Pulizia appartamento"),
    ("2026-06-01", "Uscita", "Commercialista", 120.00, "Bonifico", "", "Parcella trimestrale"),
    ("2026-06-15", "Uscita", "Manutenzione", 75.00, "Carta", "", "Ricambio lampadine"),
    ("2026-07-02", "Uscita", "Tasse di soggiorno", 60.00, "Bonifico", "", "Versamento tassa soggiorno"),
]

# ─── Scadenze di esempio ────────────────────────────────────
SCADENZE = [
    ("Affitto mensile", "Uscita", "Affitto", 800.00, "2026-08-05", "Mensile", "Bonifico", "In attesa"),
    ("Bolletta luce", "Uscita", "Bollette luce gas", 150.00, "2026-08-08", "Mensile", "Bonifico", "In attesa"),
    ("Internet fibra", "Uscita", "Internet", 29.90, "2026-08-12", "Mensile", "Bonifico", "In attesa"),
    ("Pulizia appartamento", "Uscita", "Pulizie", 90.00, "2026-08-22", "Mensile", "Contante", "In attesa"),
    ("Parcella commercialista", "Uscita", "Commercialista", 120.00, "2026-09-01", "Trimestrale", "Bonifico", "In attesa"),
    ("Tassa di soggiorno", "Uscita", "Tasse di soggiorno", 60.00, "2026-08-02", "Mensile", "Bonifico", "In attesa"),
]

# ─── Prenotazioni di esempio ─────────────────────────────────
PRENOTAZIONI = [
    ("Mario Rossi", "2026-05-01", "2026-05-03", 2, "Camera 1", "Diretto", 420.00, 0, 20.00, "Completata", True),
    ("Anna Bianchi", "2026-05-09", "2026-05-10", 1, "Camera 2", "Booking", 315.00, 31.50, 10.00, "Completata", True),
    ("Luca Verdi", "2026-05-17", "2026-05-20", 3, "Appartamento", "Airbnb", 680.00, 68.00, 30.00, "Completata", True),
    ("Giulia Neri", "2026-05-24", "2026-05-25", 1, "Camera 1", "Diretto", 210.00, 0, 10.00, "Completata", True),
    ("Paolo Gialli", "2026-06-02", "2026-06-04", 2, "Appartamento", "Booking", 520.00, 52.00, 20.00, "Completata", True),
    ("Sara Blu", "2026-06-11", "2026-06-12", 1, "Camera 2", "Diretto", 315.00, 0, 10.00, "Completata", True),
    ("Marco Rosa", "2026-06-19", "2026-06-23", 4, "Appartamento", "Airbnb", 840.00, 84.00, 40.00, "Completata", True),
    ("Elena Viola", "2026-06-27", "2026-06-28", 1, "Camera 1", "Diretto", 210.00, 0, 10.00, "Completata", True),
    ("Davide Arancio", "2026-07-04", "2026-07-07", 3, "Appartamento", "Booking", 630.00, 63.00, 30.00, "Completata", True),
    ("Chiara Grigi", "2026-07-10", "2026-07-11", 1, "Camera 2", "Diretto", 315.00, 0, 10.00, "Completata", True),
    ("Andrea Marroni", "2026-07-18", "2026-07-20", 2, "Camera 1", "Airbnb", 420.00, 42.00, 20.00, "In corso", True),
    ("Francesca Indaco", "2026-07-25", "2026-07-26", 1, "Camera 1", "Diretto", 210.00, 0, 10.00, "Confermata", False),
    ("Roberto Argento", "2026-08-01", "2026-08-04", 3, "Appartamento", "Booking", 630.00, 63.00, 30.00, "Confermata", False),
    ("Martina Oro", "2026-08-08", "2026-08-10", 2, "Camera 2", "Diretto", 630.00, 0, 20.00, "Confermata", False),
]


def inserisci_categorie():
    print("📂 Inserimento categorie...")
    for tipo, nome in CATEGORIE:
        try:
            existing = supabase.table("categorie").select("id").eq("nome", nome).execute()
            if not existing.data:
                supabase.table("categorie").insert({"tipo": tipo, "nome": nome}).execute()
                print(f"   ✅ {nome}")
            else:
                print(f"   ⏭️  {nome} (già presente)")
        except Exception as e:
            print(f"   ❌ {nome}: {e}")


def inserisci_transazioni():
    print("📈 Inserimento transazioni...")
    for data, tipo, voce, importo, metodo, persona, desc in TRANS_AZIONI:
        try:
            supabase.table("transazioni").insert({
                "data": data,
                "tipo": tipo,
                "voce": voce,
                "importo": importo,
                "metodo_pagamento": metodo,
                "persona": persona,
                "descrizione": desc,
            }).execute()
        except Exception as e:
            print(f"   ❌ {data} {voce}: {e}")
    print(f"   ✅ {len(TRANS_AZIONI)} transazioni inserite")


def inserisci_scadenze():
    print("📅 Inserimento scadenze...")
    for desc, tipo, voce, importo, data_scad, ricorrenza, metodo, stato in SCADENZE:
        try:
            supabase.table("scadenze").insert({
                "descrizione": desc,
                "tipo": tipo,
                "voce": voce,
                "importo": importo,
                "data_scadenza": data_scad,
                "ricorrenza": ricorrenza,
                "metodo_pagamento": metodo,
                "stato": stato,
            }).execute()
        except Exception as e:
            print(f"   ❌ {desc}: {e}")
    print(f"   ✅ {len(SCADENZE)} scadenze inserite")


def inserisci_prenotazioni():
    print("🏨 Inserimento prenotazioni...")
    for ospite, ci, co, notti, camera, canale, importo, comm, tassa, stato, reg in PRENOTAZIONI:
        try:
            supabase.table("prenotazioni").insert({
                "ospite": ospite,
                "check_in": ci,
                "check_out": co,
                "pernottamenti": notti,
                "camera": camera,
                "canale": canale,
                "importo": importo,
                "commissione": comm,
                "tassa_soggiorno": tassa,
                "stato": stato,
                "registrata_contabilita": reg,
            }).execute()
        except Exception as e:
            print(f"   ❌ {ospite}: {e}")
    print(f"   ✅ {len(PRENOTAZIONI)} prenotazioni inserite")


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Inserimento dati demo nel progetto Supabase")
    print("=" * 50)
    inserisci_categorie()
    inserisci_transazioni()
    inserisci_scadenze()
    inserisci_prenotazioni()
    print("=" * 50)
    print("✅ Completato! Ora puoi avviare l'app con le credenziali demo.")
    print("=" * 50)
