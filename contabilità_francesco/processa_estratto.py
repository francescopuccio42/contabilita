"""
Processa un estratto conto UniCredit PDF e lo converte in un DataFrame pulito.

Esegue:
1. Estrae le tabelle movimenti da tutte le pagine del PDF
2. Combina le pagine in un'unica tabella
3. Rimuove righe superflue (intestazioni ripetute, info conto, footer, saldi di periodo)
4. Unisce descrizioni multilinea in un'unica riga pulita
5. Standardizza i nomi colonna (Data, Valuta, Descrizione, Uscite, Entrate)
6. Rileva duplicati (senza eliminarli: possono essere transazioni reali ripetute)

Uso come modulo (nell'app Streamlit):
    from processa_estratto import pdf_a_dataframe
    df = pdf_a_dataframe(uploaded_file)

Uso come CLI:
    python processa_estratto.py <percorso_pdf>
"""

import csv
import io
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pdfplumber

# Header di colonna delle tabelle movimenti nel PDF
MOVEMENT_HEADER = {"Data", "Valuta", "Descrizione", "Uscite", "Entrate"}

# Righe superflue da rimuovere dalla descrizione (dettagli tecnici, IBAN,
# mandati, numeri pratica, indirizzi sportelli, comm/tasse incassate, etc.)
SUPERFLUOUS_PATTERNS = [
    # Numeri sportello / carta / ATM
    r"\bATMNUM\.\S+",
    r"\bCARTA\s*\*?\s*\d+X*\s*",
    r"\bVERSAMENTODEL[0-9.]+ALLE\s*[0-9:]+\s*",
    r"\bEDITATM\d+\s*",
    r"\bRICARICACARTA([A-Z]|\d|[\*\s])+",
    # Indirizzi sportelli
    r"CASTELBELFORTE\(\w+\)|CASTELD'AZZANO\(\w+\)|SANGIORGIODIMANTOVA\(\w+\)",
    r"-VIAG\.\S+|-VIAGROSSI,?\d*|-VIAXXVAPRILE,?\d*|-PIAZZAVIOLINI\S*|-PIAZZA\s*\S*",
    r"\bUNICREDITATM\d*\s*",
    r"\bTREVENZUOLOVR\s*",
    # Riferimenti bonifico / SDD / mandati
    r"\bBONIFICOSEPADA:\S+",
    r"\bBONIFICOSEPAA:\S+",
    r"\bSDDda[A-Z]{2}\d+\s*",
    r"\bmandatonr\.\S+",
    r"\bComm\s*[0-9.,]+\s*",
    r"\bIncasso\S*",
    r"\bRDBRUMV[A-Z0-9-]+\s*",
    r"\bCO\d+\s*",
    r"\bCAB\d+\s*",
    # Commissioni / spese / oneri nel corpo descrizione
    r"COMM:?\s*[0-9.,]+\s*",
    r"SPESE:?\s*[0-9.,]+\s*",
    r"COMMSERV:?\s*[0-9.,]+\s*",
    r"BONIFICICOMM:?\s*[0-9.,]+\s*",
    r"\bSP\.INC[0-9.,]+\s*",
    r"\bONERI[0-9.,]+\s*",
    r"\bIMP[0-9.,]+\s*",
    # Dati pratica / documento
    r"\bPERIODODA[0-9-]+A[0-9-]+\s*",
    r"\bNUMEROPRATICA\d+\s*",
    r"\bNRIC:\d+\s*",
    r"\bDOCUM\.\S+",
    r"\bRATANUM\.:?\s*\d*\s*",
    r"\bFINANZIAM\.\s*NUMERO:?\s*\d+\s*",
    r"\bSALDO\s*$",
    r"\bDEL[0-9.]+\s*",
    r"\bIL[0-9.]+\s*",
    # Residui numerici in coda riga (orari, importi commissione)
    r"\b[0-9]{1,2}:[0-9]{2}\s*$",
    r"\b[0-9]{1,3}[.,][0-9]{2}\s*$",
    r"\bPer\s+$",
]

# Descrizioni/righe che rappresentano saldi di periodo, non movimenti contabili
BALANCE_DESCRIPTIONS = {"SALDOINIZIALEAVS.DEBITO", "SALDOFINALEAVS.DEBITO"}


def clean_description(desc: str) -> str:
    """Pulisce una descrizione: unisce le righe e rimuove dettagli superflui."""
    if not desc:
        return ""
    # Unisci le righe della descrizione
    text = re.sub(r"\s*\n\s*", " ", desc)
    # Rimuovi pattern superflui
    for pattern in SUPERFLUOUS_PATTERNS:
        text = re.sub(pattern, " ", text)
    # Comprimi spazi multipli
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def parse_amount(value: str) -> float:
    """Converte '1.629,28' -> 1629.28. Restituisce 0.0 per valori vuoti."""
    if not value:
        return 0.0
    value = value.strip().replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_date(value: str) -> str:
    """Converte '31.03.26' -> '2026-03-31' (formato ISO, usato dall'app)."""
    value = value.strip()
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%d.%m.%y").strftime("%Y-%m-%d")
    except ValueError:
        return value


def is_account_table(table: list[list]) -> bool:
    """Individua la tabella con le informazioni del conto (IBAN), da scartare."""
    for row in table:
        if row and row[0] in {"Paese", "CodiceBICSWIFT"}:
            return True
    return False


