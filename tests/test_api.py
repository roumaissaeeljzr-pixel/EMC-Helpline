from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_cyberharassment() -> None:
    response = client.post(
        "/chat",
        json={
            "message": (
                "Je suis victime de cyberharcèlement, "
                "que dois-je faire ?"
            )
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["matched"] is True
    assert data["intent"] == "Cyberharcèlement"
    assert data["faq_code"] == "faq_001"


def test_chat_emergency() -> None:
    response = client.post(
        "/chat",
        json={
            "message": (
                "Je suis en danger et j'ai besoin "
                "d'aide immédiatement"
            )
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["matched"] is True
    assert data["emergency"] is True
    assert data["priority"] == 1


def test_chat_unknown_question() -> None:
    response = client.post(
        "/chat",
        json={
            "message": "Quel temps fera-t-il demain ?"
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["matched"] is False
    assert data["alternatives"] == []


def test_chat_empty_message() -> None:
    response = client.post(
        "/chat",
        json={
            "message": ""
        },
    )

    assert response.status_code == 422


def test_chat_returns_alternatives() -> None:
    response = client.post(
        "/chat",
        json={
            "message": "On me menace avec mes photos intimes"
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["matched"] is True
    assert "alternatives" in data
    assert 1 <= len(data["alternatives"]) <= 3
    assert (
        data["alternatives"][0]["score"]
        >= data["alternatives"][-1]["score"]
    )


def test_faq_endpoint() -> None:
    response = client.get("/faq")

    data = response.json()

    assert response.status_code == 200
    assert data["count"] == 19
    assert len(data["items"]) == 19


def test_categories_endpoint() -> None:
    response = client.get("/categories")

    data = response.json()

    assert response.status_code == 200
    assert data["count"] > 0
    assert "Cyberharcèlement" in data["categories"]