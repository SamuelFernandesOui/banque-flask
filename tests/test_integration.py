import pytest
from app import app, conn, cur

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_transfert_argent(client):
    # Création utilisateurs test (id_client uniques)
    cur.execute("INSERT INTO utilisateurs (id_client, nom, prenom, iban, solde, mot_de_passe) VALUES (%s,%s,%s,%s,%s,%s)",
                ("test_sender", "Test", "Sender", "FR000", 1000, "pass"))
    cur.execute("INSERT INTO utilisateurs (id_client, nom, prenom, iban, solde, mot_de_passe) VALUES (%s,%s,%s,%s,%s,%s)",
                ("test_receiver", "Test", "Receiver", "FR001", 500, "pass"))
    conn.commit()

    # Récupérer les id internes des utilisateurs
    cur.execute("SELECT id FROM utilisateurs WHERE id_client = %s", ("test_sender",))
    sender_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM utilisateurs WHERE id_client = %s", ("test_receiver",))
    receiver_id = cur.fetchone()[0]

    # Simuler session connectée avec sender_id
    with client.session_transaction() as sess:
        sess['user_id'] = sender_id

    # Envoyer un transfert de 200€ du sender vers receiver
    response = client.post('/transfert', data={
        'dest_id_client': 'test_receiver',
        'montant': '200'
    })

    assert b'✅ Transfert de 200.00 € effectué avec succès' in response.data

    # Vérifier que les soldes ont changé dans la DB
    cur.execute("SELECT solde FROM utilisateurs WHERE id = %s", (sender_id,))
    sender_solde = cur.fetchone()[0]
    cur.execute("SELECT solde FROM utilisateurs WHERE id = %s", (receiver_id,))
    receiver_solde = cur.fetchone()[0]

    assert sender_solde == 800
    assert receiver_solde == 700

    # Nettoyer après test
    cur.execute("DELETE FROM utilisateurs WHERE id_client IN (%s, %s)", ("test_sender", "test_receiver"))
    conn.commit()
