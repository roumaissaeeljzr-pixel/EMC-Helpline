"""
scripts/create_admin.py

Script CLI -- crée un compte administrateur.

Aucun endpoint public n'existe pour créer un compte admin
(POST /auth/register force toujours role=victim) -- c'est le SEUL
moyen prévu de créer un compte admin pour ce MVP.

Usage (depuis 06_Development, venv activé, .env configuré) :

    python -m scripts.create_admin
"""

import getpass
import sys

from auth.security import hash_password
from db.database import SessionLocal
from db.models import User, UserRole


def main() -> None:

    print("=== Création d'un compte administrateur EMC Helpline ===")
    print()

    username = input("Nom d'utilisateur : ").strip()
    email = input("Email : ").strip()
    password = getpass.getpass("Mot de passe (min. 8 caractères) : ")
    password_confirm = getpass.getpass("Confirmer le mot de passe : ")

    if not username or not email:
        print("Le nom d'utilisateur et l'email sont obligatoires.")
        sys.exit(1)

    if password != password_confirm:
        print("Les mots de passe ne correspondent pas.")
        sys.exit(1)

    if len(password) < 8:
        print("Le mot de passe doit contenir au moins 8 caractères.")
        sys.exit(1)

    db = SessionLocal()

    try:
        existing = (
            db.query(User)
            .filter(
                (User.username == username) | (User.email == email)
            )
            .first()
        )

        if existing is not None:
            print("Ce nom d'utilisateur ou cet email existe déjà.")
            sys.exit(1)

        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.admin,
        )

        db.add(admin)
        db.commit()

        print()
        print(f"Compte administrateur créé avec succès : {username}")

    finally:
        db.close()


if __name__ == "__main__":
    main()