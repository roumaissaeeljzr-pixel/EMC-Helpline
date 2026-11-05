"""
alembic/env.py

Configuration d'exécution d'Alembic. Deux adaptations par rapport au
squelette généré par `alembic init` :

1. DATABASE_URL est lue depuis les variables d'environnement (.env
   via python-dotenv), jamais depuis alembic.ini -- pour ne jamais
   committer d'identifiants PostgreSQL dans le dépôt.

2. target_metadata pointe vers db.database.Base.metadata, après
   import de db.models (nécessaire pour qu'Alembic "voie" les
   modèles User/Case lors de `alembic revision --autogenerate`).
"""

import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

load_dotenv()

# Importe les modèles pour peupler Base.metadata avant qu'Alembic
# ne le lise -- sans cet import, autogenerate ne détecterait aucune
# table.
from db.database import Base  # noqa: E402
from db import models  # noqa: E402, F401

config = context.config

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL manquante -- voir .env.example à la racine du projet."
    )

config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Génère le SQL des migrations sans se connecter réellement à la
    base (mode `alembic upgrade head --sql`). Non utilisé dans le
    flux de développement habituel, mais conservé pour compatibilité.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Mode standard : se connecte réellement à PostgreSQL pour
    appliquer (ou générer, en autogenerate) les migrations.
    """

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()