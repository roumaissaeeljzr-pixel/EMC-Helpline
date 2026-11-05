"""
tests/test_rag_generator_arabic.py

Suite de test du pipeline complet EMC Helpline en arabe :
détection de langue -> retrieval sémantique arabe (CamemBERT ignoré,
non fiable sur l'arabe) -> intention dérivée par vote majoritaire ->
Llama 3.1 en arabe.

Miroir exact de tests/test_rag_generator.py (français), mais adapté
pour l'arabe sur trois points :

1. Le champ "intent_confidence" est toujours None en arabe (l'intention
   n'est pas issue d'un classifieur mais d'un vote majoritaire sur le
   contenu récupéré) -- ce n'est pas un défaut, c'est le comportement
   attendu depuis la correction du bug CamemBERT/arabe.

2. Deux cas dédiés vérifient explicitement le mécanisme de
   clarification d'âge (Sextorsion / Diffusion non consentie d'images)
   déclenché sans appel au LLM lorsque l'âge n'est pas précisé.

3. Les mêmes intentions hors périmètre (Grooming, Cybermenaces) sont
   suivies séparément et non comptées dans l'accuracy, pour la même
   raison que côté français : elles ne font partie d'aucune des 11
   intentions taguées dans le corpus, quelle que soit la langue.
"""

from typing import Any

from rag.generator import generate_answer


# ============================================================
# 1. CAS DE TEST — LES 11 INTENTIONS SUPPORTÉES
# ============================================================
#
# Pour Sextorsion et Diffusion non consentie d'images, un signal
# d'âge est inclus dans la question afin d'obtenir une réponse
# complète (le mécanisme de clarification d'âge est testé
# séparément, section 2, avec des questions SANS signal d'âge).

SUPPORTED_TEST_CASES: list[dict[str, str]] = [
    {
        "question": "أتلقى باستمرار رسائل مهينة ومذلة عبر مواقع التواصل الاجتماعي.",
        "expected_intent": "Cyberharcèlement",
    },
    {
        "question": "شخص يهددني بنشر صوري الحميمة، وكنت قاصرًا وقت التقاط تلك الصور.",
        "expected_intent": "Sextorsion",
    },
    {
        "question": "تم اختراق حسابي على إنستغرام. ماذا أفعل؟",
        "expected_intent": "Piratage de compte",
    },
    {
        "question": "قام شخص بنشر عنواني ورقم هاتفي دون موافقتي.",
        "expected_intent": "Divulgation de données personnelles (Doxing)",
    },
    {
        "question": "كيف يمكنني الاحتفاظ بالأدلة على التحرش الإلكتروني؟",
        "expected_intent": "Conservation des preuves",
    },
    {
        "question": "ما هي حقوقي إذا نشر شخص صوري دون موافقتي؟",
        "expected_intent": "Informations juridiques",
    },
    {
        "question": "شخص ينتحل هويتي وينشر صورًا مزيفة باسمي على فيسبوك.",
        "expected_intent": "Usurpation d'identité",
    },
    {
        "question": "نشر شخص صوري الحميمة دون موافقتي، وكنت بالغة وقت التقاط تلك الصور.",
        "expected_intent": "Diffusion non consentie d'images",
    },
    {
        "question": "كيف يمكنني الإبلاغ عن محتوى مسيء منشور على الإنترنت؟",
        "expected_intent": "Signalement",
    },
    {
        "question": "أفكر في إيذاء نفسي ولم تعد لدي القوة على الاستمرار.",
        "expected_intent": "Situation d'urgence",
    },
    {
        "question": "أريد التحدث إلى شخص ما، لا أعرف ماذا أفعل بعد كل هذا.",
        "expected_intent": "Accompagnement de la victime",
    },
]


# ============================================================
# 2. CAS DE TEST — CLARIFICATION D'ÂGE (SANS SIGNAL D'ÂGE)
# ============================================================
#
# Ces questions ne précisent PAS l'âge de la victime au moment des
# faits. Le pipeline doit court-circuiter l'appel au LLM et renvoyer
# une question de clarification déterministe, en arabe, sans choisir
# Take It Down ou StopNCII à la place de l'utilisateur.

