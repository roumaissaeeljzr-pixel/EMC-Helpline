import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.intent_classifier import predict_intent


# ============================================================
# 1. CHEMINS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

VECTOR_STORE_DIR = BASE_DIR / "vector_store"

INDEX_FILE = (
    VECTOR_STORE_DIR
    / "emc_faiss.index"
)

CHUNKS_FILE = (
    VECTOR_STORE_DIR
    / "chunks.json"
)

CONFIG_FILE = (
    VECTOR_STORE_DIR
    / "rag_config.json"
)


# ============================================================
# 2. VÉRIFICATION DES FICHIERS
# ============================================================

for file_path in [
    INDEX_FILE,
    CHUNKS_FILE,
    CONFIG_FILE,
]:

    if not file_path.exists():

        raise FileNotFoundError(
            f"Fichier RAG introuvable : "
            f"{file_path}"
        )


# ============================================================
# 3. CHARGEMENT CONFIG
# ============================================================

with CONFIG_FILE.open(
    "r",
    encoding="utf-8",
) as file:

    config = json.load(
        file
    )


EMBEDDING_MODEL_NAME = (
    config["embedding_model"]
)


# ============================================================
# 4. CHARGEMENT DES CHUNKS
# ============================================================

with CHUNKS_FILE.open(
    "r",
    encoding="utf-8",
) as file:

    chunks = json.load(
        file
    )


# ============================================================
# 5. CHARGEMENT INDEX FAISS
# ============================================================

index = faiss.read_index(
    str(INDEX_FILE)
)


# ============================================================
# 6. VÉRIFICATION COHÉRENCE INDEX / CHUNKS
# ============================================================

if index.ntotal != len(chunks):

    raise RuntimeError(
        "Incohérence entre FAISS et chunks.json : "
        f"{index.ntotal} vecteurs FAISS "
        f"pour {len(chunks)} chunks."
    )


# ============================================================
# 7. CHARGEMENT MODÈLE EMBEDDING
# ============================================================

print("=" * 70)
print("CHARGEMENT DU RETRIEVER RAG")
print("=" * 70)

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)

print(
    "Retriever RAG prêt."
)

print(
    "Chunks :",
    len(chunks),
)

print(
    "Vecteurs FAISS :",
    index.ntotal,
)

print(
    "Langues :",
    config.get(
        "languages_indexed",
        [],
    ),
)


# ============================================================
# 8. NORMALISATION TEXTE
# ============================================================

