"""
db/database.py

Configuration centrale de la connexion PostgreSQL via SQLAlchemy 2.x
et le driver psycopg 3 (postgresql+psycopg://...).

N'appelle JAMAIS Base.metadata.create_all() : la création et
l'évolution du schéma passent exclusivement par Alembic
(alembic upgrade head), conformément au choix de garder un historique
de migrations propre pendant tout le développement du PFE.

Ce module est totalement indépendant du pipeline IA/RAG existant
(rag/, backend/intent_classifier.py) -- aucune dépendance croisée.
"""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# ============================================================
# 1. VARIABLES D'ENVIRONNEMENT
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise RuntimeError(
        "La variable d'environnement DATABASE_URL est manquante. "
        "Créez un fichier .env à la racine du projet "
        "(voir .env.example) avec, par exemple :\n"
        "DATABASE_URL="
        "postgresql+psycopg://"
        "emc_user:emc_password@localhost:5432/emc_helpline"
    )


if not DATABASE_URL.startswith(
    "postgresql+psycopg://"
):
    raise RuntimeError(
        "DATABASE_URL doit utiliser le driver psycopg 3 "
        "explicitement "
        "(postgresql+psycopg://...), pas psycopg2. "
        f"Valeur actuelle : {DATABASE_URL!r}"
    )


# ============================================================
# 2. ENGINE SQLALCHEMY
# ============================================================

# pool_pre_ping=True :
# vérifie qu'une connexion du pool est encore valide avant
# de la réutiliser. C'est utile en développement si PostgreSQL
# est redémarré indépendamment de FastAPI.

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# 3. SESSION SQLALCHEMY
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# 4. BASE DÉCLARATIVE
# ============================================================

class Base(DeclarativeBase):
    """
    Classe de base déclarative SQLAlchemy 2.x.

    Tous les modèles définis dans db/models.py héritent de cette
    classe.

    Alembic utilise Base.metadata pour détecter les tables et
    générer les migrations.
    """

    pass


# ============================================================
# 5. DÉPENDANCE FASTAPI
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    Fournit une session SQLAlchemy à une requête FastAPI.

    Exemple futur :

        db: Session = Depends(get_db)

    Une session est créée pour la requête puis fermée
    automatiquement grâce au bloc finally.

    Cette fonction utilise `yield`, donc son type de retour est
    Generator[Session, None, None] et non simplement Session.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()