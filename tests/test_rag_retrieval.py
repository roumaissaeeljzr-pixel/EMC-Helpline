from rag.retriever import retrieve


# ============================================================
# CAS DE TEST
# ============================================================

TEST_CASES = [
    {
        "message": (
            "Quelqu'un m'insulte tous les jours "
            "sur Facebook."
        ),
        "expected_intent": "Cyberharcèlement",
    },
    {
        "message": (
            "On menace de publier mes photos "
            "privées."
        ),
        "expected_intent": "Sextorsion",
    },
    {
        "message": (
            "Une personne a publié mes photos "
            "intimes sans mon accord."
        ),
        "expected_intent": (
            "Diffusion non consentie d'images"
        ),
    },
    {
        "message": (
            "Quelqu'un a créé un faux profil "
            "avec mon nom."
        ),
        "expected_intent": (
            "Usurpation d'identité"
        ),
    },
    {
        "message": (
            "Mon compte Instagram a été piraté."
        ),
        "expected_intent": "Piratage de compte",
    },
    {
        "message": (
            "Comment conserver les captures "
            "d'écran comme preuves ?"
        ),
        "expected_intent": (
            "Conservation des preuves"
        ),
    },
    {
        "message": (
            "Comment puis-je signaler "
            "ce contenu ?"
        ),
        "expected_intent": "Signalement",
    },
    {
        "message": (
            "Quels sont mes droits "
            "dans cette situation ?"
        ),
        "expected_intent": (
            "Informations juridiques"
        ),
    },
    {
        "message": (
            "J'ai besoin de parler à quelqu'un "
            "et d'être accompagné."
        ),
        "expected_intent": (
            "Accompagnement de la victime"
        ),
    },
    {
        "message": (
            "Je suis en danger et j'ai besoin "
            "d'aide immédiatement."
        ),
        "expected_intent": (
            "Situation d'urgence"
        ),
    },
    {
        "message": (
            "Quelqu'un a publié mon adresse "
            "et mon numéro de téléphone "
            "sans mon accord."
        ),
        "expected_intent": (
            "Divulgation de données "
            "personnelles (Doxing)"
        ),
    },
]


# ============================================================
# NORMALISATION
# ============================================================

def normalize(text):
    if text is None:
        return ""

    return str(text).lower().strip()


# ============================================================
# TEST DU RETRIEVER
# ============================================================

def run_tests():

    total = len(TEST_CASES)

    intent_correct = 0
    top1_correct = 0
    top3_correct = 0

    print()
    print("=" * 90)
    print("TEST AUTOMATIQUE DU RETRIEVER RAG")
    print("=" * 90)

    for number, test in enumerate(
        TEST_CASES,
        start=1,
    ):

        message = test["message"]

        expected_intent = test[
            "expected_intent"
        ]

        results = retrieve(
            query=message,
            top_k=5,
            use_intent=True,
        )

        print()
        print("#" * 90)
        print(
            f"TEST {number}/{total}"
        )
        print("#" * 90)

        print(
            "Message :",
            message,
        )

        print(
            "Intention attendue :",
            expected_intent,
        )

        if not results:

            print(
                "❌ Aucun résultat RAG"
            )

            continue

        predicted_intent = results[0].get(
            "predicted_intent"
        )

        print(
            "Intention CamemBERT :",
            predicted_intent,
        )

        # ----------------------------------------------------
        # TEST CLASSIFICATION CAMEMBERT
        # ----------------------------------------------------

        intent_ok = (
            normalize(predicted_intent)
            ==
            normalize(expected_intent)
        )

        if intent_ok:
            intent_correct += 1

        print(
            "CamemBERT :",
            "PASS ✅"
            if intent_ok
            else "FAIL ❌",
        )

        # ----------------------------------------------------
        # TEST TOP 1
        # ----------------------------------------------------

        top1 = results[0]

        top1_intent = top1.get(
            "chunk_intent"
        )

        top1_theme = top1.get(
            "chunk_theme"
        )

        top1_text = normalize(
            top1.get("text")
        )

        expected_normalized = normalize(
            expected_intent
        )

        top1_ok = (
            normalize(top1_intent)
            == expected_normalized
            or expected_normalized
            in normalize(top1_theme)
            or expected_normalized
            in top1_text
        )

        if top1_ok:
            top1_correct += 1

        print()
        print("--- TOP 1 ---")

        print(
            "Document :",
            top1.get("document"),
        )

        print(
            "Thème :",
            top1_theme,
        )

        print(
            "Intent chunk :",
            top1_intent,
        )

        print(
            "Score final :",
            top1.get("score"),
        )

        print(
            "Score sémantique :",
            top1.get(
                "semantic_score"
            ),
        )

        print(
            "Résultat Top 1 :",
            "PASS ✅"
            if top1_ok
            else "FAIL ❌",
        )

        # ----------------------------------------------------
        # TEST TOP 3
        # ----------------------------------------------------

        top3_ok = False

        for result in results[:3]:

            result_intent = normalize(
                result.get(
                    "chunk_intent"
                )
            )

            result_theme = normalize(
                result.get(
                    "chunk_theme"
                )
            )

            result_text = normalize(
                result.get("text")
            )

            if (
                result_intent
                == expected_normalized
                or expected_normalized
                in result_theme
                or expected_normalized
                in result_text
            ):
                top3_ok = True
                break

        if top3_ok:
            top3_correct += 1

        print(
            "Résultat Top 3 :",
            "PASS ✅"
            if top3_ok
            else "FAIL ❌",
        )

        # ----------------------------------------------------
        # AFFICHER TOP 3
        # ----------------------------------------------------

        print()
        print("Top 3 passages :")

        for rank, result in enumerate(
            results[:3],
            start=1,
        ):

            print(
                f"  {rank}. "
                f"{result.get('document')} | "
                f"{result.get('chunk_theme')} | "
                f"score={result.get('score')}"
            )

    # ========================================================
    # RÉSUMÉ
    # ========================================================

    print()
    print("=" * 90)
    print("RÉSUMÉ")
    print("=" * 90)

    print(
        f"Nombre de tests : {total}"
    )

    print(
        "CamemBERT correct : "
        f"{intent_correct}/{total} "
        f"({intent_correct / total * 100:.1f}%)"
    )

    print(
        "Bon passage en Top 1 : "
        f"{top1_correct}/{total} "
        f"({top1_correct / total * 100:.1f}%)"
    )

    print(
        "Bon passage en Top 3 : "
        f"{top3_correct}/{total} "
        f"({top3_correct / total * 100:.1f}%)"
    )


# ============================================================
# EXÉCUTION
# ============================================================

if __name__ == "__main__":
    run_tests()