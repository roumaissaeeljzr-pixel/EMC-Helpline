"""
db/test_connection.py

Script utilitaire -- vérifie uniquement que la connexion à
PostgreSQL fonctionne (SELECT 1), sans dépendre d'Alembic ni des
modèles. Utile pour valider DATABASE_URL avant de lancer les
migrations.

Lancement (depuis 06_Development, venv activé) :

    python -m db.test_connection
"""

from sqlalchemy import text

from db.database import engine


def main() -> None:

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()

        if value == 1:
            print("Connexion PostgreSQL OK -- SELECT 1 a retourné 1.")
        else:
            print(f"Connexion établie mais résultat inattendu : {value!r}")

    except Exception as exc:
        print("Échec de la connexion à PostgreSQL.")
        print(f"Erreur : {exc}")
        raise


if __name__ == "__main__":
    main()