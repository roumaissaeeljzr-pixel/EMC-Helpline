"""
tests/test_rag_generator.py

Suite de test manuel du pipeline complet EMC Helpline :
CamemBERT -> Retriever RAG -> filtrage par intention -> Llama 3.1.

IMPORTANT (documenté et validé) :
CamemBERT est entraîné sur 11 intentions. "Grooming" et "Cybermenaces"
n'en font PAS partie (voir 01_cyberviolences_et_typologies :
"Intention CamemBERT associée : Aucune association établie parmi
les 11 intentions actuelles"). Les questions correspondantes sont
donc conservées ici à titre de suivi, mais NE SONT PAS comptées
dans l'accuracy du classifieur : les compter comme des erreurs
donnerait une mesure trompeuse d'un modèle sur une tâche qu'il n'a
jamais été entraîné à accomplir.

Si Grooming et Cybermenaces doivent devenir des intentions autonomes
(Option C), il faudra réentraîner CamemBERT avec 13 classes et
déplacer les cas correspondants dans SUPPORTED_TEST_CASES.
"""

from typing import Any

from rag.generator import generate_answer


# ============================================================
# 1. CAS DE TEST — INTENTIONS SUPPORTÉES PAR CAMEMBERT
# ============================================================
#
# Ces 8 cas correspondent à des intentions réellement présentes
# parmi les 11 classes de CamemBERT. Ce sont les seuls cas comptés
# dans l'accuracy du classifieur.

SUPPORTED_TEST_CASES: list[dict[str, str]] = [
    {
        "question": "Je reçois constamment des messages insultants et humiliants sur les réseaux sociaux.",
        "expected_intent": "Cyberharcèlement",
    },
    {
        "question": "On menace de publier mes photos privées.",
        "expected_intent": "Sextorsion",
    },
    {
        "question": "Mon compte Instagram a été piraté. Que dois-je faire ?",
        "expected_intent": "Piratage de compte",
    },
    {
        "question": "Quelqu'un a publié mon adresse et mon numéro de téléphone sans mon accord.",
        "expected_intent": "Divulgation de données personnelles (Doxing)",
    },
    {
        "question": "Comment conserver les preuves d'un cyberharcèlement ?",
        "expected_intent": "Conservation des preuves",
    },
    {
        "question": "Quels sont mes droits si quelqu'un publie mes photos sans mon accord ?",
        "expected_intent": "Informations juridiques",
    },
    {
        "question": "Quelqu'un utilise mon nom et mes photos pour créer un faux compte.",
        "expected_intent": "Usurpation d'identité",
    },
    {
        "question": "Quelqu'un a diffusé mes photos intimes sans mon consentement.",
        "expected_intent": "Diffusion non consentie d'images",
    },
]


# ============================================================
# 2. CAS DE TEST — HORS PÉRIMÈTRE ACTUEL DU CLASSIFIEUR
# ============================================================
#
# Ces intentions ne font pas partie des 11 classes de CamemBERT.
# Elles sont suivies séparément, à titre de documentation des
# limites connues du MVP, et NE SONT PAS comptées dans l'accuracy.

KNOWN_LIMITATION_TEST_CASES: list[dict[str, str]] = [
    {
        "question": "Un adulte contacte un enfant sur Internet avec des intentions sexuelles.",
        "expected_intent": "Grooming",
        "reason": (
            "\"Grooming\" ne fait pas partie des 11 intentions sur "
            "lesquelles CamemBERT a été entraîné."
        ),
    },
    {
        "question": "Quelqu'un me menace sur Internet.",
        "expected_intent": "Cybermenaces",
        "reason": (
            "\"Cybermenaces\" ne fait pas partie des 11 intentions sur "
            "lesquelles CamemBERT a été entraîné."
        ),
    },
]


# ============================================================
# 3. AFFICHAGE D'UN CAS DE TEST
# ============================================================