AGE_CLARIFICATION_TEST_CASES: list[dict[str, str]] = [
    {
        "question": "شخص يهدد بنشر صوري الخاصة.",
        "expected_intent": "Sextorsion",
    },
    {
        "question": "شخص نشر صوري الحميمة دون موافقتي.",
        "expected_intent": "Diffusion non consentie d'images",
    },
]


# ============================================================
# 3. CAS DE TEST — HORS PÉRIMÈTRE ACTUEL (LES DEUX LANGUES)
# ============================================================
#
# "Grooming" et "Cybermenaces" ne font partie d'aucune des 11
# intentions taguées dans le corpus (français OU arabe) -- voir
# 01_cyberviolences_et_typologies : "Intention CamemBERT associée :
# Aucune association établie parmi les 11 intentions actuelles".
# Suivis ici à titre de documentation, non comptés dans l'accuracy.

KNOWN_LIMITATION_TEST_CASES: list[dict[str, str]] = [
    {
        "question": "شخص بالغ يتواصل مع طفل عبر الإنترنت بنوايا جنسية.",
        "expected_intent": "Grooming",
        "reason": (
            "\"Grooming\" ne fait partie d'aucune des 11 intentions "
            "taguées dans le corpus, en arabe comme en français."
        ),
    },
    {
        "question": "شخص يهددني على الإنترنت.",
        "expected_intent": "Cybermenaces",
        "reason": (
            "\"Cybermenaces\" ne fait partie d'aucune des 11 intentions "
            "taguées dans le corpus, en arabe comme en français."
        ),
    },
]


# ============================================================
# 4. EXÉCUTION D'UN CAS STANDARD
# ============================================================

def run_single_case(
    case: dict[str, str],
    index: int,
    total: int,
    counted_in_accuracy: bool,
) -> bool:

    question = case["question"]
    expected_intent = case["expected_intent"]

    print()
    print("=" * 100)
    print(f"TEST {index}/{total}" + ("" if counted_in_accuracy else "  [HORS PÉRIMÈTRE]"))
    print("=" * 100)
    print("Question :")
    print(question)
    print()
    print("Attendu :", expected_intent)

    if not counted_in_accuracy:
        print("Motif   :", case.get("reason", "Intention non taguée dans le corpus."))

    result: dict[str, Any] = generate_answer(question)

    predicted_intent = result["predicted_intent"]
    detected_language = result.get("language")

    is_correct = predicted_intent == expected_intent
    is_arabic = detected_language == "ar"

    print("Langue détectée :", detected_language, "✅" if is_arabic else "❌ ATTENDU 'ar'")
    print("Prédit  :", predicted_intent)
    print(
        "Confiance :", result["intent_confidence"],
        "(None attendu en arabe -- intention dérivée du contenu, pas de CamemBERT)"
    )

    if counted_in_accuracy:
        print("Résultat :", "✅ CORRECT" if (is_correct and is_arabic) else "❌ INCORRECT")
    else:
        print(
            "Résultat :",
            "✅ (concorde malgré tout)" if is_correct else "ℹ️ (attendu, hors périmètre)",
        )

    print()
    if result.get("emergency_override"):
        print("⚠️  Garde d'urgence déclenchée (mots-clés documentés)")

    print("Chunks utilisés :", result["retrieved_chunks"])
    print()
    print("Réponse :")
    print(result["answer"])

    print()
    print("Sources :")
    if not result["sources"]:
        print("Aucune source.")
    else:
        for source in result["sources"]:
            print(
                f"- {source.get('document')} | langue={source.get('language')} "
                f"| {source.get('theme')} | {source.get('intent')} | page {source.get('page')}"
            )
            if source.get("language") != "ar":
                print("  ⚠️  FUITE DE LANGUE DÉTECTÉE (source non arabe dans une réponse arabe)")

    return is_correct and is_arabic


# ============================================================
# 5. EXÉCUTION D'UN CAS DE CLARIFICATION D'ÂGE
# ============================================================

