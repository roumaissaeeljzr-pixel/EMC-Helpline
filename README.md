# EMC Helpline

## Présentation

**EMC Helpline** est une plateforme web intelligente d’assistance et d’accompagnement destinée aux victimes de cyberviolences.

Le projet combine une application web sécurisée, un système d’authentification, une API FastAPI et un moteur d’intelligence artificielle basé sur une architecture **RAG – Retrieval-Augmented Generation**.

La plateforme permet notamment :

* d’accompagner les utilisateurs victimes de cyberviolences ;
* d’analyser leur situation ;
* de proposer des recommandations adaptées ;
* d’accéder à un assistant IA ;
* de gérer les informations liées à leur dossier ;
* d’organiser les preuves et ressources ;
* de proposer une expérience en français et en arabe standard ;
* de sécuriser l’accès aux comptes utilisateurs.

---

# Architecture générale

Le projet est organisé principalement autour des composants suivants :

```text
EMC_Helpline/
│
├── alembic/            # Migrations de la base de données
├── api/                # API et routes FastAPI
├── auth/               # Authentification et sécurité
├── backend/            # Logique principale du backend
├── data/               # Données nécessaires au projet
├── db/                 # Modèles et accès PostgreSQL
├── frontend/           # Interface utilisateur React
├── knowledge_base/     # Base documentaire utilisée par le RAG
├── models/             # Modèles IA et configurations associées
├── rag/                # Pipeline Retrieval-Augmented Generation
├── scripts/            # Scripts utilitaires
├── tests/              # Tests du projet
│
├── .env.example        # Exemple de configuration
├── alembic.ini         # Configuration Alembic
├── requirements.txt    # Dépendances Python
└── README.md
```

---

# Technologies utilisées

## Backend

* Python
* FastAPI
* Uvicorn
* SQLAlchemy
* PostgreSQL
* Alembic
* JWT
* Pydantic

## Intelligence artificielle

* Transformers
* CamemBERT
* AraBERT
* FAISS
* Retrieval-Augmented Generation
* Hugging Face Transformers

## Frontend

* React
* JavaScript / JSX
* CSS
* API REST

## Base de données

* PostgreSQL
* SQLAlchemy ORM
* Alembic pour les migrations

---

# Fonctionnalités principales

## Assistant IA

L'assistant analyse les messages de l'utilisateur et fournit une réponse adaptée à sa situation.

Le système combine :

```text
Message utilisateur
        ↓
Détection de la langue
        ↓
Classification de l'intention
        ↓
Recherche documentaire
        ↓
RAG / FAISS
        ↓
Génération de la réponse
        ↓
Réponse utilisateur
```

L'assistant prend en charge :

* le français ;
* l'arabe standard.

---

# Authentification

EMC Helpline dispose d'un système complet de gestion des comptes utilisateurs.

Fonctionnalités disponibles :

```text
POST /auth/register
POST /auth/resend-verification-code
POST /auth/verify-email

POST /auth/login
POST /auth/logout
GET  /auth/me

POST /auth/forgot-password
POST /auth/verify-reset-code
POST /auth/reset-password
```

Le système prend notamment en charge :

* création d'un compte utilisateur ;
* vérification de l'adresse e-mail ;
* envoi d'un code de vérification ;
* renvoi du code ;
* authentification ;
* gestion sécurisée des sessions ;
* déconnexion ;
* récupération du compte ;
* réinitialisation du mot de passe.

Un compte nouvellement créé doit vérifier son adresse e-mail avant de pouvoir se connecter.

Les mots de passe sont stockés sous forme de hash et ne sont jamais enregistrés directement en clair dans la base de données.

---

# Sécurité

Plusieurs mécanismes de sécurité sont intégrés à la plateforme :

* mots de passe hashés ;
* authentification JWT ;
* cookies HTTPOnly pour les jetons d'accès ;
* protection CSRF ;
* expiration des jetons ;
* vérification de l'adresse e-mail ;
* limitation des tentatives de vérification ;
* expiration des codes de vérification ;
* limitation du renvoi des codes ;
* mécanisme sécurisé de réinitialisation du mot de passe ;
* messages génériques afin de limiter l'énumération des comptes ;
* séparation des données sensibles et du code source.

Les secrets de l'application ne doivent jamais être enregistrés dans le dépôt Git.

---

# Configuration

Créer un fichier :

```text
.env
```

à partir du modèle :

```text
.env.example
```

Exemple :

```env
DATABASE_URL=postgresql+psycopg://emc_user:CHANGE_ME@localhost:5432/emc_helpline
ENVIRONMENT=development
```

Selon la configuration utilisée, d'autres variables peuvent également être nécessaires, notamment pour :

```text
JWT
SMTP
Cookies
CORS
Chiffrement
Réinitialisation du mot de passe
Vérification e-mail
```

Ne jamais utiliser les valeurs d'exemple en production.

Le fichier `.env` ne doit jamais être publié sur GitHub ni envoyé avec une version publique du projet.

---

# Installation du backend

## 1. Installer Python

