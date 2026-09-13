from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import uuid

app = Flask(__name__)

app.secret_key = "chambre203-secret-2026"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def accueil():
    return render_template("index.html")


@app.route("/commande", methods=["GET", "POST"])
def commande():

    if request.method == "POST":

        nom = request.form["nom"]
        telephone = request.form["telephone"]
        service = request.form["service"]
        quantite = request.form["quantite"]
        instructions = request.form.get("instructions", "")

        fichier = request.files.get("fichier")
        nom_fichier = ""

        if fichier and fichier.filename:

            extension = os.path.splitext(fichier.filename)[1]
            nom_fichier = str(uuid.uuid4()) + extension

            chemin = os.path.join(
                app.config["UPLOAD_FOLDER"],
                nom_fichier
            )

            fichier.save(chemin)

        numero = "CMD-203-" + str(uuid.uuid4())[:6].upper()

        conn = sqlite3.connect("database/chambre203.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO commandes
        (
            numero,
            nom_client,
            telephone,
            service,
            fichier,
            quantite,
            instructions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            numero,
            nom,
            telephone,
            service,
            nom_fichier,
            quantite,
            instructions
        ))

        conn.commit()
        conn.close()

        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Commande envoyée</title>

            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f5f7fb;
                    text-align: center;
                    padding: 40px 20px;
                }}

                .box {{
                    max-width: 600px;
                    margin: auto;
                    background: white;
                    padding: 40px;
                    border-radius: 15px;
                }}

                h1 {{
                    color: #16a34a;
                }}

                .numero {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #1d4ed8;
                    margin: 20px;
                }}

                a {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 20px;
                    background: #1d4ed8;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                }}
            </style>
        </head>

        <body>

            <div class="box">

                <h1>✅ Commande envoyée !</h1>

                <p>Merci <strong>{nom}</strong>.</p>

                <p>Votre commande a été enregistrée avec succès.</p>

                <p>Votre numéro de commande :</p>

                <div class="numero">
                    {numero}
                </div>

                <p>
                    📌 Conservez ce numéro pour suivre votre commande.
                </p>

                <a href="/">
                    ← Retour à l'accueil
                </a>

            </div>

        </body>
        </html>
        """

    return render_template("commande.html")


# =========================
# CONNEXION ADMIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "203admin":

            session["admin_connecte"] = True

            return redirect("/admin")

        return render_template(
            "login.html",
            erreur="Nom d'utilisateur ou mot de passe incorrect."
        )

    return render_template("login.html")


# =========================
# ADMIN
# =========================

@app.route("/admin")
def admin():

    if not session.get("admin_connecte"):
        return redirect("/login")

    conn = sqlite3.connect("database/chambre203.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM commandes")
    nombre_commandes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM clients")
    nombre_clients = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        nombre_commandes=nombre_commandes,
        nombre_clients=nombre_clients
    )


# =========================
# COMMANDES
# =========================

@app.route("/commandes")
def commandes():

    if not session.get("admin_connecte"):
        return redirect("/login")

    conn = sqlite3.connect("database/chambre203.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM commandes ORDER BY id DESC"
    )

    commandes = cursor.fetchall()

    conn.close()

    return render_template(
        "commandes.html",
        commandes=commandes
    )


# =========================
# MODIFIER STATUT
# =========================

@app.route("/modifier-statut/<int:commande_id>", methods=["POST"])
def modifier_statut(commande_id):

    if not session.get("admin_connecte"):
        return redirect("/login")

    statut = request.form["statut"]

    conn = sqlite3.connect("database/chambre203.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE commandes
        SET statut = ?
        WHERE id = ?
    """, (statut, commande_id))

    conn.commit()
    conn.close()

    return redirect("/commandes")


# =========================
# DECONNEXION
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8081,
        debug=True
    )
