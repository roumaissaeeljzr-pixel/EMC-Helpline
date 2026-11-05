"""
tests/compare_embedding_models_arabic.py

Compare plusieurs modèles d'embedding multilingues sur le retrieval
cross-lingue (question en arabe -> passages en français), SANS
toucher à l'index FAISS de production.

Objectif : décider si le modèle d'embedding actuel
(paraphrase-multilingual-MiniLM-L12-v2) doit être remplacé avant de
lancer une réindexation complète (qui prend du temps).

Principe :
- on charge les chunks déjà générés (rag/vector_store/chunks.json) ;
- pour chaque modèle candidat, on encode TOUS les chunks à la volée
  en mémoire (pas de FAISS, pas de fichier écrit) ;
- on encode les 4 questions arabes et on calcule la similarité
  cosinus directement avec numpy ;
- on affiche le Top 3 par modèle pour comparaison visuelle.

Ce script est volontairement autonome et ne modifie rien dans
rag/vector_store/. Une fois le meilleur modèle choisi, il suffit de
changer EMBEDDING_MODEL_NAME dans rag/build_index.py et de relancer
`python -m rag.build_index`.
"""

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# 1. MODÈLES CANDIDATS
# ============================================================
#
# - Modèle actuel : gardé comme référence.
# - multilingual-e5-base : ~278M paramètres, entraîné et évalué
#   spécifiquement sur du retrieval cross-lingue (benchmark MIRACL,
#   qui inclut l'arabe). Bon compromis qualité/vitesse sur CPU.
# - multilingual-e5-large : plus lourd (~560M), meilleure qualité,
#   mais plus lent sur CPU. À tester seulement si e5-base ne suffit
#   pas.

CANDIDATE_MODELS = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "intfloat/multilingual-e5-base",
    # "intfloat/multilingual-e5-large",  # décommenter si besoin, plus lent sur CPU
]


# ============================================================
# 2. CHEMINS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent  # racine du projet
CHUNKS_FILE = BASE_DIR / "rag" / "vector_store" / "chunks.json"

if not CHUNKS_FILE.exists():
    raise FileNotFoundError(
        f"Fichier de chunks introuvable : {CHUNKS_FILE}\n"
        "Lancez d'abord 'python -m rag.build_index' au moins une fois."
    )


# ============================================================
# 3. CAS DE TEST
# ============================================================

TEST_CASES = [
    {
        "question": "تم اختراق حسابي على إنستغرام، ماذا أفعل؟",
        "expected_intent": "Piratage de compte",
    },
    {
        "question": "شخص يهدد بنشر صوري الخاصة.",
        "expected_intent": "Sextorsion",
    },
    {
        "question": "قام شخص بنشر عنواني ورقم هاتفي دون موافقتي.",
        "expected_intent": "Divulgation de données personnelles",
    },
    {
        "question": "كيف يمكنني الاحتفاظ بالأدلة على التحرش الإلكتروني؟",
        "expected_intent": "Conservation des preuves",
    },
]


# ============================================================
# 4. CHARGEMENT DES CHUNKS
# ============================================================

with CHUNKS_FILE.open("r", encoding="utf-8") as file:
    chunks = json.load(file)

print(f"Chunks chargés : {len(chunks)}")


def snippet(text: str, length: int = 130) -> str:
    flattened = " ".join(text.split())
    if len(flattened) <= length:
        return flattened
    return flattened[:length].rstrip() + "…"


# ============================================================
# 5. PRÉFIXAGE REQUIS PAR CERTAINS MODÈLES (FAMILLE E5)
# ============================================================
#
# CORRECTIF IMPORTANT :
# Les résultats précédents avec multilingual-e5-base montraient des
# scores anormalement resserrés (0.78-0.81) et un classement qui ne
# correspondait à rien — signature typique d'un modèle e5 utilisé
# SANS ses préfixes obligatoires "query: " / "passage: ".
#
# On ne se fie plus à model.encode_query()/encode_document() pour
# gérer ça automatiquement (comportement dépendant de la version de
# sentence-transformers et de la config exacte du modèle sur HF,
# visiblement pas fiable ici). On préfixe manuellement le texte
# nous-mêmes pour les modèles qui l'exigent, et on utilise .encode()
# classique pour tous les modèles.

E5_FAMILY_PREFIXES = (
    "e5-",
    "multilingual-e5",
)


def is_e5_family(model_name: str) -> bool:
    lowered = model_name.lower()
    return any(marker in lowered for marker in E5_FAMILY_PREFIXES)


def evaluate_model(model_name: str) -> None:

    print()
    print("#" * 100)
    print(f"MODÈLE : {model_name}")
    print("#" * 100)

    model = SentenceTransformer(model_name)

    needs_e5_prefix = is_e5_family(model_name)

    if needs_e5_prefix:
        print(
            "Modèle de la famille e5 détecté -> préfixage manuel "
            "'query: ' / 'passage: ' appliqué."
        )

    def encode_documents(texts: list[str]) -> np.ndarray:
        if needs_e5_prefix:
            texts = ["passage: " + text for text in texts]
        vectors = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return np.asarray(vectors, dtype="float32")

    def encode_query(text: str) -> np.ndarray:
        if needs_e5_prefix:
            text = "query: " + text
        vector = model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.asarray(vector, dtype="float32")[0]

    texts = [chunk["text"] for chunk in chunks]

    print("Encodage des chunks (peut prendre un moment)...")
    doc_vectors = encode_documents(texts)

    for i, test in enumerate(TEST_CASES, start=1):

        question = test["question"]
        expected = test["expected_intent"]

        query_vector = encode_query(question)

        # Similarité cosinus = produit scalaire (vecteurs normalisés)
        scores = doc_vectors @ query_vector

        top_indices = np.argsort(-scores)[:3]

        print()
        print("-" * 100)
        print(f"Test {i} — attendu : {expected}")
        print(f"Question : {question}")
        print()

        found = False

        for rank, idx in enumerate(top_indices, start=1):

            chunk = chunks[idx]
            score = float(scores[idx])
            intent = chunk.get("intent")
            document = chunk.get("document")

            print(f"  {rank}. document={document} | score={score:.4f} | intent={intent}")
            print(f"     extrait : {snippet(chunk['text'])}")

            if intent and expected.lower() in intent.lower():
                found = True

        print()
        print("  Résultat :", "✅ PASS" if found else "❌ FAIL")


# ============================================================
# 6. EXÉCUTION
# ============================================================

if __name__ == "__main__":

    for model_name in CANDIDATE_MODELS:
        evaluate_model(model_name)

    print()
    print("=" * 100)
    print(
        "Comparez les scores et le PASS/FAIL par modèle ci-dessus. "
        "Si un modèle candidat fait clairement mieux, changez "
        "EMBEDDING_MODEL_NAME dans rag/build_index.py puis relancez "
        "'python -m rag.build_index' pour reconstruire l'index FAISS "
        "avec ce modèle."
    )
    print("=" * 100)