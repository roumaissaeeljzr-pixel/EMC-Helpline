import re
import unicodedata
from typing import Any

from rapidfuzz import fuzz


def normalize_text(text: str) -> str:
    """
    Normalise le texte :
    - passage en minuscules ;
    - suppression des accents ;
    - suppression de la ponctuation ;
    - réduction des espaces.
    """
    text = text.lower().strip()

    text = unicodedata.normalize("NFD", text)
    text = "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
    )

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def calculate_keyword_score(
    normalized_message: str,
    keywords: list[str],
) -> float:
    """
    Calcule un score selon les mots-clés présents dans le message.
    """
    if not keywords:
        return 0.0

    matched_keywords = 0

    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)

        if normalized_keyword and normalized_keyword in normalized_message:
            matched_keywords += 1

    return (matched_keywords / len(keywords)) * 100


def calculate_faq_score(
    message: str,
    faq: dict[str, Any],
    predicted_intent: str | None = None,
) -> float:
    """
    Calcule le score entre le message utilisateur et une FAQ.

    CamemBERT est utilisé comme bonus uniquement lorsqu'il existe
    déjà un indice textuel suffisant reliant le message à la FAQ.
    """

    normalized_message = normalize_text(message)

    question = normalize_text(
        str(faq.get("question", ""))
    )

    category = normalize_text(
        str(faq.get("category", ""))
    )

    intent = normalize_text(
        str(faq.get("intent", ""))
    )

    keywords = faq.get("keywords", [])
    tags = faq.get("tags", [])

    # =========================================================
    # 1. SCORES TEXTUELS
    # =========================================================

    question_score = fuzz.token_set_ratio(
        normalized_message,
        question,
    )

    category_score = fuzz.partial_ratio(
        normalized_message,
        category,
    )

    intent_score = fuzz.partial_ratio(
        normalized_message,
        intent,
    )

    keyword_score = calculate_keyword_score(
        normalized_message,
        keywords,
    )

    tag_score = calculate_keyword_score(
        normalized_message,
        tags,
    )

    # =========================================================
    # 2. SCORE DE BASE
    # =========================================================

    base_score = (
        question_score * 0.45
        + keyword_score * 0.25
        + tag_score * 0.15
        + intent_score * 0.10
        + category_score * 0.05
    )

    # =========================================================
    # 3. VÉRIFICATION D'UNE VRAIE PREUVE TEXTUELLE
    # =========================================================
    #
    # Une FAQ n'est considérée comme candidate que si :
    #
    # - au moins un keyword correspond,
    # OU
    # - au moins un tag correspond,
    # OU
    # - la question ressemble suffisamment au message.
    #
    # Cela évite qu'un message hors domaine obtienne une FAQ
    # uniquement grâce aux similarités partielles.
    # =========================================================

    strong_text_evidence = (
        keyword_score > 0.0
        or tag_score > 0.0
        or question_score >= 50.0
    )

    if not strong_text_evidence:
        return 0.0

    final_score = base_score

    # =========================================================
    # 4. BONUS CAMEMBERT
    # =========================================================

    if predicted_intent:

        normalized_predicted_intent = normalize_text(
            predicted_intent
        )

        if intent == normalized_predicted_intent:
            final_score += 20.0

    # =========================================================
    # 5. URGENCE
    # =========================================================

    emergency_terms = {
        "danger",
        "urgence",
        "detresse",
    }

    if faq.get("emergency") is True:

        if any(
            term in normalized_message
            for term in emergency_terms
        ):
            final_score += 15.0

    return min(
        round(final_score, 2),
        100.0,
    )


def find_best_faq(
    message: str,
    faq_items: list[dict[str, Any]],
    minimum_score: float = 35.0,
    predicted_intent: str | None = None,
) -> dict[str, Any] | None:
    """
    Retourne la FAQ la plus proche du message utilisateur.

    L'intention prédite par CamemBERT est utilisée
    comme information supplémentaire.
    """

    if not message or not message.strip():
        return None

    best_faq: dict[str, Any] | None = None
    best_score = 0.0

    for faq in faq_items:

        if not isinstance(faq, dict):
            continue

        if faq.get("validated") is not True:
            continue

        score = calculate_faq_score(
            message=message,
            faq=faq,
            predicted_intent=predicted_intent,
        )

        if score > best_score:
            best_score = score
            best_faq = faq

    if (
        best_faq is None
        or best_score < minimum_score
    ):
        return None

    return {
        "score": best_score,
        "faq": best_faq,
    }


def find_top_faqs(
    message: str,
    faq_items: list[dict[str, Any]],
    limit: int = 3,
    minimum_score: float = 20.0,
    predicted_intent: str | None = None,
) -> list[dict[str, Any]]:
    """
    Retourne les FAQ les plus proches du message utilisateur.

    L'intention CamemBERT est utilisée comme bonus,
    mais les autres intentions restent candidates.
    """

    if not message or not message.strip():
        return []

    results: list[dict[str, Any]] = []

    for faq in faq_items:

        if not isinstance(faq, dict):
            continue

        if faq.get("validated") is not True:
            continue

        score = calculate_faq_score(
            message=message,
            faq=faq,
            predicted_intent=predicted_intent,
        )

        if score >= minimum_score:

            results.append(
                {
                    "score": score,
                    "faq": faq,
                }
            )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:limit]