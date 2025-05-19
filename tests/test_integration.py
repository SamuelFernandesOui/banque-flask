import sys
import os
import pytest


# Ajouter le dossier parent (racine projet) au PATH Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, conn, cur

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_transfert_argent(client):
    # Suppression utilisateurs test (commit nécessaire après)
    cur.execute("DELETE FROM utilisateurs WHERE id_client = ANY(%s)", (["test_sender", "test_receiver"],))
    conn.commit()

    # Création utilisateurs test
    cur.execute("INSERT INTO utilisateurs (id_client, nom, prenom, iban, solde, mot_de_passe) VALUES (%s,%s,%s,%s,%s,%s)",
                ("test_sender", "Test", "Sender", "FR000", 1000, "pass"))
    cur.execute("INSERT INTO utilisateurs (id_client, nom, prenom, iban, solde, mot_de_passe) VALUES (%s,%s,%s,%s,%s,%s)",
                ("test_receiver", "Test", "Receiver", "FR001", 500, "pass"))
    conn.commit()

    # Récupérer les id internes
    cur.execute("SELECT id FROM utilisateurs WHERE id_client = %s", ("test_sender",))
    sender_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM utilisateurs WHERE id_client = %s", ("test_receiver",))
    receiver_id = cur.fetchone()[0]

    # Simuler session
    with client.session_transaction() as sess:
        sess['user_id'] = sender_id

    # Faire la requête POST
    response = client.post('/transfert', data={
        'iban_dest': 'FR001',
        'montant': '200'
    })

    # Pour debug : print la réponse
    print(response.data.decode())

    assert response.status_code == 200

    # Vérifier soldes mis à jour
    cur.execute("SELECT solde FROM utilisateurs WHERE id = %s", (sender_id,))
    sender_solde = cur.fetchone()[0]
    cur.execute("SELECT solde FROM utilisateurs WHERE id = %s", (receiver_id,))
    receiver_solde = cur.fetchone()[0]

    assert sender_solde == 800
    assert receiver_solde == 700

    # Nettoyer après test
    cur.execute("DELETE FROM utilisateurs WHERE id_client = ANY(%s)", (["test_sender", "test_receiver"],))
    conn.commit()
