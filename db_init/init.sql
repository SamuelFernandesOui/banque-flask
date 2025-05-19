CREATE TABLE IF NOT EXISTS utilisateurs (
    id SERIAL PRIMARY KEY,
    nom TEXT,
    prenom TEXT,
    iban TEXT UNIQUE,
    solde NUMERIC DEFAULT 0,
    mot_de_passe TEXT,
    id_client TEXT UNIQUE
);
