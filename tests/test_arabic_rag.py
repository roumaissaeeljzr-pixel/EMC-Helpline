"""
tests/test_arabic_rag.py

Test complet du pipeline arabe EMC Helpline :

Question arabe
    -> traduction AR -> FR
    -> CamemBERT sur la traduction française
    -> intention française
    -> RAG arabe avec predicted_intent_override
    -> validation du Top 1 / Top 3

Le corpus RAG est bilingue :
- français : language="fr"
- arabe    : language="ar"

CamemBERT reste français. Pour l'arabe, on ne lui donne donc
jamais directement la question arabe : on traduit d'abord la
question vers le français avec le modèle Marian.
"""

from backend.intent_classifier import predict_intent
from rag.query_translator import translate_arabic_to_french
from rag.retriever import retrieve


# ============================================================
# 1. CAS DE TEST
# ============================================================

TEST_CASES = [
    {
        "question": (
            "تم اختراق حسابي على إنستغرام، ماذا أفعل؟"
        ),
        "expected_intent": "Piratage de compte",
    },
    {
        "question": (
            "شخص يهدد بنشر صوري الخاصة."
        ),
        "expected_intent": "Sextorsion",
    },
    {
        "question": (
            "قام شخص بنشر عنواني ورقم هاتفي دون موافقتي."
        ),
        "expected_intent": (
            "Divulgation de données personnelles (Doxing)"
        ),
    },
    {
        "question": (
            "كيف يمكنني الاحتفاظ بالأدلة "
            "على التحرش الإلكتروني؟"
        ),
        "expected_intent": "Conservation des preuves",
    },
]


# ============================================================
# 2. UTILITAIRE D'AFFICHAGE
# ============================================================

def snippet(
    text: str | None,
    length: int = 160,
) -> str:
    """
    Retourne un extrait court du chunk.
    """

    if not text:
        return "(texte vide)"

    flattened = " ".join(
        text.split()
    )

    if len(flattened) <= length:
        return flattened

    return (
        flattened[:length].rstrip()
        + "…"
    )


# ============================================================
# 3. NORMALISATION LÉGÈRE POUR TEST
# ============================================================

def normalized(
    text: str | None,
) -> str:

    if not text:
        return ""

    return (
        text
        .strip()
        .lower()
    )


# ============================================================
# 4. EXÉCUTION DES TESTS
# ============================================================

