import os
import psycopg2
from flask import Flask, request, render_template, session
from dotenv import load_dotenv 


load_dotenv()  # charge les variables depuis .env

# Création de l'application Flask
app = Flask(__name__)
app.secret_key = "une_clé_secrète_à_changer"  # À externaliser plus tard dans un .env

# Connexion à PostgreSQL via variables d'environnement (compatibles Docker)
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST")
)
cur = conn.cursor()

@app.route("/", methods=["GET", "POST"])
def formulaire():
    if request.method == "POST":
        id_client = request.form["id_client"]
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        iban = request.form["iban"]
        mot_de_passe = request.form["mot_de_passe"]

        # Vérifier que l'id_client est unique
        # Vérifier que l’IBAN est unique
        cur.execute("SELECT id FROM utilisateurs WHERE iban = %s", (iban,))
        if cur.fetchone():
            return "❌ IBAN déjà utilisé. <a href='/'>Réessayer</a>"

        cur.execute("SELECT id FROM utilisateurs WHERE id_client = %s", (id_client,))
        if cur.fetchone():
            return "❌ id_client déjà pris. <a href='/'>Réessayer</a>"

        # Insérer l'utilisateur
        cur.execute(
            "INSERT INTO utilisateurs (id_client, nom, prenom, iban, solde, mot_de_passe) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (id_client, nom, prenom, iban, 0, mot_de_passe)
        )
        nouvel_id = cur.fetchone()[0]
        conn.commit()

        # Connecter automatiquement
        session["user_id"] = nouvel_id

        return f"""
            ✅ Compte créé avec succès !<br><br>
            <a href='/transfert'>Faire un virement</a><br>
            <a href='/logout'>Se déconnecter</a>
        """

    return render_template("formulaire.html")

@app.route("/utilisateurs")
def liste_utilisateurs():
    cur.execute("SELECT id, nom, prenom, iban FROM utilisateurs ORDER BY id")
    utilisateurs = cur.fetchall()
    return render_template("utilisateurs.html", utilisateurs=utilisateurs)

@app.route("/supprimer/<int:id>", methods=["POST"])
def supprimer_utilisateur(id):
    cur.execute("DELETE FROM utilisateurs WHERE id = %s", (id,))
    conn.commit()
    return "Utilisateur supprimé. <a href='/utilisateurs'>Retour</a>"

@app.route("/modifier/<int:id>", methods=["GET", "POST"])
def modifier_utilisateur(id):
    if request.method == "POST":
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        iban = request.form["iban"]

        cur.execute(
            "UPDATE utilisateurs SET nom = %s, prenom = %s, iban = %s WHERE id = %s",
            (nom, prenom, iban, id)
        )
        conn.commit()
        return "Utilisateur modifié avec succès. <a href='/utilisateurs'>Retour</a>"

    # Si méthode GET → on affiche le formulaire avec les données actuelles
    cur.execute("SELECT nom, prenom, iban FROM utilisateurs WHERE id = %s", (id,))
    utilisateur = cur.fetchone()
    return render_template("modifier.html", id=id, utilisateur=utilisateur)

@app.route("/transfert", methods=["GET", "POST"])
def transfert():
    if "user_id" not in session:
        return "Vous devez vous connecter. <a href='/'>Créer un compte</a>"

    source_id = session["user_id"]

    # Récupérer solde et IBAN du connecté
    cur.execute("SELECT solde, iban FROM utilisateurs WHERE id = %s", (source_id,))
    row = cur.fetchone()
    if not row:
        return "Utilisateur introuvable."

    solde, iban_source = row

    if request.method == "POST":
        iban_dest = request.form["iban_dest"].strip()

        try:
            montant = float(request.form["montant"])
        except ValueError:
            return "❌ Montant invalide. <a href='/transfert'>Réessayer</a>"

        if montant <= 0:
            return "❌ Le montant doit être supérieur à 0. <a href='/transfert'>Réessayer</a>"

        # Empêcher de se virer à soi-même par IBAN
        if iban_dest == iban_source:
            return "❌ Vous ne pouvez pas vous envoyer de l'argent à vous-même. <a href='/transfert'>Retour</a>"

        # Vérifie si le destinataire existe
        cur.execute("SELECT id FROM utilisateurs WHERE iban = %s", (iban_dest,))
        row = cur.fetchone()

        if not row:
            return "❌ Destinataire introuvable. <a href='/transfert'>Réessayer</a>"

        dest_id = row[0]

        if solde < montant:
            return "❌ Solde insuffisant. <a href='/transfert'>Retour</a>"

        # Mise à jour des soldes
        cur.execute("UPDATE utilisateurs SET solde = solde - %s WHERE id = %s", (montant, source_id))
        cur.execute("UPDATE utilisateurs SET solde = solde + %s WHERE id = %s", (montant, dest_id))
        conn.commit()

        return f"""
            ✅ Transfert de {montant:.2f} € effectué avec succès à l’IBAN {iban_dest}.<br><br>
            <a href='/transfert'>Faire un autre virement</a><br>
            <a href='/'>Retour à l'accueil</a>
        """

    return render_template("transfert.html", source_id=source_id, solde=solde, iban_source=iban_source)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        id_client = request.form["id_client"]
        mot_de_passe = request.form["mot_de_passe"]

        # On récupère l'id numérique ET le mot de passe d'un coup
        cur.execute("SELECT id, mot_de_passe FROM utilisateurs WHERE id_client = %s", (id_client,))
        row = cur.fetchone()

        if not row:
            return "❌ Utilisateur non trouvé."

        id_num, mot_de_passe_en_base = row

        if mot_de_passe != mot_de_passe_en_base:
            return "❌ Mot de passe incorrect."

        # On stocke l’ID NUMÉRIQUE dans la session
        session["user_id"] = id_num

        return f"""
            ✅ Connecté en tant qu'utilisateur {id_client}.<br>
            <a href='/transfert'>Faire un virement</a><br>
            <a href='/logout'>Se déconnecter</a>
        """

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return "Déconnecté avec succès.<br><a href='/'>Accueil</a>"

# Lancer le serveur web Flask
if __name__ == "__main__":
    app.run(debug=True)