def run_age_clarification_case(
    case: dict[str, str],
    index: int,
    total: int,
) -> bool:

    question = case["question"]
    expected_intent = case["expected_intent"]

    print()
    print("=" * 100)
    print(f"TEST {index}/{total}  [CLARIFICATION D'ÂGE]")
    print("=" * 100)
    print("Question :")
    print(question)
    print()
    print("Intention attendue :", expected_intent)

    result: dict[str, Any] = generate_answer(question)

    clarification_triggered = result.get("clarification_required") == "age_at_time_of_facts"
    zero_chunks = result.get("retrieved_chunks") == 0
    # Les deux intentions "Sextorsion" et "Diffusion non consentie
    # d'images" partagent le même mécanisme de garde par âge : ce
    # qui est testé ici, c'est que la ressource n'est JAMAIS choisie
    # sans connaître l'âge -- pas la classification exacte de
    # l'intention, qui peut légitimement hésiter entre les deux
    # tellement les scénarios sont proches (menace vs diffusion déjà
    # effective d'un contenu intime).
    AGE_DEPENDENT_INTENTS_FOR_TEST = {
        "Sextorsion",
        "Diffusion non consentie d'images",
    }
    correct_intent = result.get("predicted_intent") in AGE_DEPENDENT_INTENTS_FOR_TEST
    is_arabic_answer = bool(result.get("answer")) and any(
        "\u0600" <= ch <= "\u06FF" for ch in result["answer"]
    )

    passed = clarification_triggered and zero_chunks and correct_intent and is_arabic_answer

    print("Intention détectée :", result.get("predicted_intent"))
    print("Clarification déclenchée :", clarification_triggered)
    print("Chunks utilisés (doit être 0) :", result.get("retrieved_chunks"))
    print("Réponse en arabe :", is_arabic_answer)
    print()
    print("Réponse :")
    print(result["answer"])
    print()
    print("Résultat :", "✅ CORRECT" if passed else "❌ INCORRECT")

    return passed


# ============================================================
# 6. EXÉCUTION COMPLÈTE
# ============================================================

def run_all_tests() -> None:

    total_supported = len(SUPPORTED_TEST_CASES)
    total_age = len(AGE_CLARIFICATION_TEST_CASES)
    total_limitations = len(KNOWN_LIMITATION_TEST_CASES)
    total_cases = total_supported + total_age + total_limitations

    correct_supported = 0
    correct_age = 0
    limitation_results = []

    for i, case in enumerate(SUPPORTED_TEST_CASES, start=1):
        if run_single_case(case, i, total_cases, counted_in_accuracy=True):
            correct_supported += 1

    for j, case in enumerate(
        AGE_CLARIFICATION_TEST_CASES,
        start=total_supported + 1,
    ):
        if run_age_clarification_case(case, j, total_cases):
            correct_age += 1

    for k, case in enumerate(
        KNOWN_LIMITATION_TEST_CASES,
        start=total_supported + total_age + 1,
    ):
        is_correct = run_single_case(
            case, k, total_cases, counted_in_accuracy=False
        )
        limitation_results.append((case, is_correct))

    print()
    print("=" * 100)
    print("RÉSUMÉ DES TESTS ARABE")
    print("=" * 100)

    accuracy = (correct_supported / total_supported * 100) if total_supported else 0.0
    age_accuracy = (correct_age / total_age * 100) if total_age else 0.0

    print(f"Intentions correctes (11 intentions supportées) : {correct_supported}/{total_supported}")
    print(f"Accuracy (intentions supportées) : {accuracy:.2f}%")
    print()
    print(f"Clarifications d'âge correctes : {correct_age}/{total_age}")
    print(f"Accuracy (clarification d'âge) : {age_accuracy:.2f}%")

    print()
    print("-" * 100)
    print("CAS HORS PÉRIMÈTRE ACTUEL (non comptés dans l'accuracy)")
    print("-" * 100)
    for case, is_correct in limitation_results:
        status = "concorde malgré tout" if is_correct else "prédiction hors classe attendue (attendu)"
        print(f"- \"{case['expected_intent']}\" -> {status}")

    print("=" * 100)


if __name__ == "__main__":
    run_all_tests()