def extract_movements(pdf_source) -> list[dict]:
    """Estrae i movimenti da tutte le pagine del PDF, escludendo i saldi di periodo.

    `pdf_source` può essere un percorso file o un oggetto file-like (BytesIO),
    come gli UploadedFile di Streamlit.
    """
    movimenti = []
    with pdfplumber.open(pdf_source) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                # Scarta la tabella con le informazioni del conto (IBAN, ABI, CAB)
                if is_account_table(table):
                    continue
                for row in table:
                    # Salta intestazioni ripetute di colonna
                    if row and row[0] in MOVEMENT_HEADER:
                        continue
                    # Filtra righe malformate (attese 5 colonne)
                    if not row or len(row) < 5:
                        continue
                    data = (row[0] or "").strip()
                    valuta = (row[1] or "").strip()
                    desc_raw = (row[2] or "").strip()
                    uscite = (row[3] or "").strip()
                    entrate = (row[4] or "").strip()

                    # Salta righe nulle
                    if not data and not desc_raw:
                        continue

                    desc = clean_description(desc_raw)
                    importo_usc = parse_amount(uscite)
                    importo_ent = parse_amount(entrate)

                    # Salta i saldi di periodo (saldo iniziale / finale)
                    if desc in BALANCE_DESCRIPTIONS:
                        print(f"   [info] Saltato saldo: {desc} = {importo_usc or importo_ent}")
                        continue
                    # Salta righe con importo nullo (es. COMPETENZE 0,00)
                    if importo_usc == 0.0 and importo_ent == 0.0:
                        print(f"   [info] Saltata riga a importo zero: {desc}")
                        continue

                    movimenti.append({
                        "data": parse_date(data),
                        "valuta": parse_date(valuta),
                        "descrizione": desc,
                        "uscite": importo_usc,
                        "entrate": importo_ent,
                    })
    return movimenti


def find_duplicates(movimenti: list[dict]) -> list[tuple[int, int]]:
    """Rileva coppie di movimenti identici (stessa data, descrizione, importo).

    Nota: rilevare NON significa eliminare: nel conto possono esistere
    transazioni identiche ripetute (es. due prelievi uguali nello stesso giorno).
    """
    seen = {}
    duplicati = []
    for i, m in enumerate(movimenti):
        key = (m["data"], m["descrizione"], m["uscite"], m["entrate"])
        if key in seen:
            duplicati.append((seen[key], i))
        else:
            seen[key] = i
    return duplicati


def pdf_a_dataframe(pdf_source) -> pd.DataFrame:
    """Converte un PDF estrattoconto in un DataFrame pulito.

    Colonne: Data, Valuta, Descrizione, Uscite, Entrate
    (date in formato ISO YYYY-MM-DD, importi come float con virgola).
    """
    movimenti = extract_movements(pdf_source)
    if not movimenti:
        raise ValueError(
            "Il PDF non contiene tabelle di movimenti estraibili. "
            "Probabilmente è un PDF scansionato (solo immagini) oppure non è un estratto conto UniCredit standard. "
            "Prova a esportare l'estratto conto come Excel o CSV dal tuo home banking."
        )
    df = pd.DataFrame(movimenti, columns=[
        "data", "valuta", "descrizione", "uscite", "entrate"
    ])
    df = df.rename(columns={
        "data": "Data",
        "valuta": "Valuta",
        "descrizione": "Descrizione",
        "uscite": "Uscite",
        "entrate": "Entrate",
    })
    return df


def main():
    if len(sys.argv) < 2:
        print("Uso: python processa_estratto.py <percorso_pdf>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    output_csv = Path(pdf_path).with_suffix("").name + "_pulito.csv"

    print(f"Estrazione movimenti da {pdf_path} ...")
    df = pdf_a_dataframe(pdf_path)
    print(f"   Trovati {len(df)} movimenti.")

    # Scrivi CSV pulito
    df["Uscite"] = df["Uscite"].map(lambda v: f"{v:.2f}".replace(".", ","))
    df["Entrate"] = df["Entrate"].map(lambda v: f"{v:.2f}".replace(".", ","))
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"CSV pulito scritto: {output_csv}")

    # Verifica duplicati (solo segnalazione, non rimozione)
    movimenti = df.to_dict("records")
    movimenti = [
        {
            "data": m["Data"],
            "descrizione": m["Descrizione"],
            "uscite": float(m["Uscite"].replace(",", ".")) if isinstance(m["Uscite"], str) else m["Uscite"],
            "entrate": float(m["Entrate"].replace(",", ".")) if isinstance(m["Entrate"], str) else m["Entrate"],
        }
        for m in movimenti
    ]
    duplicati = find_duplicates(movimenti)
    if duplicati:
        print(f"ATTENZIONE: {len(duplicati)} movimenti ripetuti trovati "
              f"(possono essere transazioni reali, NON vengono rimossi):")
        for orig, dup in duplicati:
            m = movimenti[dup]
            print(f"   - Righe {orig+1} e {dup+1}: {m['data']} {m['descrizione']} "
                  f"Uscite={m['uscite']} Entrate={m['entrate']}")
    else:
        print("Nessun movimento ripetuto trovato.")

    # Riepilogo (dovrebbe coincidere con il riepilogo ufficiale del PDF)
    tot_usc = sum(float(m["Uscite"].replace(",", ".")) if isinstance(m["Uscite"], str) else m["Uscite"] for m in df.to_dict("records"))
    tot_ent = sum(float(m["Entrate"].replace(",", ".")) if isinstance(m["Entrate"], str) else m["Entrate"] for m in df.to_dict("records"))
    print(f"\nRiepilogo:")
    print(f"   Totale Uscite:  {tot_usc:,.2f} EUR")
    print(f"   Totale Entrate: {tot_ent:,.2f} EUR")
    print(f"   Saldo:          {tot_ent - tot_usc:,.2f} EUR")


if __name__ == "__main__":
    main()