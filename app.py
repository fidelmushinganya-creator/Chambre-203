from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os
import uuid

app = Flask(__name__)

app.secret_key = "chambre203-secret-2026"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("database", exist_ok=True)


# =========================
# BASE DE DONNÉES
# =========================

def get_db():
    conn = sqlite3.connect("database/chambre203.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# ACCUEIL
# =========================

@app.route("/")
def accueil():
    return render_template("index.html")


# =========================
# COMMANDE CLIENT
# =========================

@app.route("/commande", methods=["GET", "POST"])
def commande():

    if request.method == "POST":

        nom = request.form.get("nom", "").strip()
        telephone = request.form.get("telephone", "").strip()
        service = request.form.get("service", "").strip()
        quantite = request.form.get("quantite", "1")
        instructions = request.form.get("instructions", "").strip()

        if not nom or not telephone or not service:
            return "Veuillez remplir tous les champs obligatoires.", 400

        # Numéro de commande
        numero = "CMD-203-" + str(uuid.uuid4())[:6].upper()

        conn = get_db()
        cursor = conn.cursor()

        # Enregistrer la commande
        cursor.execute("""
            INSERT INTO commandes
            (
                numero,
                nom_client,
                telephone,
                service,
                quantite,
                instructions,
                statut
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            numero,
            nom,
            telephone,
            service,
            quantite,
            instructions,
            "En attente"
        ))

        commande_id = cursor.lastrowid

        # Récupérer TOUS les fichiers envoyés
        fichiers = request.files.getlist("fichier")

        for fichier in fichiers:

            if fichier and fichier.filename:

                nom_original = fichier.filename

                # Extension du fichier
                extension = os.path.splitext(
                    nom_original
                )[1].lower()

                # Nom sécurisé pour le stockage
                nouveau_nom = str(uuid.uuid4()) + extension

                chemin = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    nouveau_nom
                )

                # Sauvegarder le fichier
                fichier.save(chemin)

                # Enregistrer le fichier dans la base
                cursor.execute("""
                    INSERT INTO fichiers
                    (
                        commande_id,
                        nom_original,
                        nom_stockage
                    )
                    VALUES (?, ?, ?)
                """, (
                    commande_id,
                    nom_original,
                    nouveau_nom
                ))

        conn.commit()
        conn.close()

        return render_template(
            "confirmation.html",
            numero=numero,
            nom=nom
        )

    return render_template("commande.html")


# =========================
# SUIVI CLIENT
# =========================

@app.route("/suivre", methods=["GET", "POST"])
def suivre():

    commande = None

    if request.method == "POST":

        numero = request.form.get("numero", "").strip()

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM commandes
            WHERE numero = ?
        """, (numero,))

        commande = cursor.fetchone()

        conn.close()

    return render_template(
        "suivre.html",
        commande=commande
    )


# =========================
# CONNEXION ADMIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == "admin" and password == "203admin":

            session["admin_connecte"] = True

            return redirect("/admin")

        return render_template(
            "login.html",
            erreur="Nom d'utilisateur ou mot de passe incorrect."
        )

    return render_template("login.html")


# =========================
# TABLEAU DE BORD
# =========================

@app.route("/admin")
def admin():

    if not session.get("admin_connecte"):
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM commandes"
    )
    nombre_commandes = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM clients"
    )
    nombre_clients = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM commandes
        WHERE statut = 'En attente'
    """)
    commandes_attente = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM commandes
        WHERE statut = 'En cours'
    """)
    commandes_en_cours = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        nombre_commandes=nombre_commandes,
        nombre_clients=nombre_clients,
        commandes_attente=commandes_attente,
        commandes_en_cours=commandes_en_cours
    )


# =========================
# LISTE DES COMMANDES
# =========================