Python doit être installé sur la machine.

Vérification :

```bash
python --version
```

---

## 2. Créer l'environnement virtuel

Depuis le dossier du projet :

```bash
python -m venv venv
```

Sous Windows :

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

# PostgreSQL

Le projet utilise PostgreSQL comme système de gestion de base de données.

Créer une base :

```text
emc_helpline
```

Puis configurer la connexion dans `.env`.

Exemple :

```env
DATABASE_URL=postgresql+psycopg://emc_user:PASSWORD@localhost:5432/emc_helpline
```

Remplacer :

```text
PASSWORD
```

par le mot de passe PostgreSQL correspondant à l'environnement local.

---

# Migrations Alembic

Après configuration de PostgreSQL, appliquer les migrations :

```bash
alembic upgrade head
```

Cette commande crée ou met à jour les tables nécessaires au fonctionnement de l'application.

Pour vérifier les migrations :

```bash
alembic current
```

---

# Lancement du backend

Le backend FastAPI doit être lancé depuis la racine du projet avec Uvicorn.

Selon le point d'entrée configuré dans le projet, la commande suit le format :

```bash
uvicorn <module_principal>:app --reload
```

Par exemple, si l'application FastAPI se trouve dans `backend/main.py` :

```bash
uvicorn backend.main:app --reload
```

Une fois démarrée, l'API est généralement accessible sur :

```text
http://127.0.0.1:8000
```

La documentation Swagger de FastAPI est disponible sur :

```text
http://127.0.0.1:8000/docs
```

---

# Installation du frontend

Accéder au dossier :

```bash
cd frontend
```

Installer les dépendances :

```bash
npm install
```

Puis lancer l'application :

```bash
npm run dev
```

Le frontend est alors accessible sur l'adresse affichée par le serveur de développement.

---

# Communication frontend/backend

Le frontend communique avec FastAPI à travers des endpoints REST.

Exemples :

```text
GET  /health
POST /chat
```

ainsi que les endpoints d'authentification :

```text
/auth/register
/auth/verify-email
/auth/login
/auth/logout
/auth/me
/auth/forgot-password
/auth/verify-reset-code
/auth/reset-password
```

---

# Système RAG

EMC Helpline utilise une architecture :

**Retrieval-Augmented Generation**

Le principe est le suivant :

```text
Question utilisateur
        ↓
Analyse de la requête
        ↓
Recherche dans la base documentaire
        ↓
Sélection des passages pertinents
        ↓
Construction du contexte
        ↓
Génération de la réponse
```

La base documentaire est stockée dans :

```text
knowledge_base/
```

et les composants du moteur RAG sont principalement situés dans :

```text
rag/
```

---

# Modèles IA

Le projet utilise des modèles spécialisés pour le traitement du français et de l'arabe.

Les modèles sont chargés au démarrage du système ou lorsque les composants IA concernés sont utilisés.

Les fichiers de modèles volumineux peuvent être exclus du dépôt Git et fournis séparément si nécessaire.

---

# Interface utilisateur

L'espace utilisateur contient plusieurs fonctionnalités, notamment :

```text
Tableau de bord
Assistant IA
Évaluation de la situation
Plan d'action
Dossier
Preuves
Ressources
Suivi
Historique
Profil utilisateur
```

Une interface d'administration peut également permettre le suivi de la plateforme et de ses composants IA.

---

# Tests

Les tests du projet sont disponibles dans :

```text
tests/
```

Ils peuvent être exécutés avec :

```bash
pytest
```

ou :

```bash
python -m pytest
```

---

# Fichiers exclus de la livraison

Les éléments suivants ne doivent pas être inclus dans une version publique ou un dépôt Git :

```text
.env
venv/
node_modules/
__pycache__/
.pytest_cache/
archive/
protected_storage/
```

Les données utilisateur réelles, preuves, mots de passe, clés JWT, identifiants SMTP et autres secrets doivent également rester exclus.

---

# Reconstruction de l'environnement

Le dossier `venv` n'est pas nécessaire pour transférer le projet.

L'environnement peut être reconstruit avec :

```bash
python -m venv venv
```

puis :

```bash
pip install -r requirements.txt
```

Pour le frontend :

```bash
cd frontend
npm install
```

---

# Démarrage rapide

Backend :

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn <module_principal>:app --reload
```

Frontend :

```bash
cd frontend
npm install
npm run dev
```

---

# Confidentialité

EMC Helpline traite potentiellement des informations sensibles.

Toute utilisation en environnement réel doit respecter les principes suivants :

* minimisation des données collectées ;
* protection des données personnelles ;
* stockage sécurisé ;
* contrôle des accès ;
* protection des secrets ;
* journalisation maîtrisée ;
* chiffrement lorsque nécessaire ;
* absence de données personnelles réelles dans le dépôt Git.

---

# Projet

**Nom :** EMC Helpline
**Type :** Plateforme intelligente d'assistance aux victimes de cyberviolences
**Architecture :** React + FastAPI + PostgreSQL + RAG + modèles IA
**Langues :** Français et arabe standard