def normalize_text(
    text: str,
) -> str:
    """
    Normalise un texte pour comparer
    thèmes et intentions.
    """

    text = str(
        text
    ).lower().strip()

    text = unicodedata.normalize(
        "NFD",
        text,
    )

    text = "".join(
        character
        for character in text
        if unicodedata.category(
            character
        ) != "Mn"
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# 9. EXTRACTION INTENTION D'UN CHUNK
# ============================================================

def extract_chunk_intent(
    text: str,
) -> str | None:
    """
    Recherche :

    Intention CamemBERT : ...
    ou
    Intention CamemBERT associée : ...
    """

    patterns = [
        (
            r"Intention\s+CamemBERT\s*:\s*"
            r"([^\n\r]+)"
        ),
        (
            r"Intention\s+CamemBERT\s+"
            r"associ[eé]e\s*:\s*"
            r"([^\n\r]+)"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            intent = (
                match
                .group(1)
                .strip()
            )

            # Ancien format français
            intent = intent.split(
                "Type d'information"
            )[0].strip()

            # Format arabe éventuel
            intent = intent.split(
                "نوع المعلومات"
            )[0].strip()

            return intent

    return None


# ============================================================
# 10. EXTRACTION THÈME D'UN CHUNK
# ============================================================

def extract_chunk_theme(
    text: str,
) -> str | None:
    """
    Recherche :

    Français :
        Thème : ...

    Arabe :
        الموضوع : ...
    """

    patterns = [
        r"Th[eè]me\s*:\s*([^\n\r]+)",
        r"الموضوع\s*:\s*([^\n\r]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        theme = (
            match
            .group(1)
            .strip()
        )

        theme = theme.split(
            "Intention CamemBERT"
        )[0].strip()

        return theme

    return None


# ============================================================
# 11. BONUS INTENTION
# ============================================================

def calculate_intent_bonus(
    chunk: dict[str, Any],
    predicted_intent: str | None,
    bonus_value: float = 0.10,
) -> tuple[float, str | None]:
    """
    Retourne toujours l'intention réelle
    du chunk.

    Le bonus est appliqué uniquement
    lorsqu'une prédiction CamemBERT existe
    et correspond.
    """

    chunk_intent = (
        chunk.get(
            "intent"
        )
        or extract_chunk_intent(
            chunk["text"]
        )
    )

    if not chunk_intent:

        return (
            0.0,
            None,
        )

    if not predicted_intent:

        return (
            0.0,
            chunk_intent,
        )

    predicted_normalized = (
        normalize_text(
            predicted_intent
        )
    )

    chunk_normalized = (
        normalize_text(
            chunk_intent
        )
    )

    if (
        predicted_normalized
        == chunk_normalized
    ):

        return (
            bonus_value,
            chunk_intent,
        )

    return (
        0.0,
        chunk_intent,
    )


# ============================================================
# 12. BONUS THÈME
# ============================================================

def calculate_theme_bonus(
    chunk: dict[str, Any],
    predicted_intent: str | None,
    bonus_value: float = 0.08,
) -> tuple[float, str | None]:
    """
    Retourne toujours le thème réel
    du chunk.

    Pour le français, un bonus peut être
    appliqué lorsque le thème correspond
    à l'intention CamemBERT.

    Pour l'arabe, predicted_intent sera
    normalement None.
    """

    chunk_theme = (
        chunk.get(
            "theme"
        )
        or extract_chunk_theme(
            chunk["text"]
        )
    )

    if not chunk_theme:

        return (
            0.0,
            None,
        )

    if not predicted_intent:

        return (
            0.0,
            chunk_theme,
        )

    predicted_normalized = (
        normalize_text(
            predicted_intent
        )
    )

    theme_normalized = (
        normalize_text(
            chunk_theme
        )
    )

    if (
        predicted_normalized
        in theme_normalized
        or theme_normalized
        in predicted_normalized
    ):

        return (
            bonus_value,
            chunk_theme,
        )

    return (
        0.0,
        chunk_theme,
    )


# ============================================================
# 13. VALIDATION LANGUE
# ============================================================

def validate_language(
    language: str | None,
) -> str | None:
    """
    Valeurs acceptées :
        None
        "fr"
        "ar"
    """

    if language is None:
        return None

    language = (
        str(language)
        .lower()
        .strip()
    )

    if language not in {
        "fr",
        "ar",
    }:

        raise ValueError(
            "Langue RAG non supportée : "
            f"{language}. "
            "Utilisez 'fr', 'ar' ou None."
        )

    return language


# ============================================================
# 14. TEST LANGUE D'UN CHUNK
# ============================================================

def chunk_matches_language(
    chunk: dict[str, Any],
    language: str | None,
) -> bool:
    """
    Si aucune langue n'est demandée :
        accepte tous les chunks.

    Sinon :
        ne conserve que la langue demandée.
    """

    if language is None:
        return True

    chunk_language = (
        chunk.get(
            "language"
        )
    )

    return (
        chunk_language
        == language
    )


# ============================================================
# 15. RECHERCHE HYBRIDE BILINGUE
# ============================================================

def retrieve(
    query: str,
    top_k: int = 5,
    minimum_score: float = 0.25,
    use_intent: bool = True,
    intent_bonus: float = 0.10,
    theme_bonus: float = 0.08,
    candidate_k: int = 30,
    language: str | None = None,
    predicted_intent_override: str | None = None,
) -> list[dict[str, Any]]:
    """
    Recherche RAG bilingue.

    Français :
        - question française
        - CamemBERT directement
        - retrieval dans les chunks français

    Arabe :
        - question arabe
        - traduction AR -> FR faite en amont
        - CamemBERT sur la traduction
        - l'intention obtenue est passée via
          predicted_intent_override
        - retrieval uniquement dans les chunks arabes

    Exemple arabe :

        retrieve(
            query="شخص يهدد بنشر صوري الخاصة.",
            top_k=3,
            language="ar",
            use_intent=False,
            predicted_intent_override="Sextorsion",
        )
    """

    if not query or not query.strip():
        return []

    language = validate_language(
        language
    )

    # ========================================================
    # A. INTENTION
    # ========================================================

    predicted_intent = None
    intent_confidence = None

    # --------------------------------------------------------
    # CAS 1 :
    # intention déjà calculée en amont
    # (utile pour arabe -> traduction FR -> CamemBERT)
    # --------------------------------------------------------

    if predicted_intent_override:

        predicted_intent = (
            predicted_intent_override.strip()
        )

    # --------------------------------------------------------
    # CAS 2 :
    # français normal -> CamemBERT
    # --------------------------------------------------------

    elif (
        use_intent
        and language != "ar"
    ):

        try:

            intent_result = predict_intent(
                query
            )

            predicted_intent = (
                intent_result["intent"]
            )

            intent_confidence = float(
                intent_result["confidence"]
            )

        except Exception as exc:

            print(
                "Attention : "
                "CamemBERT indisponible :",
                exc,
            )

            predicted_intent = None
            intent_confidence = None

    # ========================================================
    # B. EMBEDDING QUESTION
    # ========================================================

    query_embedding = (
        embedding_model.encode_query(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32",
    )

    # ========================================================
    # C. CANDIDATS FAISS
    # ========================================================

    # Lorsque la langue est connue, on cherche
    # dans tout le petit index puis on filtre.
    if language is not None:

        search_k = len(
            chunks
        )

    else:

        search_k = min(
            max(
                candidate_k,
                top_k,
            ),
            len(chunks),
        )

    scores, indices = index.search(
        query_embedding,
        search_k,
    )

    candidate_scores: dict[
        int,
        float,
    ] = {}

    for semantic_score, chunk_id in zip(
        scores[0],
        indices[0],
    ):

        chunk_id = int(
            chunk_id
        )

        if chunk_id < 0:
            continue

        chunk = chunks[
            chunk_id
        ]

        # ====================================================
        # FILTRAGE PAR LANGUE
        # ====================================================

        if not chunk_matches_language(
            chunk,
            language,
        ):
            continue

        candidate_scores[
            chunk_id
        ] = float(
            semantic_score
        )

    # ========================================================
    # D. AJOUT DE TOUS LES CHUNKS DE LA BONNE INTENTION
    # ========================================================
    #
    # Très important pour l'arabe :
    #
    # query arabe
    #     ↓
    # traduction FR
    #     ↓
    # CamemBERT
    #     ↓
    # Sextorsion
    #     ↓
    # ici on récupère tous les chunks AR
    # intent="Sextorsion"
    # ========================================================

    if predicted_intent:

        normalized_predicted = (
            normalize_text(
                predicted_intent
            )
        )

        for chunk_id, chunk in enumerate(
            chunks
        ):

            # Toujours respecter la langue
            if not chunk_matches_language(
                chunk,
                language,
            ):
                continue

            chunk_intent = (
                chunk.get(
                    "intent"
                )
                or extract_chunk_intent(
                    chunk["text"]
                )
            )

            if not chunk_intent:
                continue

            normalized_chunk_intent = (
                normalize_text(
                    chunk_intent
                )
            )

            if (
                normalized_chunk_intent
                != normalized_predicted
            ):
                continue

            # Déjà calculé par FAISS
            if (
                chunk_id
                in candidate_scores
            ):
                continue

            # Récupérer directement le vecteur
            # déjà stocké dans FAISS
            chunk_vector = index.reconstruct(
                int(chunk_id)
            )

            chunk_vector = np.asarray(
                chunk_vector,
                dtype="float32",
            )

            semantic_score = float(
                np.dot(
                    query_embedding[0],
                    chunk_vector,
                )
            )

            candidate_scores[
                chunk_id
            ] = semantic_score

    # ========================================================
    # E. RERANKING
    # ========================================================

    candidates = []

    for (
        chunk_id,
        semantic_score,
    ) in candidate_scores.items():

        chunk = chunks[
            chunk_id
        ]

        (
            intent_bonus_value,
            chunk_intent,
        ) = calculate_intent_bonus(
            chunk=chunk,
            predicted_intent=(
                predicted_intent
            ),
            bonus_value=(
                intent_bonus
            ),
        )

        (
            theme_bonus_value,
            chunk_theme,
        ) = calculate_theme_bonus(
            chunk=chunk,
            predicted_intent=(
                predicted_intent
            ),
            bonus_value=(
                theme_bonus
            ),
        )

        final_score = (
            semantic_score
            + intent_bonus_value
            + theme_bonus_value
        )

        candidates.append(
            {
                "score": round(
                    final_score,
                    4,
                ),

                "semantic_score": round(
                    semantic_score,
                    4,
                ),

                "intent_bonus": round(
                    intent_bonus_value,
                    4,
                ),

                "theme_bonus": round(
                    theme_bonus_value,
                    4,
                ),

                "predicted_intent":
                    predicted_intent,

                "intent_confidence": (
                    round(
                        intent_confidence,
                        4,
                    )
                    if intent_confidence
                    is not None
                    else None
                ),

                "chunk_intent":
                    chunk_intent,

                "chunk_theme":
                    chunk_theme,

                "language":
                    chunk.get(
                        "language"
                    ),

                "document":
                    chunk.get(
                        "document"
                    ),

                "source_file":
                    chunk.get(
                        "source_file"
                    ),

                "page":
                    chunk.get(
                        "page"
                    ),

                "chunk_index":
                    chunk.get(
                        "chunk_index"
                    ),

                "text":
                    chunk.get(
                        "text",
                        "",
                    ),
            }
        )

    # ========================================================
    # F. TRI GLOBAL
    # ========================================================

    candidates.sort(
        key=lambda item: item[
            "score"
        ],
        reverse=True,
    )

    # ========================================================
    # G. PRIORITÉ ABSOLUE À LA BONNE INTENTION
    # ========================================================

    if predicted_intent:

        normalized_predicted = (
            normalize_text(
                predicted_intent
            )
        )

        intent_results = [
            candidate
            for candidate in candidates
            if (
                candidate.get(
                    "chunk_intent"
                )
                and normalize_text(
                    candidate[
                        "chunk_intent"
                    ]
                )
                == normalized_predicted
            )
        ]

        # On conserve une sécurité sémantique minimale.
        intent_results = [
            candidate
            for candidate in intent_results
            if candidate.get(
                "semantic_score",
                0.0,
            ) >= 0.0
        ]

        if intent_results:

            intent_results.sort(
                key=lambda item: item[
                    "score"
                ],
                reverse=True,
            )

            return intent_results[
                :top_k
            ]

    # ========================================================
    # H. FALLBACK SÉMANTIQUE
    # ========================================================

    results = [
        candidate
        for candidate in candidates
        if candidate.get(
            "semantic_score",
            0.0,
        )
        >= minimum_score
    ]

    return results[
        :top_k
    ]

# ============================================================
# 16. AFFICHAGE
# ============================================================

def print_results(
    query: str,
    top_k: int = 5,
    use_intent: bool = True,
    language: str | None = None,
) -> None:

    print()
    print("=" * 80)
    print("QUESTION")
    print("=" * 80)

    print(
        query
    )

    print(
        "Langue RAG :",
        language,
    )

    results = retrieve(
        query=query,
        top_k=top_k,
        use_intent=use_intent,
        language=language,
    )

    if not results:

        print(
            "\nAucun passage pertinent trouvé."
        )

        return

    first_result = (
        results[0]
    )

    print()
    print("=" * 80)
    print("CLASSIFICATION")
    print("=" * 80)

    print(
        "Intention prédite :",
        first_result.get(
            "predicted_intent"
        ),
    )

    print(
        "Confiance :",
        first_result.get(
            "intent_confidence"
        ),
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print()
        print("-" * 80)

        print(
            f"RANG {rank}"
        )

        print(
            "Langue            :",
            result.get(
                "language"
            ),
        )

        print(
            "Score final       :",
            result.get(
                "score"
            ),
        )

        print(
            "Score sémantique  :",
            result.get(
                "semantic_score"
            ),
        )

        print(
            "Bonus intention   :",
            result.get(
                "intent_bonus"
            ),
        )

        print(
            "Bonus thème       :",
            result.get(
                "theme_bonus"
            ),
        )

        print(
            "Intent chunk      :",
            result.get(
                "chunk_intent"
            ),
        )

        print(
            "Thème chunk       :",
            result.get(
                "chunk_theme"
            ),
        )

        print(
            "Document          :",
            result.get(
                "document"
            ),
        )

        print(
            "Source            :",
            result.get(
                "source_file"
            ),
        )

        print(
            "Page              :",
            result.get(
                "page"
            ),
        )

        print(
            "Chunk             :",
            result.get(
                "chunk_index"
            ),
        )

        print()
        print(
            result.get(
                "text",
                "",
            )
        )


# ============================================================
# 17. COMPARAISON
# ============================================================

def compare_retrieval(
    query: str,
    top_k: int = 5,
    language: str | None = None,
) -> None:

    print()
    print("#" * 80)
    print("COMPARAISON")
    print("#" * 80)

    print()
    print(
        ">>> RAG SÉMANTIQUE SEUL"
    )

    print_results(
        query=query,
        top_k=top_k,
        use_intent=False,
        language=language,
    )

    # CamemBERT seulement en français
    if language != "ar":

        print()
        print()

        print(
            ">>> CAMEMBERT + RAG "
            "+ BONUS THÈME"
        )

        print_results(
            query=query,
            top_k=top_k,
            use_intent=True,
            language=language,
        )


# ============================================================
# 18. TEST MANUEL
# ============================================================

if __name__ == "__main__":
        print()
        print()
        print("#" * 80)
        print("TEST ARABE AVEC INTENTION OVERRIDE")
        print("#" * 80)

        results = retrieve(
            query="شخص يهدد بنشر صوري الخاصة.",
            top_k=3,
            language="ar",
            use_intent=False,
            predicted_intent_override="Sextorsion",
        )

        for rank, result in enumerate(results, start=1):
            print()
            print(f"RANG {rank}")
            print("Langue :", result.get("language"))
            print("Intention :", result.get("chunk_intent"))
            print("Thème :", result.get("chunk_theme"))
            print("Score sémantique :", result.get("semantic_score"))
            print("Score final :", result.get("score"))
            print()
            print(result.get("text", ""))
            print()
            print("#" * 80)
            print("TEST FRANÇAIS")
            print("#" * 80)

            compare_retrieval(
                query=(
                    "Mon compte Instagram "
                    "a été piraté."
                ),
                top_k=3,
                language="fr",
            )

            print()
            print()
            print("#" * 80)
            print("TEST ARABE")
            print("#" * 80)

            compare_retrieval(
                query=(
                    "تم اختراق حسابي على "
                    "إنستغرام، ماذا أفعل؟"
                ),
                top_k=3,
                language="ar",
            )