import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.search_engine import (
    find_best_faq,
    find_top_faqs,
)
from backend.intent_classifier import predict_intent
from rag.retriever import retrieve
from rag.generator import generate_answer

app = FastAPI(
    title="EMC Helpline API",
    description="API du chatbot EMC Helpline",
    version="1.0.0",
)


BASE_DIR = Path(__file__).resolve().parent.parent
FAQ_FILE = BASE_DIR / "knowledge_base" / "faq_v2.json"


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Message envoyé par l'utilisateur",
        examples=[
            "Je suis victime de cyberharcèlement, que dois-je faire ?"
        ],
    )


def load_faq() -> list[dict[str, Any]]:
    """
    Charge la base de connaissances depuis faq_v2.json.
    """
    try:
        with FAQ_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Le fichier FAQ est introuvable : {FAQ_FILE}",
        ) from exc

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Le fichier faq_v2.json contient "
                "une erreur de syntaxe JSON."
            ),
        ) from exc

    if not isinstance(data, list):
        raise HTTPException(
            status_code=500,
            detail="Le fichier FAQ doit contenir une liste JSON.",
        )

    return data


@app.get("/")
def root() -> dict[str, str]:
    """
    Route d'accueil de l'API.
    """
    return {
        "message": "Bienvenue dans l'API EMC Helpline",
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """
    Vérifie que l'API fonctionne.
    """
    return {
        "status": "ok",
    }


@app.get("/faq")
def get_all_faq() -> dict[str, Any]:
    """
    Retourne toutes les FAQ validées.
    """
    faq_items = load_faq()

    validated_items = [
        item
        for item in faq_items
        if isinstance(item, dict)
        and item.get("validated") is True
    ]

    return {
        "count": len(validated_items),
        "items": validated_items,
    }


@app.get("/categories")
def get_categories() -> dict[str, Any]:
    """
    Retourne la liste des catégories disponibles.
    """
    faq_items = load_faq()

    categories = sorted(
        {
            item["category"]
            for item in faq_items
            if isinstance(item, dict)
            and item.get("validated") is True
            and item.get("category")
        }
    )

    return {
        "count": len(categories),
        "categories": categories,
    }

@app.post("/predict-intent")
def predict_message_intent(
    request: ChatRequest,
) -> dict[str, Any]:
    """
    Prédit l'intention du message avec CamemBERT.
    """

    try:
        result = predict_intent(
            request.message
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Une erreur est survenue pendant "
                "la prédiction de l'intention."
            ),
        ) from exc

    return {
        "message": request.message,
        "intent": result["intent"],
        "confidence": result["confidence"],
        "model": "CamemBERT",
    }
@app.post("/rag-search")
def rag_search(
    request: ChatRequest,
) -> dict[str, Any]:
    """
    Recherche les passages RAG les plus pertinents
    pour le message utilisateur.

    Cet endpoint sert uniquement à tester le retrieval.
    Il ne génère pas encore de réponse avec un LLM.
    """

    try:
        results = retrieve(
            query=request.message,
            top_k=3,
            use_intent=True,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Une erreur est survenue pendant "
                "la recherche RAG."
            ),
        ) from exc

    if not results:
        return {
            "matched": False,
            "message": request.message,
            "predicted_intent": None,
            "intent_confidence": None,
            "results": [],
        }

    first_result = results[0]

    rag_results = []

    for rank, result in enumerate(
        results,
        start=1,
    ):
        rag_results.append(
            {
                "rank": rank,
                "document": result.get(
                    "document"
                ),
                "page": result.get(
                    "page"
                ),
                "chunk_index": result.get(
                    "chunk_index"
                ),
                "theme": result.get(
                    "chunk_theme"
                ),
                "intent": result.get(
                    "chunk_intent"
                ),
                "score": result.get(
                    "score"
                ),
                "semantic_score": result.get(
                    "semantic_score"
                ),
                "intent_bonus": result.get(
                    "intent_bonus"
                ),
                "theme_bonus": result.get(
                    "theme_bonus"
                ),
                "text": result.get(
                    "text"
                ),
            }
        )

    return {
        "matched": True,
        "message": request.message,
        "predicted_intent": first_result.get(
            "predicted_intent"
        ),
        "intent_confidence": first_result.get(
            "intent_confidence"
        ),
        "results": rag_results,
    }
