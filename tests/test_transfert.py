def verifier_solde(solde, montant):
    return solde >= montant

def test_verifier_solde():
    assert verifier_solde(100, 50) is True
    assert verifier_solde(20, 50) is False
