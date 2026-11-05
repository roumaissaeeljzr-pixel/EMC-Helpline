import json
from pathlib import Path

from backend.search_engine import (
    find_best_faq,
    find_top_faqs,
)


BASE_DIR = Path(__file__).resolve().parent.parent
FAQ_FILE = BASE_DIR / "knowledge_base" / "faq_v2.json"


def load_faq() -> list[dict]:
    with FAQ_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def test_cyberharassment_search() -> None:
    faq_items = load_faq()

    result = find_best_faq(
        "On m'insulte tous les jours sur Facebook",
        faq_items,
    )

    assert result is not None
    assert result["faq"]["intent"] == "Cyberharcèlement"


def test_emergency_search() -> None:
    faq_items = load_faq()

    result = find_best_faq(
        "Je suis en danger et j'ai besoin d'aide immédiatement",
        faq_items,
    )

    assert result is not None
    assert result["faq"]["emergency"] is True


def test_empty_message() -> None:
    faq_items = load_faq()

    result = find_best_faq(
        "",
        faq_items,
    )

    assert result is None


def test_top_faqs_returns_three_results() -> None:
    faq_items = load_faq()

    results = find_top_faqs(
        "On me menace avec mes photos intimes",
        faq_items,
        limit=3,
    )

    assert 1 <= len(results) <= 3
    assert results[0]["score"] >= results[-1]["score"]


def test_top_faqs_empty_message() -> None:
    faq_items = load_faq()

    results = find_top_faqs(
        "",
        faq_items,
    )

    assert results == []