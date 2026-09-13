import sqlite3

conn = sqlite3.connect("database/chambre203.db")
cursor = conn.cursor()

# Vérifier les colonnes actuelles de la table commandes
cursor.execute("PRAGMA table_info(commandes)")
colonnes = [colonne[1] for colonne in cursor.fetchall()]

# Ajouter la colonne instructions si elle n'existe pas
if "instructions" not in colonnes:
    cursor.execute("""
    ALTER TABLE commandes
    ADD COLUMN instructions TEXT
    """)

conn.commit()
conn.close()

print("Base de données CHAMBRE 203 mise à jour avec succès !")
