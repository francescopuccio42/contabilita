-- ============================================================
-- Script SQL per creare un progetto Supabase DEMO
-- con dati di esempio realistici (per mostrare il lavoro)
--
-- COME USARE:
-- 1. Crea un nuovo progetto su https://supabase.com (account tuo)
-- 2. Apri SQL Editor del nuovo progetto
-- 3. Incolla ed esegui TUTTO questo script
-- 4. Prendi URL e chiave anon (Settings → API) e mettili in
--    .streamlit/secrets.toml e .env
-- ============================================================

-- 1. Tabella transazioni
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

-- 3. Categorie di esempio
INSERT INTO categorie (tipo, nome) VALUES
    ('Entrata', 'Fatturato / Vendite'),
    ('Entrata', 'Prestazione Servizi'),
    ('Entrata', 'Prenotazioni B&B'),
    ('Entrata', 'Altro (Entrata)'),
    ('Uscita', 'Affitto'),
    ('Uscita', 'Stipendi'),
    ('Uscita', 'Bollette luce gas'),
    ('Uscita', 'Tasse di soggiorno'),
    ('Uscita', 'Internet'),
    ('Uscita', 'Commissioni OTA'),
    ('Uscita', 'Pulizie'),
    ('Uscita', 'Commercialista'),
    ('Uscita', 'Manutenzione'),
    ('Uscita', 'Altro (Uscita)')
ON CONFLICT (nome) DO NOTHING;

-- 4. Disabilita Row Level Security
ALTER TABLE transazioni DISABLE ROW LEVEL SECURITY;
ALTER TABLE categorie DISABLE ROW LEVEL SECURITY;

-- 5. Tabella scadenze
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