def run_tests() -> None:

    total = len(
        TEST_CASES
    )

    correct_translation_intent = 0
    correct_top1 = 0
    correct_top3 = 0

    for index, test in enumerate(
        TEST_CASES,
        start=1,
    ):

        question = test[
            "question"
        ]

        expected_intent = test[
            "expected_intent"
        ]

        print()
        print("=" * 100)

        print(
            f"TEST ARABE "
            f"{index}/{total}"
        )

        print("=" * 100)

        print()
        print("QUESTION ARABE")
        print("-" * 100)
        print(question)

        print()
        print(
            "INTENTION ATTENDUE :",
            expected_intent,
        )

        # ====================================================
        # A. TRADUCTION AR -> FR
        # ====================================================

        try:

            french_question = (
                translate_arabic_to_french(
                    question
                )
            )

        except Exception as exc:

            print()
            print(
                "❌ ERREUR TRADUCTION :",
                exc,
            )

            continue

        print()
        print("TRADUCTION FRANÇAISE")
        print("-" * 100)
        print(french_question)

        # ====================================================
        # B. CAMEMBERT SUR LA TRADUCTION FRANÇAISE
        # ====================================================

        try:

            intent_result = (
                predict_intent(
                    french_question
                )
            )

        except Exception as exc:

            print()
            print(
                "❌ ERREUR CAMEMBERT :",
                exc,
            )

            continue

        predicted_intent = (
            intent_result[
                "intent"
            ]
        )

        confidence = float(
            intent_result[
                "confidence"
            ]
        )

        print()
        print("CAMEMBERT")
        print("-" * 100)

        print(
            "Intention prédite :",
            predicted_intent,
        )

        print(
            "Confiance :",
            round(
                confidence,
                4,
            ),
        )

        intent_is_correct = (
            normalized(
                predicted_intent
            )
            == normalized(
                expected_intent
            )
        )

        if intent_is_correct:

            correct_translation_intent += 1

            print(
                "Classification : ✅ PASS"
            )

        else:

            print(
                "Classification : ❌ FAIL"
            )

        # ====================================================
        # C. RETRIEVAL ARABE AVEC OVERRIDE
        # ====================================================

        results = retrieve(
            query=question,
            top_k=3,
            use_intent=False,
            language="ar",
            predicted_intent_override=(
                predicted_intent
            ),
        )

        print()
        print("TOP 3 RAG ARABE")
        print("-" * 100)

        if not results:

            print(
                "Aucun résultat."
            )

            continue

        top1_match = False
        top3_match = False

        for rank, result in enumerate(
            results,
            start=1,
        ):

            result_intent = (
                result.get(
                    "chunk_intent"
                )
            )

            result_theme = (
                result.get(
                    "chunk_theme"
                )
            )

            language = (
                result.get(
                    "language"
                )
            )

            document = (
                result.get(
                    "document"
                )
            )

            source_file = (
                result.get(
                    "source_file"
                )
            )

            semantic_score = (
                result.get(
                    "semantic_score"
                )
            )

            final_score = (
                result.get(
                    "score"
                )
            )

            text = (
                result.get(
                    "text"
                )
            )

            print()
            print(
                f"RANG {rank}"
            )

            print(
                "Langue :",
                language,
            )

            print(
                "Document :",
                document,
            )

            print(
                "Source :",
                source_file,
            )

            print(
                "Intention chunk :",
                result_intent,
            )

            print(
                "Thème :",
                result_theme,
            )

            print(
                "Score sémantique :",
                semantic_score,
            )

            print(
                "Score final :",
                final_score,
            )

            print(
                "Extrait :",
                snippet(
                    text
                ),
            )

            # ---------------------------------------------
            # Vérification stricte de l'intention
            # ---------------------------------------------

            matched = (
                normalized(
                    result_intent
                )
                == normalized(
                    expected_intent
                )
            )

            # ---------------------------------------------
            # Vérification supplémentaire de langue
            # ---------------------------------------------

            if language != "ar":

                print(
                    "⚠️ ERREUR : "
                    "chunk non arabe."
                )

                matched = False

            if matched:

                top3_match = True

                if rank == 1:
                    top1_match = True

        # ====================================================
        # D. RÉSULTAT DU CAS
        # ====================================================

        print()

        if top1_match:

            correct_top1 += 1

            print(
                "Top 1 RAG : ✅ PASS"
            )

        else:

            print(
                "Top 1 RAG : ❌ FAIL"
            )

        if top3_match:

            correct_top3 += 1

            print(
                "Top 3 RAG : ✅ PASS"
            )

        else:

            print(
                "Top 3 RAG : ❌ FAIL"
            )


    # ========================================================
    # 5. RÉSUMÉ GLOBAL
    # ========================================================

    print()
    print("=" * 100)
    print("RÉSUMÉ GLOBAL")
    print("=" * 100)

    print(
        "Classification après traduction : "
        f"{correct_translation_intent}/{total}"
    )

    print(
        "RAG arabe Top 1 : "
        f"{correct_top1}/{total}"
    )

    print(
        "RAG arabe Top 3 : "
        f"{correct_top3}/{total}"
    )

    print()

    if (
        correct_translation_intent == total
        and correct_top1 == total
    ):

        print(
            "✅ PIPELINE ARABE VALIDÉ "
            "SUR LES CAS DE TEST."
        )

    elif (
        correct_translation_intent == total
        and correct_top3 == total
    ):

        print(
            "✅ PIPELINE ARABE VALIDÉ EN TOP 3, "
            "mais le classement Top 1 peut encore "
            "être amélioré."
        )

    else:

        print(
            "⚠️ PIPELINE ARABE ENCORE À AJUSTER."
        )


# ============================================================
# 6. POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":

    run_tests()