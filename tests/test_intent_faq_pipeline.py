import json
from pathlib import Path

import pytest

from backend.intent_classifier import predict_intent
from backend.search_engine import find_best_faq


BASE_DIR = Path(__file__).resolve().parent.parent

FAQ_FILE = (
    BASE_DIR
    / "knowledge_base"
    / "faq_v2.json"
)


# ============================================================
# CHARGEMENT FAQ
# ============================================================

def load_faq():
    with FAQ_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


FAQ_ITEMS = load_faq()


# ============================================================
# CAS DE TEST
# ============================================================

TEST_CASES = [
    (
        "Quelqu'un m'insulte tous les jours sur Facebook.",
        "Cyberharcèlement",
    ),
    (
        "On menace de publier mes photos privées.",
        "Sextorsion",
    ),
    (
        "Une personne a publié mes photos sans mon accord.",
        "Diffusion non consentie d'images",
    ),
    (
        "Quelqu'un a créé un faux profil avec mon nom.",
        "Usurpation d'identité",
    ),
    (
        "Mon compte Facebook a été piraté.",
        "Piratage de compte",
    ),
    (
        "Comment conserver les captures d'écran comme preuves ?",
        "Conservation des preuves",
    ),
    (
        "Comment puis-je signaler ce contenu ?",
        "Signalement",
    ),
    (
        "Quels sont mes droits dans cette situation ?",
        "Informations juridiques",
    ),
    (
        "J'ai besoin de parler à quelqu'un et d'être accompagné.",
        "Accompagnement de la victime",
    ),
    (
        "Je suis en danger et j'ai besoin d'aide immédiatement.",
        "Situation d'urgence",
    ),
]


# ============================================================
# TEST 1 : CAMEMBERT
# ============================================================

@pytest.mark.parametrize(
    "message, expected_intent",
    TEST_CASES,
)
def test_camembert_intent(
    message,
    expected_intent,
):
    result = predict_intent(message)

    assert result["intent"] == expected_intent

    assert isinstance(
        result["confidence"],
        float,
    )

    assert 0.0 <= result["confidence"] <= 1.0


# ============================================================
# TEST 2 : PIPELINE CAMEMBERT + FAQ
# ============================================================

@pytest.mark.parametrize(
    "message, expected_intent",
    TEST_CASES,
)
def test_intent_faq_pipeline(
    message,
    expected_intent,
):

    # --------------------------------------------------------
    # CamemBERT
    # --------------------------------------------------------

    intent_result = predict_intent(
        message
    )

    predicted_intent = intent_result[
        "intent"
    ]

    # --------------------------------------------------------
    # Search Engine
    # --------------------------------------------------------

    faq_result = find_best_faq(
        message=message,
        faq_items=FAQ_ITEMS,
        minimum_score=35.0,
        predicted_intent=predicted_intent,
    )

    # Une FAQ doit être trouvée
    assert faq_result is not None

    faq = faq_result["faq"]

    # --------------------------------------------------------
    # Vérifications
    # --------------------------------------------------------

    assert predicted_intent == expected_intent

    assert faq.get("intent") == expected_intent

    assert faq.get("validated") is True

    assert faq.get("answer")

    assert faq_result["score"] >= 35.0


# ============================================================
# TEST 3 : COHÉRENCE CAMEMBERT / FAQ
# ============================================================

@pytest.mark.parametrize(
    "message, expected_intent",
    TEST_CASES,
)
def test_camembert_and_faq_are_consistent(
    message,
    expected_intent,
):

    intent_result = predict_intent(
        message
    )

    predicted_intent = intent_result[
        "intent"
    ]

    faq_result = find_best_faq(
        message=message,
        faq_items=FAQ_ITEMS,
        minimum_score=35.0,
        predicted_intent=predicted_intent,
    )

    assert faq_result is not None

    faq_intent = faq_result[
        "faq"
    ].get("intent")

    assert predicted_intent == faq_intent