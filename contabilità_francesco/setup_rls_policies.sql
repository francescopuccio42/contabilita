-- ============================================================
-- Script per configurare le Policy RLS (Row Level Security)
-- su tutte le tabelle del database Supabase
-- Esegui questo script nel SQL Editor di Supabase Dashboard
-- ============================================================

-- 1. Abilita RLS su tutte le tabelle
ALTER TABLE transazioni ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorie ENABLE ROW LEVEL SECURITY;
ALTER TABLE scadenze ENABLE ROW LEVEL SECURITY;
ALTER TABLE prenotazioni ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;

-- 2. Crea policy per la tabella transazioni
CREATE POLICY "Accesso completo transazioni"
ON transazioni
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- 3. Crea policy per la tabella categorie
CREATE POLICY "Accesso completo categorie"
ON categorie
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- 4. Crea policy per la tabella scadenze
CREATE POLICY "Accesso completo scadenze"
ON scadenze
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- 5. Crea policy per la tabella prenotazioni
CREATE POLICY "Accesso completo prenotazioni"
ON prenotazioni
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- 6. Crea policy per la tabella error_logs
CREATE POLICY "Accesso completo error_logs"
ON error_logs
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- 7. Concedi permessi sulle sequenze
GRANT USAGE, SELECT ON SEQUENCE transazioni_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE categorie_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE scadenze_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE prenotazioni_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE error_logs_id_seq TO authenticated;

-- 8. Verifica policy
SELECT tablename, policyname, roles, cmd FROM pg_policies
WHERE schemaname = 'public' ORDER BY tablename;