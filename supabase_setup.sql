-- ============================================================
-- Script SQL per creare le tabelle su Supabase
-- Esegui questo script nel SQL Editor di Supabase Dashboard
-- ============================================================

-- 1. Tabella transazioni (con metodo_pagamento e persona)
CREATE TABLE IF NOT EXISTS transazioni (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data DATE NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Entrata', 'Uscita')),
    voce TEXT NOT NULL,
    importo DOUBLE PRECISION NOT NULL,
    metodo_pagamento TEXT NOT NULL DEFAULT 'Contante' CHECK (metodo_pagamento IN ('Contante', 'Bonifico', 'Carta', 'Assegno', 'Altro')),
    persona TEXT DEFAULT '',
    descrizione TEXT,
    ricevuta_nome TEXT,
    ricevuta_percorso TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Tabella categorie
CREATE TABLE IF NOT EXISTS categorie (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('Entrata', 'Uscita')),
    nome TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Inserimento categorie iniziali
INSERT INTO categorie (tipo, nome) VALUES
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
    ('Uscita', 'f24 : rateizzazione tasse 2027'),
    ('Uscita', 'f24 : rateizzazione tasse 2028'),
    ('Uscita', 'Tasse di soggiorno'),
    ('Uscita', 'Internet'),
    ('Uscita', 'Booking - idealista - segreteria.it - immobiliare.it'),
    ('Uscita', 'pulizia nolmar / tutto igiene / Verona lux / Albanese group'),
    ('Uscita', 'Commercialista a tempora'),
    ('Uscita', 'Altro (Uscita)')
ON CONFLICT (nome) DO NOTHING;

-- 4. Aggiungi colonna persona se non esiste già (per aggiornamento)
ALTER TABLE transazioni ADD COLUMN IF NOT EXISTS persona TEXT DEFAULT '';

-- 5. Disabilita Row Level Security per permettere operazioni CRUD
--    con la chiave anonima (necessario per l'app Streamlit)
ALTER TABLE transazioni DISABLE ROW LEVEL SECURITY;
ALTER TABLE categorie DISABLE ROW LEVEL SECURITY;

-- 6. Tabella scadenze (per lo scadenzario con promemoria e ricorrenze)
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