@app.route("/commandes")
def commandes():

    if not session.get("admin_connecte"):
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM commandes
        ORDER BY id DESC
    """)

    commandes = cursor.fetchall()

    conn.close()

    return render_template(
        "commandes.html",
        commandes=commandes
    )


# =========================
# DÉTAIL COMMANDE
# =========================

@app.route("/commande/<int:commande_id>")
def detail_commande(commande_id):

    if not session.get("admin_connecte"):
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM commandes
        WHERE id = ?
    """, (commande_id,))

    commande = cursor.fetchone()

    if commande is None:

        conn.close()

        return "Commande introuvable.", 404

    cursor.execute("""
        SELECT *
        FROM fichiers
        WHERE commande_id = ?
        ORDER BY id ASC
    """, (commande_id,))

    fichiers = cursor.fetchall()

    conn.close()

    return render_template(
        "detail_commande.html",
        commande=commande,
        fichiers=fichiers
    )


# =========================
# TÉLÉCHARGER UN FICHIER
# =========================

@app.route("/telecharger/<nom_fichier>")
def telecharger(nom_fichier):

    if not session.get("admin_connecte"):
        return redirect("/login")

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        nom_fichier,
        as_attachment=True
    )


# =========================
# VOIR UN FICHIER
# =========================

@app.route("/voir-fichier/<nom_fichier>")
def voir_fichier(nom_fichier):

    if not session.get("admin_connecte"):
        return redirect("/login")

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        nom_fichier
    )


# =========================
# MODIFIER LE STATUT
# =========================

@app.route(
    "/modifier-statut/<int:commande_id>",
    methods=["POST"]
)
def modifier_statut(commande_id):

    if not session.get("admin_connecte"):
        return redirect("/login")

    statut = request.form.get("statut", "En attente")

    statuts_autorises = [
        "En attente",
        "En cours",
        "Imprimée",
        "Terminée",
        "Annulée"
    ]

    if statut not in statuts_autorises:
        return "Statut incorrect.", 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE commandes
        SET statut = ?
        WHERE id = ?
    """, (
        statut,
        commande_id
    ))

    conn.commit()
    conn.close()

    return redirect(
        f"/commande/{commande_id}"
    )


# =========================
# DÉCONNEXION
# =========================
# =========================
# MESSAGERIE CLIENT
# =========================
# =========================
# MESSAGERIE ADMIN
# =========================
# =========================
# RÉPONDRE À UN MESSAGE
# =========================

@app.route(
    "/admin/repondre-message/<int:message_id>",
    methods=["POST"]
)
def repondre_message(message_id):

    if not session.get("admin_connecte"):
        return redirect("/login")

    reponse = request.form.get("reponse", "").strip()

    if not reponse:
        return "La réponse ne peut pas être vide.", 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE messages
        SET reponse = ?
        WHERE id = ?
    """, (
        reponse,
        message_id
    ))

    conn.commit()
    conn.close()

    return redirect("/admin/messagerie")
@app.route("/admin/messagerie")
def admin_messagerie():

    if not session.get("admin_connecte"):
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM messages
        ORDER BY id DESC
    """)

    messages = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_messagerie.html",
        messages=messages
    )
@app.route("/messagerie", methods=["GET", "POST"])
@app.route("/messagerie", methods=["GET", "POST"])

# =========================
# DÉCONNEXION
# =========================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# INITIALISATION BASE
# =========================

def initialiser_base():

    conn = get_db()
    cursor = conn.cursor()

    # Clients
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            telephone TEXT NOT NULL
        )
    """)

    # Commandes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            nom_client TEXT NOT NULL,
            telephone TEXT NOT NULL,
            service TEXT NOT NULL,
            fichier TEXT,
            quantite INTEGER DEFAULT 1,
            statut TEXT DEFAULT 'En attente',
            date_commande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            instructions TEXT
        )
    """)

    # Fichiers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fichiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commande_id INTEGER NOT NULL,
            nom_original TEXT NOT NULL,
            nom_stockage TEXT NOT NULL,
            FOREIGN KEY (commande_id)
            REFERENCES commandes(id)
        )
    """)

    conn.commit()
    conn.close()


initialiser_base()


# =========================
# LANCEMENT
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8081,
        debug=True
    )