@app.post("/rag-chat")
def rag_chat(
    request: ChatRequest,
) -> dict[str, Any]:
    """
    Pipeline RAG complet :

    Message utilisateur
        -> CamemBERT
        -> Retriever RAG
        -> sélection des passages
        -> Llama 3.1 via Ollama
        -> réponse finale
    """

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Le message ne peut pas être vide.",
        )

    try:
        result = generate_answer(
            question=message
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Une erreur est survenue pendant "
                "la génération de la réponse RAG."
            ),
        ) from exc

    return {
        "success": True,
        "message": message,

        "predicted_intent": result.get(
            "predicted_intent"
        ),

        "intent_confidence": result.get(
            "intent_confidence"
        ),

        "answer": result.get(
            "answer"
        ),

        "retrieved_chunks": result.get(
            "retrieved_chunks"
        ),

        "sources": result.get(
            "sources",
            [],
        ),

        "model": result.get(
            "model"
        ),
    }

@app.post("/chat")
def chat(
    request: ChatRequest,
) -> dict[str, Any]:

    """
    Pipeline principal EMC Helpline :

    Message
        -> CamemBERT
        -> intention
        -> recherche FAQ
        -> réponse
    """

    faq_items = load_faq()

    # ========================================================
    # 1. PRÉDICTION DE L'INTENTION AVEC CAMEMBERT
    # ========================================================

    intent_result = predict_intent(
        request.message
    )

    predicted_intent = intent_result["intent"]

    intent_confidence = intent_result[
        "confidence"
    ]

    # ========================================================
    # 2. RECHERCHE FAQ GUIDÉE PAR CAMEMBERT
    # ========================================================

    result = find_best_faq(
        message=request.message,
        faq_items=faq_items,
        minimum_score=35.0,
        predicted_intent=predicted_intent,
    )

    # ========================================================
    # 3. TOP FAQ
    # ========================================================

    top_results = find_top_faqs(
        message=request.message,
        faq_items=faq_items,
        limit=3,
        minimum_score=20.0,
        predicted_intent=predicted_intent,
    )

    if result is None:
        return {
            "matched": False,
            "message": request.message,
            "predicted_intent": predicted_intent,
            "intent_confidence": intent_confidence,
            "faq_code": None,
            "category": None,
            "intent": None,
            "priority": None,
            "emergency": False,
            "score": 0.0,
            "answer": (
                "Je suis désolé(e), je n'ai pas trouvé de réponse "
                "suffisamment fiable dans la base validée. "
                "Pouvez-vous reformuler votre question ou contacter "
                "l'EMC-Helpline pour une orientation humaine ?"
            ),
            "source": None,
            "follow_up": [],
            "alternatives": [],
        }

    faq = result["faq"]

    alternatives = [
        {
            "faq_code": item["faq"].get("code"),
            "question": item["faq"].get("question"),
            "category": item["faq"].get("category"),
            "intent": item["faq"].get("intent"),
            "score": item["score"],
        }
        for item in top_results
    ]

    return {
        "matched": True,
        "message": request.message,
        "predicted_intent": predicted_intent,
        "intent_confidence": intent_confidence,
        "faq_code": faq.get("code"),
        "category": faq.get("category"),
        "intent": faq.get("intent"),
        "priority": faq.get("priority"),
        "emergency": faq.get("emergency", False),
        "score": result["score"],
        "answer": faq.get("answer"),
        "source": faq.get("source"),
        "follow_up": faq.get("follow_up", []),
        "alternatives": alternatives,
    }