-- 6. Tabella prenotazioni
CREATE TABLE IF NOT EXISTS prenotazioni (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ospite TEXT NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    pernottamenti INTEGER NOT NULL,
    camera TEXT DEFAULT '',
    canale TEXT DEFAULT 'Diretto' CHECK (canale IN ('Diretto', 'Booking', 'Airbnb', 'Expedia', 'Altro')),
    importo DOUBLE PRECISION NOT NULL DEFAULT 0,
    commissione DOUBLE PRECISION NOT NULL DEFAULT 0,
    tassa_soggiorno DOUBLE PRECISION NOT NULL DEFAULT 0,
    stato TEXT NOT NULL DEFAULT 'Confermata' CHECK (stato IN ('Confermata', 'In corso', 'Completata', 'Cancellata')),
    note TEXT DEFAULT '',
    registrata_contabilita BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE prenotazioni DISABLE ROW LEVEL SECURITY;

-- ============================================================
-- DATI DI ESEMPIO
-- ============================================================

-- 7. Transazioni di esempio (entrate e uscite degli ultimi mesi)
INSERT INTO transazioni (data, tipo, voce, importo, metodo_pagamento, persona, descrizione) VALUES
    -- ENTRATE da prenotazioni B&B
    ('2026-05-02', 'Entrata', 'Prenotazioni B&B', 420.00, 'Bonifico', 'Mario Rossi', 'Soggiorno 2 notti - Camera 1'),
    ('2026-05-10', 'Entrata', 'Prenotazioni B&B', 315.00, 'Carta', 'Anna Bianchi', 'Soggiorno 1 notte - Camera 2'),
    ('2026-05-18', 'Entrata', 'Prenotazioni B&B', 680.00, 'Bonifico', 'Luca Verdi', 'Soggiorno 3 notti - Appartamento'),
    ('2026-05-25', 'Entrata', 'Prenotazioni B&B', 210.00, 'Contante', 'Giulia Neri', 'Soggiorno 1 notte - Camera 1'),
    ('2026-06-03', 'Entrata', 'Prenotazioni B&B', 520.00, 'Bonifico', 'Paolo Gialli', 'Soggiorno 2 notti - Appartamento'),
    ('2026-06-12', 'Entrata', 'Prenotazioni B&B', 315.00, 'Carta', 'Sara Blu', 'Soggiorno 1 notte - Camera 2'),
    ('2026-06-20', 'Entrata', 'Prenotazioni B&B', 840.00, 'Bonifico', 'Marco Rosa', 'Soggiorno 4 notti - Appartamento'),
    ('2026-06-28', 'Entrata', 'Prenotazioni B&B', 210.00, 'Contante', 'Elena Viola', 'Soggiorno 1 notte - Camera 1'),
    ('2026-07-05', 'Entrata', 'Prenotazioni B&B', 630.00, 'Bonifico', 'Davide Arancio', 'Soggiorno 3 notti - Appartamento'),
    ('2026-07-11', 'Entrata', 'Prenotazioni B&B', 315.00, 'Carta', 'Chiara Grigi', 'Soggiorno 1 notte - Camera 2'),
    ('2026-07-19', 'Entrata', 'Prenotazioni B&B', 420.00, 'Bonifico', 'Andrea Marroni', 'Soggiorno 2 notti - Camera 1'),
    ('2026-07-26', 'Entrata', 'Prenotazioni B&B', 210.00, 'Contante', 'Francesca Indaco', 'Soggiorno 1 notte - Camera 1'),
    -- ENTRATE da altri servizi
    ('2026-05-15', 'Entrata', 'Prestazione Servizi', 150.00, 'Bonifico', '', 'Consulenza'),
    ('2026-06-15', 'Entrata', 'Prestazione Servizi', 150.00, 'Bonifico', '', 'Consulenza'),
    ('2026-07-15', 'Entrata', 'Prestazione Servizi', 150.00, 'Bonifico', '', 'Consulenza'),
    -- USCITE
    ('2026-05-05', 'Uscita', 'Affitto', 800.00, 'Bonifico', '', 'Affitto mensile'),
    ('2026-06-05', 'Uscita', 'Affitto', 800.00, 'Bonifico', '', 'Affitto mensile'),
    ('2026-07-05', 'Uscita', 'Affitto', 800.00, 'Bonifico', '', 'Affitto mensile'),
    ('2026-05-08', 'Uscita', 'Bollette luce gas', 145.30, 'Bonifico', '', 'Bolletta luce'),
    ('2026-06-08', 'Uscita', 'Bollette luce gas', 132.80, 'Bonifico', '', 'Bolletta luce'),
    ('2026-07-08', 'Uscita', 'Bollette luce gas', 158.40, 'Bonifico', '', 'Bolletta luce'),
    ('2026-05-12', 'Uscita', 'Internet', 29.90, 'Bonifico', '', 'Fibra'),
    ('2026-06-12', 'Uscita', 'Internet', 29.90, 'Bonifico', '', 'Fibra'),
    ('2026-07-12', 'Uscita', 'Internet', 29.90, 'Bonifico', '', 'Fibra'),
    ('2026-05-20', 'Uscita', 'Commissioni OTA', 63.00, 'Bonifico', '', 'Commissione Booking'),
    ('2026-06-20', 'Uscita', 'Commissioni OTA', 78.00, 'Bonifico', '', 'Commissione Booking'),
    ('2026-07-20', 'Uscita', 'Commissioni OTA', 52.50, 'Bonifico', '', 'Commissione Booking'),
    ('2026-05-22', 'Uscita', 'Pulizie', 90.00, 'Contante', '', 'Pulizia appartamento'),
    ('2026-06-22', 'Uscita', 'Pulizie', 90.00, 'Contante', '', 'Pulizia appartamento'),
    ('2026-07-22', 'Uscita', 'Pulizie', 90.00, 'Contante', '', 'Pulizia appartamento'),
    ('2026-06-01', 'Uscita', 'Commercialista', 120.00, 'Bonifico', '', 'Parcella trimestrale'),
    ('2026-06-15', 'Uscita', 'Manutenzione', 75.00, 'Carta', '', 'Ricambio lampadine'),
    ('2026-07-02', 'Uscita', 'Tasse di soggiorno', 60.00, 'Bonifico', '', 'Versamento tassa soggiorno')
ON CONFLICT DO NOTHING;

-- 8. Scadenze di esempio
INSERT INTO scadenze (descrizione, tipo, voce, importo, data_scadenza, ricorrenza, metodo_pagamento, stato) VALUES
    ('Affitto mensile', 'Uscita', 'Affitto', 800.00, '2026-08-05', 'Mensile', 'Bonifico', 'In attesa'),
    ('Bolletta luce', 'Uscita', 'Bollette luce gas', 150.00, '2026-08-08', 'Mensile', 'Bonifico', 'In attesa'),
    ('Internet fibra', 'Uscita', 'Internet', 29.90, '2026-08-12', 'Mensile', 'Bonifico', 'In attesa'),
    ('Pulizia appartamento', 'Uscita', 'Pulizie', 90.00, '2026-08-22', 'Mensile', 'Contante', 'In attesa'),
    ('Parcella commercialista', 'Uscita', 'Commercialista', 120.00, '2026-09-01', 'Trimestrale', 'Bonifico', 'In attesa'),
    ('Tassa di soggiorno', 'Uscita', 'Tasse di soggiorno', 60.00, '2026-08-02', 'Mensile', 'Bonifico', 'In attesa')
ON CONFLICT DO NOTHING;

-- 9. Prenotazioni di esempio
INSERT INTO prenotazioni (ospite, check_in, check_out, pernottamenti, camera, canale, importo, commissione, tassa_soggiorno, stato, registrata_contabilita) VALUES
    ('Mario Rossi', '2026-05-01', '2026-05-03', 2, 'Camera 1', 'Diretto', 420.00, 0, 20.00, 'Completata', TRUE),
    ('Anna Bianchi', '2026-05-09', '2026-05-10', 1, 'Camera 2', 'Booking', 315.00, 31.50, 10.00, 'Completata', TRUE),
    ('Luca Verdi', '2026-05-17', '2026-05-20', 3, 'Appartamento', 'Airbnb', 680.00, 68.00, 30.00, 'Completata', TRUE),
    ('Giulia Neri', '2026-05-24', '2026-05-25', 1, 'Camera 1', 'Diretto', 210.00, 0, 10.00, 'Completata', TRUE),
    ('Paolo Gialli', '2026-06-02', '2026-06-04', 2, 'Appartamento', 'Booking', 520.00, 52.00, 20.00, 'Completata', TRUE),
    ('Sara Blu', '2026-06-11', '2026-06-12', 1, 'Camera 2', 'Diretto', 315.00, 0, 10.00, 'Completata', TRUE),
    ('Marco Rosa', '2026-06-19', '2026-06-23', 4, 'Appartamento', 'Airbnb', 840.00, 84.00, 40.00, 'Completata', TRUE),
    ('Elena Viola', '2026-06-27', '2026-06-28', 1, 'Camera 1', 'Diretto', 210.00, 0, 10.00, 'Completata', TRUE),
    ('Davide Arancio', '2026-07-04', '2026-07-07', 3, 'Appartamento', 'Booking', 630.00, 63.00, 30.00, 'Completata', TRUE),
    ('Chiara Grigi', '2026-07-10', '2026-07-11', 1, 'Camera 2', 'Diretto', 315.00, 0, 10.00, 'Completata', TRUE),
    ('Andrea Marroni', '2026-07-18', '2026-07-20', 2, 'Camera 1', 'Airbnb', 420.00, 42.00, 20.00, 'In corso', TRUE),
    ('Francesca Indaco', '2026-07-25', '2026-07-26', 1, 'Camera 1', 'Diretto', 210.00, 0, 10.00, 'Confermata', FALSE),
    ('Roberto Argento', '2026-08-01', '2026-08-04', 3, 'Appartamento', 'Booking', 630.00, 63.00, 30.00, 'Confermata', FALSE),
    ('Martina Oro', '2026-08-08', '2026-08-10', 2, 'Camera 2', 'Diretto', 630.00, 0, 20.00, 'Confermata', FALSE)
ON CONFLICT DO NOTHING;

-- ============================================================
-- FINE SCRIPT DEMO
-- ============================================================
