-- ============================================================
-- Script SQL per creare le tabelle su Supabase
-- Esegui questo script nel SQL Editor di Supabase Dashboard
-- ============================================================

-- 1. Tabella transazioni
CREATE TABLE IF NOT EXISTS transazioni (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data DATE NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Entrata', 'Uscita')),
    voce TEXT NOT NULL,
    importo DOUBLE PRECISION NOT NULL,
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

-- 4. Abilita Row Level Security (opzionale, disabilitato per semplicità)
-- Se vuoi usare RLS in futuro, decommenta:
-- ALTER TABLE transazioni ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE categorie ENABLE ROW LEVEL SECURITY;