def run_single_case(
    case: dict[str, str],
    index: int,
    total: int,
    counted_in_accuracy: bool,
) -> bool:
    """
    Exécute un cas de test et affiche le résultat.

    Retourne True si l'intention prédite correspond à l'intention
    attendue, False sinon. Ce résultat n'est utilisé pour le calcul
    de l'accuracy globale que si `counted_in_accuracy` est True.
    """

    question = case["question"]
    expected_intent = case["expected_intent"]

    print()
    print("=" * 100)
    print(f"TEST {index}/{total}" + ("" if counted_in_accuracy else "  [HORS PÉRIMÈTRE CAMEMBERT]"))
    print("=" * 100)
    print("Question :")
    print(question)
    print()
    print("Attendu :", expected_intent)

    if not counted_in_accuracy:
        print("Motif   :", case.get("reason", "Intention non supportée par CamemBERT."))

    result: dict[str, Any] = generate_answer(question)

    predicted_intent = result["predicted_intent"]
    intent_confidence = result["intent_confidence"]

    is_correct = predicted_intent == expected_intent

    print("Prédit  :", predicted_intent)
    print("Confiance :", intent_confidence)

    if counted_in_accuracy:
        print("Résultat :", "✅ CORRECT" if is_correct else "❌ INCORRECT")
    else:
        print(
            "Résultat :",
            "✅ (concorde malgré tout)" if is_correct else "ℹ️ (attendu, hors périmètre du classifieur)",
        )

    print()
    print("Chunks utilisés :", result["retrieved_chunks"])
    print()

    if result.get("clarification_required"):
        print("Clarification demandée avant orientation :")
        print(f"  ({result['clarification_required']})")
        print()

    print("Réponse :")
    print(result["answer"])

    print()
    print("Sources :")

    if not result["sources"]:
        print("Aucune source (clarification demandée ou aucun résultat)." if result.get("clarification_required") else "Aucune source.")
    else:
        for source in result["sources"]:
            print(
                f"- {source.get('theme')} | {source.get('intent')} | page {source.get('page')}"
            )

    return is_correct


# ============================================================
# 4. EXÉCUTION COMPLÈTE
# ============================================================

def run_all_tests() -> None:

    total_supported = len(SUPPORTED_TEST_CASES)
    total_limitations = len(KNOWN_LIMITATION_TEST_CASES)
    total_cases = total_supported + total_limitations

    correct_supported = 0
    limitation_results = []

    # --- Cas supportés : comptés dans l'accuracy ---
    for i, case in enumerate(SUPPORTED_TEST_CASES, start=1):
        is_correct = run_single_case(
            case=case,
            index=i,
            total=total_cases,
            counted_in_accuracy=True,
        )
        if is_correct:
            correct_supported += 1

    # --- Cas hors périmètre : suivis mais non comptés ---
    for j, case in enumerate(
        KNOWN_LIMITATION_TEST_CASES,
        start=total_supported + 1,
    ):
        is_correct = run_single_case(
            case=case,
            index=j,
            total=total_cases,
            counted_in_accuracy=False,
        )
        limitation_results.append((case, is_correct))

    # ========================================================
    # RÉSUMÉ
    # ========================================================

    print()
    print("=" * 100)
    print("RÉSUMÉ DES TESTS")
    print("=" * 100)

    accuracy = (
        (correct_supported / total_supported) * 100
        if total_supported
        else 0.0
    )

    print(
        f"Intentions correctes (supportées par CamemBERT) : "
        f"{correct_supported}/{total_supported}"
    )
    print(f"Accuracy (sur intentions supportées) : {accuracy:.2f}%")

    print()
    print("-" * 100)
    print("CAS HORS PÉRIMÈTRE ACTUEL DU CLASSIFIEUR (non comptés dans l'accuracy)")
    print("-" * 100)
    print(
        "Ces intentions ne font pas partie des 11 classes sur lesquelles "
        "CamemBERT a été entraîné. Elles sont suivies ici à titre de "
        "documentation des limites connues du MVP."
    )

    for case, is_correct in limitation_results:
        status = "concorde malgré tout" if is_correct else "prédiction hors classe attendue (attendu)"
        print(f"- \"{case['expected_intent']}\" -> {status}")

    print()
    print(
        "Si l'entreprise exige explicitement ces intentions comme classes "
        "autonomes, il faudra réentraîner CamemBERT avec 13 classes "
        "(Option C) et déplacer ces cas dans SUPPORTED_TEST_CASES."
    )
    print("=" * 100)


# ============================================================
# 5. POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":
    run_all_tests()